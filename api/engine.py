"""Função da Vercel que serve o motor GraphRAG (o mesmo Handler de graphrag/service/server.py).

vercel.json reescreve /v1/<rota> para /api/engine?route=<rota>; aqui o caminho volta a ser /v1/<rota>.
O motor é montado uma vez por instância (cerca de 0,7 s) a partir dos artefatos já treinados.
"""
import os
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from graphrag.dialogue import Engine  # noqa: E402
from graphrag.llm import DeepSeek, rag_banner  # noqa: E402
from graphrag.service import server  # noqa: E402

os.environ.setdefault("RAG_EXTERNAL_DEFAULT", "off")   # #42: na Vercel, cliente sem o campo allowExternal NÃO leva a frase à DeepSeek
server.ENGINE = Engine.build(llm=DeepSeek.from_env())   # chave na variável DEEPSEEK_API_KEY da Vercel
print(rag_banner(server.ENGINE), file=sys.stderr, flush=True)      # aparece no log da função


class handler(server.Handler):
    def _route(self):
        u = urlsplit(self.path)
        route = parse_qs(u.query).get("route", [""])[0]
        if route:
            self.path = "/v1/" + route
        elif not u.path.startswith("/v1/"):
            self.path = u.path

    def do_GET(self):
        self._route()
        super().do_GET()

    def do_POST(self):
        self._route()
        super().do_POST()
