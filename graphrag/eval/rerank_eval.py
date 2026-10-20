"""Mede se o rerank por diversidade (MMR) ajuda ou atrapalha, no mesmo conjunto do calibrate.py.

  python3 graphrag/eval/rerank_eval.py

Escolha de lambda no TREINO; o TESTE só mede. nDCG@10 mede relevância; "tipos distintos no top 5" mede variedade.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from graphrag.dialogue import Engine                               # noqa: E402
from graphrag.eval.calibrate import ndcg, prec                     # noqa: E402
from graphrag.eval.ranking_set import TEST, TRAIN, relevant_ids    # noqa: E402

LAMBDAS = [1.0, 0.95, 0.9, 0.8, 0.7, 0.5]


def run(engine: Engine, data, lam: float) -> dict:
    nd = pr = ty = 0.0
    for q, rule in data:
        u = engine.nlu.understand(q)
        rel = relevant_ids(engine.cat, rule)
        ranked = engine.ret.rank(u, q, k=40)
        out = engine.ret.rerank_mmr(ranked, k=10, lam=lam)
        ids = [pid for pid, _ in out]
        nd += ndcg(ids, rel); pr += prec(ids, rel)
        ty += len({engine.cat.by_id[i]["productType"] for i in ids[:5]})
    n = len(data)
    return {"ndcg10": round(nd / n, 4), "p5": round(pr / n, 4), "tipos_top5": round(ty / n, 2)}


def main():
    eng = Engine.build()
    print(f"{'lambda':>7} | {'treino nDCG':>11} {'P@5':>6} {'tipos':>6} | {'teste nDCG':>10} {'P@5':>6} {'tipos':>6}")
    for lam in LAMBDAS:
        a, b = run(eng, TRAIN, lam), run(eng, TEST, lam)
        print(f"{lam:>7} | {a['ndcg10']:>11} {a['p5']:>6} {a['tipos_top5']:>6} | {b['ndcg10']:>10} {b['p5']:>6} {b['tipos_top5']:>6}")


if __name__ == "__main__":
    main()
