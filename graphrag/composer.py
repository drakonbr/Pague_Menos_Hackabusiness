"""Compositor de kits determinístico (regras K1 a K12 do doc 06), em Python.

O que a recuperação (retrieval.py) faz é ORDENAR candidatos; quem decide o que pode entrar num kit são estas regras:
  K1 sem repetir produto, tipo ou etapa coberta · K3 orçamento · K4 interações · K5 fotossensibilizante pede protetor
  K8 três faixas (Econômico < Essencial < Completo no preço) · K13 remédio nunca entra em kit (#40) · K9 no máximo 5 itens · K10 nada no orçamento mostra o mais
  próximo · K12 combinação proibida pedida explicitamente vira aviso.
Mais: ingrediente que a pessoa quer evitar nunca entra; estoque pode ser da loja escolhida. Medicamento NÃO entra em
kit desde 23/10 (K13, #40, regra da Anvisa); as regras de princípio ativo repetido e de anti-inflamatórios seguem no
checador (M1) e nas listas.
"""
from __future__ import annotations

import itertools
import re
from dataclasses import dataclass, field

from .data import STEP_ORDER, Catalog

SPECIALTY = {"acne", "manchas", "sinais_idade", "olheiras", "textura"}
TIER_BONUS = {"intermediario": 2, "premium": 1}   # desempate por faixa de preço; não conta como "item melhor" no Completo
GENERIC_STEPS = ["limpeza", "hidratacao", "protecao_solar", "protecao_corporal"]
NEEDS_CONCERN_MATCH = ["tratamento", "preparo", "complemento"]
GENERIC_ING = {"glicerina", "tensoativo_suave", "filtro_uv", "aloe_vera"}
DEFAULT_REASON = {
    "limpeza": "Limpa a pele sem agredir, primeira etapa da rotina.",
    "preparo": "Prepara a pele para o tratamento.",
    "tratamento": "Tratamento focado no objetivo escolhido.",
    "hidratacao": "Mantém a pele hidratada e protege a barreira.",
    "protecao_solar": "Proteção diária contra o sol, etapa essencial.",
    "protecao_corporal": "Proteção solar para o corpo.",
    "complemento": "Cuidado complementar para áreas específicas.",
    "omega3": "Suplemento de ômega 3 para a rotina diária.",
    "colageno": "Suplemento de colágeno para a rotina diária.",
    "magnesio": "Suplemento de magnésio para a rotina diária.",
    "vitaminas": "Complemento de vitaminas para a rotina diária.",
    "higiene_corpo": "Higiene do banho com toque premium.",
    "higiene_cabelo": "Cuidado diário com os cabelos.",
    "higiene_oral": "Higiene bucal completa.",
    "desodorante": "Desodorante de uso diário.",
}


# Desconto do kit (#30): proporcional ao tamanho, sempre abaixo da soma avulsa, sem exagero.
KIT_DISCOUNT_PCT = {2: 10, 3: 12}        # 4 ou mais itens: 15%; 1 item: sem desconto
MAX_KIT_DISCOUNT_PCT = 15


def kit_discount_pct(n_items: int) -> int:
    return 0 if n_items < 2 else KIT_DISCOUNT_PCT.get(n_items, MAX_KIT_DISCOUNT_PCT)


def kit_price(items_cents: int, n_items: int) -> tuple[int, int, int]:
    """(desconto %, desconto em centavos, total) do kit a partir da soma avulsa."""
    pct = kit_discount_pct(n_items)
    off = (items_cents * pct + 50) // 100          # meio centavo para cima, igual ao app (Math.floor(x + 0.5))
    return pct, off, items_cents - off


_DOSE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(mcg|mg|g|ui|%)(?![a-z])", re.I)
_TO_MG = {"mcg": 0.001, "mg": 1, "g": 1000}


def dose(name: str) -> tuple[float, str] | None:
    """Primeira dose do nome: (valor, unidade), com mcg/mg/g em mg. "Dipirona 1 g — 10 comprimidos" -> (1000, "mg")."""
    # ponytail: só a primeira dose conta; em combinações (ex.: "Dipirona 300 mg + Orfenadrina") vale o 1º ativo.
    # Basta porque better_item exige os mesmos ativos; com doses por ativo no cadastro, comparar todas.
    m = _DOSE.search(name)
    if not m:
        return None
    v, u = float(m.group(1).replace(",", ".")), m.group(2).lower()
    return (v * _TO_MG[u], "mg") if u in _TO_MG else (v, u)


def kit_cashback(items_cashback: int, pct: int) -> int:
    """Cashback do kit: o dos itens, reduzido na proporção do desconto (cashback sobre o que a pessoa paga)."""
    return items_cashback * (100 - pct) // 100


def list_pt(items: list[str]) -> str:
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " e " + items[-1]


@dataclass
class Ctx:
    goals: list[str]
    primary: str
    concerns: set[str]
    primary_concerns: set[str]
    skin: str | None
    assumed_skin: str | None
    prefs: list[str]
    pregnancy: bool
    budget: int | None
    requested: list[str] = field(default_factory=list)
    excluded: list[str] = field(default_factory=list)
    store_id: str | None = None
    rel: dict[str, float] = field(default_factory=dict)   # nota 0..1 da recuperação, por produto
    w_rel: float = 6.0

    @property
    def eff_skin(self) -> str | None:
        return self.skin or self.assumed_skin


def build_ctx(cat: Catalog, intent: dict, requested=(), excluded=(), rel=None, w_rel=6.0) -> Ctx | None:
    if not intent.get("primaryGoal"):
        return None
    defs = [cat.goal_by_id[g] for g in intent["goals"] if g in cat.goal_by_id]
    pdef = cat.goal_by_id[intent["primaryGoal"]]
    skin = intent.get("skinType")
    assumed = None
    if not skin:
        assumed = {"acne": "oleosa", "oleosidade": "oleosa", "pele_sensivel": "sensível"}.get(intent["primaryGoal"])
    return Ctx(goals=list(intent["goals"]), primary=intent["primaryGoal"],
               concerns={c for g in defs for c in g["concerns"]}, primary_concerns=set(pdef["concerns"]),
               skin=skin, assumed_skin=assumed, prefs=list(intent.get("preferences", [])),
               pregnancy=bool(intent.get("pregnancy")), budget=intent.get("budgetCents"),
               requested=list(requested), excluded=list(excluded), store_id=intent.get("storeId"),
               rel=rel or {}, w_rel=w_rel)


class Composer:
    def __init__(self, cat: Catalog):
        self.cat = cat
        self.pool = list(cat.products)
        # K13 (#40, regra da Anvisa): remédio nunca entra em kit nem na troca de item; continua nas listas de produtos
        self.kit_pool = [p for p in self.pool if p["domain"] != "medicamento"]

    # ------------------------------------------------------------ elegibilidade e nota
    def stock(self, p: dict, ctx: Ctx) -> int:
        return self.cat.stock_at(p["id"], ctx.store_id)

    def base_eligible(self, p: dict, ctx: Ctx, relax_skin: bool = False) -> bool:
        if self.stock(p, ctx) <= 0:
            return False
        if ctx.pregnancy and "consultar_se_gestante" in p["warnings"]:
            return False
        if ctx.excluded and set(ctx.excluded) & set(p["ingredients"]):
            return False
        if not all(pref in p["claims"] for pref in ctx.prefs):
            return False
        if not relax_skin:
            skin = ctx.eff_skin
            if skin and not ("todas" in p["skinTypes"] or skin in p["skinTypes"]):
                return False
        return True

    def score(self, p: dict, ctx: Ctx) -> float:
        s = 0.0
        for c in p["concerns"]:
            if c in ctx.primary_concerns:
                s += 10
            elif c in ctx.concerns:
                s += 6
        skin = ctx.eff_skin
        if skin:
            if skin in p["skinTypes"]:
                s += 6
            elif "todas" in p["skinTypes"]:
                s += 3
        elif "todas" in p["skinTypes"]:
            s += 2
        if skin == "oleosa" and "oil free" in p["claims"]:
            s += 3
        if "não comedogênico" in p["claims"]:
            s += 1
        for ing in ctx.requested:
            if ing in p["ingredients"]:
                s += 12
        s += TIER_BONUS.get(p["priceTier"], 0)
        s += ctx.w_rel * ctx.rel.get(p["id"], 0.0)       # desempate pela recuperação (BM25 + vetores + grafo)
        return round(s, 3)

    def _cmp(self, ctx: Ctx):
        return lambda p: (-self.score(p, ctx), p["priceCents"], p["id"])

    def specialty_mismatch(self, p: dict, ctx: Ctx) -> bool:
        return any(c in SPECIALTY and c not in ctx.concerns for c in p["concerns"])

    def kit_possible(self, goal_id: str) -> bool:
        """K13: o objetivo só tem kit se toda etapa obrigatória tem algum produto que não é remédio (dor de cabeça: não)."""
        steps = self.cat.goal_by_id[goal_id]["required_steps"]
        return all(any(s in p["coversSteps"] for p in self.kit_pool) for s in steps)

    def candidates_for(self, step: str, ctx: Ctx) -> tuple[list[dict], bool]:
        pool = [p for p in self.kit_pool if step in p["coversSteps"]]

        def filt(relax: bool):
            base = [p for p in pool if self.base_eligible(p, ctx, relax)
                    and (step not in NEEDS_CONCERN_MATCH or any(c in ctx.concerns for c in p["concerns"]))]
            if step not in GENERIC_STEPS:
                return base
            clean = [p for p in base if not self.specialty_mismatch(p, ctx)]
            return clean if len(clean) >= 3 else base

        strict = filt(False)
        if strict:
            return strict, False
        return filt(True), True

    def shortlist(self, lst: list[dict], ctx: Ctx) -> list[dict]:
        top = sorted(lst, key=self._cmp(ctx))[:4]
        cheapest = sorted(lst, key=lambda p: (p["priceCents"], p["id"]))[:3]
        seen, out = set(), []
        for p in top + cheapest:
            if p["id"] not in seen:
                seen.add(p["id"]); out.append(p)
        return out

    # ------------------------------------------------------------ interações (K4)
    def conflict_between(self, p: dict, q: dict) -> dict | None:
        if p["domain"] == q["domain"] == "medicamento":
            same = set(p["ingredients"]) & set(q["ingredients"])
            if same:
                name = self.cat.ingredients[sorted(same)[0]]["name"].lower()
                return {"severity": "evitar", "reason": f"Os dois têm {name}; o kit não repete princípio ativo."}
        if p["step"] == "limpeza" or q["step"] == "limpeza":
            return None
        for a in p["ingredients"]:
            for b in q["ingredients"]:
                hit = self.cat.interaction_map.get((a, b))
                if not hit:
                    continue
                if hit["severity"] == "evitar":
                    return {"severity": "evitar", "reason": hit["reason"]}
                ok = {p["usagePeriod"], q["usagePeriod"]} == {"dia", "noite"}
                if not ok:
                    return {"severity": "separar", "reason": hit["reason"]}
        return None

    @staticmethod
    def is_photo(p: dict) -> bool:
        return "fotossensibilizante" in p["warnings"]

    # ------------------------------------------------------------ enumeração (K1 a K9)
    def enumerate(self, steps: list[str], cand: dict[str, list[dict]], ctx: Ctx, max_budget: int | None) -> list[dict]:
        ordered = sorted(steps, key=STEP_ORDER.index)
        out: list[dict] = []
        chosen: list[tuple[str, dict]] = []
        covered: set[str] = set()

        def rec(i: int, total: int):
            if i == len(ordered):
                if any(self.is_photo(p) for _, p in chosen) and "protecao_solar" not in covered:
                    return                                   # K5
                if len(chosen) > 5:
                    return                                   # K9
                kit_total = kit_price(total, len(chosen))[2]
                if max_budget is not None and kit_total > max_budget:
                    return                                   # K3 (com o desconto do kit)
                rel = sum(self.score(p, ctx) for _, p in chosen)
                for x in range(len(chosen)):
                    for y in range(x + 1, len(chosen)):
                        if chosen[x][1]["brand"] == chosen[y][1]["brand"]:
                            rel += 2
                tier = sum(TIER_BONUS.get(p["priceTier"], 0) for _, p in chosen)
                out.append({"slots": list(chosen), "total": kit_total, "rel": rel, "relq": rel - tier,
                            "ids": [p["id"] for _, p in chosen]})
                return
            step = ordered[i]
            if step in covered:
                rec(i + 1, total)
                return
            for p in cand.get(step, []):
                if max_budget is not None and kit_price(total + p["priceCents"], 5)[2] > max_budget:
                    continue                                 # K3: nem com o maior desconto cabe
                if any(s in covered for s in p["coversSteps"]):
                    continue                                 # K1
                if any(c["id"] == p["id"] or c["productType"] == p["productType"] for _, c in chosen):
                    continue                                 # K1
                if any(self.conflict_between(c, p) for _, c in chosen):
                    continue                                 # K4
                chosen.append((step, p))
                added = [s for s in p["coversSteps"] if s not in covered]
                covered.update(added)
                rec(i + 1, total + p["priceCents"])
                covered.difference_update(added)
                chosen.pop()

        rec(0, 0)
        return out

    # ------------------------------------------------------------ textos
    def explain_item(self, p: dict, ctx: Ctx, step: str) -> str:
        cat = self.cat
        matched = [cat.concerns.get(c, c) for c in p["concerns"] if c in ctx.concerns]
        actives = [cat.ingredients[i]["name"].lower() for i in p["ingredients"]
                   if i not in GENERIC_ING and i in cat.ingredients][:2]
        parts = []
        if matched:
            parts.append(f"Atende {list_pt(matched[:3])}" + (f", com {list_pt(actives)}" if actives else "") + ".")
        elif actives:
            parts.append(f"Com {list_pt(actives)}.")
        if p["fps"]:
            parts.append(f"FPS {p['fps']}.")
        skin = ctx.eff_skin
        if skin and p["domain"] == "dermo" and skin in p["skinTypes"]:
            parts.append(f"Indicado para pele {skin}.")
        if len(p["coversSteps"]) > 1 and "protecao_solar" in p["coversSteps"]:
            parts.append("Cobre também a proteção solar, sem item extra.")
        if p.get("rx"):
            parts.append("Venda sob prescrição.")
        return " ".join(parts) if parts else DEFAULT_REASON.get(step, "Item da rotina.")

    def build_alerts(self, prods: list[dict]) -> list[dict]:
        cat = self.cat
        alerts, by_code = [], {}
        for p in prods:
            for w in p["warnings"]:
                by_code.setdefault(w, []).append(p["id"])
        for code, pids in by_code.items():
            sev = "atencao" if code in ("fotossensibilizante", "consultar_se_gestante", "consultar_se_medicacao") else "info"
            alerts.append({"code": code, "severity": sev, "text": cat.warnings[code], "productIds": pids})
        for x in range(len(prods)):
            for y in range(x + 1, len(prods)):
                p, q = prods[x], prods[y]
                if p["step"] == "limpeza" or q["step"] == "limpeza":
                    continue
                for a in p["ingredients"]:
                    for b in q["ingredients"]:
                        hit = cat.interaction_map.get((a, b))
                        if hit and hit["severity"] == "separar":
                            day = p if p["usagePeriod"] == "dia" else q
                            night = q if day is p else p
                            alerts.append({"code": "interacao_separar_periodos", "severity": "info",
                                           "text": f"Use {day['name']} de dia e {night['name']} à noite. {hit['reason']}",
                                           "productIds": [p["id"], q["id"]]})
        covered = {s for p in prods for s in p["coversSteps"]}
        if any(self.is_photo(p) for p in prods) and "protecao_solar" not in covered:
            alerts.append({"code": "sem_protetor_no_kit", "severity": "atencao",
                           "text": "Este kit inclui produto que aumenta a sensibilidade ao sol e não tem protetor solar. Use protetor durante o dia."})
        return sorted(alerts, key=lambda a: 0 if a["severity"] == "atencao" else 1)

    def cashback(self, p: dict) -> int:
        return (p["priceCents"] * p["cashbackPct"]) // 100

    def rationale(self, tier: str, steps: list[str], ctx: Ctx) -> str:
        labels = list_pt([self.cat.steps[s].lower() for s in steps])
        if tier == "economico":
            return f"Menor preço que cobre {labels}."
        if tier == "essencial":
            goal = self.cat.goal_by_id[ctx.primary]["label"].lower()
            return f"Seleção mais indicada para {goal}" + (", dentro do orçamento" if ctx.budget is not None else "") + "."
        return f"A opção mais completa: cobre {labels}."

    @staticmethod
    def better_item(a: dict, b: dict) -> bool:
        """b é versão superior de a: mesmo tipo, preço maior e FPS estritamente maior (protetor) ou, com os mesmos ativos,
        dose maior lida do nome (ex.: dipirona 500 mg -> 1 g). Sabor, embalagem maior ou marca de referência não contam."""
        if a["productType"] != b["productType"] or b["priceCents"] <= a["priceCents"]:
            return False
        if a.get("fps") or b.get("fps"):
            return (b.get("fps") or 0) > (a.get("fps") or 0)
        da, db = dose(a["name"]), dose(b["name"])
        return set(a["ingredients"]) == set(b["ingredients"]) and da is not None and db is not None \
            and da[1] == db[1] and db[0] > da[0]

    def upgrade(self, base: dict, c: dict) -> bool:
        """Mesma quantidade e mesmas etapas, cada item igual ou em versão superior, e pelo menos um superior."""
        a, b = dict(base["slots"]), dict(c["slots"])
        if a.keys() != b.keys():
            return False
        ups = [s for s in a if a[s]["id"] != b[s]["id"]]
        return bool(ups) and all(self.better_item(a[s], b[s]) for s in ups)

    def variant(self, base: dict, c: dict) -> bool:
        """c só troca itens de base por variações do mesmo item (mesmo tipo e ativos: embalagem, sabor), sem versão superior.
        Ex.: psyllium 10 -> 30 sachês. Não serve de Completo para esse Essencial."""
        a, b = dict(base["slots"]), dict(c["slots"])
        if a.keys() != b.keys():
            return False
        ups = [s for s in a if a[s]["id"] != b[s]["id"]]
        return bool(ups) and all(a[s]["productType"] == b[s]["productType"] and set(a[s]["ingredients"]) == set(b[s]["ingredients"])
                                 and not self.better_item(a[s], b[s]) for s in ups)

    def complete_rationale(self, base: dict, comp: dict, base_name: str) -> str:
        """Diz o que o Completo tem a mais que a faixa anterior, sem prometer o que a regra não garante (#31)."""
        extra = len(comp["ids"]) - len(base["ids"])
        if extra > 0:
            return f"A opção mais completa: {extra} {'item' if extra == 1 else 'itens'} a mais que o {base_name}."
        if self.upgrade(base, comp):
            return f"Os mesmos tipos de item do {base_name}, em versões superiores (ex.: dose ou proteção maior)."
        return f"Itens com maior relevância para o seu pedido que os do {base_name}."

    def assemble(self, tier: str, slots: list[tuple[str, dict]], ctx: Ctx, request_id: str,
                 full: dict[str, list[dict]]) -> dict:
        slots = sorted(slots, key=lambda s: STEP_ORDER.index(s[0]))
        items = [{"step": st, "product": p, "reason": self.explain_item(p, ctx, st),
                  "alternativesCount": max(0, len(full.get(st, [p])) - 1)} for st, p in slots]
        return self._totals({
            "id": f"k_{request_id}_{tier}", "tier": tier, "title": self.cat.goal_by_id[ctx.primary]["label"],
            "goal": ctx.primary, "items": items, "storeId": ctx.store_id,
            "rationale": self.rationale(tier, [i["step"] for i in items], ctx)}, ctx)

    def _totals(self, kit: dict, ctx: Ctx) -> dict:
        prods = [i["product"] for i in kit["items"]]
        items_cents = sum(p["priceCents"] for p in prods)
        kit["itemsTotalCents"] = items_cents              # soma avulsa (preço de cada item hoje)
        kit["discountPct"], kit["discountCents"], kit["totalCents"] = kit_price(items_cents, len(prods))
        kit["listTotalCents"] = sum(p["listPriceCents"] for p in prods)
        kit["withinBudget"] = True if ctx.budget is None else kit["totalCents"] <= ctx.budget
        kit["cashbackCents"] = kit_cashback(sum(self.cashback(p) for p in prods), kit["discountPct"])
        kit["alerts"] = self.build_alerts(prods)
        return kit

    # ------------------------------------------------------------ composição (K8 e K10)
    def compose(self, ctx: Ctx, request_id: str) -> dict:
        goal = self.cat.goal_by_id[ctx.primary]
        notes: list[str] = []
        full: dict[str, list[dict]] = {}
        short: dict[str, list[dict]] = {}
        relaxed = []
        for step in goal["required_steps"] + goal["optional_steps"]:
            lst, r = self.candidates_for(step, ctx)
            if not lst:
                continue
            if r:
                relaxed.append(step)
            full[step] = lst
            short[step] = self.shortlist(lst, ctx)
        required = goal["required_steps"]
        if any(s not in short for s in required):
            return {"status": "not_applicable", "kits": [], "closestKit": None,
                    "notes": ["Não encontramos produtos suficientes para montar um kit completo com essas preferências."]}
        for s in [x for x in relaxed if x in required]:
            if s in ("limpeza", "preparo", "tratamento", "hidratacao", "protecao_solar", "protecao_corporal", "complemento"):
                notes.append(f"Há poucos produtos de {self.cat.steps[s].lower()} para pele {ctx.eff_skin}; incluímos o mais próximo.")

        all_req = self.enumerate(required, short, ctx, None)
        if not all_req:
            return {"status": "not_applicable", "kits": [], "closestKit": None,
                    "notes": ["Não foi possível montar um kit compatível."]}
        key_cheap = lambda c: (c["total"], -c["rel"], ",".join(c["ids"]))
        key_best = lambda c: (-c["rel"], c["total"], ",".join(c["ids"]))
        econ = sorted(all_req, key=key_cheap)[0]

        if ctx.budget is not None and econ["total"] > ctx.budget:
            return {"status": "none_in_budget", "kits": [],
                    "closestKit": self.assemble("economico", econ["slots"], ctx, request_id, full), "notes": []}

        eff = ctx.budget if ctx.budget is not None else round(econ["total"] * 2.0)
        alt_b = ctx.budget if ctx.budget is not None else round(econ["total"] * 2.4)
        max_b = max(eff, alt_b)
        optional = [s for s in goal["optional_steps"] if s in short]
        # toda combinação de opcionais que cabe no limite de 5 itens (K9), das maiores para as menores
        # ponytail: refaz a enumeração por subconjunto; com muitas opcionais, enumerar uma vez com "pular opcional"
        room = max(0, 5 - len(required))
        opt_sets = [list(c) for k in range(min(room, len(optional)), -1, -1) for c in itertools.combinations(optional, k)]

        # #31: Econômico < Essencial < Completo no preço. Completo = mais itens (etapas opcionais) e, no empate, itens
        # mais relevantes; pode repetir itens do Essencial. Essencial = o mais relevante entre os dois em preço.
        pool, ids_seen = [], set()
        for st in opt_sets:
            for c in ([c for c in all_req if c["total"] <= max_b] if not st else self.enumerate(required + st, short, ctx, max_b)):
                if tuple(sorted(c["ids"])) not in ids_seen:
                    ids_seen.add(tuple(sorted(c["ids"]))); pool.append(c)
        n = lambda c: len(c["ids"])
        comp_c = [c for c in pool if econ["total"] < c["total"] <= alt_b]
        key_full = lambda c: (-n(c), -c["rel"], c["total"], ",".join(c["ids"]))
        comp = sorted(comp_c, key=key_full)[0] if comp_c else None
        ess_c = [c for c in pool if econ["total"] < c["total"] <= eff
                 and (comp is None or (c["total"] < comp["total"]
                                       and (n(c) < n(comp) or (c["relq"] < comp["relq"] and not self.variant(c, comp)))))]
        ess = sorted(ess_c, key=key_best)[0] if ess_c else None
        if comp and not ess:
            # sem meio-termo (ex.: só kits de 2 itens): Essencial = o mais relevante; Completo = mais itens ou a mesma
            # cesta em versão superior (upgrade). Se não houver, fica o Completo do passo anterior, sem Essencial.
            ess_c = [c for c in pool if econ["total"] < c["total"] <= eff]
            e2 = sorted(ess_c, key=key_best)[0] if ess_c else None
            up = [c for c in pool if e2 and e2["total"] < c["total"] <= alt_b and (n(c) > n(e2) or self.upgrade(e2, c))]
            if up:
                ess, comp = e2, sorted(up, key=key_full)[0]
        if comp and not ess and not (n(comp) > n(econ) or self.upgrade(econ, comp)):
            ess, comp = comp, None            # 2º kit sem nada "a mais" que o Econômico: é um Essencial, não um Completo

        kits = [self.assemble("economico", econ["slots"], ctx, request_id, full)]
        if ess:
            kits.append(self.assemble("essencial", ess["slots"], ctx, request_id, full))
        if comp:
            kits.append(self.assemble("completo", comp["slots"], ctx, request_id, full))
            kits[-1]["rationale"] = self.complete_rationale(ess or econ, comp, "Essencial" if ess else "Econômico")
        for i in self.cat.interactions:                                                      # K12
            if i["severity"] == "evitar" and i["a"] in ctx.requested and i["b"] in ctx.requested:
                an, bn = self.cat.ingredients[i["a"]]["name"], self.cat.ingredients[i["b"]]["name"]
                notes.append(f"{an} e {bn.lower()} não entram no mesmo kit. {i['reason']}")
        if len(kits) == 1:
            notes.append("Só encontramos uma combinação relevante para esse pedido.")
        return {"status": "ok" if len(kits) >= 2 else "partial", "kits": kits, "closestKit": None, "notes": notes}

    # ------------------------------------------------------------ lista de produtos
    def rank_products(self, ctx: Ctx | None, steps: list[str], rel: dict[str, float], limit: int = 12,
                      prefs=(), excluded=(), store_id=None, skin=None, pregnancy=False, w_rel=1.0) -> list[dict]:
        probe = ctx or Ctx(goals=[], primary="", concerns=set(), primary_concerns=set(), skin=skin, assumed_skin=None,
                           prefs=list(prefs), pregnancy=pregnancy, budget=None, excluded=list(excluded),
                           store_id=store_id, rel=rel, w_rel=w_rel)
        pool = [p for p in self.pool if (not steps or any(s in p["coversSteps"] for s in steps))]
        strict = [p for p in pool if self.base_eligible(p, probe, False)]
        use = strict if len(strict) >= min(3, len(pool)) else [p for p in pool if self.base_eligible(p, probe, True)]
        def key(p):
            return (-(probe.w_rel * 10 * rel.get(p["id"], 0.0) + (self.score(p, ctx) if ctx else 0)), p["priceCents"], p["id"])
        return sorted(use, key=key)[:limit]

    # ------------------------------------------------------------ troca de item
    def _covered(self, prods: list[dict]) -> set[str]:
        return {s for p in prods for s in p["coversSteps"]}

    def swap_compat(self, kit: dict, idx: int, cand: dict) -> dict | None:
        others = [i["product"] for k, i in enumerate(kit["items"]) if k != idx]
        cov_o = self._covered(others)
        if any(s in cov_o for s in cand["coversSteps"]):
            return None
        if any(o["productType"] == cand["productType"] for o in others):
            return None
        before = self._covered([i["product"] for i in kit["items"]])
        after = cov_o | set(cand["coversSteps"])
        lost = [s for s in before if s not in after]
        if lost:
            return {"compatible": False, "reason": f"Deixaria o kit sem {self.cat.steps[lost[0]].lower()}."}
        for o in others:
            c = self.conflict_between(o, cand)
            if c:
                return {"compatible": False, "reason": f"Não combina com {o['name']}. {c['reason']}"}
        if self.is_photo(cand) and "protecao_solar" not in after:
            return {"compatible": False, "reason": "Pede protetor solar no kit."}
        return {"compatible": True}

    def swap_options(self, kit: dict, step: str, ctx: Ctx) -> list[dict]:
        idx = next((k for k, i in enumerate(kit["items"]) if i["step"] == step), -1)
        if idx < 0:
            return []
        cur = kit["items"][idx]["product"]
        out = []
        for p in self.kit_pool:
            if p["id"] == cur["id"] or step not in p["coversSteps"] or not self.base_eligible(p, ctx, False):
                continue
            compat = self.swap_compat(kit, idx, p)
            if compat is None:
                continue
            o = {"product": p, "deltaCents": p["priceCents"] - cur["priceCents"], "compatible": compat["compatible"]}
            if compat.get("reason"):
                o["reason"] = compat["reason"]
            out.append((o, self.score(p, ctx)))
        out.sort(key=lambda t: (not t[0]["compatible"], -t[1], t[0]["product"]["priceCents"], t[0]["product"]["id"]))
        good = [o for o, _ in out if o["compatible"]][:10]
        bad = [o for o, _ in out if not o["compatible"]][:3]
        return good + bad

    def apply_swap(self, kit: dict, step: str, product_id: str, ctx: Ctx) -> dict:
        idx = next((k for k, i in enumerate(kit["items"]) if i["step"] == step), -1)
        cand = self.cat.by_id.get(product_id)
        if idx < 0 or cand is None:
            raise ValueError("Troca inválida.")
        if cand["domain"] == "medicamento":
            raise ValueError("Remédio não entra em kit.")       # K13
        compat = self.swap_compat(kit, idx, cand)
        if compat is None or not compat["compatible"]:
            raise ValueError((compat or {}).get("reason", "Produto incompatível com o kit."))
        if not self.base_eligible(cand, ctx, False):
            raise ValueError("Produto indisponível para essas preferências.")
        items = [dict(i) for i in kit["items"]]
        items[idx] = {**items[idx], "product": cand, "reason": f"Escolhido por você. {self.explain_item(cand, ctx, step)}"}
        new = {**kit, "items": items, "storeId": ctx.store_id}
        new["rationale"] = kit["rationale"] if kit["rationale"].endswith("(editado)") else kit["rationale"] + " (editado)"
        return self._totals(new, ctx)

    def adapt_to_store(self, kit: dict, store_id: str, ctx: Ctx) -> dict | None:
        sctx = Ctx(**{**ctx.__dict__, "store_id": store_id})
        current = {**kit, "storeId": store_id}
        replaced = []
        for item in kit["items"]:
            if self.cat.stock_at(item["product"]["id"], store_id) > 0:
                continue
            opts = [o for o in self.swap_options(current, item["step"], sctx) if o["compatible"]]
            if not opts:
                return None
            pick = sorted(opts[:3], key=lambda o: abs(o["deltaCents"]))[0]
            current = self.apply_swap(current, item["step"], pick["product"]["id"], sctx)
            k = next(i for i, it in enumerate(current["items"]) if it["step"] == item["step"])
            current["items"][k] = {**current["items"][k],
                                   "reason": f"Trocado por falta de estoque na loja. {self.explain_item(pick['product'], sctx, item['step'])}"}
            replaced.append({"step": item["step"], "from": item["product"], "to": pick["product"]})
        return {"kit": {**current, "storeId": store_id}, "replaced": replaced}
