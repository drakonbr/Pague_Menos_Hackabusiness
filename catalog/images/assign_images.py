#!/usr/bin/env python3
"""Liga cada produto fictício a uma foto APROVADA do mesmo formato de embalagem.

Lê   catalog/images/candidates.json   (saída de fetch_pexels.mjs, com o campo `review`)
     catalog/data/products.json
Grava catalog/data/images.json        {"byProduct": {id: [foto]}, "banners": [foto], "missingForms": [...]}

Regras:
- só entra foto com review == "aprovada" e arquivo existente;
- distribuição determinística: produtos de um formato (ordem de id) recebem as fotos aprovadas
  do formato em rodízio, deslocado pela marca, para produtos vizinhos da mesma marca não repetirem foto;
- formato sem foto aprovada fica sem imagem (o app mostra o desenho provisório) e é listado.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"


def main() -> int:
    cand_path = HERE / "candidates.json"
    if not cand_path.exists():
        print("Sem candidates.json: rode antes  node catalog/images/fetch_pexels.mjs")
        return 1
    cands = json.loads(cand_path.read_text(encoding="utf-8"))["images"]
    products = json.loads((DATA / "products.json").read_text(encoding="utf-8"))

    approved: dict[str, list[dict]] = {}
    for c in cands:
        if c.get("review") == "aprovada" and (HERE / c["file"]).exists():
            approved.setdefault(c["group"], []).append(c)
    for g in approved.values():
        g.sort(key=lambda c: c["id"])

    keep = ("file", "alt", "photographer", "photographerUrl", "pageUrl", "license", "licenseUrl", "id")
    brands = sorted({p["brand"] for p in products})
    by_product: dict[str, list[dict]] = {}
    missing = set()
    counters: dict[str, int] = {}
    for p in sorted(products, key=lambda x: x["id"]):
        pool = approved.get(p["form"], [])
        if not pool:
            missing.add(p["form"])
            continue
        k = counters.get(p["form"], 0)
        counters[p["form"]] = k + 1
        pick = pool[(k + brands.index(p["brand"])) % len(pool)]
        by_product[p["id"]] = [{f: pick[f] for f in keep if f in pick}]

    banners = [{f: c[f] for f in keep if f in c} for c in approved.get("banner", [])][:3]
    out = {"byProduct": by_product, "banners": banners, "missingForms": sorted(missing)}
    (DATA / "images.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    used = {e["id"] for v in by_product.values() for e in v}
    print(f"OK: {len(by_product)}/{len(products)} produtos com foto; {len(used)} fotos distintas; "
          f"{len(banners)} banners; formatos sem foto: {', '.join(sorted(missing)) or 'nenhum'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
