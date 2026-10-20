"""Recuperação híbrida (o "R" do GraphRAG), tudo escrito do zero:

  1. BM25 sobre o texto de cada produto (nome, tipo, preocupações, ingredientes, alegações, descrição);
  2. similaridade de cosseno entre o vetor da frase e o vetor do produto (vetores treinados em embed.py);
  3. ativação espalhada no grafo de conhecimento, a partir das entidades que a pessoa citou
     (objetivo, preocupação, ingrediente, etapa, tipo de pele, alegação).

Cada canal vira uma nota de 0 a 1 e as três são somadas com pesos (graphrag/artifacts/weights.json),
calibrados por subida de coordenadas num conjunto de treino e medidos num conjunto de teste (eval/).

Medicamentos NUNCA entram aqui: a busca em texto livre não os enxerga (privacidade e doc 07).
"""
from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

import numpy as np

from .data import Catalog
from .embed import WordVectors
from .graph import KnowledgeGraph, nid
from .nlu import Understanding
from .text import tokens

ARTIFACTS = Path(__file__).resolve().parent / "artifacts"
DEFAULT_WEIGHTS = {"bm25": 0.30, "emb": 0.25, "graph": 0.45, "ret_in_kit": 6.0}


def load_weights() -> dict:
    p = ARTIFACTS / "weights.json"
    if p.exists():
        return {**DEFAULT_WEIGHTS, **json.loads(p.read_text(encoding="utf-8"))["weights"]}
    return dict(DEFAULT_WEIGHTS)


def product_text(cat: Catalog, p: dict) -> str:
    return " ".join([
        p["name"], p["brand"], p["productType"], cat.steps.get(p["step"], ""),
        " ".join(cat.concerns.get(c, c) for c in p["concerns"]),
        " ".join(cat.ingredients[i]["name"] for i in p["ingredients"] if i in cat.ingredients),
        " ".join(p["claims"]), " ".join(p["skinTypes"]), p["description"],
    ])


class Retriever:
    K1, B = 1.4, 0.75

    def __init__(self, cat: Catalog, graph: KnowledgeGraph, wv: WordVectors | None, weights: dict | None = None):
        self.cat, self.graph, self.wv = cat, graph, wv
        self.weights = weights or load_weights()
        self.pids = [p["id"] for p in cat.products if p["domain"] != "medicamento"]
        self.docs = {pid: tokens(product_text(cat, cat.by_id[pid])) for pid in self.pids}
        self.dl = {pid: len(t) for pid, t in self.docs.items()}
        self.avgdl = sum(self.dl.values()) / max(1, len(self.dl))
        df = Counter(t for toks in self.docs.values() for t in set(toks))
        n = len(self.pids)
        self.idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}
        self.tf = {pid: Counter(toks) for pid, toks in self.docs.items()}
        self.dvec = {}
        if wv is not None:
            for pid, toks in self.docs.items():
                self.dvec[pid] = wv.vector(toks)

    # ------------------------------------------------------------ canais
    def bm25(self, query: str) -> dict[str, float]:
        q = tokens(query)
        out = {}
        for pid in self.pids:
            tf, dl, s = self.tf[pid], self.dl[pid], 0.0
            for t in q:
                f = tf.get(t, 0)
                if f:
                    s += self.idf.get(t, 0.0) * f * (self.K1 + 1) / (f + self.K1 * (1 - self.B + self.B * dl / self.avgdl))
            out[pid] = s
        return out

    def embedding(self, query: str) -> dict[str, float]:
        if self.wv is None:
            return {pid: 0.0 for pid in self.pids}
        qv = self.wv.vector(tokens(query))
        if not np.linalg.norm(qv):
            return {pid: 0.0 for pid in self.pids}
        return {pid: float(max(0.0, qv @ self.dvec[pid])) for pid in self.pids}

    def seeds(self, u: Understanding) -> dict[str, float]:
        s: dict[str, float] = {}

        def add(node, w):
            s[node] = max(s.get(node, 0.0), w)

        for g in u.goals:
            add(nid("goal", g), 1.0)
        for c in u.concerns:
            add(nid("concern", c), 1.0)
        for i in u.requested_ingredients:
            add(nid("ingredient", i), 1.3)
        for st in u.steps:
            add(nid("step", st), 0.9)
        if u.skin:
            add(nid("skin", u.skin), 0.5)
        for pref in u.preferences:
            add(nid("claim", pref), 0.5)
        for pid in u.product_ids:
            if self.cat.by_id[pid]["domain"] != "medicamento":
                add(nid("product", pid), 1.0)
        return {k: v for k, v in s.items() if k in self.graph.g}

    def graph_scores(self, u: Understanding) -> dict[str, float]:
        act = self.graph.activation(self.seeds(u))
        return {pid: act.get(pid, 0.0) for pid in self.pids}

    # ------------------------------------------------------------ combinação
    @staticmethod
    def _unit(d: dict[str, float]) -> dict[str, float]:
        m = max(d.values()) if d else 0.0
        return {k: (v / m if m > 0 else 0.0) for k, v in d.items()}

    def channels(self, u: Understanding, query: str) -> dict[str, dict[str, float]]:
        return {"bm25": self._unit(self.bm25(query)), "emb": self._unit(self.embedding(query)),
                "graph": self._unit(self.graph_scores(u))}

    def score(self, u: Understanding, query: str, weights: dict | None = None) -> dict[str, float]:
        w = weights or self.weights
        ch = self.channels(u, query)
        return {pid: w["bm25"] * ch["bm25"][pid] + w["emb"] * ch["emb"][pid] + w["graph"] * ch["graph"][pid]
                for pid in self.pids}

    def rank(self, u: Understanding, query: str, k: int = 10, weights: dict | None = None) -> list[tuple[str, float]]:
        sc = self.score(u, query, weights)
        return sorted(sc.items(), key=lambda kv: (-kv[1], kv[0]))[:k]

    # ------------------------------------------------------------ segunda etapa (rerank)
    def _facets(self, pid: str) -> set[str]:
        p = self.cat.by_id[pid]
        return {f"t:{p['productType']}", f"b:{p['brand']}", *(f"c:{c}" for c in p["concerns"]),
                *(f"i:{i}" for i in p["ingredients"])}

    def rerank_mmr(self, ranked: list[tuple[str, float]], k: int = 10, lam: float = 0.8) -> list[tuple[str, float]]:
        """Relevância marginal máxima: escolhe um a um o produto que equilibra nota e novidade em relação aos já
        escolhidos (mesmo tipo, marca, preocupações e ingredientes contam como parecido). lam=1 desliga (só relevância)."""
        if lam >= 1.0 or len(ranked) <= 1:
            return ranked[:k]
        top = ranked[0][1] or 1.0
        pool = [(pid, sc / top) for pid, sc in ranked]
        chosen: list[tuple[str, float]] = []
        facets = {pid: self._facets(pid) for pid, _ in pool}
        while pool and len(chosen) < k:
            def mmr(item):
                pid, sc = item
                sim = max((len(facets[pid] & facets[c]) / len(facets[pid] | facets[c]) for c, _ in chosen), default=0.0)
                return lam * sc - (1 - lam) * sim
            best = max(pool, key=lambda it: (mmr(it), it[1], it[0]))
            pool.remove(best)
            chosen.append((best[0], best[1] * top))
        return chosen
