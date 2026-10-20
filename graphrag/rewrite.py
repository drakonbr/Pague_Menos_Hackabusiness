"""Reescrita da consulta: transforma o pedido de agora MAIS o que a conversa já sabia numa frase autônoma.

Exemplo: depois de "rotina anti idade" e "sem retinol", o pedido "e até R$ 300?" vira
"Rotina anti-idade, sem retinol, até R$ 300,00". A frase serve para mostrar à pessoa o que foi buscado (chip na barra)
e para depurar. A recuperação em si já usa o estado estruturado (`context`), que é mais preciso do que reescrever texto.

Só usa rótulos do catálogo (objetivo, etapa, preocupação, ingrediente, preferência) e valores: nunca devolve o texto
digitado nem qualquer coisa de saúde da pessoa.
"""
from __future__ import annotations

from .composer import list_pt
from .data import Catalog
from .text import money

PEOPLE_FREE = {"oleosa": "pele oleosa", "mista": "pele mista", "seca": "pele seca", "normal": "pele normal",
               "sensível": "pele sensível"}


def rewrite_query(cat: Catalog, u, res: dict) -> str | None:
    """`u` = Understanding do pedido atual; `res` = resposta já montada (intent, context, act)."""
    if res.get("safety", {}).get("decision") == "blocked" or res.get("act") in {"repor_medicamento", "similar"}:
        return None
    ctx = res.get("context") or {}
    intent = res.get("intent") or {}
    parts: list[str] = []
    goal = intent.get("primaryGoal")
    if goal and goal in cat.goal_by_id:
        parts.append(cat.goal_by_id[goal]["label"])
    else:
        parts += [cat.steps[s].lower() for s in u.steps if s in cat.steps]
        parts += [cat.concerns[c] for c in u.concerns if c in cat.concerns]
    if not parts:
        return None
    ing = lambda i: cat.ingredients[i]["name"].lower() if i in cat.ingredients else i          # noqa: E731
    requested = ctx.get("requested") if ctx else u.requested_ingredients
    excluded = ctx.get("excluded") if ctx else u.excluded_ingredients
    if requested:
        parts.append("com " + list_pt([ing(i) for i in requested]))
    if excluded:
        parts.append("sem " + list_pt([ing(i) for i in excluded]))
    if intent.get("skinType"):
        parts.append(PEOPLE_FREE.get(intent["skinType"], str(intent["skinType"])))
    parts += list(intent.get("preferences") or [])
    if intent.get("budgetCents"):
        parts.append(f"até {money(intent['budgetCents'])}")
    text = ", ".join(parts)
    return text[0].upper() + text[1:]
