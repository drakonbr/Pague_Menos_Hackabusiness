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
        fake = Fake({"zona": {"objetivos": ["dor_de_cabeca"]}})
        r = eng(fake).search({"query": "minha cabeça tá uma zona"})
        self.assertTrue(r.get("rag"))
        self.assertEqual(r["kits"], [])                                     # #40: remédio nunca em kit
        self.assertTrue(r["products"] and all(p["domain"] == "medicamento" for p in r["products"]))
        self.assertFalse(check_response(r))

    def test_gestacao_vale_na_busca_feita_pela_deepseek(self):
        fake = Fake({"zona": {"objetivos": ["dor_de_cabeca"]}})
        q = "estou grávida e minha cabeça tá uma zona"
        r = eng(fake).search({"query": q})
        self.assertEqual(fake.calls, 1)
        self.assertTrue(r["intent"]["pregnancy"])
        self.assertEqual(r["safety"]["decision"], GRAPH.search({"query": q})["safety"]["decision"])
        self.assertNotEqual(r["safety"]["decision"], "allow")
        self.assertTrue(r["context"]["intent"]["pregnancy"])                       # os próximos turnos continuam filtrando

    def test_replay_do_chat_nao_chama_a_deepseek(self):
        from graphrag.chat_stream import replay
        fake = Fake({"zona": {"objetivos": ["dor_de_cabeca"]}})
        replay(eng(fake), ["minha cabeça tá uma zona", "caganeira desde ontem"], {})
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
        q = "minha cabeça tá uma zona"
        for fake in (None, Fake(raw="isto não é json"), Fake(raw=None), Fake({"zona": {"objetivos": ["inventado"]}})):
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

    def test_pessoa_pode_desligar_o_servico_externo(self):
        # #42 (LGPD): allowExternal=false nunca deixa a frase sair; ausente ou true funciona como antes
        q = "minha cabeça tá uma zona"
        fake = Fake({"zona": {"objetivos": ["dor_de_cabeca"]}})
        r = eng(fake).search({"query": q, "allowExternal": False})
        self.assertEqual(fake.calls, 0)
        r.pop("rag", None)
        self.assertEqual(r, GRAPH.search({"query": q, "allowExternal": False}))
        for req in ({"query": q}, {"query": q, "allowExternal": True}):
            f2 = Fake({"zona": {"objetivos": ["dor_de_cabeca"]}})
            self.assertTrue(eng(f2).search(req).get("rag"))
            self.assertEqual(f2.calls, 1)

    def test_palavra_desconhecida_so_confere_e_o_grafo_continua_valendo(self):
        # #61: "melada" o catálogo não conhece. O grafo respondeu rotina básica. A DeepSeek só troca se EXPLICAR a palavra
        # com algo do catálogo que o grafo não cobriu
        q = "quero cuidar da pele que vive melada"
        base = GRAPH.search({"query": q})
        self.assertEqual(base["intent"]["primaryGoal"], "skincare_basico")
        fake = Fake({"melada": {"objetivos": ["oleosidade"], "palavras": {"melada": "oleosidade"}}})
        E = eng(fake)
        r = E.search({"query": q})
        self.assertEqual((fake.calls, r.get("rag"), r["intent"]["primaryGoal"]), (1, True, "oleosidade"))
        self.assertEqual((E.stats["fraco"], E.stats["trocou"]), (1, 1))
        self.assertIn("Palavras que o catálogo não conhece: ", fake.sent[0]); self.assertIn("melada", fake.sent[0])
        # leu oleosidade mas NÃO explicou nenhuma palavra: era enchimento, vale o grafo, intacto
        fake = Fake({"melada": {"objetivos": ["oleosidade"]}})
        r = eng(fake).search({"query": q}); r.pop("rag", None)
        self.assertEqual((fake.calls, r), (1, base))
        # explicou com algo que o grafo já cobria: também fica a do grafo
        fake = Fake({"melada": {"objetivos": ["skincare_basico"], "palavras": {"melada": "skincare_basico"}}})
        r = eng(fake).search({"query": q}); r.pop("rag", None)
        self.assertEqual(r, base)
        # explicação inventada (id que não existe) não vale; nem palavra que não foi perguntada
        fake = Fake({"melada": {"objetivos": ["oleosidade"], "palavras": {"melada": "inventado", "ontem": "oleosidade"}}})
        r = eng(fake).search({"query": q}); r.pop("rag", None)
        self.assertEqual(r, base)
        # e se ela não leu nada do catálogo, também fica a do grafo
        fake = Fake()
        r = eng(fake).search({"query": q}); r.pop("rag", None)
        self.assertEqual((fake.calls, r), (1, base))

    def test_conferencia_nunca_vira_lista_de_remedio_sem_pedido_de_saude(self):
        # #61: o revisor provou na API real que "corpo arrebentado e cansado" virava ibuprofeno/naproxeno; agora a troca é recusada
        q = "sinto o corpo todo arrebentado e cansado"
        base = GRAPH.search({"query": q})
        self.assertFalse(any(p["domain"] == "medicamento" for p in base["products"]))
        fake = Fake({"arrebentado": {"preocupacoes": ["dor_no_corpo"], "palavras": {"arrebentado": "dor_no_corpo"}}})
        E = eng(fake)
        r = E.search({"query": q}); r.pop("rag", None)
        self.assertEqual(r, base)
        self.assertEqual(E.stats["recusou"], 1)
        # com palavra de saúde na frase a troca vale ("doendo" é pedido de alívio)
        fake = Fake({"arrebentado": {"preocupacoes": ["dor_no_corpo"], "palavras": {"arrebentado": "dor_no_corpo"}}})
        r = eng(fake).search({"query": "sinto o corpo todo arrebentado e doendo"})
        self.assertTrue(any(p["domain"] == "medicamento" for p in r["products"]))

    def test_trava_de_remedio_nao_e_furada_por_to_com(self):
        # #61 (revisor, 2ª rodada): "tô com o corpo todo arrebentado" tem "tô com", que aparece em qualquer queixa; não é pedido de remédio
        for q in ("tô com o corpo todo arrebentado e cansado", "estou com o corpo todo arrebentado e cansado", "sinto o corpo todo arrebentado e cansado"):
            base = GRAPH.search({"query": q})
            fake = Fake({"arrebentado": {"preocupacoes": ["dor_no_corpo"], "palavras": {"arrebentado": "dor_no_corpo"}}})
            E = eng(fake)
            r = E.search({"query": q}); r.pop("rag", None)
            self.assertEqual((r, E.stats["recusou"]), (base, 1), q)
        # "tomo sol" e "tomar banho" não são pedido de remédio
        fake = Fake({"arrebentada": {"preocupacoes": ["dor_no_corpo"], "palavras": {"arrebentada": "dor_no_corpo"}}})
        E = eng(fake)
        r = E.search({"query": "tomo muito sol e minha pele fica arrebentada"})
        self.assertFalse(any(p["domain"] == "medicamento" for p in r["products"]))
        for q in ("tô com dor no corpo todo arrebentado", "preciso de um remédio, o corpo está arrebentado"):   # pedido de alívio: vale
            fake = Fake({"arrebentado": {"preocupacoes": ["dor_no_corpo"], "palavras": {"arrebentado": "dor_no_corpo"}}})
            r = eng(fake).search({"query": q})
            self.assertTrue(any(p["domain"] == "medicamento" for p in r["products"]), q)

    def test_troca_usa_so_o_que_a_deepseek_explicou(self):
        # #61: ela leu oleosidade (explicou "melada") e também protetor solar e acne (sem explicar nada disso): só a explicada entra
        q = "quero cuidar da pele que vive melada"
        fake = Fake({"melada": {"objetivos": ["acne", "protecao_solar"], "preocupacoes": ["oleosidade"], "etapas": ["limpeza"],
                                 "palavras": {"melada": "oleosidade"}}})
        r = eng(fake).search({"query": q})
        self.assertTrue(r.get("rag"))
        self.assertEqual(r["intent"]["primaryGoal"], "oleosidade")                      # não virou acne nem proteção solar
        self.assertNotIn("protecao_solar", r["intent"]["goals"]); self.assertNotIn("acne", r["intent"]["goals"])

    def test_fala_com_palavras_no_meio_e_pergunta_sem_produto(self):
        # #62 + #61: variações de "parte do corpo + estado" valem, e frase que vira "pergunta sem produto" e sem conversa vai à conferência
        from graphrag.lexicon import canon_state
        casos = {"meu ombro tá bem travado": "meu ombro dor muscular", "ombro todo travado": "ombro dor muscular",
                 "meu ombro ficou travado ontem": "meu ombro dor muscular ontem", "minha mandibula esta travada": "minha mandibula dor muscular",
                 "nariz bem tapado": "nariz entupido", "meu nariz ficou tapado de noite": "meu nariz entupido de noite",
                 "meu intestino ficou travado esses dias": "meu intestino preso esses dias", "poros tapados": "poros tapados",
                 "minha pia tá tapada": "minha pia tá tapada"}
        for q, esperado in casos.items():
            from graphrag.text import norm
            self.assertEqual(canon_state(norm(q)), norm(esperado), q)
        self.assertEqual(GRAPH.search({"query": "minha pia tá tapada"})["products"], [])      # a palavra solta não entrou no vocabulário
        self.assertTrue(GRAPH.search({"query": "meu intestino ficou travado esses dias"})["products"])   # "esses dias" não desvia mais
        # sem produto e sem conversa ("meu intestino está preso esses dias" é lido como "similar" de quê?): vai à conferência
        fake = Fake({"preso": {"preocupacoes": ["prisao_de_ventre"], "palavras": {"preso": "prisao_de_ventre"}}})
        r = eng(fake).search({"query": "meu intestino está preso esses dias"})
        self.assertEqual(fake.calls, 1)
        # a negação não vira queixa: "meu nariz não está tapado" não pode trazer descongestionante
        for q in ("meu nariz não está tapado", "meu ombro não está travado, é só o cotovelo"):
            self.assertEqual(GRAPH.search({"query": q})["products"], [], q)
        # #62 (blind5): "solto demais" É diarreia; a negação de "travado" não pode esconder isso
        r = GRAPH.search({"query": "meu intestino não é travado, é solto demais"})
        self.assertTrue(r["products"] and all("diarreia" in x["concerns"] for x in r["products"][:3]))
        # mais partes do corpo, vírgula no meio
        for q in ("meu braço está travado", "tô com a perna travada", "meu pé tá travado", "ombro, travado"):
            ps = GRAPH.search({"query": q})["products"]
            self.assertTrue(ps and all("dor_muscular" in p["concerns"] or "dor_no_corpo" in p["concerns"] for p in ps), q)

    def test_palavra_negada_nunca_vira_pedido(self):
        # #61 (revisor, 3ª rodada, provado na API real): "protetor que NÃO fique melado" não pode virar kit de oleosidade
        for q, regra in (("quero um protetor solar que não fique melado na pele", "protecao_solar"),
                         ("quero um hidratante leve que não deixe a pele melada", None)):
            base = GRAPH.search({"query": q})
            fake = Fake({"melad": {"objetivos": ["oleosidade"], "preocupacoes": ["oleosidade"], "palavras": {"melado": "oleosidade", "melada": "oleosidade"}}})
            E = eng(fake)
            r = E.search({"query": q}); r.pop("rag", None)
            self.assertEqual(r, base, q)
            self.assertEqual(E.stats["trocou"], 0, q)
            if regra:
                self.assertEqual(base["intent"]["primaryGoal"], regra)

    def test_negacao_da_conferencia_e_tela_sem_texto_reescrito(self):
        from graphrag.dialogue import Engine as En
        neg = En._negated
        for q, w in (("quero um hidratante leve, nada melado", "melado"), ("protetor que deixe a pele menos melada", "melada"),
                     ("quero um protetor solar que não fique melado na pele", "melado"), ("nenhum produto melado por favor", "melado")):
            self.assertTrue(neg(q, w), q)
        for q, w in (("pele sem brilho e melada de manhã", "melada"), ("não gosto de perfume mas minha pele é melada", "melada"),
                     ("quero cuidar da pele que vive melada", "melada")):
            self.assertFalse(neg(q, w), q)                      # a negação não atravessa "e" nem "mas"
        # o texto reescrito pelo corpo não aparece como "correção" na tela, e o corretor não troca a parte do corpo
        for q in ("tô com a perna travada", "meu braço está travado", "meu ombro tá bem travado"):
            r = GRAPH.search({"query": q})
            self.assertNotIn("correctedQuery", r, q)
            self.assertTrue(r["products"], q)
        self.assertEqual(GRAPH.speller.correct_word("braco"), "braco")
        self.assertEqual(GRAPH.speller.correct_word("perna"), "perna")
        self.assertEqual(GRAPH.search({"query": "protetor soalr"}).get("correctedQuery"), "protetor solar")   # typo comum segue aparecendo

    def test_caminho_do_objetivo_so_quando_o_grafo_estava_no_escuro(self):
        # explicou um objetivo, mas o grafo já tinha um objetivo próprio (não o de reserva): troca a palavra na frase, mantém o resto
        q = "preciso de um protetor solar para a praia, pele melada"
        base = GRAPH.search({"query": q})
        fake = Fake({"melada": {"objetivos": ["oleosidade"], "palavras": {"melada": "oleosidade"}}})
        self.assertEqual(base["intent"]["primaryGoal"], "protecao_solar")
        r = eng(fake).search({"query": q})
        self.assertTrue(r.get("rag"))                                        # a palavra foi explicada e a busca refeita...
        self.assertEqual(r["intent"]["primaryGoal"], "protecao_solar")       # ...sem trocar o objetivo que o grafo já tinha

    def test_conferencia_so_em_busca_nova_e_respeita_o_desligar(self):
        fake = Fake({"melada": {"objetivos": ["oleosidade"]}})
        E = eng(fake)
        E.search({"query": "quero cuidar da pele que vive melada", "allowExternal": False})
        self.assertEqual(fake.calls, 0)
        base = GRAPH.search({"query": "pele oleosa"})
        E.search({"query": "tira o que é melado", "context": base["context"]})       # ajuste de conversa: outro caminho
        self.assertEqual(E.stats["fraco"], 0)
        # typo corrigido pelo corretor também confere, mas concordando nada muda
        fake = Fake({"solr": {"etapas": ["protecao_solar"], "objetivos": ["protecao_solar"]}})
        r = eng(fake).search({"query": "protetor solr"}); r.pop("rag", None)
        self.assertEqual(fake.calls, 1)
        self.assertEqual(r["intent"]["primaryGoal"], "protecao_solar")

    def test_frase_com_etapa_e_preocupacao_nao_perde_a_etapa(self):
        # "pasta de dente pra dente sensível": a DeepSeek lê etapa higiene_oral + sensibilidade; as duas chegam ao grafo
        from graphrag.llm import phrase
        p = {**EMPTY, "etapas": ["higiene_oral"], "preocupacoes": ["sensibilidade"], "ajuste": EMPTY["ajuste"]}
        q = phrase(GRAPH.cat, p, False)
        self.assertIn("higiene", q); self.assertIn("sensibilidade", q)

    def test_sem_chave_o_servidor_avisa_e_a_saude_diz(self):
        # #60: a falha silenciosa (chave sumiu do .env.local) virou aviso na partida e campo na saúde
        from graphrag.llm import rag_banner
        self.assertIn("DESLIGADO", rag_banner(GRAPH))
        self.assertIn("LIGADO", rag_banner(eng(Fake())))
        import threading, urllib.request
        from http.server import ThreadingHTTPServer
        from graphrag.service import server
        for engine, esperado in ((GRAPH, False), (eng(Fake()), True)):
            server.ENGINE = engine
            srv = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
            threading.Thread(target=srv.serve_forever, daemon=True).start()
            try:
                body = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{srv.server_port}/v1/health", timeout=10).read())
            finally:
                srv.shutdown(); srv.server_close()
            self.assertIs(body["rag"], esperado)
            self.assertIsInstance(body["ragCalls"], dict)
        server.ENGINE = GRAPH

    def test_vocabulario_do_dia_a_dia_e_corretor(self):
        # #62: as frases de ajuste do AMPLO passam só com o grafo (sem DeepSeek); o conjunto de TESTE nunca ajusta o léxico
        from graphrag.eval import rag_set
        from graphrag.eval.rag_eval import ok_search
        ruins = [q for q, rule in rag_set.AMPLO_TRAIN if not ok_search(GRAPH.cat, GRAPH.search({"query": q}), rule)]
        self.assertEqual(ruins, [])
        # o corretor não troca a 1ª letra em correção de 2 erros ("rinite atacada" não é "rinite tapada"), mas segue corrigindo typo
        self.assertNotEqual(GRAPH.speller.correct_word("atacada"), "tapada")
        self.assertEqual(GRAPH.speller.correct_word("solr"), "solr")                      # curta demais: nunca muda
        self.assertEqual(GRAPH.speller.fix("protetor soalr")[0], "protetor solar")         # typo de 1 erro continua corrigido
        # as palavras soltas não vazam: "tapado" de poros não é nariz, e a pia não é assunto da loja
        for q in ("meus poros estão tapados", "poros tapados no nariz"):
            self.assertFalse(any("nariz_entupido" in p["concerns"] for p in GRAPH.search({"query": q})["products"]), q)
        self.assertEqual(GRAPH.search({"query": "minha pia tá tapada"})["products"], [])
        # as formas do dia a dia (tá, está, meio, todo) valem para a parte do corpo, não só uma frase pronta
        for q in ("meu ombro está travado", "meu ombro tá todo travado", "o joelho travou", "meu pescoço tá duro"):
            ps = GRAPH.search({"query": q})["products"]
            self.assertTrue(ps and all("dor_muscular" in p["concerns"] or "dor_no_corpo" in p["concerns"] for p in ps), q)
        self.assertTrue(all("prisao_de_ventre" in p["concerns"] for p in GRAPH.search({"query": "meu intestino tá meio travado"})["products"]))
        r = GRAPH.search({"query": "rinite atacada"})
        self.assertTrue(all("alergia" in p["concerns"] for p in r["products"]))

    def test_remedio_de_receita_nunca_tem_preco_riscado_no_motor(self):
        # #41: vale no carregamento do catálogo e na ingestão, venha o dado como vier
        self.assertEqual([p["id"] for p in GRAPH.cat.products if p["rx"] and p["listPriceCents"] > p["priceCents"]], [])
        from graphrag.ingest import _apply
        novo = {**GRAPH.cat.products[0], "id": "p9999", "rx": "receita_simples", "priceCents": 1000, "listPriceCents": 1500,
                "cashbackPct": 0, "salesRank": 1}
        antes = list(GRAPH.cat.products)
        try:
            _apply(GRAPH.cat, novo, {})
            self.assertEqual(GRAPH.cat.by_id["p9999"]["listPriceCents"], 1000)
        finally:
            GRAPH.cat.products[:] = antes
            GRAPH.cat.by_id.pop("p9999", None)

    def test_servico_externo_falha_fechado(self):
        # #42: só allowExternal exatamente true (ou ausente, com o padrão ligado) leva a frase à DeepSeek
        q = "minha cabeça tá uma zona"
        for valor in (False, 0, "false", None, "nao", []):
            fake = Fake({"zona": {"objetivos": ["dor_de_cabeca"]}})
            eng(fake).search({"query": q, "allowExternal": valor})
            self.assertEqual(fake.calls, 0, repr(valor))
        fake = Fake({"zona": {"objetivos": ["dor_de_cabeca"]}})
        E = eng(fake)
        E.external_default = False                      # produção: RAG_EXTERNAL_DEFAULT=off
        E.search({"query": q})                          # cliente antigo, sem o campo
        self.assertEqual(fake.calls, 0)
        E.search({"query": q, "allowExternal": True})   # quem consentiu explicitamente
        self.assertEqual(fake.calls, 1)
        with mock.patch.dict(os.environ, {"RAG_EXTERNAL_DEFAULT": "off"}):
            self.assertFalse(eng(Fake()).external_default)
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("RAG_EXTERNAL_DEFAULT", None)
            self.assertTrue(eng(Fake()).external_default)

    def test_cache_nao_repete_a_chamada(self):
        fake = Fake({"zona": {"objetivos": ["dor_de_cabeca"]}})
        E = eng(fake)
        E.search({"query": "minha cabeça tá uma zona"})
        E.search({"query": "minha cabeça tá uma zona"})
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
