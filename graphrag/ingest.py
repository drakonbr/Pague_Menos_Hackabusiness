"""Ingestão incremental de produtos: valida, resolve entidades, atualiza catálogo, grafo e índices.

  python -m graphrag.ingest novos_produtos.json            # aplica e grava em artifacts/delta_products.json
  python -m graphrag.ingest novos_produtos.json --dry-run  # só mostra o que aconteceria

Sem modelo de linguagem de propósito: o catálogo já é estruturado, então "extrair entidades" aqui é VALIDAR contra a
ontologia (ontology.py) e RESOLVER cada valor para o nó que já existe. Isso evita a classe de erro que a extração por
LLM traz (nó inventado, ingrediente com outro nome, marca duplicada) e mantém tudo local e auditável.

Resolução de entidades:
  - vocabulário FECHADO (etapa, preocupação, ingrediente, aviso, tipo de pele): casa por id ou rótulo, sem acento nem
    caixa; se não casar, o registro é RECUSADO (a ontologia não ganha nó por acidente);
  - vocabulário ABERTO (marca, tipo de produto, alegação): casa por texto normalizado ("AURORA DERMO" = "Aurora Dermo");
    se for novo, vira nó novo;
  - produto: mesmo (marca, nome) é o MESMO produto. Sem id, atualiza o existente (reenviar o mesmo lote não duplica);
    com id diferente de um produto de mesma marca e nome, é recusado como duplicata.

Escrita: só em graphrag/artifacts/delta_products.json (nunca em catalog/). O motor recarrega catálogo-base + delta
ao subir; `Engine.ingest` aplica o mesmo delta sem reiniciar. Os vetores de palavras NÃO são retreinados aqui: o vetor
do produto novo é a média dos vetores das palavras que o vocabulário já conhece (as desconhecidas são listadas em
`oovTokens`; rode `python -m graphrag.train` para incorporá-las).
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import ValidationError

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from graphrag.data import Catalog, load_catalog                 # noqa: E402
from graphrag.ontology import ProductRecord                      # noqa: E402
from graphrag.text import norm, tokens                           # noqa: E402

ARTIFACTS = Path(__file__).resolve().parent / "artifacts"
DELTA_PATH = ARTIFACTS / "delta_products.json"
NEW_PRODUCT_RANK_BASE = 1000          # produto novo ainda não tem histórico de vendas: entra depois dos que têm
SKIN_TYPES = ("oleosa", "mista", "seca", "normal", "sensível", "todas")


@dataclass
class RecordResult:
    index: int
    id: str | None
    status: str                       # created | updated | unchanged | rejected
    reasons: list[str] = field(default_factory=list)
    resolved: list[str] = field(default_factory=list)     # "marca 'AURORA DERMO' -> 'Aurora Dermo'"
    newNodes: list[str] = field(default_factory=list)     # nós abertos criados (marca, tipo, alegação)

    def as_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v not in ([], None)}


@dataclass
class IngestReport:
    results: list[RecordResult] = field(default_factory=list)
    oovTokens: list[str] = field(default_factory=list)
    applied: list[dict] = field(default_factory=list)    # registros resolvidos que mudaram o catálogo (vão para o delta)

    @property
    def changed(self) -> bool:
        return any(r.status in ("created", "updated") for r in self.results)

    def counts(self) -> dict:
        out: dict[str, int] = {}
        for r in self.results:
            out[r.status] = out.get(r.status, 0) + 1
        return out

    def as_dict(self) -> dict:
        return {"counts": self.counts(), "results": [r.as_dict() for r in self.results], "oovTokens": self.oovTokens}


# --------------------------------------------------------------------------- resolução
class _Index:
    """texto normalizado -> id canônico, para um vocabulário."""

    def __init__(self, pairs: list[tuple[str, list[str]]]):
        self.m: dict[str, str] = {}
        for cid, names in pairs:
            for n in [cid, *names]:
                self.m.setdefault(norm(n), cid)

    def get(self, text: str) -> str | None:
        return self.m.get(norm(text))


def _indexes(cat: Catalog) -> dict[str, _Index]:
    open_brand = sorted({p["brand"] for p in cat.products})
    open_ptype = sorted({p["productType"] for p in cat.products})
    open_claim = sorted({c for p in cat.products for c in p["claims"]})
    return {
        "step": _Index([(s, [lbl]) for s, lbl in cat.steps.items()]),
        "concern": _Index([(c, [lbl]) for c, lbl in cat.concerns.items()]),
        "ingredient": _Index([(i, [d["name"]]) for i, d in cat.ingredients.items()]),
        "warning": _Index([(w, []) for w in cat.warnings]),
        "skin": _Index([(s, []) for s in SKIN_TYPES]),
        "brand": _Index([(b, []) for b in open_brand]),
        "ptype": _Index([(t, []) for t in open_ptype]),
        "claim": _Index([(c, []) for c in open_claim]),
        "equiv": _Index([(e, []) for e in sorted({p["equivalence"]["group"] for p in cat.products if p["equivalence"]})]),
    }


def _resolve_list(kind: str, values: list[str], idx: dict[str, _Index], label: str, notes: list[str],
                  errors: list[str], closed: bool, new_nodes: list[str]) -> list[str]:
    out: list[str] = []
    for v in values:
        hit = idx[kind].get(v)
        if hit is None:
            if closed:
                errors.append(f"{label} desconhecido: {v!r} (vocabulário fechado da ontologia)")
                continue
            hit = v.strip()
            idx[kind].m[norm(hit)] = hit            # vale para os próximos registros do mesmo lote
            new_nodes.append(f"{kind}:{hit}")
        elif hit != v:
            notes.append(f"{label} {v!r} -> {hit!r}")
        if hit not in out:
            out.append(hit)
    return out


def _resolve_one(kind: str, value: str, idx: dict[str, _Index], label: str, notes: list[str], errors: list[str],
                 closed: bool, new_nodes: list[str]) -> str:
    r = _resolve_list(kind, [value], idx, label, notes, errors, closed, new_nodes)
    return r[0] if r else value


def _product_key(p: dict) -> tuple[str, str]:
    return norm(p["brand"]), norm(p["name"])


COMPARE_FIELDS = ("name", "brand", "line", "step", "coversSteps", "productType", "form", "size", "skinTypes", "concerns",
                  "ingredients", "fps", "usagePeriod", "claims", "warnings", "description", "howToUse", "priceTier",
                  "priceCents", "listPriceCents", "stockQty", "domain", "rx", "equivalence")


def _next_id(cat: Catalog, taken: set[str]) -> str:
    n = max([int(p["id"][1:]) for p in cat.products] + [int(t[1:]) for t in taken] + [0]) + 1
    return f"p{n:03d}"


def _build_product(cat: Catalog, rec: ProductRecord, pid: str, idx: dict[str, _Index], notes: list[str],
                   errors: list[str], new_nodes: list[str], keep: dict | None) -> dict | None:
    d = rec.model_dump(exclude={"id", "storeStock"})
    if float(d["size"]["value"]).is_integer():
        d["size"]["value"] = int(d["size"]["value"])
    d["step"] = _resolve_one("step", d["step"], idx, "etapa", notes, errors, True, new_nodes)
    d["coversSteps"] = _resolve_list("step", d["coversSteps"], idx, "etapa", notes, errors, True, new_nodes)
    d["concerns"] = _resolve_list("concern", d["concerns"], idx, "preocupação", notes, errors, True, new_nodes)
    d["ingredients"] = _resolve_list("ingredient", d["ingredients"], idx, "ingrediente", notes, errors, True, new_nodes)
    d["warnings"] = _resolve_list("warning", d["warnings"], idx, "aviso", notes, errors, True, new_nodes)
    d["skinTypes"] = _resolve_list("skin", d["skinTypes"], idx, "tipo de pele", notes, errors, True, new_nodes)
    d["brand"] = _resolve_one("brand", d["brand"], idx, "marca", notes, errors, False, new_nodes)
    d["productType"] = _resolve_one("ptype", d["productType"], idx, "tipo de produto", notes, errors, False, new_nodes)
    d["claims"] = _resolve_list("claim", d["claims"], idx, "alegação", notes, errors, False, new_nodes)
    if d["step"] not in d["coversSteps"]:
        errors.append("coversSteps precisa conter a etapa principal (depois de resolvida)")
    if d.get("equivalence"):
        d["equivalence"]["group"] = _resolve_one("equiv", d["equivalence"]["group"], idx, "grupo de equivalência",
                                                 notes, errors, False, [])
    if errors:
        return None
    same_domain = [p["cashbackPct"] for p in cat.products if p["domain"] == d["domain"]]
    if d.get("cashbackPct") is None:
        d["cashbackPct"] = keep["cashbackPct"] if keep else int(statistics.median(same_domain or [2]))
    if d["domain"] == "medicamento":
        d["cashbackPct"] = 0          # #45 (RDC 96/2008): remédio não tem cashback promocional, venha o registro como vier
    d.update({"id": pid, "salesRank": keep["salesRank"] if keep else NEW_PRODUCT_RANK_BASE + int(pid[1:]),
              "categoryIds": keep["categoryIds"] if keep else [], "images": keep["images"] if keep else []})
    return d


# --------------------------------------------------------------------------- aplicação
def _apply(cat: Catalog, product: dict, store_stock: dict[str, int]) -> None:
    pid = product["id"]
    if product.get("rx") or product.get("domain") == "medicamento":
        product["listPriceCents"] = product["priceCents"]      # #41/#45: remédio nunca tem preço riscado
    if pid in cat.by_id:
        cat.products[[p["id"] for p in cat.products].index(pid)] = product
    else:
        cat.products.append(product)
    cat.by_id[pid] = product
    cat.commerce["cashbackPct"][pid] = product["cashbackPct"]
    cat.commerce["salesRank"][pid] = product["salesRank"]
    for sid, qty in store_stock.items():
        cat.store_stock.setdefault(sid, {})[pid] = qty


def ingest_records(cat: Catalog, raw_records: list[dict], word_vocab: set[str] | None = None) -> IngestReport:
    """Aplica os registros em `cat` (em memória). Cada registro é independente: um recusado não derruba o lote."""
    report = IngestReport()
    idx = _indexes(cat)
    by_key = {_product_key(p): p["id"] for p in cat.products}
    taken: set[str] = set()
    oov: set[str] = set()
    for i, raw in enumerate(raw_records):
        res = RecordResult(index=i, id=(raw or {}).get("id") if isinstance(raw, dict) else None, status="rejected")
        report.results.append(res)
        try:
            rec = ProductRecord.model_validate(raw)
        except ValidationError as ex:
            res.reasons = [f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in ex.errors()]
            continue
        errors: list[str] = []
        key = (norm(rec.brand), norm(rec.name))
        existing_id = by_key.get(key)
        if rec.id and existing_id and rec.id != existing_id:
            res.reasons = [f"duplicata de {existing_id} (mesma marca e nome); reenvie sem id ou com id {existing_id}"]
            continue
        pid = rec.id or existing_id or _next_id(cat, taken)
        keep = cat.by_id.get(pid)
        # alguns valores já existentes na base têm outra grafia: a chave usa a marca já resolvida
        product = _build_product(cat, rec, pid, idx, res.resolved, errors, res.newNodes, keep)
        res.id = pid
        if errors or product is None:
            res.reasons = errors
            continue
        stock = dict(rec.storeStock)
        bad = [s for s in stock if s not in {st["id"] for st in cat.stores}]
        if bad:
            res.reasons = [f"loja desconhecida em storeStock: {', '.join(bad)}"]
            continue
        if keep and all(keep.get(f) == product.get(f) for f in COMPARE_FIELDS) \
                and all(cat.store_stock.get(s, {}).get(pid) == q for s, q in stock.items()):
            res.status = "unchanged"
            continue
        res.status = "updated" if keep else "created"
        _apply(cat, product, stock)
        by_key[_product_key(product)] = pid
        taken.add(pid)
        report.applied.append({**{f: product[f] for f in COMPARE_FIELDS}, "id": pid, "cashbackPct": product["cashbackPct"],
                               **({"storeStock": stock} if stock else {})})
        if word_vocab is not None:
            from graphrag.retrieval import product_text
            oov |= {t for t in tokens(product_text(cat, product)) if t not in word_vocab}
    report.oovTokens = sorted(oov)
    return report


# --------------------------------------------------------------------------- delta em disco
def read_delta(path: Path | None = None) -> list[dict]:
    path = path or DELTA_PATH
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8")).get("products", [])


def write_delta(applied: list[dict], path: Path | None = None) -> Path:
    """Junta os registros resolvidos ao delta (por id; o mais novo vence). Ordem estável, arquivo determinístico."""
    path = path or DELTA_PATH
    by_id = {r["id"]: r for r in read_delta(path)}
    for r in applied:
        by_id[r["id"]] = r
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"version": 1, "products": [by_id[k] for k in sorted(by_id)]},
                               ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return path


def load_catalog_with_delta(delta_path: Path | None = None) -> tuple[Catalog, IngestReport | None]:
    cat = load_catalog()
    recs = read_delta(delta_path)
    if not recs:
        return cat, None
    return cat, ingest_records(cat, recs)


def main():
    ap = argparse.ArgumentParser(description="Ingestão incremental de produtos no GraphRAG local")
    ap.add_argument("arquivo", help="JSON com uma lista de produtos (ou {\"products\": [...]})")
    ap.add_argument("--dry-run", action="store_true", help="não grava o delta")
    a = ap.parse_args()
    data = json.loads(Path(a.arquivo).read_text(encoding="utf-8"))
    records = data["products"] if isinstance(data, dict) else data
    cat, _ = load_catalog_with_delta()
    from graphrag import embed
    wv = embed.load()
    rep = ingest_records(cat, records, set(wv.vocab) if wv is not None else None)
    print(json.dumps(rep.as_dict(), ensure_ascii=False, indent=1))
    if rep.changed and not a.dry_run:
        print("delta gravado em", write_delta(rep.applied))
        if rep.oovTokens:
            print("palavras novas fora do vocabulário vetorial:", ", ".join(rep.oovTokens),
                  "\n  rode `python -m graphrag.train` para incorporá-las")
    return 0 if all(r.status != "rejected" for r in rep.results) else 1


if __name__ == "__main__":
    sys.exit(main())
