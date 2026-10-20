"""Leitura SOMENTE LEITURA do catálogo sintético (catalog/data/).

Regras de separação (docs/04, doc 14):
  - o GraphRAG nunca escreve em catalog/;
  - a lista de arquivos lidos é FIXA abaixo. `persona.json` (perfil, medicamentos e histórico da cliente)
    NÃO está na lista de propósito: o motor nunca vê dados da pessoa, só o catálogo.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("CATALOG_DATA_DIR") or ROOT / "catalog" / "data")

ALLOWED_FILES = (
    "products.json", "inventory.json", "ingredients.json", "interactions.json", "goals.json", "warnings.json",
    "steps.json", "concerns.json", "stores.json", "store_stock.json", "commerce.json", "categories.json",
)

# ordem das etapas dentro de um kit (as antigas primeiro, depois as dos novos departamentos)
STEP_ORDER = [
    "limpeza", "preparo", "tratamento", "hidratacao", "protecao_solar", "protecao_corporal", "complemento",
    "omega3", "colageno", "magnesio", "vitaminas",
    "higiene_corpo", "higiene_cabelo", "higiene_oral", "desodorante",
    "reposicao",
]


def _load(name: str):
    assert name in ALLOWED_FILES, f"arquivo fora da lista permitida: {name}"
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


def camel_product(p: dict, inv: dict, commerce: dict, cats_of: dict) -> dict:
    """Produto no formato do contrato (camelCase, preço e estoque do inventário). Sem imagens: o app as anexa."""
    return {
        "id": p["id"], "name": p["name"], "brand": p["brand"], "line": p["line"], "step": p["step"],
        "coversSteps": p["covers_steps"], "productType": p["product_type"], "form": p["form"], "size": p["size"],
        "skinTypes": p["skin_types"], "concerns": p["concerns"], "ingredients": p["ingredients"], "fps": p["fps"],
        "usagePeriod": p["usage_period"], "claims": p["claims"], "warnings": p["warnings"],
        "description": p["description"], "howToUse": p["how_to_use"], "priceTier": p["price_tier"],
        "priceCents": inv["price_cents"], "listPriceCents": inv["list_price_cents"], "stockQty": inv["stock_qty"],
        "cashbackPct": commerce["cashbackPct"][p["id"]], "salesRank": commerce["salesRank"][p["id"]],
        "categoryIds": sorted(cats_of.get(p["id"], [])), "images": [],
        "domain": p["domain"], "rx": p["rx"], "equivalence": p["equivalence"],
    }


@dataclass
class Catalog:
    products: list[dict]
    by_id: dict[str, dict]
    goals: list[dict]
    goal_by_id: dict[str, dict]
    steps: dict[str, str]
    concerns: dict[str, str]
    ingredients: dict[str, dict]
    interactions: list[dict]
    warnings: dict[str, str]
    stores: list[dict]
    store_stock: dict[str, dict[str, int]]
    commerce: dict
    categories: dict
    interaction_map: dict = field(default_factory=dict)

    def stock_at(self, pid: str, store_id: str | None) -> int:
        if store_id:
            return self.store_stock.get(store_id, {}).get(pid, 0)
        return self.by_id[pid]["stockQty"]

    @property
    def delivery(self) -> list[dict]:
        return self.commerce["delivery"]

    @property
    def free_shipping_cents(self) -> int:
        return self.commerce["freeShippingFromCents"]


def load_catalog() -> Catalog:
    inventory = {i["id"]: i for i in _load("inventory.json")}
    commerce = _load("commerce.json")
    categories = _load("categories.json")
    cats_of: dict[str, list[str]] = {}
    for n in categories["nodes"]:
        for pid in n["productIds"]:
            cats_of.setdefault(pid, []).append(n["id"])
    products = [camel_product(p, inventory[p["id"]], commerce, cats_of) for p in _load("products.json")]
    goals = _load("goals.json")
    stock: dict[str, dict[str, int]] = {}
    for x in _load("store_stock.json"):
        stock.setdefault(x["storeId"], {})[x["productId"]] = x["qty"]
    inter = _load("interactions.json")
    imap = {}
    for i in inter:
        imap[(i["a"], i["b"])] = i
        imap[(i["b"], i["a"])] = i
    return Catalog(
        products=products,
        by_id={p["id"]: p for p in products},
        goals=goals,
        goal_by_id={g["id"]: g for g in goals},
        steps=_load("steps.json"),
        concerns=_load("concerns.json"),
        ingredients={i["id"]: i for i in _load("ingredients.json")},
        interactions=inter,
        warnings=_load("warnings.json"),
        stores=_load("stores.json"),
        store_stock=stock,
        commerce=commerce,
        categories=categories,
        interaction_map=imap,
    )
