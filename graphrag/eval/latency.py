"""Mede a latência do motor (em processo) e do endpoint SSE (HTTP local).

  python3 graphrag/eval/latency.py [--url http://127.0.0.1:8787]

Em processo: tempo de Engine.search por frase, com e sem contexto. HTTP: tempo até o primeiro evento (rewrite) e até o
último (done). Máquina de desenvolvimento, uma pessoa por vez: serve para ver ordem de grandeza e regressões, não é
teste de carga.
"""
from __future__ import annotations

import argparse
import http.client
import json
import statistics
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from graphrag.dialogue import Engine        # noqa: E402

FRASES = ["rotina anti idade premium até R$ 400, sem retinol", "kit de suplementos", "higiene premium", "ômega 3", "sérum",
          "pele oleosa com cravos até R$ 100", "protetor solar vegano", "quero começar a cuidar da pele", "creme dental",
          "shampoo e condicionador reparador", "magnésio para dormir", "manchas de sol no rosto", "colágeno em pó",
          "preciso repor meu remédio", "que remédio eu tomo pra dor", "oi", "desodorante sem alumínio", "pele sensível sem fragrância"]
SEGUINTES = ["mais barato", "troca o hidratante", "total com entrega", "sem fragrância", "esse é vegano?", "fechado pode adicionar"]


def pct(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(q * len(xs)))]


def resumo(nome, xs):
    print(f"{nome:<34} n={len(xs):<4} p50={statistics.median(xs):7.1f} ms  p95={pct(xs, .95):7.1f} ms  máx={max(xs):7.1f} ms")


def em_processo(rep=5):
    e = Engine.build()
    novos, seguintes = [], []
    for _ in range(rep):
        for f in FRASES:
            t = time.perf_counter(); r = e.search({"query": f}); novos.append((time.perf_counter() - t) * 1000)
            ctx = r["context"]
            if r["kits"]:
                for s in SEGUINTES:
                    t = time.perf_counter(); e.search({"query": s, "context": ctx}); seguintes.append((time.perf_counter() - t) * 1000)
    resumo("em processo: busca nova", novos)
    resumo("em processo: turno com contexto", seguintes)


def http_sse(url, rep=5):
    u = urlparse(url)
    primeiro, ultimo = [], []
    for _ in range(rep):
        for f in FRASES:
            c = http.client.HTTPConnection(u.hostname, u.port, timeout=20)
            t = time.perf_counter()
            c.request("POST", "/v1/search-chat", json.dumps({"query": f}), {"Content-Type": "application/json"})
            r = c.getresponse()
            first = None
            while True:
                line = r.fp.readline()
                if first is None and line.startswith(b"event: rewrite"):
                    first = (time.perf_counter() - t) * 1000
                if not line:
                    break
            primeiro.append(first or 0); ultimo.append((time.perf_counter() - t) * 1000)
            c.close()
    resumo("SSE: até o 1º evento (rewrite)", primeiro)
    resumo("SSE: até o fim (done)", ultimo)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=None)
    a = ap.parse_args()
    em_processo()
    if a.url:
        http_sse(a.url)
