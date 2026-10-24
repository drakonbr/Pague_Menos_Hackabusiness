"""Servidor HTTP do motor (biblioteca padrão do Python, sem framework). Contrato: contracts/README.md.

  python -m graphrag.service.server --port 8787

O motor lê SÓ o catálogo sintético. Dados da pessoa (persona, receitas, histórico) ficam no aparelho; o app envia
apenas a frase, o `context` devolvido na resposta anterior e ids de produto.
"""
from __future__ import annotations

import argparse
import json
import sys
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from graphrag.chat_stream import BadRequest, search_chat_events, sse        # noqa: E402
from graphrag.dialogue import Engine, api_adapt, api_swap, api_swap_options  # noqa: E402
from graphrag.llm import DeepSeek, rag_banner  # noqa: E402

ENGINE: Engine | None = None
ALLOW_INGEST = False
LOCAL_ORIGINS = ("http://localhost", "http://127.0.0.1", "http://[::1]")


class Handler(BaseHTTPRequestHandler):
    server_version = "GraphRAGLocal/1.0"

    def log_message(self, fmt, *args):      # silencioso: nada da frase da pessoa vai para o log
        pass

    def _cors(self):
        origin = self.headers.get("Origin", "")
        if origin.startswith(LOCAL_ORIGINS):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")

    def _send(self, code: int, body: dict):
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self._cors()
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path == "/v1/health":
            e = ENGINE
            self._send(200, {"ok": True, "products": len(e.cat.products), "graph": e.graph.stats()["totalNodes"],
                             "vocab": len(e.wv.vocab), "weights": {k: e.weights[k] for k in ("bm25", "emb", "graph")},
                             "rag": e.rag is not None, "ragCalls": dict(e.stats)})   # #60: sem chave, a busca fica pior em silêncio
        else:
            self._send(404, {"error": "rota inexistente"})

    def _stream_chat(self, body: dict):
        """SSE: erros de validação saem como 400 JSON ANTES de abrir o fluxo; depois disso, só eventos."""
        events = search_chat_events(ENGINE, body)
        first = next(events)                       # roda o motor; BadRequest sobe daqui, ainda sem cabeçalho enviado
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Accel-Buffering", "no")
        self.send_header("Connection", "close")
        self._cors()
        self.end_headers()
        try:
            self.wfile.write(sse(*first)); self.wfile.flush()
            for ev in events:
                self.wfile.write(sse(*ev)); self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass                                   # a pessoa fechou a aba no meio da resposta
        self.close_connection = True

    def do_POST(self):
        try:
            n = int(self.headers.get("Content-Length", "0"))
            if n > 200_000:
                return self._send(413, {"error": "corpo grande demais"})
            body = json.loads(self.rfile.read(n) or b"{}")
            e = ENGINE
            if self.path == "/v1/search-chat":
                return self._stream_chat(body)
            if self.path == "/v1/admin/ingest":
                if not ALLOW_INGEST:
                    return self._send(403, {"error": "ingestão desligada (suba o servidor com --allow-ingest)"})
                records = body["products"] if isinstance(body, dict) else body
                return self._send(200, e.ingest(records).as_dict())
            if self.path == "/v1/search":
                if not isinstance(body.get("query"), str):
                    return self._send(400, {"error": "campo query é obrigatório"})
                return self._send(200, e.search(body))
            if self.path == "/v1/kits/swap-options":
                return self._send(200, api_swap_options(e, body["kit"], body["step"], body["intent"]))
            if self.path == "/v1/kits/swap":
                return self._send(200, api_swap(e, body["kit"], body["step"], body["productId"], body["intent"]))
            if self.path == "/v1/kits/adapt-to-store":
                return self._send(200, api_adapt(e, body["kit"], body["storeId"], body["intent"]))
            if self.path == "/v1/similars":
                return self._send(200, e.similars(body["productId"], body.get("storeId")))
            if self.path == "/v1/delivery-quote":
                return self._send(200, {"options": e.delivery_quote(int(body["totalCents"]))})
            return self._send(404, {"error": "rota inexistente"})
        except (KeyError, ValueError, BadRequest) as ex:
            return self._send(400, {"error": str(ex)})
        except Exception:                      # noqa: BLE001
            traceback.print_exc()
            return self._send(500, {"error": "erro interno"})


def main():
    global ENGINE, ALLOW_INGEST
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8787)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--allow-ingest", action="store_true", help="liga POST /v1/admin/ingest (só para uso local)")
    a = ap.parse_args()
    ALLOW_INGEST = a.allow_ingest
    ENGINE = Engine.build(llm=DeepSeek.from_env())     # sem DEEPSEEK_API_KEY: só o grafo
    print(rag_banner(ENGINE), flush=True)
    srv = ThreadingHTTPServer((a.host, a.port), Handler)
    print(f"GraphRAG local em http://{a.host}:{a.port}  (GET /v1/health)")
    srv.serve_forever()


if __name__ == "__main__":
    main()
