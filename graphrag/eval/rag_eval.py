"""Avaliação do RAG com DeepSeek (#33 e #38): grafo sozinho x grafo + DeepSeek, e quantas buscas chamariam a API.

    python -m graphrag.eval.rag_eval            # só o grafo e a contagem de chamadas (sem gastar nada)
    python -m graphrag.eval.rag_eval --live     # também com a DeepSeek de verdade (precisa de DEEPSEEK_API_KEY)

Grava o relatório em graphrag/eval/report_rag.md.
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

from graphrag.dialogue import Engine
from graphrag.eval import rag_set, search_set
from graphrag.eval.invariants import check_response
from graphrag.llm import DeepSeek

OUT = Path(__file__).with_name("report_rag.md")


class Counter:
    """Cliente falso que só conta: devolve None (como API fora do ar), então a resposta é a do grafo."""
    def __init__(self):
        self.calls = 0

    def complete(self, system, user):
        self.calls += 1
        return None


def _shown(r):
    return [i["product"] for k in r["kits"] for i in k["items"]] + r["products"][:5]


def ok_search(cat, r, rule) -> bool:
    kind, *vals = rule
    if kind == "missing":
        return not r["kits"] and not r["products"]
    goal = r["intent"].get("primaryGoal")
    if kind == "goal":
        return goal in vals
    if kind == "concern":
        gc = set(cat.goal_by_id[goal]["concerns"]) if goal in cat.goal_by_id else set()
        shown = _shown(r)                         # sem objetivo: a maioria do que aparece trata a preocupação
        return bool(set(vals) & gc) or (bool(shown) and sum(bool(set(vals) & set(p["concerns"])) for p in shown) * 2 >= len(shown))
    if kind == "step":
        return any(set(vals) & set(p["coversSteps"]) for p in _shown(r))
    raise ValueError(rule)


def ok_adjust(base, r, rule) -> bool:
    kind, *vals = rule
    i = r["intent"]
    if kind == "any":
        return any(ok_adjust(base, r, v) for v in vals)
    if kind == "pref":
        return vals[0] in (i.get("preferences") or [])
    if kind == "skin":
        return i.get("skinType") == vals[0]
    tots = [k["totalCents"] for k in base["kits"]]
    focus = next((k["totalCents"] for k in base["kits"] if k["tier"] == "essencial"), max(tots))
    if kind == "cheaper":                      # o motor faz "mais barato" = 85% do kit em foco (Essencial)
        return i.get("budgetCents") is not None and i["budgetCents"] < focus
    if kind == "richer":
        return i.get("budgetCents") is not None and i["budgetCents"] > max(tots)
    if kind == "excl":
        return any(x.startswith(vals[0]) for x in (r["context"].get("excluded") or []))
    raise ValueError(rule)


def run(E, cases, adjust) -> tuple[int, list, float]:
    hits, fails, t0 = 0, [], time.time()
    for case in cases:
        if adjust:
            base_q, q, rule = case
            base = E.search({"query": base_q})
            r = E.search({"query": q, "context": base["context"]})
            good = ok_adjust(base, r, rule)
        else:
            q, rule = case
            r = E.search({"query": q})
            good = ok_search(E.cat, r, rule)
        good = good and not check_response(r)
        hits += good
        if not good:
            fails.append(q)
    return hits, fails, (time.time() - t0) / max(1, len(cases))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    a = ap.parse_args()
    lines = ["# Avaliação do RAG com DeepSeek (#33 e #38)", "",
             "Frases que o grafo não entendia em 23/10 (graphrag/eval/rag_set.py). Acerto = regra do caso e nenhuma "
             "violação das invariantes.", ""]
    sets = [("TRAIN busca", rag_set.TRAIN, False), ("TRAIN ajuste", rag_set.TRAIN_ADJUST, True),
            ("TEST busca", rag_set.TEST, False), ("TEST ajuste", rag_set.TEST_ADJUST, True),
            ("NOVO busca", rag_set.NOVO, False), ("NOVO ajuste", rag_set.NOVO_ADJUST, True)]
    graph = Engine.build()
    engines = [("só o grafo", graph)]
    live = DeepSeek.from_env() if a.live else None
    if a.live and not live:
        raise SystemExit("sem DEEPSEEK_API_KEY")
    if live:
        engines.append(("grafo + DeepSeek", Engine.build(llm=live)))
    lines += ["| Conjunto | n | " + " | ".join(n for n, _ in engines) + " |", "|---|---|" + "---|" * len(engines)]
    fails_by = {}
    for label, cases, adj in sets:
        row = [label, str(len(cases))]
        for name, E in engines:
            hits, fails, dt = run(E, cases, adj)
            row.append(f"{hits}/{len(cases)} ({dt:.1f} s/frase)")
            fails_by.setdefault(name, []).extend(fails)
        lines.append("| " + " | ".join(row) + " |")
    for name, f in fails_by.items():
        lines += ["", f"Erros ({name}): " + ("; ".join(f) if f else "nenhum")]

    # quantas buscas chamariam a DeepSeek: todo o conjunto de busca do motor (o grafo acerta a maioria) + o deste RAG
    cnt = Counter()
    E = Engine.build(llm=cnt)
    qs = [q for q, _ in search_set.TRAIN + search_set.TEST]
    for q in qs:
        E.search({"query": q})
    base_calls = cnt.calls
    for q, _ in rag_set.TRAIN + rag_set.TEST + rag_set.NOVO:
        E.search({"query": q})
    total = len(qs) + len(rag_set.TRAIN) + len(rag_set.TEST) + len(rag_set.NOVO)
    lines += ["", f"Chamadas à DeepSeek: {base_calls} de {len(qs)} frases do conjunto de busca do motor "
                  f"({100 * base_calls / len(qs):.0f}%); {cnt.calls} de {total} contando as frases deste RAG "
                  f"({100 * cnt.calls / total:.0f}%). Meta do #34: abaixo de 15% no conjunto do motor.", ""]
    if live:
        lines.append(f"Chamadas reais feitas nesta avaliação: {live.calls} (com cache).")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
