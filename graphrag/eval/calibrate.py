"""Calibra os pesos da recuperação híbrida por SUBIDA DE COORDENADAS no conjunto de treino e mede no de teste.

Métrica: nDCG@10 e precisão@5. Linhas de base: só BM25, só vetores, só grafo, pesos iniciais.
Saída: graphrag/artifacts/weights.json (pesos + resultados) e graphrag/eval/report_ranking.md.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from graphrag.data import load_catalog                      # noqa: E402
from graphrag.dialogue import Engine                        # noqa: E402
from graphrag.eval.ranking_set import TEST, TRAIN, relevant_ids  # noqa: E402
from graphrag.retrieval import DEFAULT_WEIGHTS, ARTIFACTS    # noqa: E402


def ndcg(ranked: list[str], rel: set[str], k=10) -> float:
    dcg = sum(1 / math.log2(i + 2) for i, pid in enumerate(ranked[:k]) if pid in rel)
    ideal = sum(1 / math.log2(i + 2) for i in range(min(k, len(rel))))
    return dcg / ideal if ideal else 0.0


def prec(ranked, rel, k=5) -> float:
    return sum(1 for pid in ranked[:k] if pid in rel) / k


def evaluate(engine: Engine, data, weights) -> dict:
    n, nd, pr = 0, 0.0, 0.0
    for q, rule in data:
        u = engine.nlu.understand(q)
        rel = relevant_ids(engine.cat, rule)
        ranked = [pid for pid, _ in engine.ret.rank(u, q, k=10, weights=weights)]
        nd += ndcg(ranked, rel); pr += prec(ranked, rel); n += 1
    return {"ndcg10": round(nd / n, 4), "p5": round(pr / n, 4), "n": n}


def coordinate_ascent(engine: Engine, data, start: dict, rounds=3) -> dict:
    w = {k: start[k] for k in ("bm25", "emb", "graph")}
    grid = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0]
    best = evaluate(engine, data, {**start, **w})["ndcg10"]
    for _ in range(rounds):
        changed = False
        for k in w:
            for v in grid:
                trial = {**w, k: v}
                if sum(trial.values()) == 0:
                    continue
                s = evaluate(engine, data, {**start, **trial})["ndcg10"]
                if s > best + 1e-9:
                    best, w, changed = s, trial, True
        if not changed:
            break
    total = sum(w.values())
    return {k: round(v / total, 3) for k, v in w.items()}


def main():
    eng = Engine.build(use_artifacts=False)
    base = dict(DEFAULT_WEIGHTS)
    configs = {"somente BM25": {**base, "bm25": 1, "emb": 0, "graph": 0},
               "somente vetores": {**base, "bm25": 0, "emb": 1, "graph": 0},
               "somente grafo": {**base, "bm25": 0, "emb": 0, "graph": 1},
               "híbrido (pesos iniciais)": base}
    tuned = coordinate_ascent(eng, TRAIN, base)
    configs["híbrido calibrado no treino"] = {**base, **tuned}
    rows = []
    for name, w in configs.items():
        rows.append((name, evaluate(eng, TRAIN, w), evaluate(eng, TEST, w)))
    ARTIFACTS.mkdir(exist_ok=True)
    (ARTIFACTS / "weights.json").write_text(json.dumps({
        "weights": {**tuned, "ret_in_kit": base["ret_in_kit"]},
        "calibratedOn": f"{len(TRAIN)} frases de treino",
        "results": {n: {"train": a, "test": b} for n, a, b in rows}}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    lines = ["# Ranking: treino x teste", "", f"Pesos calibrados no treino: {tuned}", "",
             "| Configuração | nDCG@10 treino | P@5 treino | nDCG@10 teste | P@5 teste |", "|---|---|---|---|---|"]
    for n, a, b in rows:
        lines.append(f"| {n} | {a['ndcg10']} | {a['p5']} | {b['ndcg10']} | {b['p5']} |")
    lines += ["", f"Treino: {len(TRAIN)} frases. Teste: {len(TEST)} frases, nunca usadas na calibração."]
    (ROOT / "graphrag" / "eval" / "report_ranking.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
