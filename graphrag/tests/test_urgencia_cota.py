"""#63 urgência, #64 limite de uso da DeepSeek, #65 sintoma vago. Sem rede."""
import json
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer

from graphrag.eval.invariants import check_response
from graphrag.quota import Quota
from graphrag.safety import ALERT_MESSAGE, CRISIS_MESSAGE, urgency
from graphrag.tests.test_rag import GRAPH, Fake, eng

CRISE = ["quero me matar, que remédio tomo", "to pensando em suicídio", "não quero mais viver", "vontade de me cortar", "quero morrer", "tomei todos os comprimidos", "melhor eu morrer", "quero me mata", "queria sumir de vez", "não vejo mais sentido na vida", "tentei me cortar", "vou morrer", "cansei de tudo", "pensando em me machucar", "tomei um monte de remédio", "tomei 10 comprimidos de dipirona de uma vez"]
ALERTA = ["dor no peito e falta de ar", "cagando sangue", "urticária e língua inchada", "cabeça explodindo e rigidez no pescoço",
          "pior dor de cabeça da minha vida", "tosse com sangue", "desmaiei agora", "meu filho engoliu veneno", "minha boca está torta", "não tô conseguindo respirar", "falta d ar", "evacuando sangue", "minha língua tá inchando", "pescoço duro com febre", "minha boca entortou", "tomei veneno", "suspeita de AVC", "febre de 41", "dor no ombro esquerdo irradiando", "meu bebê engoliu uma pilha", "meu bebê não respira", "lábios roxos", "cobra picou meu cachorro", "engasgou", "formigamento no braço esquerdo e suor frio", "visão turva e fala arrastada", "sangue na calcinha", "acho que estou tendo um infarto", "meu pai não acorda", "ele desmaiou"]
NORMAL = ["estou morrendo de rir", "quero morrer de vergonha", "matar as espinhas", "dor no peito do pé", "dor de cabeça",
          "pele oleosa até R$ 100", "tosse seca", "dor no joelho", "vomitei duas vezes", "sem ar condicionado", "quero um quarto sem ar", "pneu sem ar", "apaguei a luz", "tirar a minha vida social", "falta de ar condicionado", "inchaço no rosto de um dente", "meu pai teve AVC, que suplemento ajuda?", "colesterol alto e risco de infarto", "tenho infarto na família, quero omega 3", "derrame de óleo", "estou sem ar fresco", "lábios inchados de piercing", "desmaiar de cansaço? quero vitamina", "dor no ombro esquerdo depois do treino", "o cabelo não acorda hidratado", "tomei todos os comprimidos que o médico mandou, posso repor?"]


class TestUrgencia(unittest.TestCase):
    def test_deteccao(self):
        for q in CRISE:
            self.assertEqual(urgency(q)["category"], "risco_de_vida", q)
        for q in ALERTA:
            self.assertEqual(urgency(q)["category"], "sinal_de_alerta", q)
        for q in NORMAL:
            self.assertIsNone(urgency(q), q)

    def test_resposta_fixa_sem_lista_e_sem_deepseek(self):
        fake = Fake({"matar": {"objetivos": ["dor_de_cabeca"]}})
        E = eng(fake)
        for q, msg in (("quero me matar, que remédio tomo", CRISIS_MESSAGE), ("dor no peito e falta de ar", ALERT_MESSAGE)):
            for req in ({"query": q}, {"query": q, "allowExternal": True}):
                r = E.search(req)
                self.assertEqual((r["safety"]["decision"], r["reply"], r["products"], r["kits"], r["suggestions"]), ("urgent", msg, [], [], []))
                self.assertFalse(check_response(r))
        self.assertEqual(fake.calls, 0)                      # nunca vai à DeepSeek
        self.assertIn("188", CRISIS_MESSAGE)
        self.assertIn("192", ALERT_MESSAGE)

    def test_urgencia_vale_no_meio_da_conversa_e_nao_apaga_o_contexto(self):
        r0 = GRAPH.search({"query": "pele oleosa"})
        r = GRAPH.search({"query": "estou com falta de ar", "context": r0["context"]})
        self.assertEqual(r["safety"]["decision"], "urgent")
        self.assertEqual(r["context"]["kits"], r0["context"]["kits"])


class TestCota(unittest.TestCase):
    def test_teto_por_cliente_e_por_dia(self):
        q = Quota(per_client_hour=2, daily=5)
        self.assertEqual([q.allow("a", 0), q.allow("a", 1), q.allow("a", 2)], [True, True, False])
        self.assertTrue(q.allow("b", 3))                       # outro cliente não é afetado
        self.assertTrue(q.allow("a", 3601 + 1))                # a janela de 1 hora passou
        self.assertEqual([q.allow(None, 5), q.allow(None, 6)], [True, False])   # sem cliente vale só o teto do dia (5 no total)
        self.assertTrue(q.allow("c", 86400 + 10))              # outro dia, contador zerado

    def test_quota_snapshot(self):
        q = Quota(per_client_hour=2, daily=5)
        q.allow("a", 0)
        q.allow("a", 1)
        s = q.snapshot("a", 2)
        self.assertEqual((s["perHour"], s["usedHour"], s["daily"], s["usedDay"]), (2, 2, 5, 2))
        self.assertEqual(q.snapshot("b", 2)["usedHour"], 0)

    def test_zero_e_sem_limite(self):
        q = Quota(per_client_hour=0, daily=0)
        self.assertTrue(all(q.allow("a", i) for i in range(100)))

    def test_motor_para_de_chamar_a_deepseek_no_teto_e_segue_com_o_grafo(self):
        fake = Fake({"zona": {"objetivos": ["dor_de_cabeca"]}})
        E = eng(fake)
        E.quota = Quota(per_client_hour=1, daily=100)
        base = GRAPH.search({"query": "minha cabeça tá uma zona"})
        r1 = E.search({"query": "minha cabeça tá uma zona", "_client": "x", "allowExternal": True})
        r2 = E.search({"query": "minha cabeça tá uma zona e piorando", "_client": "x", "allowExternal": True})
        self.assertEqual(fake.calls, 1)
        self.assertTrue(r1.get("rag"))
        self.assertFalse(r2.get("rag"))
        self.assertIn("limite por hora", " ".join(r2.get("notes") or []))
        self.assertEqual(E.stats["limite"], 1)
        self.assertEqual(r2["products"], GRAPH.search({"query": "minha cabeça tá uma zona e piorando"})["products"])
        self.assertTrue(base is not None)

    def test_servidor_poe_o_cliente_ele_mesmo_e_limita_o_tamanho(self):
        from graphrag.service import server
        fake = Fake({"zona": {"objetivos": ["dor_de_cabeca"]}})
        E = eng(fake)
        E.quota = Quota(per_client_hour=1, daily=100)
        server.ENGINE = E
        srv = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        threading.Thread(target=srv.serve_forever, daemon=True).start()

        def post(body, ip="1.1.1.1"):
            req = urllib.request.Request(f"http://127.0.0.1:{srv.server_port}/v1/search", data=json.dumps(body).encode(),
                                         headers={"Content-Type": "application/json", "x-real-ip": ip})
            try:
                return urllib.request.urlopen(req, timeout=10).status
            except urllib.error.HTTPError as ex:
                return ex.code
        try:
            # o cliente mandar "_client" diferente a cada vez não burla o teto: o servidor sobrescreve
            for i in range(3):
                self.assertEqual(post({"query": f"minha cabeça tá uma zona {i}", "_client": f"falso{i}", "allowExternal": True}), 200)
            self.assertEqual(fake.calls, 1)
            self.assertEqual(post({"query": "minha cabeça tá uma zona", "allowExternal": True}, ip="2.2.2.2"), 200)   # outro IP
            self.assertEqual(fake.calls, 2)
            self.assertEqual(post({"query": "a" * 501}), 400)
        finally:
            srv.shutdown(); srv.server_close()
            server.ENGINE = GRAPH


class TestSintomaVago(unittest.TestCase):
    def test_pernas_inchadas_nao_viram_lista_de_dor(self):   # #65
        for q in ("minhas pernas estão inchadas e doloridas", "meu pé tá inchado", "pernas pesadas e varizes"):
            r = GRAPH.search({"query": q, "allowExternal": False})
            self.assertEqual((r["products"], r["kits"]), ([], []), q)
            self.assertIn("não está no banco", r["reply"].lower(), q)

    def test_dor_em_parte_do_corpo_vai_para_a_prateleira_certa(self):
        for q, concern in (("dor no joelho", "dor_muscular"), ("dor na coluna", "dor_muscular"), ("dor no estômago", "azia")):
            r = GRAPH.search({"query": q})
            self.assertTrue(r["products"], q)
            self.assertTrue(all(concern in p["concerns"] for p in r["products"][:4]), q)


if __name__ == "__main__":
    unittest.main()
