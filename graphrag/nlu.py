"""Entendimento de frases em português, do zero.

Duas partes:
  1. ATO DE FALA (o que a pessoa quer fazer): Naive Bayes multinomial treinado em graphrag/nlu_corpus.py
     (treino) e medido em frases separadas (teste). Regras de alta precisão corrigem os casos críticos.
  2. ENTIDADES (o que ela falou): preocupações, tipo de pele, preferências, ingredientes (a pedir ou a evitar),
     objetivo, etapa/produto, orçamento, gestação. Casamento de frases com o léxico + nomes do grafo; se nada
     casa, os vetores de palavras (embed.py) aproximam do objetivo mais parecido.
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from . import lexicon
from .data import Catalog
from .embed import WordVectors
from .nlu_corpus import TRAIN
from .slang import FIGURATIVE
from .text import norm, parse_money_cents, stem, stemmed_all, tokens

ACTS = list(TRAIN)
ARTIFACTS = Path(__file__).resolve().parent / "artifacts"

GOAL_PRIORITY = ["acne", "manchas", "anti_idade", "protecao_solar", "skincare_basico", "pele_sensivel",
                 "oleosidade", "suplementos", "higiene_premium"]
# objetivos de saúde (doc 16): do mais específico para o mais amplo
HEALTH_GOALS = ["tosse_seca", "enjoo", "diarreia", "prisao_de_ventre", "dor_de_garganta", "alergia", "azia",
                "dor_de_barriga", "dor_muscular", "dor_de_cabeca", "dor_no_corpo", "tosse", "gripe"]
GOAL_PRIORITY += HEALTH_GOALS


# ====================================================================== 1. ato de fala
def _features(text: str) -> list[str]:
    t = stemmed_all(text)
    return t + [f"{a}_{b}" for a, b in zip(t, t[1:])]


class ActClassifier:
    """Naive Bayes multinomial com suavização de Laplace (α), em Python puro."""

    def __init__(self, alpha: float = 0.4):
        self.alpha = alpha
        self.log_prior: dict[str, float] = {}
        self.log_like: dict[str, dict[str, float]] = {}
        self.default: dict[str, float] = {}
        self.vocab: set[str] = set()

    def fit(self, data: dict[str, list[str]]) -> "ActClassifier":
        counts: dict[str, Counter] = {a: Counter() for a in data}
        for act, texts in data.items():
            for t in texts:
                counts[act].update(_features(t))
        self.vocab = {f for c in counts.values() for f in c}
        n_docs = sum(len(v) for v in data.values())
        V = len(self.vocab)
        for act, c in counts.items():
            self.log_prior[act] = math.log(len(data[act]) / n_docs)
            total = sum(c.values()) + self.alpha * (V + 1)
            self.log_like[act] = {f: math.log((c[f] + self.alpha) / total) for f in self.vocab}
            self.default[act] = math.log(self.alpha / total)
        return self

    def proba(self, text: str) -> dict[str, float]:
        feats = _features(text)
        scores = {}
        for act in self.log_prior:
            s = self.log_prior[act]
            ll = self.log_like[act]
            for f in feats:
                if f in self.vocab:
                    s += ll[f]            # palavra desconhecida não pesa (nem a favor nem contra)
            scores[act] = s
        m = max(scores.values())
        e = {a: math.exp(s - m) for a, s in scores.items()}
        z = sum(e.values())
        return {a: v / z for a, v in e.items()}

    def predict(self, text: str) -> tuple[str, float]:
        p = self.proba(text)
        a = max(p, key=p.get)
        return a, p[a]

    def save(self, path: Path | None = None) -> Path:
        path = path or ARTIFACTS / "nlu_model.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"alpha": self.alpha, "logPrior": self.log_prior, "logLike": self.log_like,
                                    "default": self.default}, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        return path

    @classmethod
    def load(cls, path: Path | None = None) -> "ActClassifier | None":
        path = path or ARTIFACTS / "nlu_model.json"
        if not path.exists():
            return None
        d = json.loads(path.read_text(encoding="utf-8"))
        m = cls(d["alpha"])
        m.log_prior, m.log_like, m.default = d["logPrior"], d["logLike"], d["default"]
        m.vocab = set(next(iter(m.log_like.values())))
        return m


# ====================================================================== 2. entendimento
@dataclass
class Understanding:
    text: str
    act: str = "busca"
    act_confidence: float = 0.0
    goals: list[str] = field(default_factory=list)
    primary_goal: str | None = None
    concerns: list[str] = field(default_factory=list)
    skin: str | None = None
    preferences: list[str] = field(default_factory=list)
    requested_ingredients: list[str] = field(default_factory=list)
    excluded_ingredients: list[str] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)
    product_ids: list[str] = field(default_factory=list)
    budget_cents: int | None = None
    budget_mentioned: bool = False
    pregnancy: bool = False
    cheaper: bool = False
    richer: bool = False
    tier: str | None = None
    want_products: bool = False
    from_vectors: bool = False

    @property
    def has_domain_signal(self) -> bool:
        return bool(self.goals or self.concerns or self.steps or self.requested_ingredients or self.product_ids)


_NEG_CUES = ("sem", "tira", "tirar", "retira", "remove", "evitar", "evita", "nada de", "nada com", "nao quero", "nao use", "sem o", "sem a",
             "nenhum", "nenhuma", "nao quero nada", "livre de", "longe de", "dispenso")
_AFTER_BATH = re.compile(r"\b(depois|antes|apos|pos)\s+(d[oa]\s+)?banho\b")
_NO_ACID = re.compile(r"\b(sem|nada de|nada com|nao quero|nao use|evitar|evita|tira|tirar|livre de|nenhum|nao pode)\s+(os\s+|o\s+)?acidos?\b(?!\s+(hialuronico|ascorbico|folico|acetilsalicilico|tranexamico|azelaico|salicilico|glicolico|mandelico|graxos?|lactico|kojico))")
_CHEAPER = re.compile(r"\b(reduzir o valor|diminuir o preco|diminuir o valor|baixar o preco|baixar o valor|reduzir o preco|ta salgado|esta salgado|muito caro|ta caro|fora do orcamento|pesou no bolso|mais barato|mais barata|mais em conta|mais economico|menor preco|baratinho|economizar|gastar menos|orcamento menor|menos de uns)\b")
_RICHER = re.compile(r"\b(mais top|opcao melhor|algo melhor|top de linha|o melhor que tiver|mais completo|mais completa|gastar mais|aumenta o orcamento|aumentar o orcamento|premium|melhor qualidade|mais caro)\b")
_PREGNANT = re.compile(r"\b(gravida|gestante|gravidez|gestacao|amamentando|amamentacao|lactante|gravidinha)\b")
_TIER = [(re.compile(r"\b(economico|primeiro|mais barato de todos)\b"), "economico"),
         (re.compile(r"\b(essencial|segundo)\b"), "essencial"),
         (re.compile(r"\b(?<!mais )(completo|alternativo|terceiro)\b"), "completo")]
_REPOR = re.compile(r"\b(repor|reposicao|repoe|recompr\w+|comprar de novo|acabando|acabou|acabar|renovar|ficar sem|falta pouco|no fim)\b")
_MED = re.compile(r"\b(remedio|remedios|medicamento|medicamentos|medicacao|medicacoes|uso continuo)\b")
_MY_MEDS = re.compile(r"\b(meus|minhas|meu|minha) (remedio|remedios|medicamento|medicamentos|medicacao|medicacoes)\b|\buso continuo\b")
# "não consigo cagar", "meu nariz não para de escorrer": é sintoma, não negação do que veio antes.
_CANNOT = re.compile(r"\b(nao consigo|nao consigo mais|nao dou conta de|nao para de|nao para)\b")


class Understander:
    def __init__(self, cat: Catalog, wv: WordVectors | None, clf: ActClassifier):
        self.cat, self.wv, self.clf = cat, wv, clf
        self._build_phrase_index()
        self._build_product_index()
        self._goal_vecs = None
        if wv is not None:
            self._goal_vecs = {}
            for g in cat.goals:
                v = wv.vector(tokens(g["label"] + " " + " ".join(g["synonyms"]) + " " + " ".join(cat.concerns[c] for c in g["concerns"])))
                if np.linalg.norm(v) > 0:
                    self._goal_vecs[g["id"]] = v

    # ------------------------------------------------------------ índices
    def _phrase(self, s: str) -> tuple[str, ...]:
        return tuple(stemmed_all(s))

    def _build_phrase_index(self):
        idx: dict[tuple[str, ...], list[tuple[str, str]]] = defaultdict(list)

        def put(text, kind, key):
            ph = self._phrase(text)
            if ph and (kind, key) not in idx[ph]:
                idx[ph].append((kind, key))

        for cid, aliases in lexicon.CONCERN_ALIASES.items():
            for a in aliases:
                put(a, "concern", cid)
            if cid in self.cat.concerns:
                put(self.cat.concerns[cid], "concern", cid)
        for skin, aliases in lexicon.SKIN_ALIASES.items():
            for a in aliases:
                put(a if len(a.split()) > 1 or skin == "mista" else "pele " + a if False else a, "skin", skin)
            put("pele " + skin, "skin", skin)
        for claim, aliases in lexicon.PREFERENCE_ALIASES.items():
            for a in aliases:
                put(a, "pref", claim)
            put(claim, "pref", claim)
        for ing, aliases in lexicon.INGREDIENT_ALIASES.items():
            for a in aliases:
                put(a, "ing", ing)
        for ing in self.cat.ingredients.values():
            put(ing["name"], "ing", ing["id"])
        for g in self.cat.goals:
            for s in g["synonyms"]:
                put(s, "goal", g["id"])
            put(g["label"], "goal", g["id"])
        for brand in sorted({p["brand"] for p in self.cat.products}):
            put(brand, "brand", brand)
        # "pele oleosa" etc.: o casamento mais longo vence (resolvido na varredura)
        self.phrases = dict(idx)
        self.max_len = max(len(k) for k in self.phrases)

    def _build_product_index(self):
        generic = {"de", "da", "do", "com", "e", "para", "em", "na", "no", "a", "o"}
        self.prod_tokens: dict[str, set[str]] = {}
        for p in self.cat.products:
            toks = {stem(t) for t in norm(p["name"]).replace("-", " ").split() if t not in generic}
            self.prod_tokens[p["id"]] = {t for t in toks if not t.isdigit() and len(t) > 1}

    # ------------------------------------------------------------ varredura de entidades
    def _scan(self, text: str):
        text = _AFTER_BATH.sub(" ", norm(text))
        toks = stemmed_all(text)
        i, found = 0, []
        while i < len(toks):
            hit = None
            for L in range(min(self.max_len, len(toks) - i), 0, -1):
                key = tuple(toks[i:i + L])
                if key in self.phrases:
                    hit = (L, self.phrases[key])
                    break
            if hit:
                found.append((i, hit[0], hit[1]))
                i += hit[0]
            else:
                i += 1
        return toks, found

    def _negated(self, toks: list[str], start: int) -> bool:
        window = " ".join(toks[max(0, start - 4):start])
        return any(re.search(r"(^|\s)" + re.escape(" ".join(stemmed_all(c))) + r"(\s|$)", window) for c in _NEG_CUES)

    def match_products(self, text: str, limit: int = 2) -> list[str]:
        q = {stem(t) for t in norm(text).replace("-", " ").split()}
        scored = []
        for pid, pt in self.prod_tokens.items():
            if len(pt) < 2:
                continue
            inter = len(pt & q)
            if inter >= 2 and inter / len(pt) >= 0.7:
                scored.append((inter / len(pt), inter, pid))
        scored.sort(key=lambda x: (-x[0], -x[1], x[2]))
        return [pid for *_, pid in scored[:limit]]

    # ------------------------------------------------------------ interface
    def understand(self, text: str, has_context: bool = False) -> Understanding:
        clean = FIGURATIVE.sub(" ", text)      # "me caguei de medo" não é diarreia
        q = _AFTER_BATH.sub(" ", norm(clean))   # "repuxa depois do banho" é a pele, não o banho
        u = Understanding(text=text)
        toks, found = self._scan(clean)

        concern_hits: Counter = Counter()
        goal_hits: Counter = Counter()
        for start, L, entries in found:
            for kind, key in entries:
                if kind == "concern":
                    concern_hits[key] += 1
                elif kind == "skin":
                    u.skin = u.skin or key
                elif kind == "pref":
                    if key not in u.preferences:
                        u.preferences.append(key)
                elif kind == "ing":
                    if self._negated(toks, start):
                        if key not in u.excluded_ingredients:
                            u.excluded_ingredients.append(key)
                    elif key not in u.requested_ingredients:
                        u.requested_ingredients.append(key)
                elif kind == "goal":
                    goal_hits[key] += 3
        # "sem ácido, por favor": os ácidos esfoliantes saem (salicílico, glicólico, mandélico), não um ingrediente só
        if _NO_ACID.search(q):
            for k in ("acido_salicilico", "acido_glicolico", "acido_mandelico"):   # os esfoliantes; azelaico e tranexâmico só saem se pedidos pelo nome
                if k not in u.excluded_ingredients:
                    u.excluded_ingredients.append(k)
        # "sem fragrância" etc. não podem virar pedido do ingrediente; já são preferências.
        u.concerns = [c for c, _ in concern_hits.most_common()]
        for c, n in concern_hits.items():
            for g in self.cat.goals:
                if c in g["concerns"]:
                    goal_hits[g["id"]] += n / len(g["concerns"])   # objetivo "dono" da preocupação pesa mais
        for pat, step in lexicon.STEP_PATTERNS:
            if re.search(pat, q):
                if step not in u.steps:
                    u.steps.append(step)
        step_goal = {"omega3": "suplementos", "colageno": "suplementos", "magnesio": "suplementos",
                     "vitaminas": "suplementos", "higiene_corpo": "higiene_premium", "higiene_cabelo": "higiene_premium",
                     "higiene_oral": "higiene_premium", "desodorante": "higiene_premium"}
        for s in u.steps:
            if s in step_goal:
                goal_hits[step_goal[s]] += 4
        if re.search(r"\bkit de suplement|\bsuplement", q):
            goal_hits["suplementos"] += 4
        if re.search(r"\bhigiene\b", q):
            goal_hits["higiene_premium"] += 4

        # orçamento, gestação, tendência de preço, faixa
        u.budget_cents = parse_money_cents(text)
        u.budget_mentioned = u.budget_cents is not None
        u.pregnancy = bool(_PREGNANT.search(q))
        u.cheaper = bool(_CHEAPER.search(q))
        u.richer = bool(_RICHER.search(q))
        for pat, tier in _TIER:
            if pat.search(q):
                u.tier = tier
                break
        u.product_ids = self.match_products(text)

        # objetivo: pontua cada um; entram os que chegam perto do melhor; o principal segue a prioridade do projeto
        if goal_hits:
            top = max(goal_hits.values())
            chosen = [g for g, v in goal_hits.items() if v >= 0.75 * top]
            chosen.sort(key=lambda g: GOAL_PRIORITY.index(g) if g in GOAL_PRIORITY else 99)
            u.goals, u.primary_goal = chosen, chosen[0]
        if u.skin is None and u.primary_goal == "pele_sensivel":
            u.skin = "sensível"
        # ingrediente pedido sem objetivo: o objetivo vem das preocupações dos produtos que o contêm
        if not u.goals and u.requested_ingredients:
            tally: Counter = Counter()
            for p in self.cat.products:
                if p["domain"] in ("dermo", "medicamento") and set(p["ingredients"]) & set(u.requested_ingredients):
                    for c in p["concerns"]:
                        for g in self.cat.goals:
                            if c in g["concerns"] and (g["id"] in GOAL_PRIORITY[:7] or g["id"] in HEALTH_GOALS):
                                tally[g["id"]] += 1 / len(g["concerns"])
            if tally:
                top = max(tally.values())
                chosen = sorted([g for g, v in tally.items() if v >= 0.75 * top],
                                key=lambda g: GOAL_PRIORITY.index(g))
                u.goals, u.primary_goal = chosen, chosen[0]
        # vetores: nenhuma pista léxica, tenta o objetivo mais parecido
        if not u.goals and self.wv is not None and self._goal_vecs and re.search(
                r"\b(pele|kit|rotina|cuidar|produto|remedio|medicamento|sintoma|estou com|to com|sinto)", q):
            v = self.wv.vector(tokens(text))
            if np.linalg.norm(v) > 0:
                sims = {g: float(v @ gv) for g, gv in self._goal_vecs.items()}
                best = max(sims, key=sims.get)
                if sims[best] >= 0.55:
                    u.goals, u.primary_goal, u.from_vectors = [best], best, True

        if not u.goals and re.search(r"\b(pele|rosto|skin ?care|skincare)\b", q) and not u.steps:
            u.goals, u.primary_goal = ["skincare_basico"], "skincare_basico"
        # quer lista de produtos (e não kit)?
        wants_kit = bool(re.search(r"\b(kit|rotina|monta|montar|montei|combo|conjunto)\b", q))
        single = bool(re.search(r"\b(me mostra|mostra|mostrar|quais|tem |tem$|ver |procuro|lista)\b", q))
        u.want_products = bool(u.steps) and single and not wants_kit and not u.budget_mentioned
        if u.want_products and u.primary_goal is None:
            u.want_products = True

        # ---- ato de fala
        act, conf = self.clf.predict(clean)
        if _REPOR.search(q) and _MED.search(q):
            act, conf = "repor_medicamento", max(conf, 0.9)
        elif act == "repor_medicamento" and not (_REPOR.search(q) or _MY_MEDS.search(q)):
            act = "busca"                  # "remédio pra dor de cabeça" é busca; reposição precisa de repor/acabar/meus remédios
        if act == "negacao" and _CANNOT.search(q) and (u.has_domain_signal or not has_context):
            act = "busca"                  # "não consigo cagar" é sintoma, não negação do turno anterior
        if act in ("busca", "refinar") and has_context:
            only_modifiers = not (u.goals or u.steps or u.product_ids) or (
                u.goals == ["oleosidade"] and u.skin == "oleosa" and len(u.concerns) <= 1 and len(toks) <= 4)
            if only_modifiers and (u.preferences or u.skin or u.budget_mentioned or u.cheaper or u.richer or
                                   u.excluded_ingredients or u.pregnancy or u.tier):
                act = "refinar"
        if act == "refinar" and not has_context:
            act = "busca" if (u.has_domain_signal or u.budget_mentioned) else "busca"
        if act == "trocar_item" and not (u.steps or u.product_ids or has_context):
            act = "busca" if u.has_domain_signal else act
        if act == "busca" and not u.has_domain_signal and not (u.preferences or u.skin or u.budget_mentioned):
            if conf < 0.5:
                act = "desconhecido"
        u.act, u.act_confidence = act, conf
        return u
