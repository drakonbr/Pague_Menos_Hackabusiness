"""Testes do motor: cenários T1-T12 do doc 08, persona, conversa de vários turnos, varredura de invariantes,
determinismo e testes NEGATIVOS do checador (ele precisa pegar defeitos injetados)."""
import copy
import itertools
import json
import unittest

from graphrag.dialogue import Engine
from graphrag.eval.invariants import check_kit, check_response

E = Engine.build()


def S(q, ctx=None, **kw):
    return E.search({"query": q, "context": ctx, **kw} if ctx is not None else {"query": q, **kw})


def total_ok(r):
    return all(not check_response(r) for _ in [0])


class TestScenariosDoc08(unittest.TestCase):
    def ok(self, r, excluded=()):
        self.assertEqual(check_response(r, excluded), [])

    def test_T1(self):
        r = S("Quero cuidar da pele até R$ 120"); self.ok(r)
        self.assertEqual(r["intent"]["primaryGoal"], "skincare_basico"); self.assertEqual(r["intent"]["budgetCents"], 12000)
        self.assertTrue(r["kits"] and all(k["totalCents"] <= 12000 for k in r["kits"]))
        self.assertEqual(r["clarification"]["id"], "skinType")

    def test_T2(self):
        r = S("Quero fazer skin care"); self.ok(r)
        self.assertIsNone(r["intent"]["budgetCents"]); self.assertEqual(r["kitsStatus"], "ok"); self.assertEqual(len(r["kits"]), 3)

    def test_T3(self):
        r = S("Preciso de produtos para tratamento de acne"); self.ok(r)
        self.assertEqual(r["intent"]["primaryGoal"], "acne")
        for k in r["kits"]:
            self.assertTrue({"limpeza", "tratamento", "hidratacao"} <= {i["step"] for i in k["items"]})

    def test_T4(self):
        r = S("Protetor solar para pele oleosa"); self.ok(r)
        self.assertEqual(r["intent"]["primaryGoal"], "protecao_solar")
        for k in r["kits"]:
            self.assertTrue({"protecao_solar", "protecao_corporal"} <= {i["step"] for i in k["items"]})
            for i in k["items"]:
                self.assertTrue({"oleosa", "todas"} & set(i["product"]["skinTypes"]))

    def test_T5(self):
        r = S("Quero uniformizar manchas até R$ 80"); self.ok(r)
        self.assertEqual(r["intent"]["primaryGoal"], "manchas")
        for k in r["kits"]:
            self.assertLessEqual(k["totalCents"], 8000)
            self.assertIn("protecao_solar", {s for i in k["items"] for s in i["product"]["coversSteps"]})

    def test_T6(self):
        r = S("Acne, pele oleosa, até R$ 40"); self.ok(r)
        self.assertEqual(r["kitsStatus"], "none_in_budget"); self.assertEqual(r["kits"], []); self.assertIsNotNone(r["closestKit"])
        self.assertGreater(r["closestKit"]["totalCents"], 4000)

    def test_T7_dor_de_cabeca_traz_kit_de_dipirona_e_paracetamol(self):
        # doc 16, A3: antes era bloqueio; agora é busca de farmácia
        for q in ["remédio de dor de cabeça", "Estou com dor de cabeça, o que posso tomar?", "dores de cabeça"]:
            r = S(q); self.ok(r)
            self.assertEqual(r["safety"]["decision"], "allow"); self.assertEqual(r["intent"]["primaryGoal"], "dor_de_cabeca")
            self.assertGreaterEqual(len(r["kits"]), 2, q)
            for k in r["kits"]:
                ings = {i for it in k["items"] for i in it["product"]["ingredients"]}
                self.assertTrue({"dipirona", "paracetamol"} <= ings, (q, k["tier"]))
            self.assertTrue(r["products"] and all(p["domain"] == "medicamento" for p in r["products"]))

    def test_T8_areas_de_saude_montam_kit_da_area(self):
        # doc 16, A4: cada área devolve medicamentos e kits que atendem aquela queixa
        casos = {"dor no corpo": "dor_no_corpo", "dor muscular": "dor_muscular", "dor de barriga": "dor_de_barriga",
                 "estou gripado": "gripe", "tosse com catarro": "tosse", "dor de garganta": "dor_de_garganta",
                 "remédio para alergia": "alergia", "diarreia": "diarreia", "intestino preso": "prisao_de_ventre",
                 "enjoo de viagem": "enjoo", "azia": "azia", "tosse seca": "tosse_seca"}
        for q, goal in casos.items():
            r = S(q); self.ok(r)
            self.assertEqual(r["intent"]["primaryGoal"], goal, q); self.assertTrue(r["kits"], q)
            alvo = set(E.cat.goal_by_id[goal]["concerns"])
            for k in r["kits"]:
                self.assertTrue(all(it["product"]["domain"] == "medicamento" for it in k["items"]), q)
                self.assertTrue(any(set(it["product"]["concerns"]) & alvo for it in k["items"]), q)

    def test_sem_remedio_no_catalogo_diz_so_que_nao_esta(self):
        # doc 16, A6
        for q in ["remédio para diabetes", "remédio pra dormir", "antibiótico", "dor de dente"]:
            r = S(q)
            self.assertEqual(r["reply"], "Não está no banco de dados ainda.", q)
            self.assertEqual((r["kits"], r["products"]), ([], []), q)

    def test_nenhuma_resposta_manda_procurar_profissional(self):
        # doc 16, A5 (a invariante M2 varre resposta, sugestões, notas e segurança)
        for q in ["Qual remédio para acne forte?", "tenho rosácea e minha pele vive vermelha", "qual a dose do dorflex",
                  "posso tomar ômega 3 com remédio de pressão", "estou grávida, quero remédio para enjoo",
                  "o que tomar para colesterol", "tem similar", "kit de suplementos", "ajuda", "oi"]:
            r = S(q); self.assertEqual([m for m in check_response(r) if "M2" in m], [], q)

    def test_T9(self):
        r = S("Estou grávida, quero um kit anti-idade"); self.ok(r)
        self.assertEqual(r["safety"]["decision"], "caution")
        self.assertTrue(all("retinol" not in i["product"]["ingredients"] for k in r["kits"] for i in k["items"]))

    def test_T10(self):
        r = S("Quero um kit com retinol e ácido glicólico"); self.ok(r)
        for k in r["kits"]:
            ings = {x for i in k["items"] for x in i["product"]["ingredients"]}
            self.assertFalse({"retinol", "acido_glicolico"} <= ings)
        self.assertTrue(any("não entram no mesmo kit" in n for n in r["notes"]))

    def test_T11(self):
        r = S("Kit vegano para pele seca até R$ 150"); self.ok(r)
        self.assertTrue(r["kits"])
        for k in r["kits"]:
            for i in k["items"]:
                self.assertIn("vegano", i["product"]["claims"]); self.assertTrue({"seca", "todas"} & set(i["product"]["skinTypes"]))

    def test_T12(self):
        r = S("asdfgh"); self.ok(r)
        self.assertEqual(r["kits"], []); self.assertEqual(r["products"], []); self.assertIn("Não encontrei", r["reply"])
        self.assertTrue(r["catalogNotice"])


class TestPersona(unittest.TestCase):
    def test_suplementos(self):
        r = S("quero um kit de suplementos ômega 3 colágeno e magnésio"); self.assertEqual(check_response(r), [])
        self.assertEqual(r["intent"]["primaryGoal"], "suplementos")
        for k in r["kits"]:
            self.assertTrue({"omega3", "colageno", "magnesio"} <= {i["step"] for i in k["items"]})
            self.assertTrue(any(a["code"] == "consultar_se_medicacao" for a in k["alerts"]))
        self.assertNotIn("clarification", r)

    def test_higiene(self):
        r = S("kit de higiene premium até R$ 250"); self.assertEqual(check_response(r), [])
        self.assertEqual(r["intent"]["primaryGoal"], "higiene_premium"); self.assertTrue(r["kits"])
        self.assertTrue(all(k["totalCents"] <= 25000 for k in r["kits"]))

    def test_antissinais_premium(self):
        r = S("quero uma rotina anti idade premium até 400 reais"); self.assertEqual(check_response(r), [])
        self.assertEqual(r["intent"]["primaryGoal"], "anti_idade")

    def test_busca_que_nao_e_de_remedio_nao_traz_remedio(self):
        for q in ["kit de suplementos", "rotina anti idade", "me mostra colágeno em pó", "higiene premium", "quero meu remédio"]:
            r = S(q)
            for p in r["products"]:
                self.assertNotEqual(p["domain"], "medicamento")
            for k in r["kits"]:
                for i in k["items"]:
                    self.assertNotEqual(i["product"]["domain"], "medicamento")

    def test_reposicao_abre_tela_sem_recomendar(self):
        for q in ["preciso repor meu remédio de pressão", "meus medicamentos estão no fim", "reposição dos meus remédios"]:
            r = S(q); self.assertEqual(r["action"]["type"], "open_refill", q); self.assertEqual(r["safety"]["decision"], "allow")

    def test_dose_e_sintoma_nao_bloqueiam_nem_encaminham(self):
        for q in ["qual remédio devo tomar para pressão alta", "qual a dose do meu remédio, posso dobrar", "preciso repor remédio, estou com tontura",
                  "o que tomar para colesterol", "estou com dor no peito, repor meu remédio"]:
            r = S(q); self.assertNotEqual(r["safety"]["decision"], "blocked", q); self.assertEqual(check_response(r), [], q)
        r = S("remédio para pressão alta")                 # o medicamento de pressão do catálogo é achado pela busca
        self.assertTrue(any("hipertensao" in p["concerns"] for p in r["products"]))

    def test_equivalentes_med(self):
        r = E.similars("p136", "s01")           # p136 sem estoque na Loja Madalena (premissa da demonstração)
        self.assertFalse(r["inStockHere"])
        ids = {o["product"]["id"]: o for o in r["options"]}
        self.assertTrue({"p137", "p138"} <= set(ids))
        self.assertTrue(ids["p138"]["inStock"]); self.assertTrue(all(o["sameActive"] for o in r["options"]))
        self.assertFalse(any(o["needsPharmacistConfirmation"] for o in r["options"]))   # doc 16: sem encaminhamento
        self.assertTrue(all(r["options"][i]["inStock"] >= r["options"][i + 1]["inStock"] for i in range(len(r["options"]) - 1)))

    def test_kit_de_remedio_nunca_repete_ativo_nem_junta_dois_antiinflamatorios(self):
        aines = {"ibuprofeno", "naproxeno", "diclofenaco_potassico", "diclofenaco_sodico", "diclofenaco_dietilamonio",
                 "nimesulida", "acido_acetilsalicilico", "flurbiprofeno", "benzidamina"}
        for q in ["dor muscular", "dor no corpo", "dor de cabeça", "dor de garganta", "gripe", "remédio para cólica"]:
            for b in (None, 3000, 8000):
                r = S(q + (f" até {b // 100} reais" if b else ""))
                self.assertEqual(check_response(r), [], q)
                for k in r["kits"]:
                    ings = [i for it in k["items"] for i in it["product"]["ingredients"]]
                    self.assertEqual(len(ings), len(set(ings)), (q, b, k["tier"]))
                    self.assertLessEqual(len(aines & set(ings)), 1, (q, b, k["tier"]))

    def test_checador_pega_ativo_repetido(self):
        r = S("remédio de dor de cabeça")
        k = copy.deepcopy(r["kits"][0])
        dip = next(p for p in E.cat.products if p["id"] != k["items"][0]["product"]["id"] and "dipirona" in p["ingredients"]
                   and p["step"] != k["items"][0]["step"])
        k["items"].append({"step": dip["step"], "product": dip, "reason": ""})
        k["totalCents"] += dip["priceCents"]
        self.assertTrue(any("M1" in m for m in check_kit(k, r["intent"])))

    def test_similar_nao_med(self):
        r = E.similars("p001", None)
        self.assertTrue(r["options"] and all(o["product"]["domain"] != "medicamento" for o in r["options"]))


class TestConversa(unittest.TestCase):
    def test_dialogo_acne(self):
        r1 = S("preciso de produtos para tratamento de acne")
        r2 = S("sem fragrância", r1["context"]); self.assertEqual(r2["act"], "refinar")
        self.assertIn("sem fragrância", r2["intent"]["preferences"]); self.assertEqual(check_response(r2), [])
        r3 = S("até 130 reais", r2["context"]); self.assertEqual(r3["intent"]["budgetCents"], 13000)
        self.assertIn("sem fragrância", r3["intent"]["preferences"]); self.assertEqual(check_response(r3), [])
        self.assertTrue(all(k["totalCents"] <= 13000 for k in r3["kits"]))
        r4 = S("qual o frete", r3["context"]); self.assertEqual(r4["action"]["type"], "delivery_quote")
        kit_total = r4["action"]["kitTotalCents"]
        for o in r4["action"]["options"]:
            self.assertEqual(o["totalCents"], kit_total + o["feeCents"])
        retirada = next(o for o in r4["action"]["options"] if o["id"] == "retirada"); self.assertEqual(retirada["feeCents"], 0)

    def test_excluir_ingrediente(self):
        r1 = S("rotina anti idade")
        r2 = S("sem retinol", r1["context"]); self.assertEqual(check_response(r2, ["retinol"]), [])
        self.assertTrue(r2["kits"]); self.assertIn("retinol", r2["context"]["excluded"])
        r3 = S("até 500 reais", r2["context"]); self.assertEqual(check_response(r3, ["retinol"]), [])

    def test_trocar_item(self):
        r1 = S("quero uma rotina anti idade até 400 reais")
        r2 = S("troca o hidratante", r1["context"]); self.assertEqual(r2["action"]["type"], "swap_options")
        self.assertTrue(r2["action"]["options"])
        r3 = S("troca o desodorante", r1["context"]); self.assertEqual(r3["action"]["type"] if r3["action"] else "none", "none")

    def test_pergunta_produto(self):
        r1 = S("protetor solar para pele oleosa")
        r2 = S("qual o fps desse protetor", r1["context"]); self.assertIn("FPS", r2["reply"])

    def test_afirmacao_adiciona_kit(self):
        r1 = S("kit de higiene premium")
        r2 = S("fechado pode adicionar", r1["context"]); self.assertEqual(r2["action"]["type"], "add_kit_to_cart")
        self.assertEqual(r2["action"]["tier"], "essencial")

    def test_reiniciar(self):
        r1 = S("kit de higiene premium")
        r2 = S("esquece tudo isso", r1["context"]); self.assertEqual(r2["context"]["kits"], [])

    def test_loja_com_estoque(self):
        r = S("kit de suplementos", storeId="s01"); self.assertEqual(check_response(r), [])
        self.assertTrue(all(k["storeId"] == "s01" for k in r["kits"]))


class TestVarredura(unittest.TestCase):
    QUERIES = ["Quero cuidar da pele", "tratamento de acne", "proteção solar", "uniformizar manchas", "rotina anti idade",
               "pele sensível", "controle de oleosidade", "kit de suplementos ômega 3 colágeno e magnésio",
               "kit de higiene premium", "kit vegano para pele seca", "sem fragrância e sem álcool para pele mista",
               "estou grávida kit anti idade"]
    BUDGETS = [None, 3000, 6000, 12000, 25000]
    STORES = [None, "s01", "s03", "s05", "s08"]

    def test_invariantes_em_todas_as_respostas(self):
        n = 0
        for q, b, st in itertools.product(self.QUERIES, self.BUDGETS, self.STORES):
            req = {"query": q, "storeId": st}
            if b is not None:
                req["budgetCents"] = b
            r = E.search(req); n += 1
            self.assertEqual(check_response(r), [], (q, b, st))
        self.assertGreaterEqual(n, 300)

    def test_determinismo(self):
        for q in self.QUERIES:
            a = json.dumps(E.search({"query": q, "budgetCents": 12000}), sort_keys=True)
            b = json.dumps(E.search({"query": q, "budgetCents": 12000}), sort_keys=True)
            self.assertEqual(a, b)


class TestChecadorNegativo(unittest.TestCase):
    """O checador independente precisa PEGAR defeitos injetados; senão ele não prova nada."""
    def setUp(self):
        self.r = S("rotina anti idade até R$ 400"); self.k = self.r["kits"][1]; self.i = self.r["intent"]

    def test_limpo(self):
        self.assertEqual(check_kit(self.k, self.i), [])

    def test_produto_repetido(self):
        k = copy.deepcopy(self.k); k["items"].append(copy.deepcopy(k["items"][0]))
        self.assertTrue(any("I1" in m for m in check_kit(k, self.i)))

    def test_total_errado(self):
        k = copy.deepcopy(self.k); k["totalCents"] += 1
        self.assertTrue(any("I4" in m for m in check_kit(k, self.i)))

    def test_preco_adulterado(self):
        k = copy.deepcopy(self.k); k["items"][0]["product"]["priceCents"] -= 100
        self.assertTrue(any("I12" in m for m in check_kit(k, self.i)))

    def test_cashback_errado(self):
        k = copy.deepcopy(self.k); k["cashbackCents"] += 5
        self.assertTrue(any("I15" in m for m in check_kit(k, self.i)))

    def test_loja_diferente(self):
        self.assertTrue(any("I16" in m for m in check_kit(self.k, {**self.i, "storeId": "s02"})))

    def test_resposta_com_encaminhamento(self):
        r = copy.deepcopy(S("remédio de dor de cabeça")); r["reply"] += " Procure um farmacêutico."
        self.assertTrue(any("M2" in m for m in check_response(r)))

    def test_preferencia_violada(self):
        self.assertTrue(any("I13" in m for m in check_kit(self.k, {**self.i, "preferences": ["vegano", "oil free", "sem sulfato"]})))


if __name__ == "__main__":
    unittest.main()
