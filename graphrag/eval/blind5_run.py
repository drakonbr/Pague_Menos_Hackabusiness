"""Mede o grafo (sem DeepSeek) no conjunto cego blind5 (escrito por agente independente, 24/10/2026).
Metade A (índices pares) serve para diagnosticar e ajustar; metade B (ímpares) NÃO é olhada: só o total é impresso.
  python -m graphrag.eval.blind5_run          # A com detalhes, B só a contagem
"""
from __future__ import annotations

import sys

from graphrag.dialogue import Engine
from graphrag.eval import rag_blind5 as B
from graphrag.eval.rag_eval import _good


def main(show_b: bool = False) -> None:
    from graphrag.llm import DeepSeek
    e = Engine.build(llm=DeepSeek.from_env() if "--live" in sys.argv else None)
    cases = [(c, False) for c in B.BLIND5] + [(c, True) for c in B.BLIND5_ADJUST]
    for name, parity in (("A (diagnóstico)", 0), ("B (cego, só a contagem)", 1)):
        sub = [(c, adj) for i, (c, adj) in enumerate(cases) if i % 2 == parity]
        res = [(_good(e, c, adj)) for c, adj in sub]
        ok = sum(g for _, g in res)
        print(f"{name}: {ok}/{len(res)}")
        if parity == 0 or show_b:
            for q, g in res:
                if not g:
                    print("   ✗", q)


if __name__ == "__main__":
    main("--mostrar-b" in sys.argv)
