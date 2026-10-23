"""Escopo da busca: de que PRATELEIRA a pessoa está falando.

Resolve o problema "falei higiene bucal e veio sabonete": antes de ranquear, descobre as prateleiras (etapa, tipo de
produto, preocupação) que a frase pede e só deixa entrar produto dessas prateleiras. Três fontes, em ordem:

  1. conceitos escritos à mão (concepts.py) e conceitos AUTOMÁTICOS, um por tipo de produto do catálogo: produto novo
     de um tipo novo já pode ser achado pelo nome do tipo, sem editar nada;
  2. preocupações/ingredientes que o entendimento de frases achou ("pele oleosa", "retinol");
  3. votação da recuperação (BM25 + vetores + grafo): se nada acima casou, as prateleiras dos produtos mais próximos.

Se nada casa, a busca diz que não encontrou (em vez de empurrar produto qualquer). Conceito marcado `absent` vira aviso
"não temos X" e, quando há prateleira vizinha, a lista dela como sugestão.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .concepts import ARTICLES, CONCEPTS, GENERIC, NEGATORS, Concept
from .data import Catalog
from .lexicon import CONCERN_ALIASES, INGREDIENT_ALIASES
from .spell import COMMON
from .text import STOPWORDS, norm, raw_tokens, stem, stemmed_all

POS_ACNE = re.compile(r"marca|mancha|clare|uniform|pos acne|cicatriz|escur")
VOTE_MIN = 0.28          # nota mínima (0..1, relativa ao melhor possível) do melhor produto para a votação valer
VOTE_REL = 0.55          # entra na lista da votação quem tem ao menos esta fração da nota do melhor
MAX_LIST = 24
MED_WORDS = ("remedio", "remedios", "medicamento", "medicamentos", "medicacao", "medicacoes", "farmacia",
             "comprimido", "comprimidos", "capsula", "capsulas", "remedio pra", "remedio para")


@dataclass
class Scope:
    kind: str                                    # shelf | concern | ingredient | goal | vote | absent | unknown
    steps: set[str] = field(default_factory=set)
    concept_filters: list[Concept] = field(default_factory=list)   # união: o produto precisa casar com ALGUM
    concerns: set[str] = field(default_factory=set)
    ingredients: list[str] = field(default_factory=list)
    missing: list[Concept] = field(default_factory=list)
    shelves: list[str] = field(default_factory=list)
    matched_phrases: list[str] = field(default_factory=list)

    @property
    def has_products_scope(self) -> bool:
        return self.kind not in ("unknown",) and bool(self.steps or self.concept_filters or self.concerns or self.ingredients)


def _concept_matches(c: Concept, p: dict, type_norm: str) -> bool:
    if c.steps and not (p["step"] in c.steps or set(p["coversSteps"]) & set(c.steps)):
        return False
    if c.types and not any(t in type_norm for t in c.types):
        return False
    if c.concerns and not (set(p["concerns"]) & set(c.concerns)):
        return False
    return bool(c.steps or c.types or c.concerns)


class ScopeResolver:
    def __init__(self, cat: Catalog, known_words=()):
        self.cat = cat
        self.known = {stem(w) for w in known_words}
        self.type_norm = {p["id"]: norm(p["productType"]) for p in cat.products}
        self._ptext: dict[str, str] = {}
        self.concepts = list(CONCEPTS) + self.auto_concepts(cat)
        self.index: dict[str, list[tuple[tuple[str, ...], Concept]]] = {}
        for c in self.concepts:
            for ph in c.phrases:
                toks = tuple(stemmed_all(ph))
                if toks:
                    self.index.setdefault(toks[0], []).append((toks, c))

    @staticmethod
    def auto_concepts(cat: Catalog) -> list[Concept]:
        """Um conceito por tipo de produto (nome do tipo = frase). Mantém a busca viva para tipos que ninguém cadastrou à mão."""
        seen: dict[str, set[str]] = {}
        for p in cat.products:
            seen.setdefault(norm(p["productType"]), set()).add(p["step"])
        out = []
        for t, steps in sorted(seen.items()):
            out.append(Concept(id=f"tipo:{t}", label=t, phrases=(t,), steps=tuple(sorted(steps)), types=(t,),
                               shelf=t))
        return out + ScopeResolver.health_concepts(cat)

    @staticmethod
    def health_concepts(cat: Catalog) -> list[Concept]:
        """Um conceito por objetivo de saúde (doc 16), tirado do catálogo: frases = sinônimos do objetivo; prateleira =
        etapas dos medicamentos que atendem aquelas preocupações. "Dor de cabeça" traz dipirona e paracetamol e também
        o anti-inflamatório que serve para dor de cabeça. Mais dois conceitos gerais ("remédio" e "dor")."""
        # área de saúde: remédio ou item das linhas de remédio (psyllium e vitamina C viraram suplemento no #40, mas
        # continuam aparecendo na busca do sintoma)
        meds = [p for p in cat.products if p["domain"] == "medicamento" or p["line"].startswith("med_")]
        med_steps = {p["step"] for p in meds}
        out = []

        def steps_for(concerns):
            return tuple(sorted({p["step"] for p in meds if set(p["concerns"]) & set(concerns)}))

        # um conceito por QUEIXA ("dor de cabeça" não traz o antigripal que só serve para febre) ...
        taken: set[str] = set()
        for c in sorted({c for p in meds for c in p["concerns"]} - {"reposicao"}):
            phrases = tuple(sorted({norm(x) for x in CONCERN_ALIASES.get(c, []) + [cat.concerns.get(c, c)]}))
            taken |= set(phrases)
            out.append(Concept(id=f"queixa:{c}", label=cat.concerns.get(c, c), phrases=phrases, steps=steps_for([c]),
                               concerns=(c,), shelf=cat.concerns.get(c, c)))
        # ... e um por objetivo, com os sinônimos que não são de uma queixa só ("antitérmico", "antigripal", "xarope")
        for g in cat.goals:
            if not set(g["required_steps"]) <= med_steps:
                continue
            phrases = tuple(sorted({norm(x) for x in g["synonyms"] + [g["label"]]} - taken))
            if phrases:
                out.append(Concept(id=f"saude:{g['id']}", label=g["label"].lower(), phrases=phrases,
                                   steps=steps_for(g["concerns"]), concerns=tuple(g["concerns"]), shelf=g["label"].lower()))
        all_steps = tuple(sorted(med_steps))
        out.append(Concept(id="remedio", label="medicamentos", phrases=MED_WORDS, steps=all_steps, shelf="medicamentos"))
        pain = ("dor_de_cabeca", "dor_no_corpo", "dor_muscular", "dor_de_barriga", "dor_de_garganta")
        out.append(Concept(id="dor", label="dor", phrases=("dor", "dores", "doendo", "dolorido", "dolorida"),
                           steps=steps_for(pain), concerns=pain, shelf="dor"))
        return out

    # ------------------------------------------------------------ casamento de frases
    def match(self, text: str) -> list[tuple[Concept, str]]:
        toks = stemmed_all(text)
        cand: list[tuple[int, int, int, Concept, str]] = []     # (-tamanho, início, fim, conceito, frase)
        for i, t in enumerate(toks):
            for phrase, c in self.index.get(t, ()):
                n = len(phrase)
                if tuple(toks[i:i + n]) == phrase:
                    nxt = toks[i + n] if i + n < len(toks) else ""
                    if phrase[-1] == "vitamin" and nxt in ("c", "b3", "b5"):
                        continue                                  # "vitamina c" é ingrediente de cosmético, não suplemento
                    prev = toks[i - 1] if i >= 1 else ""
                    prev2 = toks[i - 2] if i >= 2 else ""
                    if prev in NEGATORS or (prev in ARTICLES and prev2 in NEGATORS):
                        continue                                  # "sem perfume", "sem o perfume": preferência, não pedido
                    cand.append((n, i, i + n, c, " ".join(phrase)))
        cand.sort(key=lambda x: (-x[0], x[1]))
        taken: set[int] = set()
        out: list[tuple[int, Concept, str]] = []
        for n, s, e, c, ph in cand:
            if any(k in taken for k in range(s, e)):
                continue
            taken.update(range(s, e))
            out.append((s, c, ph))
        out.sort(key=lambda x: x[0])
        seen, res = set(), []
        for _, c, ph in out:
            if c.id not in seen:
                seen.add(c.id); res.append((c, ph))
        return res

    HYGIENE = {"higiene_corpo", "higiene_cabelo", "higiene_oral", "desodorante"}

    def _refine_concepts(self, present: list[Concept]) -> list[Concept]:
        """Dois ajustes de bom senso: (1) conceito geral perde para o específico da mesma família ("suplemento para os
        ossos" fica com vitaminas); (2) "sabonete" junto de cabelo/boca/desodorante é o sabonete do banho."""
        out = list(present)
        for g in [c for c in out if c.id in GENERIC]:
            if any(o is not g and o.id not in GENERIC and set(o.steps) and set(o.steps) <= set(g.steps) for o in out):
                out.remove(g)
        if any(c.id == "sabonete" for c in out):
            others = [c for c in out if c.id != "sabonete" and c.steps]
            if others and all(set(c.steps) <= self.HYGIENE for c in others):
                out = [c for c in out if c.id != "sabonete"]
                if not any(c.id == "banho" for c in out):
                    out.append(next(c for c in self.concepts if c.id == "banho"))
        return out

    # ------------------------------------------------------------ resolução
    def resolve(self, u, query: str, scores: dict[str, float] | None = None) -> Scope:
        found = self.match(query)
        present = [c for c, _ in found if not c.absent]
        missing = [c for c, _ in found if c.absent]
        present = self._refine_concepts(present)
        if any(c.shelf == "medicamentos" for c in missing):
            present = [c for c in present if c.id not in ("remedio", "dor")]   # "remédio para diabetes": só o aviso
        phrases = [ph for _, ph in found]
        shelves = list(dict.fromkeys(c.shelf for c in present if c.shelf))
        if present and all(not c.steps and not c.types for c in present) and any(c.concerns for c in present):
            return Scope("concern", concerns={x for c in present for x in c.concerns}, missing=missing, shelves=shelves,
                         matched_phrases=phrases)
        if present:
            sc = Scope("shelf", steps={s for c in present for s in c.steps}, concept_filters=present,
                       concerns={x for c in present for x in c.concerns}, missing=missing, shelves=shelves,
                       matched_phrases=phrases)
            # ingrediente pedido junto ("sérum de vitamina c"): afina a lista dentro da prateleira
            sc.ingredients = list(u.requested_ingredients) if len(present) == 1 else []
            return sc
        if missing:
            near = {s for c in missing for s in c.near}
            sh = list(dict.fromkeys(c.shelf for c in missing if c.shelf))
            return Scope("absent", steps=near, concept_filters=[], missing=missing, shelves=sh, matched_phrases=phrases)
        if u.requested_ingredients:
            return Scope("ingredient", ingredients=list(u.requested_ingredients))
        if u.concerns:
            cons = set(u.concerns)
            if {"acne", "manchas"} <= cons and POS_ACNE.search(norm(query)):
                cons = {"manchas"}                              # "marquinhas que ficaram da espinha": quer clarear, não tratar acne
            return Scope("concern", concerns=cons)
        if u.primary_goal:
            g = self.cat.goal_by_id[u.primary_goal]
            return Scope("goal", steps=set(g["required_steps"]) | set(g["optional_steps"]), concerns=set(g["concerns"]))
        # votação da recuperação (só quando toda palavra de conteúdo é conhecida; "fita adesiva" não vira curativo)
        if scores and self._all_known(query):
            top = max(scores.values(), default=0.0)
            if top >= VOTE_MIN:
                ranked = [pid for pid, v in sorted(scores.items(), key=lambda kv: -kv[1]) if v >= VOTE_REL * top][:8]
                mass: dict[str, float] = {}
                for pid in ranked:
                    mass[self.cat.by_id[pid]["step"]] = mass.get(self.cat.by_id[pid]["step"], 0.0) + scores[pid]
                step = max(mass, key=mass.get)
                return Scope("vote", steps={step})
        return Scope("unknown")

    def _all_known(self, query: str) -> bool:
        if not self.known:
            return True
        for w in raw_tokens(query):
            if len(w) < 4 or w.isdigit() or w in STOPWORDS or w in COMMON:
                continue
            if stem(w) not in self.known:
                return False
        return True

    def restore(self, d: dict) -> Scope:
        """Reconstrói o escopo guardado no contexto da conversa (o cliente devolve só ids)."""
        by_id = {c.id: c for c in self.concepts}
        return Scope(d.get("kind", "shelf"), steps=set(d.get("steps", [])),
                     concept_filters=[by_id[i] for i in d.get("concepts", []) if i in by_id],
                     concerns=set(d.get("concerns", [])), ingredients=list(d.get("ingredients", [])))

    # ------------------------------------------------------------ pertencimento
    def has_ing(self, p: dict, ings) -> bool:
        """O produto tem algum desses ingredientes? Vale o cadastro; e também o nome, para o produto recém
        ingerido que ainda não listou o ingrediente."""
        if set(ings) & set(p["ingredients"]):
            return True
        if p["ingredients"]:
            return False                      # cadastro completo: vale só ele ("alternativo ao retinol" não tem retinol)
        text = self._ptext.get(p["id"])
        if text is None:
            text = self._ptext[p["id"]] = " " + norm(p["name"]) + " "
        return any(" " + norm(a) + " " in text for i in ings for a in INGREDIENT_ALIASES.get(i, ()))

    def in_scope(self, scope: Scope, p: dict) -> bool:
        if scope.kind == "shelf":
            return any(_concept_matches(c, p, self.type_norm[p["id"]]) for c in scope.concept_filters)
        if scope.kind == "absent":
            return bool(scope.steps) and (p["step"] in scope.steps or bool(set(p["coversSteps"]) & scope.steps))
        if scope.kind == "ingredient":
            return self.has_ing(p, scope.ingredients)
        if scope.kind == "concern":
            return bool(scope.concerns & set(p["concerns"]))
        if scope.kind in ("goal", "vote"):
            return p["step"] in scope.steps or bool(set(p["coversSteps"]) & scope.steps)
        return False
