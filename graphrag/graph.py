"""Grafo de conhecimento (a parte "Graph" do GraphRAG), construído do zero a partir do catálogo.

Nós: Product, Brand, Ingredient, Concern, Goal, Step, SkinType, Claim, Warning, ProductType, Domain, EquivGroup.
Arestas (doc 06, mais as que a persona exigiu):
  OF_BRAND, CONTAINS, ADDRESSES, SUITS, COVERS, HAS_CLAIM, HAS_WARNING, OF_TYPE, IN_DOMAIN,
  TARGETS (Goal->Concern), REQUIRES (Goal->Step), CONFLICTS_WITH (Ingredient->Ingredient),
  EQUIVALENT_TO (Product<->Product, só medicamento: mesmo princípio ativo e dose),
  SIMILAR_TO (Product->Product, calculada: mesma etapa, preocupações e ingredientes parecidos).

Preço e estoque NÃO entram no grafo (consulta viva, doc 06).
"""
from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path

import networkx as nx

from .data import Catalog

ARTIFACTS = Path(__file__).resolve().parent / "artifacts"

# quanto de "ativação" cada tipo de aresta passa adiante na recuperação em grafo
EDGE_WEIGHT = {
    "TARGETS": 1.0, "ADDRESSES": 1.0, "CONTAINS": 0.8, "COVERS": 0.6, "SUITS": 0.5, "HAS_CLAIM": 0.6,
    "OF_BRAND": 0.4, "OF_TYPE": 0.7, "SIMILAR_TO": 0.3, "REQUIRES": 0.5, "IN_DOMAIN": 0.2,
}


def nid(kind: str, key: str) -> str:
    return f"{kind}:{key}"


def jaccard(a, b) -> float:
    a, b = set(a), set(b)
    return len(a & b) / len(a | b) if a | b else 0.0


class KnowledgeGraph:
    def __init__(self, g: nx.MultiDiGraph):
        self.g = g
        # adjacência não direcionada com peso, para a recuperação
        self.adj: dict[str, list[tuple[str, float, str]]] = defaultdict(list)
        for u, v, d in g.edges(data=True):
            w = EDGE_WEIGHT.get(d["type"], 0.2)
            if d["type"] in ("CONFLICTS_WITH", "EQUIVALENT_TO"):
                continue
            self.adj[u].append((v, w, d["type"]))
            self.adj[v].append((u, w, d["type"]))
        self.degree = {n: max(1, len(es)) for n, es in self.adj.items()}

    # ------------------------------------------------------------ consultas
    def neighbors(self, node: str, etype: str | None = None, direction: str = "out") -> list[str]:
        if direction == "out":
            return [v for _, v, d in self.g.out_edges(node, data=True) if etype is None or d["type"] == etype]
        return [u for u, _, d in self.g.in_edges(node, data=True) if etype is None or d["type"] == etype]

    def equivalents(self, product_id: str) -> list[str]:
        n = nid("product", product_id)
        return sorted({v.split(":", 1)[1] for _, v, d in self.g.out_edges(n, data=True) if d["type"] == "EQUIVALENT_TO"})

    def similar(self, product_id: str, k: int = 8) -> list[tuple[str, float]]:
        n = nid("product", product_id)
        out = [(v.split(":", 1)[1], d["weight"]) for _, v, d in self.g.out_edges(n, data=True) if d["type"] == "SIMILAR_TO"]
        return sorted(out, key=lambda x: (-x[1], x[0]))[:k]

    def activation(self, seeds: dict[str, float], hops: int = 3, decay: float = 0.55) -> dict[str, float]:
        """Ativação espalhada: cada salto passa peso*decay para os vizinhos, amortecido pelo grau do nó
        (evita que nós muito comuns, como 'todas as peles', dominem). Retorna só produtos."""
        total: dict[str, float] = defaultdict(float)
        frontier = dict(seeds)
        for n, v in seeds.items():
            total[n] += v
        for _ in range(hops):
            nxt: dict[str, float] = defaultdict(float)
            for n, val in frontier.items():
                for m, w, _t in self.adj.get(n, ()):
                    nxt[m] += val * w * decay / math.sqrt(self.degree[n])
            for n, v in nxt.items():
                total[n] += v
            frontier = nxt
        return {n.split(":", 1)[1]: v for n, v in total.items() if n.startswith("product:")}

    def stats(self) -> dict:
        kinds = defaultdict(int)
        for n in self.g.nodes:
            kinds[n.split(":", 1)[0]] += 1
        etypes = defaultdict(int)
        for _, _, d in self.g.edges(data=True):
            etypes[d["type"]] += 1
        return {"nodes": dict(sorted(kinds.items())), "edges": dict(sorted(etypes.items())),
                "totalNodes": self.g.number_of_nodes(), "totalEdges": self.g.number_of_edges()}

    # ------------------------------------------------------------ persistência
    def save(self, path: Path | None = None) -> Path:
        path = path or ARTIFACTS / "graph.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        nodes = [{"id": n, **{k: v for k, v in d.items()}} for n, d in sorted(self.g.nodes(data=True))]
        edges = sorted(
            ({"from": u, "to": v, **d} for u, v, d in self.g.edges(data=True)),
            key=lambda e: (e["from"], e["to"], e["type"]),
        )
        path.write_text(json.dumps({"nodes": nodes, "edges": edges, "stats": self.stats()},
                                   ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        return path


def build_graph(cat: Catalog) -> KnowledgeGraph:
    g = nx.MultiDiGraph()

    def add(kind, key, **attrs):
        g.add_node(nid(kind, key), kind=kind, **attrs)

    def edge(u, v, etype, **attrs):
        g.add_edge(u, v, type=etype, **attrs)

    for sid, label in cat.steps.items():
        add("step", sid, label=label)
    for cid, label in cat.concerns.items():
        add("concern", cid, label=label)
    for ing in cat.ingredients.values():
        add("ingredient", ing["id"], label=ing["name"], family=ing["family"], function=ing["function"],
            photosensitizing=ing["photosensitizing"])
    for code, text in cat.warnings.items():
        add("warning", code, label=text)
    for skin in ("oleosa", "mista", "seca", "normal", "sensível", "todas"):
        add("skin", skin, label=skin)
    for d in ("dermo", "suplemento", "higiene", "medicamento"):
        add("domain", d, label=d)

    for goal in cat.goals:
        add("goal", goal["id"], label=goal["label"], synonyms=goal["synonyms"])
        for c in goal["concerns"]:
            edge(nid("goal", goal["id"]), nid("concern", c), "TARGETS")
        for s in goal["required_steps"]:
            edge(nid("goal", goal["id"]), nid("step", s), "REQUIRES", required=True)
        for s in goal["optional_steps"]:
            edge(nid("goal", goal["id"]), nid("step", s), "REQUIRES", required=False)

    for i in cat.interactions:
        edge(nid("ingredient", i["a"]), nid("ingredient", i["b"]), "CONFLICTS_WITH", severity=i["severity"], reason=i["reason"])
        edge(nid("ingredient", i["b"]), nid("ingredient", i["a"]), "CONFLICTS_WITH", severity=i["severity"], reason=i["reason"])

    for p in cat.products:
        pn = nid("product", p["id"])
        add("product", p["id"], label=p["name"], brand=p["brand"], step=p["step"], domain=p["domain"])
        add("brand", p["brand"], label=p["brand"])
        add("ptype", p["productType"], label=p["productType"])
        edge(pn, nid("brand", p["brand"]), "OF_BRAND")
        edge(pn, nid("ptype", p["productType"]), "OF_TYPE")
        edge(pn, nid("domain", p["domain"]), "IN_DOMAIN")
        for s in p["coversSteps"]:
            edge(pn, nid("step", s), "COVERS", primary=(s == p["step"]))
        for c in p["concerns"]:
            edge(pn, nid("concern", c), "ADDRESSES")
        for i in p["ingredients"]:
            edge(pn, nid("ingredient", i), "CONTAINS")
        for sk in p["skinTypes"]:
            edge(pn, nid("skin", sk), "SUITS")
        for cl in p["claims"]:
            add("claim", cl, label=cl)
            edge(pn, nid("claim", cl), "HAS_CLAIM")
        for w in p["warnings"]:
            edge(pn, nid("warning", w), "HAS_WARNING")

    # equivalência (medicamento): mesmo princípio ativo e dose, apresentações diferentes
    groups: dict[str, list[dict]] = defaultdict(list)
    for p in cat.products:
        if p["equivalence"]:
            groups[p["equivalence"]["group"]].append(p)
    for gid, items in groups.items():
        add("equiv", gid, label=f"{items[0]['equivalence']['active']} {items[0]['equivalence']['dose']}")
        for a in items:
            edge(nid("product", a["id"]), nid("equiv", gid), "IN_EQUIV_GROUP", presentation=a["equivalence"]["presentation"])
            for b in items:
                if a["id"] != b["id"]:
                    edge(nid("product", a["id"]), nid("product", b["id"]), "EQUIVALENT_TO",
                         presentation=b["equivalence"]["presentation"])

    # similaridade calculada (vizinhos mais próximos dentro da mesma etapa e domínio)
    by_step: dict[str, list[dict]] = defaultdict(list)
    for p in cat.products:
        by_step[p["step"]].append(p)
    for step, items in by_step.items():
        for a in items:
            scored = []
            for b in items:
                if a["id"] == b["id"]:
                    continue
                near_price = 1.0 - min(1.0, abs(a["priceCents"] - b["priceCents"]) / max(a["priceCents"], b["priceCents"]))
                s = (0.40 * jaccard(a["concerns"], b["concerns"]) + 0.30 * jaccard(a["ingredients"], b["ingredients"])
                     + 0.10 * (a["brand"] == b["brand"]) + 0.10 * near_price
                     + 0.10 * jaccard(a["skinTypes"], b["skinTypes"]))
                scored.append((round(s, 4), b["id"]))
            for s, bid in sorted(scored, key=lambda x: (-x[0], x[1]))[:6]:
                edge(nid("product", a["id"]), nid("product", bid), "SIMILAR_TO", weight=s)

    return KnowledgeGraph(g)
