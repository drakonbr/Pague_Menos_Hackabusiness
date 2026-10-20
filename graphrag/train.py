"""Treina e grava os artefatos do motor (tudo do zero, sem download):

  python -m graphrag.train

  graphrag/artifacts/graph.json            grafo de conhecimento
  graphrag/artifacts/embeddings.npz        vetores de palavras (PPMI + SVD) + manifesto
  graphrag/artifacts/nlu_model.json        classificador de atos (Naive Bayes) + relatório de teste
  graphrag/artifacts/weights.json          pesos da recuperação (python graphrag/eval/calibrate.py)
  graphrag/artifacts/ontology.schema.json  ontologia e esquema de entrada da ingestão
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from graphrag import embed                                  # noqa: E402
from graphrag.ingest import load_catalog_with_delta         # noqa: E402
from graphrag.graph import ARTIFACTS, build_graph           # noqa: E402
from graphrag.nlu import ActClassifier                      # noqa: E402
from graphrag.nlu_corpus import TEST, TRAIN                 # noqa: E402
from graphrag.ontology import export_schema, validate_graph  # noqa: E402


def main():
    cat, delta = load_catalog_with_delta()          # catálogo-base + produtos ingeridos (graphrag/ingest.py), se houver
    if delta:
        print(f"delta de ingestão aplicado: {delta.counts()}")
    g = build_graph(cat)
    errs = validate_graph(g.g)
    assert not errs, f"grafo fora da ontologia: {errs[:3]}"
    g.save()
    export_schema()
    print("grafo:", json.dumps(g.stats(), ensure_ascii=False))
    sents = embed.build_corpus(cat)
    wv = embed.train(sents)
    embed.save(wv, sents)
    print(f"vetores: vocabulário {len(wv.vocab)}, {len(sents)} frases")
    overlap = {t for ts in TRAIN.values() for t in ts} & {t for ts in TEST.values() for t in ts}
    assert not overlap, f"frases repetidas entre treino e teste: {overlap}"
    clf = ActClassifier().fit(TRAIN)
    clf.save()
    ok = tot = 0
    per = {}
    for act, texts in TEST.items():
        hit = sum(clf.predict(t)[0] == act for t in texts)
        per[act] = {"acertos": hit, "total": len(texts)}
        ok += hit; tot += len(texts)
    report = {"treino": sum(len(v) for v in TRAIN.values()), "teste": tot, "acertos": ok,
              "acuracia": round(ok / tot, 4), "porAto": per}
    (ARTIFACTS / "nlu_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"classificador de atos: {ok}/{tot} no teste ({report['acuracia']:.1%}); treino {report['treino']} frases")


if __name__ == "__main__":
    main()
