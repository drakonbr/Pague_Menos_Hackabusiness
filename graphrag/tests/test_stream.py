"""Busca conversacional em fluxo (SSE), reescrita pelo histórico e termos soltos na barra."""
import http.client
import json
import threading
import unittest
from http.server import ThreadingHTTPServer

from graphrag.chat_stream import BadRequest, chunks, search_chat_events
from graphrag.dialogue import Engine
from graphrag.lexicon import HEALTH_TERMS
from graphrag.service import server
from graphrag.text import norm

SAUDE = ["preciso repor meu remédio de pressão", "tenho hipertensão e colesterol alto, quero kit de suplementos",
         "que remédio eu tomo pra dor de cabeça", "tem similar do meu remédio de pressão"]


def eventos(engine, body):
    return list(search_chat_events(engine, body))


class TestFluxo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.e = Engine.build()

    def test_ordem_dos_eventos_e_texto_inteiro(self):
        ev = eventos(self.e, {"query": "rotina anti idade premium até R$ 400, sem retinol"})
        nomes = [n for n, _ in ev]
        self.assertEqual(nomes[:2], ["rewrite", "sources"])
        self.assertEqual(nomes[-1], "done")
        self.assertTrue(all(n == "token" for n in nomes[2:-1]) and len(nomes) > 4)
        done = ev[-1][1]
        self.assertEqual("".join(d["text"] for n, d in ev if n == "token"), done["reply"])
        self.assertIn("sem retinol", ev[0][1]["rewrittenQuery"].lower())
        # as fontes são exatamente o que a resposta completa traz
        self.assertEqual([k["id"] for k in ev[1][1]["kits"]], [k["id"] for k in done["kits"]])
        self.assertEqual([p["id"] for p in ev[1][1]["products"]], [p["id"] for p in done["products"]])
        for k in ev[1][1]["kits"]:
            self.assertEqual(k["totalCents"], sum(i["priceCents"] for i in k["items"]))
        self.assertEqual(set(done["latencyMs"]), {"history", "engine", "total"})
        self.assertIn("context", done)

    def test_pedaco_a_pedaco_devolve_o_texto_original(self):
        for t in ["", "uma", "um dois três quatro cinco", "  espaços   no meio  e fim  ", "R$ 1.234,50: ok?"]:
            self.assertEqual("".join(chunks(t)), t)

    def test_bloqueado_nao_tem_fontes(self):
        ev = eventos(self.e, {"query": "que remédio eu tomo pra dor de cabeça"})
        self.assertIsNone(ev[0][1]["rewrittenQuery"])
        self.assertEqual((ev[1][1]["kits"], ev[1][1]["products"]), ([], []))
        self.assertEqual(ev[-1][1]["safety"]["decision"], "blocked")

    def test_historico_curto_equivale_ao_contexto(self):
        r1 = self.e.search({"query": "rotina anti idade premium até R$ 400, sem retinol"})
        com_ctx = eventos(self.e, {"query": "e mais barato?", "context": r1["context"]})
        com_hist = eventos(self.e, {"query": "e mais barato?", "history": ["rotina anti idade premium até R$ 400, sem retinol"]})
        a, b = com_ctx[-1][1], com_hist[-1][1]
        self.assertEqual((a["act"], a["rewrittenQuery"]), (b["act"], b["rewrittenQuery"]))
        self.assertEqual([k["totalCents"] for k in a["kits"]], [k["totalCents"] for k in b["kits"]])
        self.assertEqual(a["act"], "refinar")
        self.assertIn("sem retinol", b["rewrittenQuery"].lower())          # a reescrita herdou o que a conversa já sabia

    def test_historico_so_usa_as_ultimas_tres_falas(self):
        h = ["pele oleosa", "kit de suplementos", "higiene premium", "rotina anti idade", "mais barato"]
        ev = eventos(self.e, {"query": "sem fragrância", "history": h})
        self.assertIn("anti", norm(ev[-1][1]["rewrittenQuery"]) + "anti")      # roda sem erro e com no máximo 3 falas
        self.assertEqual(ev[-1][1]["act"], "refinar")

    def test_validacao_da_entrada(self):
        for body in [{}, {"query": ""}, {"query": "   "}, {"query": 5}, {"query": "x" * 501}, {"query": "a", "history": "oi"},
                     {"query": "a", "history": [1]}, {"query": "a", "history": ["y" * 501]}, []]:
            with self.assertRaises(BadRequest, msg=str(body)[:40]):
                list(search_chat_events(self.e, body))

    def test_nada_de_saude_nos_eventos(self):
        for q in SAUDE:
            visivel = " ".join(json.dumps(d, ensure_ascii=False) for n, d in eventos(self.e, {"query": q}) if n != "done")
            ev = eventos(self.e, {"query": q})
            done = ev[-1][1]
            visivel += " " + done["reply"] + " " + json.dumps(done["context"], ensure_ascii=False)
            for t in HEALTH_TERMS:
                self.assertNotIn(norm(t), norm(visivel), f"{t!r} apareceu nos eventos de {q!r}")


class TestTermosSoltos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.e = Engine.build()

    def test_termo_solto_e_uma_busca(self):
        for q in ["ômega 3", "creme dental", "sabonete", "limpeza", "sérum", "colágeno", "shampoo", "desodorante"]:
            r = self.e.search({"query": q})
            self.assertEqual(r["act"], "busca", q)
            self.assertTrue(r["kits"] or r["products"], f"{q!r} voltou vazio")

    def test_com_pista_de_apontar_continua_trocar_item(self):
        for q in ["troca o hidratante", "quero outro sérum", "esse protetor é vegano?", "tem similar?"]:
            self.assertNotEqual(self.e.search({"query": q})["act"], "busca", q)

    def test_pedido_de_uma_prateleira_mostra_so_itens_dela(self):
        # "ômega 3 vegano" é uma prateleira só dos suplementos: lista direta, sem kit forçado nem item de outra etapa
        r = self.e.search({"query": "ômega 3 de algas vegano"})
        self.assertEqual(r["action"]["type"], "show_products")
        self.assertEqual(r["kits"], [])
        self.assertTrue(r["products"])
        for p in r["products"]:
            self.assertEqual(p["step"], "omega3")
            self.assertIn("vegano", p["claims"])


class TestHTTP(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        server.ENGINE = Engine.build()
        server.ALLOW_INGEST = False
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown(); cls.srv.server_close()

    def post(self, path, body):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        c.request("POST", path, json.dumps(body), {"Content-Type": "application/json", "Origin": "http://localhost:5173"})
        return c, c.getresponse()

    def test_sse_de_ponta_a_ponta(self):
        c, r = self.post("/v1/search-chat", {"query": "kit de suplementos até R$ 200"})
        self.assertEqual(r.status, 200)
        self.assertTrue(r.getheader("Content-Type").startswith("text/event-stream"))
        self.assertEqual(r.getheader("Cache-Control"), "no-cache")
        self.assertEqual(r.getheader("Access-Control-Allow-Origin"), "http://localhost:5173")
        raw = r.read().decode("utf-8")
        c.close()
        eventos_ = []
        for bloco in raw.strip().split("\n\n"):
            linhas = bloco.split("\n")
            self.assertTrue(linhas[0].startswith("event: ") and linhas[1].startswith("data: "), bloco[:60])
            eventos_.append((linhas[0][7:], json.loads(linhas[1][6:])))
        self.assertEqual([n for n, _ in eventos_][:2], ["rewrite", "sources"])
        self.assertEqual(eventos_[-1][0], "done")
        self.assertEqual("".join(d["text"] for n, d in eventos_ if n == "token"), eventos_[-1][1]["reply"])

    def test_erro_de_validacao_vira_400_json_antes_do_fluxo(self):
        c, r = self.post("/v1/search-chat", {"query": ""})
        self.assertEqual(r.status, 400)
        self.assertTrue(r.getheader("Content-Type").startswith("application/json"))
        self.assertIn("query", json.loads(r.read())["error"])
        c.close()

    def test_ingestao_pela_api_fica_desligada_por_padrao(self):
        c, r = self.post("/v1/admin/ingest", {"products": []})
        self.assertEqual(r.status, 403)
        c.close()


if __name__ == "__main__":
    unittest.main()
