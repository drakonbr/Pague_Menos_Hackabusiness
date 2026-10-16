"""Dados sintéticos do ECOSSISTEMA de compra, por cima dos 100 produtos fictícios.

Gera (em catalog/data/):
  stores.json        8 lojas fictícias (bairros reais de Fortaleza só para o mapa)
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
    ("s01", "Loja Aldeota", "Aldeota", "grande", True, -3.7365, -38.5050, "Rua das Acácias, 120"),
    ("s02", "Loja Meireles", "Meireles", "grande", False, -3.7270, -38.4960, "Av. Beira-Sol, 455"),
    ("s03", "Loja Benfica", "Benfica", "media", False, -3.7400, -38.5390, "Rua dos Ipês, 88"),
    ("s04", "Loja Messejana", "Messejana", "media", True, -3.8320, -38.4920, "Av. Lagoa Azul, 1500"),
    ("s05", "Loja Parangaba", "Parangaba", "media", False, -3.7760, -38.5620, "Rua da Estação, 310"),
    ("s06", "Loja Centro", "Centro", "pequena", False, -3.7260, -38.5270, "Rua do Mercado, 42"),
    ("s07", "Loja Cocó", "Cocó", "grande", False, -3.7470, -38.4780, "Av. das Dunas, 900"),
    ("s08", "Loja Montese", "Montese", "pequena", False, -3.7620, -38.5420, "Rua das Palmeiras, 15"),
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

KIT_PRESETS = [
    {"id": "oleosa", "label": "Pele oleosa e acne", "query": "pele oleosa com acne"},
    {"id": "manchas", "label": "Manchas", "query": "uniformizar manchas"},
    {"id": "basico", "label": "Primeira rotina", "query": "quero começar a cuidar da pele"},
    {"id": "sol", "label": "Sol todo dia", "query": "proteção solar para o dia a dia"},
    {"id": "sensivel", "label": "Pele sensível", "query": "pele sensível"},
    {"id": "idade", "label": "Antissinais", "query": "cuidado antissinais"},
]


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def dump(name, obj):
    (DATA / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- categorias
def has_ing(p, *ids):
    return any(i in p["ingredients"] for i in ids)


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
]


def build_categories(products):
    nodes, empty = [], []
    for cid, name, parent, rule in CATEGORY_RULES:
        ids = [p["id"] for p in products if rule(p)] if rule else None
        if ids is not None and not ids:
            empty.append(name)
            continue
        nodes.append({"id": cid, "name": name, "parent": parent, "productIds": ids})
    # nós de agrupamento recebem a união dos filhos
    for n in nodes:
        if n["productIds"] is None:
            kids = [c for c in nodes if c["parent"] == n["id"]]
            union = sorted({pid for c in kids for pid in (c["productIds"] or [])})
            n["productIds"] = union
    # a raiz recebe tudo que está em qualquer categoria
    root = next(n for n in nodes if n["id"] == "dermo")
    root["productIds"] = sorted({pid for n in nodes if n["id"] != "dermo" for pid in n["productIds"]})
    return {"nodes": nodes, "emptyOmitted": empty, "outOfScope": [
        "Ofertas", "Medicamentos e Saúde", "Mamães e bebês", "Higiene pessoal", "Vida Saudável",
        "Serviços de Saúde", "Pet shop", "Fitness e Nutrição"]}


# ---------------------------------------------------------------- lojas e estoque
def build_stores_and_stock(products, inventory, rng):
    inv = {i["id"]: i for i in inventory}
    stores = [
        {"id": sid, "name": name, "neighborhood": hood, "city": "Fortaleza", "uf": "CE",
         "address": f"{street} — {hood}", "size": size, "open24h": h24,
         "hours": "00:00 às 23:59" if h24 else "07:00 às 22:00",
         "lat": lat, "lng": lng, "pickup": True}
        for sid, name, hood, size, h24, lat, lng, street in STORES
    ]
    stock = []
    for s in stores:
        for p in products:
            if inv[p["id"]]["stock_qty"] <= 0:
                qty = 0
            else:
                chance = AVAIL[s["size"]] * (PREMIUM_FACTOR if p["price_tier"] == "premium" else 1.0)
                qty = rng.randint(1, 12) if rng.random() < chance else 0
            stock.append({"storeId": s["id"], "productId": p["id"], "qty": qty})
    return stores, stock


# ---------------------------------------------------------------- comércio
def build_commerce(products, inventory, rng):
    inv = {i["id"]: i for i in inventory}
    cashback = {}
    for p in products:
        r = rng.random()
        cashback[p["id"]] = 0 if r < 0.7 else rng.choice([2, 3, 5, 10])
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
    on_sale = [p["id"] for p in products
               if inv[p["id"]]["list_price_cents"] > inv[p["id"]]["price_cents"] and inv[p["id"]]["stock_qty"] > 0]
    sun = [pid for pid in ranking if next(p for p in products if p["id"] == pid)["step"] == "protecao_solar"]
    in_stock = [pid for pid in ranking if inv[pid]["stock_qty"] > 0]
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
            {"id": "protetor", "title": "Protetor solar facial", "type": "products",
             "productIds": [pid for pid in sun if inv[pid]["stock_qty"] > 0][:10]},
        ],
        "kitPresets": KIT_PRESETS,
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
