"""Checador das invariantes I1 a I16 do contrato (docs/08), escrito de forma INDEPENDENTE do compositor:
lê os JSON brutos do catálogo (catalog/data) e não importa nada de graphrag.composer nem de graphrag.data.

Medicamentos (doc 16): M1 = nenhum princípio ativo repetido no kit (os dois anti-inflamatórios caem em I6, pelas
interações); M2 = nenhum texto da resposta manda procurar médico ou farmacêutico."""
from __future__ import annotations

import json
import os
import re
import unicodedata
from pathlib import Path

REFERRAL = re.compile(r"medic[oa]s?\b|farmaceutic|profissional de saude|procure|consulte|converse com")

DATA = Path(os.environ.get("CATALOG_DATA_DIR") or Path(__file__).resolve().parents[2] / "catalog" / "data")


def _j(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


class Truth:
    def __init__(self):
        inv = {i["id"]: i for i in _j("inventory.json")}
        com = _j("commerce.json")
        self.prod = {}
        for p in _j("products.json"):
            self.prod[p["id"]] = {"price": inv[p["id"]]["price_cents"], "stock": inv[p["id"]]["stock_qty"],
                                  "cashbackPct": com["cashbackPct"][p["id"]], "covers": p["covers_steps"],
                                  "type": p["product_type"], "step": p["step"], "ings": p["ingredients"],
                                  "period": p["usage_period"], "claims": p["claims"], "warn": p["warnings"],
                                  "domain": p["domain"]}
        self.store_stock = {}
        for x in _j("store_stock.json"):
            self.store_stock.setdefault(x["storeId"], {})[x["productId"]] = x["qty"]
        self.rules = _j("interactions.json")
        self.photo = {i["id"] for i in _j("ingredients.json") if i["photosensitizing"]}


T = Truth()


def check_kit(kit: dict, intent: dict) -> list[str]:
    v, tag = [], kit["id"]
    prods = [i["product"] for i in kit["items"]]
    ids = [p["id"] for p in prods]
    truth = [T.prod.get(i) for i in ids]
    if len(set(ids)) != len(ids):
        v.append(f"{tag} I1: produto repetido")
    for i, t in zip(ids, truth):                                            # M5 (#40): remédio nunca entra em kit
        if t and t["domain"] == "medicamento":
            v.append(f"{tag} M5: {i} é remédio e está no kit")
    covered = [s for t in truth if t for s in t["covers"]]
    if len(set(covered)) != len(covered):
        v.append(f"{tag} I2: etapa coberta duas vezes")
    if len({t["type"] for t in truth if t}) != len(ids):
        v.append(f"{tag} I2: tipo repetido")
    if not 0 < len(ids) <= 5:
        v.append(f"{tag} I9: {len(ids)} itens")
    for pid, t in zip(ids, truth):
        if t is None:
            v.append(f"{tag}: {pid} não existe"); continue
        qty = T.store_stock.get(kit["storeId"], {}).get(pid, 0) if kit.get("storeId") else t["stock"]
        if qty <= 0:
            v.append(f"{tag} I3: {pid} sem estoque")
        p = next(p for p in prods if p["id"] == pid)
        if p["priceCents"] != t["price"]:
            v.append(f"{tag} I12: preço de {pid}")
    items = sum(t["price"] for t in truth if t)
    pct = 0 if len(ids) < 2 else {2: 10, 3: 12}.get(len(ids), 15)       # regra do doc 16 (#30), escrita de novo aqui
    if kit.get("itemsTotalCents") != items:
        v.append(f"{tag} I4: soma avulsa {kit.get('itemsTotalCents')} != {items}")
    if kit.get("discountPct") != pct or kit.get("discountCents") != (items * pct + 50) // 100:
        v.append(f"{tag} M3: desconto {kit.get('discountPct')}% / {kit.get('discountCents')} fora da regra")
    if kit["totalCents"] != items - (items * pct + 50) // 100:
        v.append(f"{tag} I4: total {kit['totalCents']} != soma {items} menos desconto")
    if len(ids) >= 2 and not kit["totalCents"] < items:
        v.append(f"{tag} M3: kit não sai mais barato que os itens avulsos")
    b = intent.get("budgetCents")
    if b is not None:
        if kit["withinBudget"] and kit["totalCents"] > b:
            v.append(f"{tag} I5: acima do orçamento")
        if not kit["withinBudget"] and kit["totalCents"] <= b:
            v.append(f"{tag} I5: marcado fora mas cabe")
    for x in range(len(truth)):
        for y in range(x + 1, len(truth)):
            p, q = truth[x], truth[y]
            if p and q and p["domain"] == q["domain"] == "medicamento" and set(p["ings"]) & set(q["ings"]):
                v.append(f"{tag} M1: {ids[x]} x {ids[y]} repetem princípio ativo")
            if not p or not q or p["step"] == "limpeza" or q["step"] == "limpeza":
                continue
            for r in T.rules:
                hit = (r["a"] in p["ings"] and r["b"] in q["ings"]) or (r["b"] in p["ings"] and r["a"] in q["ings"])
                if not hit:
                    continue
                if r["severity"] == "evitar":
                    v.append(f"{tag} I6: {ids[x]} x {ids[y]}")
                elif sorted([p["period"], q["period"]]) != ["dia", "noite"]:
                    v.append(f"{tag} I7: {ids[x]} x {ids[y]} sem separar períodos")
                elif not any(a["code"] == "interacao_separar_periodos" for a in kit["alerts"]):
                    v.append(f"{tag} I7: falta alerta")
    if any(set(t["ings"]) & T.photo for t in truth if t) and "protecao_solar" not in covered \
            and not any(a["code"] == "sem_protetor_no_kit" for a in kit["alerts"]):
        v.append(f"{tag} I8: fotossensibilizante sem protetor e sem alerta")
    cb = sum((t["price"] * t["cashbackPct"]) // 100 for t in truth if t) * (100 - pct) // 100
    if kit["cashbackCents"] != cb:
        v.append(f"{tag} I15: cashback {kit['cashbackCents']} != {cb}")
    if (intent.get("storeId") or None) != (kit.get("storeId") or None):
        v.append(f"{tag} I16: loja do kit != loja do pedido")
    if intent.get("pregnancy") and any("consultar_se_gestante" in t["warn"] for t in truth if t):
        v.append(f"{tag} I11: item com aviso de gestação")
    for pref in intent.get("preferences", []):
        bad = [i for i, t in zip(ids, truth) if t and pref not in t["claims"]]
        if bad:
            v.append(f"{tag} I13: {bad} sem '{pref}'")
    return v


def check_response(res: dict, excluded=()) -> list[str]:
    v, rid = [], res["requestId"]
    if res["safety"]["decision"] == "blocked":
        if res["kits"] or res.get("closestKit") or res["products"]:
            v.append(f"{rid} I10: bloqueado mas com kits ou produtos")
        return v
    for k in res["kits"]:
        v += check_kit(k, res["intent"])
        for it in k["items"]:
            if set(excluded) & set(T.prod[it["product"]["id"]]["ings"]):
                v.append(f"{k['id']} X1: ingrediente excluído em {it['product']['id']}")
    if res.get("closestKit"):
        v += [m for m in check_kit(res["closestKit"], res["intent"]) if "I5" not in m]
        if res["closestKit"]["withinBudget"]:
            v.append(f"{rid}: closestKit deveria estar fora do orçamento")
    sigs = [tuple(sorted(i["product"]["id"] for i in k["items"])) for k in res["kits"]]
    if len(set(sigs)) != len(sigs):
        v.append(f"{rid} I14: kits idênticos")
    order = ["economico", "essencial", "completo"]                       # M4 (#31): ordem e preço crescentes
    tiers, totals = [k["tier"] for k in res["kits"]], [k["totalCents"] for k in res["kits"]]
    if tiers != sorted(tiers, key=order.index) or len(set(tiers)) != len(tiers) \
            or any(a >= b for a, b in zip(totals, totals[1:])):
        v.append(f"{rid} M4: faixas fora de ordem ou preço não crescente {list(zip(tiers, totals))}")
    if res["kitsStatus"] == "ok" and len(res["kits"]) < 2:
        v.append(f"{rid}: status ok com menos de 2 kits")
    if res["kitsStatus"] == "none_in_budget" and (res["kits"] or not res.get("closestKit")):
        v.append(f"{rid}: none_in_budget inconsistente")
    for p in res["products"]:
        t = T.prod.get(p["id"])
        if not t or t["price"] != p["priceCents"]:
            v.append(f"{rid}: produto {p['id']} inválido na lista")
    shown = " ".join([res["reply"], *res["suggestions"], *res["notes"], res["safety"].get("message", "")])
    shown = "".join(c for c in unicodedata.normalize("NFD", shown.lower()) if unicodedata.category(c) != "Mn")
    if REFERRAL.search(shown):
        v.append(f"{rid} M2: resposta manda procurar profissional: {REFERRAL.search(shown).group(0)!r}")
    return v
