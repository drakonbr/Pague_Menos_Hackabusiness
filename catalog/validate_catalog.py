#!/usr/bin/env python3
"""
Validador do catálogo sintético. Sai com código 1 se alguma checagem falhar.

Uso:  python3 catalog/validate_catalog.py
Cada checagem imprime PASS/FAIL com o motivo. Nada aqui chama modelo de IA.
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

from medicines import MED_GOALS, MED_STEPS

DATA = Path(os.environ.get("CATALOG_DATA_DIR") or Path(__file__).resolve().parent / "data")

STEPS = {"limpeza", "preparo", "tratamento", "hidratacao", "protecao_solar", "protecao_corporal", "complemento",
         "omega3", "colageno", "magnesio", "vitaminas", "higiene_corpo", "higiene_cabelo", "higiene_oral",
         "desodorante", "reposicao"} | set(MED_STEPS)
MIN_PER_AREA = 6          # doc 16: pelo menos 6 medicamentos por área de saúde
REFERRAL_WORDS = ["médic", "farmacêutic", "profissional de saúde", "procure", "consulte"]
DOMAINS = {"dermo", "suplemento", "higiene", "medicamento"}
# alegações terapêuticas proibidas em tudo que NÃO é medicamento (a persona usa remédio para pressão e colesterol:
# nenhum suplemento ou cosmético pode sugerir efeito sobre isso)
THERAPEUTIC = ["colesterol", "hipertens", "pressão arterial", "diabet", "cura ", "previne", "reduz o risco",
               "emagrec", "trata doença", "controla a pressão", "baixa a pressão"]
PERIODS = {"dia", "noite", "dia_noite"}
SKINS = {"oleosa", "mista", "seca", "normal", "sensível", "todas"}
TIERS = {"economico", "intermediario", "premium"}
FORBIDDEN_WORDS = [
    "medicamento", "remédio", "remedio", "antibiótico", "antibiotico", "receita médica",
    "cura ", "trata doença", "tratamento de doença", "anti-inflamatório", "isotretinoína",
]
# O gabarito abaixo é o preço mínimo aceitável para o kit mais barato de cada objetivo
# (garante que o exemplo "até R$ 120" do PDF seja viável).
MAX_CHEAPEST_KIT_REAIS = 100.0
MAX_CHEAPEST_KIT_OTHER_REAIS = 180.0   # suplementos e higiene premium custam mais que o skin care básico

results: list[tuple[bool, str, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((ok, name, detail))


def load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def main() -> int:
    products = load("products.json")
    inventory = {i["id"]: i for i in load("inventory.json")}
    ingredients = {i["id"]: i for i in load("ingredients.json")}
    interactions = load("interactions.json")
    goals = load("goals.json")
    warnings = load("warnings.json")
    by_id = {p["id"]: p for p in products}

    # 1. Tamanho e unicidade
    check("tamanho do catálogo entre 200 e 240", 200 <= len(products) <= 240, f"{len(products)} produtos")
    check("domínios válidos", all(p.get("domain") in DOMAINS for p in products))
    by_domain = Counter(p["domain"] for p in products)
    check("os 100 produtos de skin care originais continuam (p001–p100, domínio dermo)",
          all(p["domain"] == "dermo" for p in products if p["id"] <= "p100") and len([p for p in products if p["id"] <= "p100"]) == 100,
          str(dict(by_domain)))
    ids = [p["id"] for p in products]
    check("ids únicos", len(ids) == len(set(ids)))
    pairs = [(p["brand"], p["name"]) for p in products]
    check("par (marca, nome) único", len(pairs) == len(set(pairs)))
    check("inventário cobre todos os produtos e só eles", set(inventory) == set(ids))

    # 2. Campos e vocabulários
    required = ["id", "name", "brand", "line", "step", "covers_steps", "product_type", "form", "size",
                "skin_types", "concerns", "ingredients", "usage_period", "description", "how_to_use", "price_tier"]
    missing = [(p["id"], k) for p in products for k in required if k not in p or p[k] in (None, "", [])]
    check("campos obrigatórios preenchidos", not missing, str(missing[:5]))
    check("etapas válidas", all(p["step"] in STEPS and set(p["covers_steps"]) <= STEPS for p in products))
    check("etapa principal está em covers_steps", all(p["step"] in p["covers_steps"] for p in products))
    check("períodos válidos", all(p["usage_period"] in PERIODS for p in products))
    check("tipos de pele válidos", all(set(p["skin_types"]) <= SKINS for p in products))
    check("faixas de preço válidas", all(p["price_tier"] in TIERS for p in products))
    check("ingredientes existem", all(i in ingredients for p in products for i in p["ingredients"]))
    check("avisos existem", all(w in warnings for p in products for w in p["warnings"]))

    # 3. Preço e estoque
    bad_price = [i for i in inventory.values() if not (isinstance(i["price_cents"], int) and i["price_cents"] > 0)]
    check("preço em centavos inteiro e positivo", not bad_price)
    check("preço de tabela >= preço", all(i["list_price_cents"] >= i["price_cents"] for i in inventory.values()))
    check("há produtos sem estoque para testar disponibilidade",
          0 < sum(1 for i in inventory.values() if i["stock_qty"] == 0) <= 10,
          f"{sum(1 for i in inventory.values() if i['stock_qty'] == 0)} sem estoque")
    prices = [i["price_cents"] for i in inventory.values()]
    check("faixa de preço ampla (do barato ao premium)", min(prices) <= 1500 and max(prices) >= 12000,
          f"R$ {min(prices)/100:.2f} a R$ {max(prices)/100:.2f}")

    # 4. FPS
    sun_steps = {"protecao_solar", "protecao_corporal"}
    fps_ok = True
    fps_detail = []
    for p in products:
        needs = bool(sun_steps & set(p["covers_steps"]))
        lip = p["product_type"] == "protetor labial"
        if (needs or lip) and not p.get("fps"):
            fps_ok = False
            fps_detail.append(p["id"])
        if not (needs or lip) and p.get("fps"):
            fps_ok = False
            fps_detail.append(p["id"])
    check("FPS só em protetores (e obrigatório neles)", fps_ok, str(fps_detail[:5]))
    check("FPS com valor plausível (15 a 100)", all(15 <= p["fps"] <= 100 for p in products if p.get("fps")))

    # 5. Segurança do conteúdo
    non_med = [p for p in products if p["domain"] != "medicamento"]
    texts = " ".join((p["name"] + " " + p["description"] + " " + p["how_to_use"]).lower() for p in non_med)
    hits = [w for w in FORBIDDEN_WORDS if w in texts]
    check("sem linguagem de medicamento ou promessa terapêutica (fora do domínio medicamento)", not hits, str(hits))
    hits = [w for w in THERAPEUTIC if w in texts]
    check("sem alegação sobre pressão, colesterol, diabetes, cura ou prevenção em suplementos e cosméticos",
          not hits, str(hits))
    photo = {k for k, v in ingredients.items() if v["photosensitizing"]}
    missing_warn = [p["id"] for p in products if set(p["ingredients"]) & photo and "fotossensibilizante" not in p["warnings"]]
    check("ingredientes fotossensibilizantes geram aviso", not missing_warn, str(missing_warn))
    check("avisos em retinol incluem 'consultar_se_gestante'",
          all("consultar_se_gestante" in p["warnings"] for p in products if "retinol" in p["ingredients"]))

    # 6. Interações
    check("interações só citam ingredientes existentes",
          all(i["a"] in ingredients and i["b"] in ingredients for i in interactions))
    check("severidade válida", all(i["severity"] in {"evitar", "separar"} for i in interactions))

    # 7. Cobertura por etapa e faixa de preço (para kits econômico, essencial e alternativo)
    step_tiers: dict[str, set] = defaultdict(set)
    for p in products:
        if inventory[p["id"]]["stock_qty"] > 0:
            step_tiers[p["step"]].add(p["price_tier"])
    core = ["limpeza", "tratamento", "hidratacao", "protecao_solar"]
    check("etapas centrais têm as 3 faixas de preço com estoque",
          all(step_tiers[s] == TIERS for s in core), str({s: sorted(step_tiers[s]) for s in core}))

    # 8. Viabilidade dos objetivos
    detail = []
    feasible = True
    for g in goals:
        total = 0
        for step in g["required_steps"]:
            cands = [
                inventory[p["id"]]["price_cents"] for p in products
                if inventory[p["id"]]["stock_qty"] > 0 and step in p["covers_steps"]
                and (set(p["concerns"]) & set(g["concerns"]) or step in ("limpeza", "hidratacao", "protecao_solar", "protecao_corporal"))
            ]
            if not cands:
                feasible = False
                detail.append(f"{g['id']}: sem candidatos para {step}")
                break
            total += min(cands)
        else:
            detail.append(f"{g['id']}: kit mínimo R$ {total/100:.2f}")
            cap = MAX_CHEAPEST_KIT_REAIS if g["id"] not in ("suplementos", "higiene_premium") else MAX_CHEAPEST_KIT_OTHER_REAIS
            if total / 100 > cap:
                feasible = False
    check(f"kit mais barato de cada objetivo <= R$ {MAX_CHEAPEST_KIT_REAIS:.0f} (suplementos e higiene: R$ {MAX_CHEAPEST_KIT_OTHER_REAIS:.0f})", feasible, "; ".join(detail))

    # 9. Cada objetivo tem produtos relevantes suficientes na etapa de tratamento
    for g in goals:
        if "tratamento" in g["required_steps"]:
            n = sum(1 for p in products if p["step"] == "tratamento" and set(p["concerns"]) & set(g["concerns"]))
            check(f"objetivo '{g['id']}': pelo menos 4 tratamentos relevantes", n >= 4, f"{n}")

    # 12. Ecossistema: lojas, estoque por loja, comércio e categorias (generate_commerce.py)
    stores = load("stores.json")
    stock = load("store_stock.json")
    commerce = load("commerce.json")
    cats = load("categories.json")
    sids = [x["id"] for x in stores]
    check("lojas: ids únicos e pelo menos 5", len(sids) == len(set(sids)) and len(sids) >= 5, f"{len(sids)} lojas")
    check("lojas: coordenadas dentro do Recife",
          all(-8.20 < x["lat"] < -7.95 and -35.05 < x["lng"] < -34.80 for x in stores))
    pairs_ss = {(x["storeId"], x["productId"]) for x in stock}
    check("estoque por loja: uma linha por (loja, produto)",
          len(pairs_ss) == len(stock) == len(sids) * len(products))
    check("estoque por loja: quantidades >= 0", all(x["qty"] >= 0 for x in stock))
    check("estoque por loja: sem estoque central = zero em todas as lojas",
          all(x["qty"] == 0 for x in stock if inventory[x["productId"]]["stock_qty"] <= 0))
    q = {(x["storeId"], x["productId"]): x["qty"] for x in stock}
    per_store = {sid: sum(1 for p in products if q[(sid, p["id"])] > 0) for sid in sids}
    check("estoque por loja: lojas diferem entre si (a escolha da loja importa)",
          max(per_store.values()) - min(per_store.values()) >= 20, str(per_store))
    feasible_any = True
    for g in goals:
        ok_stores = 0
        for sid in sids:
            if all(any(q[(sid, p["id"])] > 0 and step in p["covers_steps"]
                       and (set(p["concerns"]) & set(g["concerns"]) or step in ("limpeza", "hidratacao", "protecao_solar", "protecao_corporal"))
                       for p in products) for step in g["required_steps"]):
                ok_stores += 1
        feasible_any &= ok_stores >= len(sids) // 2
    check("estoque por loja: cada objetivo viável em pelo menos metade das lojas", feasible_any)
    cb = commerce["cashbackPct"]
    check("cashback: um valor por produto, em {0,2,3,5,10}",
          set(cb) == set(ids) and all(v in (0, 2, 3, 5, 10) for v in cb.values()))
    check("cashback: entre 10% e 50% dos produtos têm cashback",
          0.10 <= sum(1 for v in cb.values() if v) / len(cb) <= 0.50, f"{sum(1 for v in cb.values() if v)} produtos")
    rank = commerce["salesRank"]
    check("ranking de vendas: permutação de 1..N", sorted(rank.values()) == list(range(1, len(ids) + 1)))
    check("entrega: retirada sem taxa; taxas >= 0",
          any(d["id"] == "retirada" and d["feeCents"] == 0 for d in commerce["delivery"])
          and all(d["feeCents"] >= 0 for d in commerce["delivery"]))
    shown = [pid for sc in commerce["showcases"] if sc["type"] == "products" for pid in sc["productIds"]]
    check("vitrines: só produtos existentes e com estoque",
          all(pid in inventory and inventory[pid]["stock_qty"] > 0 for pid in shown), f"{len(shown)} itens")
    nodes = {n["id"]: n for n in cats["nodes"]}
    check("categorias: pais existem", all(n["parent"] is None or n["parent"] in nodes for n in nodes.values()))
    check("categorias: nenhuma categoria vazia", all(n["productIds"] for n in nodes.values()))
    leaves = [n for n in nodes.values() if not any(c["parent"] == n["id"] for c in nodes.values())]
    in_leaf = {pid for n in leaves for pid in n["productIds"]}
    check("categorias: todo produto está em pelo menos uma categoria final", in_leaf == set(ids),
          f"fora: {sorted(set(ids) - in_leaf)}")

    # 14. Ampliação da persona Renata (docs/14-persona-renata.md)
    meds = [p for p in products if p["domain"] == "medicamento" and p["equivalence"]]   # reposição (fictícios)
    check("medicamentos fictícios: 8 apresentações, todas com receita e marcadas como fictícias",
          len(meds) == 8 and all(p["rx"] and "FICTÍCIO" in p["description"] and "receita_obrigatoria" in p["warnings"] for p in meds),
          f"{len(meds)} itens")
    groups = defaultdict(list)
    for p in meds:
        groups[p["equivalence"]["group"]].append(p)
    check("medicamentos: cada grupo tem referência, genérico e similar, com o mesmo princípio ativo e dose",
          len(groups) == 2 and all(
              {x["equivalence"]["presentation"] for x in g} >= {"referencia", "generico", "similar"}
              and len({(x["equivalence"]["active"], x["equivalence"]["dose"]) for x in g}) == 1
              for g in groups.values()), str({k: len(v) for k, v in groups.items()}))
    check("medicamentos: nenhum entra em objetivo de kit (etapa reposicao só existe fora dos kits)",
          all("reposicao" not in g["required_steps"] + g["optional_steps"] for g in goals))
    meds_ids = {p["id"] for p in meds}
    in_showcase = {pid for sc in commerce["showcases"] if sc["type"] == "products" for pid in sc["productIds"]}
    check("medicamentos: fora das vitrines e sem cashback",
          not (meds_ids & in_showcase) and all(commerce["cashbackPct"][i] == 0 for i in meds_ids))
    check("medicamentos: só na categoria 'Reposição de uso contínuo' (e nos agrupadores dela)",
          all(set(n["id"] for n in cats["nodes"] if pid in n["productIds"]) <= {"reposicao", "saude"} for pid in meds_ids))
    sups = [p for p in products if p["domain"] == "suplemento"]
    check("suplementos: 12 itens, todos com o aviso sobre uso junto de medicação",
          len(sups) == 12 and all("consultar_se_medicacao" in p["warnings"] for p in sups))
    for step in ("omega3", "colageno", "magnesio", "vitaminas"):
        n = sum(1 for p in sups if p["step"] == step)
        check(f"suplementos: pelo menos 3 itens de {step}", n >= 3, str(n))
    for step in ("higiene_corpo", "higiene_cabelo", "higiene_oral", "desodorante"):
        n = sum(1 for p in products if p["step"] == step)
        check(f"higiene premium: pelo menos 3 itens de {step}", n >= 3, str(n))
    new_anti = [p for p in products if p["domain"] == "dermo" and "p101" <= p["id"] <= "p106" and "sinais_idade" in p["concerns"]]
    check("anti-idade: pelo menos 3 itens novos para a persona", len(new_anti) >= 3, str(len(new_anti)))
    persona = load("persona.json")
    check("persona: medicamentos de uso contínuo existem e são do domínio medicamento",
          all(by_id[m["productId"]]["domain"] == "medicamento" for m in persona["continuousMedications"]))
    check("persona: consentimento — saúde nunca usada para recomendar nem compartilhada",
          persona["privacy"]["consent"]["useHealthDataForRecommendations"] is False
          and persona["privacy"]["consent"]["shareHealthDataWithPartners"] is False)
    check("persona: pedidos só citam produtos existentes",
          all(i["productId"] in by_id for o in persona["orderHistory"] for i in o["items"]))
    sq = {(x["storeId"], x["productId"]): x["qty"] for x in stock}
    usual = [m["productId"] for m in persona["continuousMedications"]]
    near = min(stores, key=lambda x: (x["lat"] - persona["address"]["lat"]) ** 2 + (x["lng"] - persona["address"]["lng"]) ** 2)
    out_here = [pid for pid in usual if sq[(near["id"], pid)] == 0]
    sims = [p["id"] for p in meds if p["equivalence"]["group"] in {by_id[u]["equivalence"]["group"] for u in out_here}
            and p["id"] not in out_here and sq[(near["id"], p["id"])] > 0]
    check("persona: o medicamento dela está em ruptura na loja mais próxima, mas há equivalente em estoque nela",
          bool(out_here) and bool(sims) and all(inventory[u]["stock_qty"] > 0 for u in out_here),
          f"loja {near['name']}: sem estoque {out_here}; equivalentes {sims}")

    # 15. Medicamentos para busca e kits (catalog/medicines.py, doc 16)
    otc = [p for p in products if p["line"].startswith("med_")]
    areas = Counter(p["line"][4:] for p in otc)
    med_goal_ids = {g["id"] for g in MED_GOALS}
    check(f"medicamentos: pelo menos {MIN_PER_AREA} por área",
          bool(areas) and all(n >= MIN_PER_AREA for n in areas.values()), str(dict(areas)))
    check("medicamentos: toda área é um objetivo de kit", set(areas) <= med_goal_ids, str(set(areas) - med_goal_ids))
    check("medicamentos: domínio medicamento, tarja válida, sem equivalência de reposição",
          all(p["domain"] == "medicamento" and p["rx"] in (None, "receita_simples") and p["equivalence"] is None for p in otc))
    check("medicamentos: todo item tem princípio ativo cadastrado",
          all(p["ingredients"] and all(ingredients[i]["family"] == "princípio ativo" for i in p["ingredients"]) for p in otc))
    check("medicamentos: toda etapa dos objetivos de saúde tem pelo menos 2 opções com estoque",
          all(sum(1 for p in otc if step in p["covers_steps"] and inventory[p["id"]]["stock_qty"] > 0) >= 2
              for g in MED_GOALS for step in g["required_steps"]))
    check("medicamentos: sem cashback", all(commerce["cashbackPct"][p["id"]] == 0 for p in otc))
    texts = [w for w in warnings.values()] + [p["description"] + " " + p["how_to_use"] for p in products]
    hits = sorted({w for t in texts for w in REFERRAL_WORDS if w in t.lower()})
    check("nenhum texto manda procurar médico ou farmacêutico", not hits, str(hits))

    # 13. Banco de imagens (só existe depois da revisão; ver catalog/images/README.md)
    img_path = DATA / "images.json"
    if img_path.exists():
        imgs = load("images.json")
        cand_path = DATA.parent / "images" / "candidates.json"
        cands = {c["id"]: c for c in json.loads(cand_path.read_text(encoding="utf-8"))["images"]} if cand_path.exists() else {}
        entries = [(pid, e) for pid, es in imgs["byProduct"].items() for e in es]
        check("imagens: só produtos existentes", all(pid in by_id for pid, _ in entries))
        check("imagens: arquivo existe", all((DATA.parent / "images" / e["file"]).exists() for _, e in entries + [(None, b) for b in imgs["banners"]]))
        check("imagens: fonte, fotógrafo e licença preenchidos",
              all(e.get("pageUrl") and e.get("photographer") and e.get("license") for _, e in entries))
        check("imagens: só fotos aprovadas na revisão",
              all(cands.get(e["id"], {}).get("review") == "aprovada" for _, e in entries))
        check("imagens: formato da foto = formato da embalagem",
              all(cands.get(e["id"], {}).get("group") == by_id[pid]["form"] for pid, e in entries))

    # 10. SQLite bate com o JSON
    con = sqlite3.connect(DATA / "catalog.sqlite")
    cur = con.cursor()
    check("sqlite: contagem de produtos igual ao JSON", cur.execute("SELECT COUNT(*) FROM products").fetchone()[0] == len(products))
    check("sqlite: contagem de inventário igual ao JSON", cur.execute("SELECT COUNT(*) FROM inventory").fetchone()[0] == len(inventory))
    check("sqlite: lojas e estoque por loja batem com o JSON",
          cur.execute("SELECT COUNT(*) FROM stores").fetchone()[0] == len(stores)
          and cur.execute("SELECT COUNT(*) FROM store_stock").fetchone()[0] == len(stock))
    check("sqlite: nenhum ingrediente órfão",
          cur.execute("SELECT COUNT(*) FROM product_ingredients pi LEFT JOIN ingredients i ON i.id = pi.ingredient_id WHERE i.id IS NULL").fetchone()[0] == 0)
    con.close()

    # 11. Distribuição (informativo)
    dist = Counter(p["line"] for p in products)

    width = max(len(r[1]) for r in results)
    failed = 0
    for ok, name, detail in results:
        tag = "PASS" if ok else "FAIL"
        failed += 0 if ok else 1
        extra = f"  ({detail})" if detail else ""
        print(f"[{tag}] {name.ljust(width)}{extra}")
    print()
    print("Distribuição por linha:", dict(dist))
    print(f"Resumo: {len(results) - failed}/{len(results)} checagens passaram.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
