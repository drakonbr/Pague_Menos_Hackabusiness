#!/usr/bin/env python3
"""
Ponte de MÃO ÚNICA: catalog/data  ->  app/src/mocks/*.mock.json

Por que existe: o app não pode importar nada de catalog/ (regra de separação).
Este script é o único ponto que lê o catálogo e escreve dados simulados para o app,
já no formato do contrato (camelCase, preço e estoque juntos) descrito em contracts/README.md.

Em produção este arquivo some: o app passa a chamar o serviço de busca real.
Uso:  python3 tools/export_app_mock.py
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "catalog" / "data"
DST = ROOT / "app" / "src" / "mocks"
IMG_SRC = ROOT / "catalog" / "images"
IMG_DST = ROOT / "app" / "public" / "img"   # servido pelo Vite em /img/...


def load(name: str):
    return json.loads((SRC / name).read_text(encoding="utf-8"))


def dump(name: str, obj) -> None:
    (DST / name).write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def main() -> None:
    DST.mkdir(parents=True, exist_ok=True)
    products = load("products.json")
    inventory = {i["id"]: i for i in load("inventory.json")}
    commerce = load("commerce.json")
    categories = load("categories.json")
    cats_of: dict[str, list[str]] = {}
    for n in categories["nodes"]:
        for pid in n["productIds"]:
            cats_of.setdefault(pid, []).append(n["id"])
    # imagens: só existem depois da revisão e atribuição (catalog/images/README.md)
    images_path = SRC / "images.json"
    images = json.loads(images_path.read_text(encoding="utf-8")) if images_path.exists() else {"byProduct": {}, "banners": []}
    copied = set()

    def export_image(entry):
        rel = entry["file"]  # relativo a catalog/images
        if rel not in copied:
            dst = IMG_DST / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(IMG_SRC / rel, dst)
            copied.add(rel)
        return {
            "src": "/img/" + rel,
            "alt": entry.get("alt") or "",
            "credit": {"source": "Pexels", "photographer": entry["photographer"],
                       "photographerUrl": entry["photographerUrl"], "pageUrl": entry["pageUrl"]},
        }

    out = []
    for p in products:
        inv = inventory[p["id"]]
        out.append({
            "id": p["id"],
            "name": p["name"],
            "brand": p["brand"],
            "line": p["line"],
            "step": p["step"],
            "coversSteps": p["covers_steps"],
            "productType": p["product_type"],
            "form": p["form"],
            "size": p["size"],
            "skinTypes": p["skin_types"],
            "concerns": p["concerns"],
            "ingredients": p["ingredients"],
            "fps": p["fps"],
            "usagePeriod": p["usage_period"],
            "claims": p["claims"],
            "warnings": p["warnings"],
            "description": p["description"],
            "howToUse": p["how_to_use"],
            "priceTier": p["price_tier"],
            "priceCents": inv["price_cents"],
            "listPriceCents": inv["list_price_cents"],
            "stockQty": inv["stock_qty"],
            "cashbackPct": commerce["cashbackPct"][p["id"]],
            "salesRank": commerce["salesRank"][p["id"]],
            "categoryIds": sorted(cats_of.get(p["id"], [])),
            "images": [export_image(e) for e in images["byProduct"].get(p["id"], [])],
        })
    dump("products.mock.json", out)

    goals = [{
        "id": g["id"],
        "label": g["label"],
        "concerns": g["concerns"],
        "requiredSteps": g["required_steps"],
        "optionalSteps": g["optional_steps"],
        "synonyms": g["synonyms"],
    } for g in load("goals.json")]
    dump("goals.mock.json", goals)
    dump("interactions.mock.json", load("interactions.json"))
    dump("ingredients.mock.json", [{
        "id": i["id"], "name": i["name"], "family": i["family"],
        "function": i["function"], "photosensitizing": i["photosensitizing"],
    } for i in load("ingredients.json")])
    dump("warnings.mock.json", load("warnings.json"))
    dump("steps.mock.json", load("steps.json"))

    # ecossistema
    stock: dict[str, dict[str, int]] = {}
    for x in load("store_stock.json"):
        stock.setdefault(x["storeId"], {})[x["productId"]] = x["qty"]
    dump("stores.mock.json", [{**s, "stock": stock[s["id"]]} for s in load("stores.json")])
    dump("commerce.mock.json", {
        "freeShippingFromCents": commerce["freeShippingFromCents"],
        "delivery": commerce["delivery"],
        "showcases": commerce["showcases"],
        "kitPresets": commerce["kitPresets"],
        "banners": [export_image(e) for e in images.get("banners", [])],
        "note": commerce["note"],
    })
    dump("categories.mock.json", categories)
    with_img = sum(1 for p in out if p["images"])
    print(f"OK: {len(out)} produtos ({with_img} com foto), {len(stock)} lojas, "
          f"{len(categories['nodes'])} categorias exportados para {DST}; {len(copied)} imagens copiadas")


if __name__ == "__main__":
    main()
