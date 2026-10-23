"""RAG com DeepSeek (#34 a #38), sem rede: um cliente falso devolve respostas fixas e conta as chamadas."""
import json
import os
import unittest
from unittest import mock

from graphrag.dialogue import Engine
from graphrag.eval import search_set
from graphrag.eval.invariants import check_response
from graphrag.llm import DeepSeek, Reader, _env_key, scrub

EMPTY = {"objetivos": [], "preocupacoes": [], "ingredientes": [], "etapas": [], "evitar": [], "preferencias": [],
         "orcamento_centavos": None, "pele": None, "ajuste": {"evitar": [], "preferencias": [], "orcamento": None, "pele": None}}


class Fake:
    """Responde pelo trecho do pedido; o que não estiver no roteiro devolve tudo vazio. `sent` guarda o que foi enviado."""
    def __init__(self, script=None, raw=None):
        self.script, self.raw, self.calls, self.sent = script or {}, raw, 0, []

    def complete(self, system, user):
        self.calls += 1
        self.sent.append(user)
        if self.raw is not None:
            return self.raw
        for k, v in self.script.items():
            if k in user.split("\n")[0]:
                return json.dumps({**EMPTY, **v, "ajuste": {**EMPTY["ajuste"], **v.get("ajuste", {})}})
        return json.dumps(EMPTY)


GRAPH = Engine.build()


def eng(fake):
    return Engine(GRAPH.cat, GRAPH.graph, GRAPH.wv, GRAPH.clf, llm=fake)


class TestRag(unittest.TestCase):
    def test_grafo_que_entende_nunca_chama_a_deepseek(self):
        fake = Fake()
        E = eng(fake)
        for q, _ in search_set.TRAIN + search_set.TEST:
            E.search({"query": q})
        base = E.search({"query": "pele oleosa"})
        for q in ("sem perfume", "mais barato", "sem retinol", "quero o essencial", "obrigado", "não", "não, obrigado",
                  "não gostei", "esse serve pra mim?", "pele oleosa", "obrigada, era isso"):
            E.search({"query": q, "context": base["context"]})
        self.assertEqual(fake.calls, 0)

    def test_pedido_que_o_grafo_nao_entende_vira_kits_do_motor(self):
        fake = Fake({"qwrtz": {"objetivos": ["oleosidade"]}})              # frase que o grafo não conhece
        r = eng(fake).search({"query": "aquele qwrtz pra cara"})
        self.assertEqual(fake.calls, 1)
        self.assertTrue(r.get("rag"))
        self.assertEqual(r["query"], "aquele qwrtz pra cara")              # a tela mostra o que a pessoa escreveu
        self.assertEqual([k["tier"] for k in r["kits"]], ["economico", "essencial", "completo"])
        self.assertNotIn("Entendi", r["reply"])
        self.assertFalse(check_response(r))
        same = GRAPH.search({"query": "controle de oleosidade"})["kits"]   # os mesmos kits que o grafo monta
        self.assertEqual([[i["product"]["id"] for i in k["items"]] for k in r["kits"]],
                         [[i["product"]["id"] for i in k["items"]] for k in same])

    def test_sintoma_que_o_grafo_nao_entende_vira_lista_de_remedios(self):
        fake = Fake({"latejando": {"objetivos": ["dor_de_cabeca"]}})
        r = eng(fake).search({"query": "minha cabeça tá latejando"})
        self.assertTrue(r.get("rag"))
        self.assertEqual(r["kits"], [])                                     # #40: remédio nunca em kit
        self.assertTrue(r["products"] and all(p["domain"] == "medicamento" for p in r["products"]))
        self.assertFalse(check_response(r))

    def test_gestacao_vale_na_busca_feita_pela_deepseek(self):
        fake = Fake({"latejando": {"objetivos": ["dor_de_cabeca"]}})
        q = "estou grávida e minha cabeça tá latejando"
        r = eng(fake).search({"query": q})
        self.assertEqual(fake.calls, 1)
        self.assertTrue(r["intent"]["pregnancy"])
        self.assertEqual(r["safety"]["decision"], GRAPH.search({"query": q})["safety"]["decision"])
        self.assertNotEqual(r["safety"]["decision"], "allow")
        self.assertTrue(r["context"]["intent"]["pregnancy"])                       # os próximos turnos continuam filtrando

    def test_replay_do_chat_nao_chama_a_deepseek(self):
        from graphrag.chat_stream import replay
        fake = Fake({"latejando": {"objetivos": ["dor_de_cabeca"]}})
        replay(eng(fake), ["minha cabeça tá latejando", "caganeira desde ontem"], {})
        self.assertEqual(fake.calls, 0)

    def test_falha_da_api_nao_fica_no_cache_e_ha_teto_por_minuto(self):
        class Flaky:
            calls = 0
            def complete(self, s, u):
                Flaky.calls += 1
                return None if Flaky.calls == 1 else json.dumps({**EMPTY, "objetivos": ["dor_de_cabeca"]})
        R = Reader(GRAPH.cat, Flaky())
        self.assertIsNone(R.read("cabeça latejando"))
        self.assertEqual(R.read("cabeça latejando")["objetivos"], ["dor_de_cabeca"])   # tentou de novo
        import time
        c = DeepSeek("sk-x")
        c.recent = [time.monotonic()] * 60                                         # já fez 60 no último minuto
        self.assertIsNone(c.complete("s", "u"))                                    # nem tenta a rede
        self.assertEqual(c.calls, 0)

    def test_texto_enorme_e_cortado_antes_de_enviar(self):
        fake = Fake()
        Reader(GRAPH.cat, fake).read("cabeça " * 20000)
        self.assertLessEqual(len(fake.sent[0]), 520)

    def test_sem_deepseek_a_resposta_e_a_do_grafo(self):
        q = "minha cabeça tá latejando"
        for fake in (None, Fake(raw="isto não é json"), Fake(raw=None), Fake({"latejando": {"objetivos": ["inventado"]}})):
            E = GRAPH if fake is None else eng(fake)
            r = E.search({"query": q})
            r.pop("rag", None)
            self.assertEqual(r, GRAPH.search({"query": q}), repr(fake and fake.raw))
        class Down:
            calls = 0
            def complete(self, s, u):
                return None                                            # rede fora do ar ou tempo esgotado
        self.assertEqual(eng(Down()).search({"query": q}), GRAPH.search({"query": q}))

    def test_id_inventado_nunca_chega_ao_motor(self):
        R = Reader(GRAPH.cat, Fake(raw=json.dumps({**EMPTY, "objetivos": ["emagrecer"], "ingredientes": ["sibutramina"],
                                                    "preocupacoes": ["gases"], "pele": "verde"})))
        p = R.read("qualquer coisa")
        self.assertEqual((p["objetivos"], p["ingredientes"], p["preocupacoes"], p["pele"]), ([], [], ["gases"], None))

    def test_preferencia_mandada_em_evitar_vira_preferencia(self):
        R = Reader(GRAPH.cat, Fake(raw=json.dumps({**EMPTY, "evitar": ["sem_alcool", "acido_salicilico"]})))
        p = R.read("x")
        self.assertEqual((p["evitar"], p["preferencias"]), (["acido_salicilico"], ["sem álcool"]))

    def test_ajuste_no_meio_da_conversa_muda_os_kits(self):
        base = GRAPH.search({"query": "pele oleosa"})
        fake = Fake({"cheiro": {"ajuste": {"preferencias": ["sem fragrância"]}},
                     "em conta": {"ajuste": {"orcamento": "mais_barato"}},
                     "ácido": {"ajuste": {"evitar": ["acido_salicilico"]}}})
        E = eng(fake)
        r = E.search({"query": "tira tudo que tem cheiro", "context": base["context"]})
        self.assertIn("sem fragrância", r["intent"]["preferences"])
        self.assertEqual(r["intent"]["skinType"], "oleosa")                    # o resto da conversa continua
        r = E.search({"query": "algo mais em conta", "context": base["context"]})
        self.assertLess(r["intent"]["budgetCents"], base["kits"][1]["totalCents"])
        r = E.search({"query": "não quero ácido", "context": base["context"]})
        self.assertIn("acido_salicilico", r["context"]["excluded"])
        self.assertIn("Conversa até aqui: objetivo: Controle de oleosidade; pele: oleosa", fake.sent[0])
        self.assertTrue(all(not check_response(x) for x in [r]))

    def test_remedio_generico_sem_nada_no_catalogo_responde_so_a_frase(self):
        r = eng(Fake()).search({"query": "remédio pra unha encravada"})
        self.assertEqual(r["reply"], "Não está no banco de dados ainda.")
        self.assertEqual((r["kits"], r["products"]), ([], []))
        self.assertGreater(len(GRAPH.search({"query": "remédio pra unha encravada"})["products"]), 0)   # antes: 24 itens soltos

    def test_dados_pessoais_saem_antes_de_enviar(self):
        fake = Fake()
        Reader(GRAPH.cat, fake).read("meu nome é Renata Almeida, tenho 34 anos, fone 11 98765-4321, renata@x.com, cabeça latejando")
        sent = fake.sent[0]
        self.assertIn("cabeça latejando", sent)
        for leak in ("Renata", "Almeida", "34 anos", "98765", "renata@x.com"):
            self.assertNotIn(leak, sent)
        self.assertEqual(scrub("me chamo Ana e to com tosse"), "me chamo [nome] e to com tosse")
        for txt, leak in (("sou a Maria Souza e to com tosse", "Maria"), ("moro na rua das flores 123, Fortaleza", "flores"),
                          ("minha filha de 5 anos tá com febre", "5 anos"), ("cpf 123.456.789-09", "456"),
                          ("cep 60000-000", "60000")):
            self.assertNotIn(leak, scrub(txt), txt)
        self.assertIn("tosse", scrub("sou a Maria Souza e to com tosse"))
        self.assertIn("2 anos de acne", scrub("tenho 2 anos de acne"))

    def test_cache_nao_repete_a_chamada(self):
        fake = Fake({"latejando": {"objetivos": ["dor_de_cabeca"]}})
        E = eng(fake)
        E.search({"query": "minha cabeça tá latejando"})
        E.search({"query": "minha cabeça tá latejando"})
        self.assertEqual(fake.calls, 1)

    def test_chave_vem_do_ambiente_e_nunca_vai_para_o_app(self):
        with mock.patch.dict(os.environ, {"DEEPSEEK_API_KEY": " sk-teste "}):
            self.assertEqual(_env_key(), "sk-teste")
            self.assertIsInstance(DeepSeek.from_env(), DeepSeek)
        from pathlib import Path
        app = Path(__file__).resolve().parents[2] / "app" / "src"
        self.assertFalse([f for f in app.rglob("*") if f.is_file() and "DEEPSEEK" in f.read_text(errors="ignore")])


if __name__ == "__main__":
    unittest.main()
