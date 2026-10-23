"""Busca conversacional em fluxo (SSE) para a barra de pesquisa.

Ordem dos eventos (`POST /v1/search-chat`, `text/event-stream`):

  rewrite  {rewrittenQuery, act}            o que foi entendido, para mostrar num chip logo de cara
  sources  {kits[], products[]}             cartões já prontos para desenhar (ids, nomes, preços, estoque)
  token    {text}                           a resposta em pedaços (vários eventos)
  done     {...resposta completa, latencyMs}  mesmo corpo de /v1/search (context, action, suggestions, safety...)

Honestidade: o texto da resposta é montado por regras (não por um modelo de linguagem), então fica pronto junto com os
cartões. Os pedaços de `token` servem para a tela mostrar a resposta aos poucos e deixam o contrato pronto para o dia
em que um modelo gerar o texto de verdade. Não há espera artificial entre eventos.

Histórico curto: o cliente pode mandar `context` (preferido, exato) OU `history` (até 3 falas anteriores da pessoa); com
`history` e sem `context` o motor reexecuta essas falas para reconstruir o estado. Só frases de busca viajam; nada de
dado de saúde é guardado no servidor.
"""
from __future__ import annotations

import re
import time
from typing import Iterator

MAX_HISTORY = 3
MAX_TEXT = 500


class BadRequest(ValueError):
    pass


def validate_body(body: dict) -> tuple[str, list[str]]:
    if not isinstance(body, dict):
        raise BadRequest("o corpo deve ser um objeto JSON")
    q = body.get("query")
    if not isinstance(q, str) or not q.strip():
        raise BadRequest("campo query é obrigatório")
    if len(q) > MAX_TEXT:
        raise BadRequest(f"query passa de {MAX_TEXT} caracteres")
    hist = body.get("history") or []
    if not isinstance(hist, list) or not all(isinstance(h, str) for h in hist):
        raise BadRequest("history deve ser uma lista de textos")
    if any(len(h) > MAX_TEXT for h in hist):
        raise BadRequest(f"cada fala de history deve ter até {MAX_TEXT} caracteres")
    return q, hist[-MAX_HISTORY:]


def replay(engine, history: list[str], base: dict) -> dict | None:
    """Reconstrói o `context` rodando as falas anteriores em ordem. Devolve o contexto da última."""
    ctx = None
    for text in history:
        req = {**base, "query": text}
        if ctx:
            req["context"] = ctx
        ctx = engine.search(req, rag=False).get("context") or ctx      # replay: só o grafo (uma chamada por busca)
    return ctx


def card(p: dict) -> dict:
    return {"id": p["id"], "name": p["name"], "brand": p["brand"], "step": p["step"], "productType": p["productType"],
            "priceCents": p["priceCents"], "listPriceCents": p["listPriceCents"], "inStock": p["stockQty"] > 0,
            "cashbackPct": p["cashbackPct"]}


def kit_card(k: dict) -> dict:
    return {"id": k["id"], "tier": k["tier"], "title": k["title"], "totalCents": k["totalCents"],
            "itemsTotalCents": k.get("itemsTotalCents"), "discountPct": k.get("discountPct"),
            "cashbackCents": k.get("cashbackCents", 0), "withinBudget": k.get("withinBudget"),
            "items": [{"step": i["step"], "productId": i["product"]["id"], "name": i["product"]["name"],
                       "priceCents": i["product"]["priceCents"]} for i in k["items"]]}


def chunks(text: str, words: int = 3) -> Iterator[str]:
    """Pedaços de `words` palavras que, concatenados, devolvem o texto original byte a byte."""
    parts = re.findall(r"\s*\S+\s*", text)
    if "".join(parts) != text:                  # texto vazio ou só espaços: nada para repartir
        parts = [text] if text else []
    for i in range(0, len(parts), words):
        yield "".join(parts[i:i + words])


def search_chat_events(engine, body: dict) -> Iterator[tuple[str, dict]]:
    t0 = time.perf_counter()
    query, history = validate_body(body)
    req = {k: v for k, v in body.items() if k not in ("history",)}
    if not req.get("context") and history:
        ctx = replay(engine, history, {k: v for k, v in req.items() if k in ("storeId",)})
        if ctx:
            req["context"] = ctx
    t1 = time.perf_counter()
    res = engine.search(req)
    t2 = time.perf_counter()
    yield "rewrite", {"rewrittenQuery": res.get("rewrittenQuery"), "act": res.get("act")}
    yield "sources", {"kits": [kit_card(k) for k in res["kits"]], "products": [card(p) for p in res["products"]],
                      "closestKit": kit_card(res["closestKit"]) if res.get("closestKit") else None}
    for piece in chunks(res["reply"]):
        yield "token", {"text": piece}
    ms = lambda a, b: round((b - a) * 1000, 1)                                  # noqa: E731
    yield "done", {**res, "latencyMs": {"history": ms(t0, t1), "engine": ms(t1, t2), "total": ms(t0, time.perf_counter())}}


def sse(event: str, data: dict) -> bytes:
    import json
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n".encode("utf-8")
