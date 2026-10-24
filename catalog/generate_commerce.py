"""Dados sintéticos do ECOSSISTEMA de compra, por cima dos 100 produtos fictícios.

Gera (em catalog/data/):
  stores.json        8 lojas fictícias (bairros reais do Recife só para o mapa; ruas inventadas)
  store_stock.json   estoque por loja (Clique & Retire e Entrega Expressa saem da loja)
  commerce.json      cashback por produto, ranking de vendas simulado, modalidades de entrega,
                     régua de frete grátis, vitrines e atalhos de kits da tela inicial
  categories.json    árvore "Dermo e Beleza" com os nomes públicos do site, já resolvida em ids

Tudo é inventado e determinístico (semente própria). Os valores de frete e cashback são
PREMISSAS do protótipo; só o limite de frete grátis (R$ 150) vem da política pública de frete.
O estoque central (inventory.json, usado na Entrega Agendada) não é alterado aqui.
"""
from __future__ import annotations

import json
import random
import sqlite3
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"
SEED = 2026

STORES = [
    # id, nome, bairro, porte, abre 24h, lat, lng, rua fictícia
    ("s01", "Loja Madalena", "Madalena", "grande", True, -8.0577, -34.9046, "Rua das Hortênsias, 220"),
    ("s02", "Loja Boa Viagem", "Boa Viagem", "grande", False, -8.1180, -34.8970, "Av. Beira-Mar, 1450"),
    ("s03", "Loja Espinheiro", "Espinheiro", "media", False, -8.0430, -34.8970, "Rua dos Jacarandás, 88"),
    ("s04", "Loja Torre", "Torre", "media", True, -8.0510, -34.9180, "Av. das Mangueiras, 600"),
    ("s05", "Loja Casa Forte", "Casa Forte", "media", False, -8.0310, -34.9180, "Rua das Palmeiras, 310"),
    ("s06", "Loja Boa Vista", "Boa Vista", "pequena", False, -8.0580, -34.8840, "Rua do Comércio, 42"),
    ("s07", "Loja Graças", "Graças", "grande", False, -8.0420, -34.9030, "Av. dos Ipês, 900"),
    ("s08", "Loja Várzea", "Várzea", "pequena", False, -8.0480, -34.9580, "Rua da Estação, 15"),
]
AVAIL = {"grande": 0.94, "media": 0.8, "pequena": 0.55}
PREMIUM_FACTOR = 0.7

FREE_SHIPPING_FROM = 15000  # R$ 150, conforme a política de frete pública
DELIVERY = [
    {"id": "retirada", "label": "Retirar na loja", "eta": "Retirar em até 60 minutos",
     "feeCents": 0, "freeFromCents": None, "stockSource": "loja"},
    {"id": "expressa", "label": "Entrega Expressa", "eta": "Em até 2 h",
     "feeCents": 990, "freeFromCents": FREE_SHIPPING_FROM, "stockSource": "loja"},
    {"id": "agendada", "label": "Entrega Agendada", "eta": "Escolha o dia da entrega",
     "feeCents": 690, "freeFromCents": FREE_SHIPPING_FROM, "stockSource": "centro_distribuicao"},
]

# Ruptura por loja da persona (docs/14): o genérico que a Renata usa some da loja mais perto dela.
# (loja, produto) -> quantidade. Apresentações equivalentes seguem disponíveis (referência e similar).
FORCED_STORE_STOCK = {
    ("s01", "p132"): 10, ("s01", "p136"): 0, ("s01", "p137"): 0, ("s01", "p138"): 8, ("s01", "p135"): 3,
    ("s02", "p136"): 0, ("s02", "p137"): 2,
    ("s07", "p136"): 6,
}

KIT_PRESETS = [
    {"id": "oleosa", "label": "Pele oleosa e acne", "query": "pele oleosa com acne"},
    {"id": "manchas", "label": "Manchas", "query": "uniformizar manchas"},
    {"id": "basico", "label": "Primeira rotina", "query": "quero começar a cuidar da pele"},
    {"id": "sol", "label": "Sol todo dia", "query": "proteção solar para o dia a dia"},
    {"id": "sensivel", "label": "Pele sensível", "query": "pele sensível"},
    {"id": "idade", "label": "Antissinais", "query": "cuidado antissinais"},
    {"id": "suplementos", "label": "Ômega 3, colágeno e magnésio", "query": "kit de suplementos ômega 3 colágeno e magnésio"},
    {"id": "higiene", "label": "Higiene premium", "query": "kit de higiene premium"},
]


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def dump(name, obj):
    (DATA / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- categorias
def has_ing(p, *ids):
    return any(i in p["ingredients"] for i in ids)


def domain_of(p):
    return p.get("domain", "dermo")


def facial_sun(p):
    return p["step"] == "protecao_solar" or "protecao_solar" in p["covers_steps"] and p["step"] != "protecao_corporal"


# (id, nome público, pai, regra). Nomes copiados do menu público do site.
CATEGORY_RULES = [
    ("dermo", "Dermo e Beleza", None, None),
    ("rosto", "Rosto", "dermo", None),
    ("limpeza", "Sabonetes e Géis de Limpeza", "rosto",
     lambda p: p["step"] == "limpeza" and p["product_type"] != "água micelar"),
    ("micelar", "Água Micelar", "rosto", lambda p: p["product_type"] == "água micelar"),
    ("esfoliante", "Esfoliante Facial", "rosto", lambda p: "esfoliante" in p["product_type"]),
    ("mascara", "Máscara Facial", "rosto", lambda p: "máscara" in p["product_type"]),
    ("hidratante", "Hidratante Facial", "rosto", lambda p: p["step"] == "hidratacao"),
    ("serum", "Sérum Facial", "rosto", lambda p: p["form"] == "dropper" and p["step"] == "tratamento"),
    ("vitamina-c", "Vitamina C", "rosto", lambda p: has_ing(p, "vitamina_c")),
    ("retinol", "Retinol", "rosto", lambda p: has_ing(p, "retinol", "bakuchiol")),
    ("hialuronico", "Ácido Hialurônico", "rosto", lambda p: has_ing(p, "acido_hialuronico")),
    ("niacinamida", "Niacinamida", "rosto", lambda p: has_ing(p, "niacinamida")),
    ("olhos", "Creme Área dos Olhos", "rosto", lambda p: p["product_type"] == "contorno dos olhos"),
    ("labial", "Hidratante Labial", "rosto", lambda p: "labial" in p["product_type"]),
    ("tipo", "Pele por tipo", "dermo", None),
    ("normal-mista", "Normais e Mistas", "tipo",
     lambda p: bool({"normal", "mista", "todas"} & set(p["skin_types"]))),
    ("oleosa-acneica", "Oleosas e Acneicas", "tipo",
     lambda p: "oleosa" in p["skin_types"] or "acne" in p["concerns"]),
    ("seca-sensivel", "Secas e Sensíveis", "tipo",
     lambda p: bool({"seca", "sensível"} & set(p["skin_types"])) or "sensibilidade" in p["concerns"]),
    ("manchas", "Com Manchas", "tipo", lambda p: "manchas" in p["concerns"]),
    ("solar-facial", "Protetores Solares Faciais", "dermo", lambda p: facial_sun(p)),
    ("solar-com-cor", "Com Cor", "solar-facial", lambda p: facial_sun(p) and "com cor" in p["claims"]),
    ("solar-bastao", "Bastão", "solar-facial", lambda p: facial_sun(p) and p["form"] == "stick"),
    ("solar-toque-seco", "Toque Seco", "solar-facial", lambda p: facial_sun(p) and "toque seco" in p["claims"]),
    ("solar-mineral", "Mineral", "solar-facial", lambda p: facial_sun(p) and "filtro mineral" in p["claims"]),
    ("solar-corporal", "Protetores Solares Corporais", "dermo", lambda p: p["step"] == "protecao_corporal"),
    ("solar-spray", "Spray", "solar-corporal", lambda p: p["step"] == "protecao_corporal" and p["form"] == "spray"),
    ("solar-creme", "Creme", "solar-corporal", lambda p: p["step"] == "protecao_corporal" and p["form"] != "spray"),
    ("veganos", "Cosméticos Veganos", "dermo", lambda p: "vegano" in p["claims"]),
    # ---- ampliação da persona: demais departamentos do app ----
    ("saude", "Medicamentos e saúde", None, None),
    ("med-dor-febre", "Dor de Cabeça e Febre", "saude", lambda p: p["line"] == "med_dor_de_cabeca"),
    ("med-dor-corpo", "Dor no Corpo e Anti-inflamatórios", "saude", lambda p: p["line"] == "med_dor_no_corpo"),
    ("med-dor-muscular", "Dor Muscular", "saude", lambda p: p["line"] == "med_dor_muscular"),
    ("med-colica", "Cólica e Gases", "saude", lambda p: p["line"] == "med_dor_de_barriga"),
    ("med-azia", "Azia e Má Digestão", "saude", lambda p: p["line"] == "med_azia"),
    ("med-gripe", "Gripe e Resfriado", "saude", lambda p: p["line"] == "med_gripe"),
    ("med-tosse", "Tosse", "saude", lambda p: p["line"] == "med_tosse"),
    ("med-garganta", "Garganta", "saude", lambda p: p["line"] == "med_dor_de_garganta"),
    ("med-alergia", "Alergias", "saude", lambda p: p["line"] == "med_alergia"),
    ("med-diarreia", "Diarreia", "saude", lambda p: p["line"] == "med_diarreia"),
    ("med-intestino-preso", "Intestino Preso", "saude", lambda p: p["line"] == "med_prisao_de_ventre"),
    ("med-enjoo", "Enjoo e Náusea", "saude", lambda p: p["line"] == "med_enjoo"),
    ("reposicao", "Reposição de uso contínuo", "saude", lambda p: p["line"].startswith("reposicao_")),
    ("vida-saudavel", "Vida Saudável", None, None),
    ("omega3", "Ômega 3", "vida-saudavel", lambda p: p["step"] == "omega3"),
    ("colageno", "Colágeno", "vida-saudavel", lambda p: p["step"] == "colageno"),
    ("magnesio", "Magnésio", "vida-saudavel", lambda p: p["step"] == "magnesio"),
    ("vitaminas", "Vitaminas", "vida-saudavel", lambda p: p["step"] == "vitaminas"),
    ("higiene", "Higiene pessoal", None, None),
    ("banho", "Banho e corpo", "higiene", lambda p: p["step"] == "higiene_corpo"),
    ("cabelos", "Cabelos", "higiene", lambda p: p["step"] == "higiene_cabelo"),
    ("bucal", "Higiene bucal", "higiene", lambda p: p["step"] == "higiene_oral"),
    ("desodorantes", "Desodorantes", "higiene", lambda p: p["step"] == "desodorante"),
]


def build_categories(products):
    by_id = {cid: (name, parent) for cid, name, parent, _ in CATEGORY_RULES}

    def root_of(cid):
        while by_id[cid][1] is not None:
            cid = by_id[cid][1]
        return cid

    nodes, empty = [], []
    for cid, name, parent, rule in CATEGORY_RULES:
        ids = None
        if rule:
            # as regras do departamento Dermo só enxergam produtos de dermocosmético
            ids = [p["id"] for p in products
                   if rule(p) and (root_of(cid) != "dermo" or domain_of(p) == "dermo")]
        if ids is not None and not ids:
            empty.append(name)
            continue
        nodes.append({"id": cid, "name": name, "parent": parent, "productIds": ids})
    # nós de agrupamento recebem a união dos filhos (de baixo para cima)
    def fill(n):
        if n["productIds"] is None:
            kids = [c for c in nodes if c["parent"] == n["id"]]
            for k in kids:
                fill(k)
            n["productIds"] = sorted({pid for c in kids for pid in (c["productIds"] or [])})
    for n in nodes:
        fill(n)
    # a raiz Dermo recebe tudo que está em qualquer categoria dela
    return {"nodes": nodes, "emptyOmitted": empty, "outOfScope": [
        "Ofertas", "Mamães e bebês", "Serviços de Saúde", "Pet shop", "Fitness e Nutrição"]}


# ---------------------------------------------------------------- lojas e estoque
def _qty(s, p, inv, rng):
    if inv[p["id"]]["stock_qty"] <= 0:
        qty = 0
    else:
        chance = AVAIL[s["size"]] * (PREMIUM_FACTOR if p["price_tier"] == "premium" else 1.0)
        qty = rng.randint(1, 12) if rng.random() < chance else 0
    return {"storeId": s["id"], "productId": p["id"], "qty": qty}


def build_stores_and_stock(products, inventory, rng):
    inv = {i["id"]: i for i in inventory}
    stores = [
        {"id": sid, "name": name, "neighborhood": hood, "city": "Recife", "uf": "PE",
         "address": f"{street} — {hood}", "size": size, "open24h": h24,
         "hours": "00:00 às 23:59" if h24 else "07:00 às 22:00",
         "lat": lat, "lng": lng, "pickup": True}
        for sid, name, hood, size, h24, lat, lng, street in STORES
    ]
    stock = []
    is_base = lambda p: p["id"] <= "p100"
    is_med = lambda p: p["line"].startswith("med_")
    base = [p for p in products if is_base(p)]
    extra = [p for p in products if not is_base(p) and not is_med(p)]
    meds = [p for p in products if is_med(p)]
    for s in stores:                       # mesma ordem e mesma semente de sempre: os 100 antigos não mudam
        for p in base:
            stock.append(_qty(s, p, inv, rng))
    rng2 = random.Random(SEED + 7)
    for s in stores:
        for p in extra:
            stock.append(_qty(s, p, inv, rng2))
    rng3 = random.Random(SEED + 11)        # medicamentos (doc 16) com semente própria: o estoque antigo não muda
    for s in stores:
        for p in meds:
            stock.append(_qty(s, p, inv, rng3))
    for row in stock:                      # ruptura combinada da persona
        key = (row["storeId"], row["productId"])
        if key in FORCED_STORE_STOCK and inv[row["productId"]]["stock_qty"] > 0:
            row["qty"] = FORCED_STORE_STOCK[key]
    order = {p["id"]: n for n, p in enumerate(products)}
    stock.sort(key=lambda r: ([s["id"] for s in stores].index(r["storeId"]), order[r["productId"]]))
    return stores, stock


# ---------------------------------------------------------------- comércio
def build_commerce(products, inventory, rng):
    inv = {i["id"]: i for i in inventory}
    cashback = {}
    for p in products:
        r = rng.random()
        cashback[p["id"]] = 0 if r < 0.7 else rng.choice([2, 3, 5, 10])
        if domain_of(p) == "medicamento":
            cashback[p["id"]] = 0        # sem cashback em medicamento (premissa do protótipo)
    # ranking simulado: produtos econômicos e protetores vendem mais
    weight = {}
    for p in products:
        w = {"economico": 3.0, "intermediario": 2.0, "premium": 1.0}[p["price_tier"]]
        if p["step"] in ("protecao_solar", "limpeza"):
            w *= 1.6
        if inv[p["id"]]["stock_qty"] <= 0:
            w *= 0.3
        weight[p["id"]] = w * rng.uniform(0.6, 1.4)
    ranking = sorted(weight, key=lambda k: -weight[k])
    dermo = {p["id"] for p in products if domain_of(p) == "dermo"}
    shown_ok = {p["id"] for p in products if domain_of(p) != "medicamento"}   # ofertas: sem medicamento
    meds_ids = {p["id"] for p in products if p["line"].startswith("med_")}
    rx_ids = {p["id"] for p in products if p.get("rx")}       # #41: remédio de prescrição fora das vitrines (RDC 96/2008)
    on_sale = [p["id"] for p in products
               if p["id"] in shown_ok
               and inv[p["id"]]["list_price_cents"] > inv[p["id"]]["price_cents"] and inv[p["id"]]["stock_qty"] > 0]
    sun = [pid for pid in ranking if next(p for p in products if p["id"] == pid)["step"] == "protecao_solar"]
    in_stock = [pid for pid in ranking if inv[pid]["stock_qty"] > 0 and pid in dermo]
    return {
        "note": "Valores de cashback, frete e ranking são premissas fictícias do protótipo.",
        "cashbackPct": cashback,
        "salesRank": {pid: k + 1 for k, pid in enumerate(ranking)},
        "freeShippingFromCents": FREE_SHIPPING_FROM,
        "delivery": DELIVERY,
        "showcases": [
            {"id": "kits", "title": "Kits inteligentes para você", "type": "kit_presets"},
            {"id": "ofertas", "title": "Ofertas da semana", "type": "products", "productIds": on_sale},
            {"id": "mais-vendidos", "title": "Mais vendidos em Dermo", "type": "products", "productIds": in_stock[:12]},
            {"id": "farmacia", "title": "Mais vendidos em Medicamentos", "type": "products",
             "productIds": [pid for pid in ranking if inv[pid]["stock_qty"] > 0 and pid in meds_ids and pid not in rx_ids][:12]},
            {"id": "protetor", "title": "Protetor solar facial", "type": "products",
             "productIds": [pid for pid in sun if inv[pid]["stock_qty"] > 0][:10]},
        ],
        "kitPresets": KIT_PRESETS,
        # reposição automática de medicamento de uso contínuo (premissas do protótipo)
        "refill": {"freeShipping": True, "discountPct": 5, "alertDaysBefore": 7,
                   "note": "Frete grátis e desconto na reposição automática são premissas fictícias."},
    }


SQL = """
CREATE TABLE IF NOT EXISTS stores (id TEXT PRIMARY KEY, name TEXT, neighborhood TEXT, city TEXT, uf TEXT,
  address TEXT, size TEXT, open24h INTEGER, hours TEXT, lat REAL, lng REAL);
CREATE TABLE IF NOT EXISTS store_stock (store_id TEXT, product_id TEXT, qty INTEGER, PRIMARY KEY (store_id, product_id));
CREATE TABLE IF NOT EXISTS product_commerce (product_id TEXT PRIMARY KEY, cashback_pct INTEGER, sales_rank INTEGER);
CREATE TABLE IF NOT EXISTS categories (id TEXT PRIMARY KEY, name TEXT, parent TEXT);
CREATE TABLE IF NOT EXISTS product_categories (product_id TEXT, category_id TEXT, PRIMARY KEY (product_id, category_id));
"""


def write_sqlite(stores, stock, commerce, categories):
    con = sqlite3.connect(DATA / "catalog.sqlite")
    con.executescript(SQL)
    cur = con.cursor()
    for t in ("stores", "store_stock", "product_commerce", "categories", "product_categories"):
        cur.execute(f"DELETE FROM {t}")
    for s in stores:
        cur.execute("INSERT INTO stores VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (s["id"], s["name"], s["neighborhood"], s["city"], s["uf"], s["address"], s["size"],
                     int(s["open24h"]), s["hours"], s["lat"], s["lng"]))
    cur.executemany("INSERT INTO store_stock VALUES (?,?,?)", [(x["storeId"], x["productId"], x["qty"]) for x in stock])
    for pid, pct in commerce["cashbackPct"].items():
        cur.execute("INSERT INTO product_commerce VALUES (?,?,?)", (pid, pct, commerce["salesRank"][pid]))
    for n in categories["nodes"]:
        cur.execute("INSERT INTO categories VALUES (?,?,?)", (n["id"], n["name"], n["parent"]))
        cur.executemany("INSERT INTO product_categories VALUES (?,?)", [(pid, n["id"]) for pid in n["productIds"]])
    con.commit()
    con.close()


def main():
    products = load("products.json")
    inventory = load("inventory.json")
    rng = random.Random(SEED)
    stores, stock = build_stores_and_stock(products, inventory, rng)
    commerce = build_commerce(products, inventory, rng)
    categories = build_categories(products)
    dump("stores.json", stores)
    dump("store_stock.json", stock)
    dump("commerce.json", commerce)
    dump("categories.json", categories)
    write_sqlite(stores, stock, commerce, categories)
    print(f"OK: {len(stores)} lojas, {len(stock)} linhas de estoque por loja, "
          f"{len(categories['nodes'])} categorias (vazias omitidas: {', '.join(categories['emptyOmitted']) or 'nenhuma'})")


if __name__ == "__main__":
    main()
