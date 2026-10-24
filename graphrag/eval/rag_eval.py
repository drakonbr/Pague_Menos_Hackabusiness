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
        if goal in vals:
            return True
        # objetivo de saúde vira lista, sem objetivo na intenção (#40): vale se a maioria dos itens trata o objetivo
        shown = _shown(r)
        for g in vals:
            gc = set(cat.goal_by_id[g]["concerns"]) if g in cat.goal_by_id else set()
            if shown and gc and sum(bool(gc & set(p["concerns"])) for p in shown) * 2 >= len(shown) and not r["kits"]:
                return True
        return False
    if kind == "concern":
        gc = set(cat.goal_by_id[goal]["concerns"]) if goal in cat.goal_by_id else set()
        shown = _shown(r)                         # sem objetivo: a maioria do que aparece trata a preocupação
        return bool(set(vals) & gc) or (bool(shown) and sum(bool(set(vals) & set(p["concerns"])) for p in shown) * 2 >= len(shown))
    if kind == "nomed":                       # #61: resposta que não era de saúde não pode virar lista de remédio
        return not any(p["domain"] == "medicamento" for p in _shown(r))
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


def _good(E, case, adjust) -> tuple[str, bool]:
    if adjust:
        base_q, q, rule = case
        base = E.search({"query": base_q})
        r = E.search({"query": q, "context": base["context"]})
        good = ok_adjust(base, r, rule)
    else:
        q, rule = case
        r = E.search({"query": q})
        good = ok_search(E.cat, r, rule)
    return q, good and not check_response(r)


def run(E, cases, adjust, graph=None) -> tuple[int, list, float, list]:
    """Devolve acertos, erros, tempo médio e, se `graph` vier, as frases que o grafo acertava e o RAG ESTRAGOU."""
    hits, fails, broke, t0 = 0, [], [], time.time()
    for case in cases:
        q, good = _good(E, case, adjust)
        hits += good
        if not good:
            fails.append(q)
            if graph is not None and _good(graph, case, adjust)[1]:
                broke.append(q)
    return hits, fails, (time.time() - t0) / max(1, len(cases)), broke


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    a = ap.parse_args()
    lines = ["# Avaliação do RAG com DeepSeek (#33, #38, #61 e #62)", "",
             "Frases que o grafo não entendia em 23/10 (graphrag/eval/rag_set.py). Acerto = regra do caso e nenhuma "
             "violação das invariantes. AMPLO = 43 frases do dia a dia (a cada 3ª é TESTE, nunca usada para ajustar o "
             "vocabulário). Depois do #62 o grafo sozinho já entende parte dos conjuntos antigos: compare com os números "
             "do dia 23/10 antes do vocabulário (grafo 1 de 18 nos conjuntos TRAIN, TEST e NOVO).", ""]
    sets = [("TRAIN busca", rag_set.TRAIN, False), ("TRAIN ajuste", rag_set.TRAIN_ADJUST, True),
            ("TEST busca", rag_set.TEST, False), ("TEST ajuste", rag_set.TEST_ADJUST, True),
            ("NOVO busca", rag_set.NOVO, False), ("NOVO ajuste", rag_set.NOVO_ADJUST, True),
            ("AMPLO ajuste", rag_set.AMPLO_TRAIN, False), ("AMPLO teste", rag_set.AMPLO_TEST, False),
            ("RISCO controle", rag_set.RISCO, False)]
    graph = Engine.build()
    engines = [("só o grafo", graph)]
    live = DeepSeek.from_env() if a.live else None
    if a.live and not live:
        raise SystemExit("sem DEEPSEEK_API_KEY")
    if live:
        engines.append(("grafo + DeepSeek", Engine.build(llm=live)))
    lines += ["| Conjunto | n | " + " | ".join(n for n, _ in engines) + " |", "|---|---|" + "---|" * len(engines)]
    fails_by, broken = {}, []
    for label, cases, adj in sets:
        row = [label, str(len(cases))]
        for name, E in engines:
            hits, fails, dt, broke = run(E, cases, adj, graph if E is not graph else None)
            row.append(f"{hits}/{len(cases)} ({dt:.1f} s/frase)")
            fails_by.setdefault(name, []).extend(fails)
            broken += broke
        lines.append("| " + " | ".join(row) + " |")
    lines += ["", "Frases que o grafo acertava e a DeepSeek estragou: " + ("; ".join(broken) if broken else "nenhuma")]
    for name, f in fails_by.items():
        lines += ["", f"Erros ({name}): " + ("; ".join(f) if f else "nenhum")]

    # taxa de chamadas: cliente que só conta (devolve None, então a resposta é a do grafo). TODOS os conjuntos do motor, inclusive
    # os cegos, porque a amostra afinada (TRAIN e TEST) subestima: frase de balcão tem mais palavra que o catálogo não conhece.
    cnt = Counter()
    E = Engine.build(llm=cnt)
    lines += ["", "Chamadas à DeepSeek por conjunto de busca do motor (sem gastar nada):", "",
              "| Conjunto | frases | chamadas | taxa |", "|---|---|---|---|"]
    tot_n = tot_c = 0
    for name, cases in (("TRAIN", search_set.TRAIN), ("TEST", search_set.TEST), ("BLIND", search_set.BLIND), ("BLIND2", search_set.BLIND2),
                        ("BLIND3", search_set.BLIND3), ("BLIND4", search_set.BLIND4), ("MED", search_set.MED), ("MED_BLIND", search_set.MED_BLIND)):
        before = cnt.calls
        for q, _ in cases:
            E.search({"query": q})
        c = cnt.calls - before
        tot_n += len(cases); tot_c += c
        lines.append(f"| {name} | {len(cases)} | {c} | {100 * c / len(cases):.0f}% |")
    before = cnt.calls
    for q, _ in rag_set.AMPLO:
        E.search({"query": q})
    lines += [f"| AMPLO (dia a dia) | {len(rag_set.AMPLO)} | {cnt.calls - before} | {100 * (cnt.calls - before) / len(rag_set.AMPLO):.0f}% |",
              f"| **Total do motor** | {tot_n} | {tot_c} | {100 * tot_c / tot_n:.1f}% |", "",
              "Cada chamada leva cerca de 1,3 s e custa uma fração de centavo; o cache evita repetir a mesma frase.", ""]
    if live:
        lines.append(f"Chamadas reais feitas nesta avaliação: {live.calls} (com cache).")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
