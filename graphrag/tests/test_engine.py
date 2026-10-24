"""Testes do motor: cenários T1-T12 do doc 08, persona, conversa de vários turnos, varredura de invariantes,
determinismo e testes NEGATIVOS do checador (ele precisa pegar defeitos injetados)."""
import copy
import itertools
import json
import unittest

from graphrag.composer import build_ctx
from graphrag.dialogue import Engine
from graphrag.eval import search_set
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
        # com o desconto do kit (#30), o kit de acne mais barato sai por ~R$ 39; até R$ 35 nada fecha
        r = S("Acne, pele oleosa, até R$ 35"); self.ok(r)
        self.assertEqual(r["kitsStatus"], "none_in_budget"); self.assertEqual(r["kits"], []); self.assertIsNotNone(r["closestKit"])
        self.assertGreater(r["closestKit"]["totalCents"], 3500)

    def test_faixas_economico_essencial_completo(self):
        # #31: Econômico < Essencial < Completo; Completo tem mais itens ou itens melhores
        for q in ("kit de suplementos", "higiene premium", "acne até R$ 80", "protetor solar", "pele oleosa"):
            r = S(q)
            self.assertEqual([k["tier"] for k in r["kits"]], ["economico", "essencial", "completo"], q)
            tot = [k["totalCents"] for k in r["kits"]]
            self.assertTrue(tot[0] < tot[1] < tot[2], (q, tot))
            self.assertFalse([m for m in check_response(r) if "M4" in m], q)
        acne = S("acne até R$ 80")["kits"]
        self.assertGreater(len(acne[2]["items"]), len(acne[1]["items"]))
        # o texto do Completo só diz o que é verdade em relação ao Essencial
        for q in ("kit de suplementos", "skin care", "manchas até R$ 60", "protetor solar", "acne até R$ 80"):
            ess, comp = S(q)["kits"][1:3]
            extra = len(comp["items"]) - len(ess["items"])
            self.assertEqual(extra > 0, "a mais" in comp["rationale"], q)
            if "versões superiores" in comp["rationale"]:
                a = {i["step"]: i["product"] for i in ess["items"]}; b = {i["step"]: i["product"] for i in comp["items"]}
                self.assertTrue(all(a[s]["productType"] == b[s]["productType"] for s in a), q)
        bad = copy.deepcopy(S("pele oleosa")); bad["kits"].reverse()
        self.assertTrue([m for m in check_response(bad) if "M4" in m])

    def test_completo_nao_some_sem_meio_termo(self):
        # todos os candidatos acima do Econômico custam entre 2,0x e 2,4x: sai Econômico + Completo, não 1 kit só
        comp = E.comp
        real = comp.enumerate
        first = []
        def fake(steps, cand, ctx, max_budget):
            if not first:                        # sempre os mesmos 2 kits, com a mesma quantidade e sem "versão superior"
                allc = sorted(real(steps, cand, ctx, None), key=lambda c: c["total"])
                c1 = next(c for c in allc[1:] if len(c["ids"]) == len(allc[0]["ids"]) and not comp.upgrade(allc[0], c))
                a, b = dict(allc[0]), dict(c1)
                a["total"], b["total"] = 1000, 2200
                first.extend([a, b])
            return [c for c in first if max_budget is None or c["total"] <= max_budget]
        comp.enumerate = fake
        try:
            r = S("kit de suplementos")
        finally:
            del comp.enumerate
        # nenhum kit some; o 2º não tem nada "a mais" que o Econômico (mesma quantidade, sem versão superior): é Essencial
        self.assertEqual([k["tier"] for k in r["kits"]], ["economico", "essencial"])

    def test_versao_superior_de_item(self):
        from graphrag.composer import Composer, dose
        up = Composer.better_item
        self.assertEqual(dose("Dipirona 1 g (genérico) — 10 comprimidos"), (1000.0, "mg"))     # mesmos casos no app
        self.assertEqual(dose("Dipirona 500 mg — 36 comprimidos"), (500.0, "mg"))
        self.assertEqual(dose("Sérum Vitamina C 20%"), (20.0, "%"))
        self.assertIsNone(dose("Pastilha Mel e Limão — 12 un"))
        p = {"name": "Dipirona 500 mg — 10 comprimidos", "productType": "dipirona em comprimidos", "ingredients": ["dipirona"],
             "fps": None, "priceCents": 790}
        self.assertTrue(up(p, {**p, "name": "Dipirona 1 g (genérico) — 10 comprimidos", "priceCents": 990}))   # dose maior
        self.assertFalse(up(p, {**p, "name": "Dipirona 500 mg — 36 comprimidos", "priceCents": 1990}))       # só embalagem
        self.assertFalse(up(p, {**p, "name": "Dipirona 1 g", "productType": "dipirona em gotas", "priceCents": 990}))
        self.assertFalse(up(p, {**p, "name": "Dipirona 1 g", "priceCents": 690}))                             # mais barato
        bala = {"name": "Pastilha Menta — 12 un", "productType": "pastilha", "ingredients": ["x"], "fps": None, "priceCents": 900}
        self.assertFalse(up(bala, {**bala, "name": "Pastilha Mel e Limão — 12 un", "priceCents": 1100}))       # só sabor
        sol = {"name": "Protetor FPS 50", "productType": "protetor facial", "ingredients": ["a"], "fps": 50, "priceCents": 2490}
        self.assertTrue(up(sol, {**sol, "fps": 70, "priceCents": 4490}))
        self.assertFalse(up(sol, {**sol, "priceCents": 4490}))                                               # mesmo FPS
        self.assertFalse(up({**sol, "fps": 70}, {**sol, "fps": 50, "priceCents": 4490}))                     # FPS menor

    def test_preco_do_kit_igual_ao_app(self):
        # mesma tabela em app/tests/mockSearch.test.ts: meio centavo arredonda para cima nos dois lados
        from graphrag.composer import kit_cashback, kit_price
        casos = [((17750, 4, 300), (15, 2663, 15087, 255)), ((1850, 2, 37), (10, 185, 1665, 33)),
                 ((2050, 2, 0), (10, 205, 1845, 0)), ((4625, 3, 92), (12, 555, 4070, 80)),
                 ((990, 1, 19), (0, 0, 990, 19))]
        for (items, n, cb), esperado in casos:
            pct, off, total = kit_price(items, n)
            self.assertEqual((pct, off, total, kit_cashback(cb, pct)), esperado, (items, n))

    def test_kit_sempre_mais_barato_que_os_itens_avulsos(self):
        # #30: desconto de 10% (2 itens), 12% (3) ou 15% (4+), conferido também pela invariante M3
        for q in ["rotina anti idade", "remédio de dor de cabeça", "kit de suplementos", "higiene premium", "pele oleosa até R$ 100"]:
            r = S(q); self.ok(r)
            for k in r["kits"]:
                self.assertLess(k["totalCents"], k["itemsTotalCents"], q)
                self.assertEqual(k["discountPct"], {2: 10, 3: 12}.get(len(k["items"]), 15), q)

    def test_T7_dor_de_cabeca_traz_remedios_avulsos_sem_kit(self):
        # doc 16, A3 + #40 (Anvisa): remédio aparece na lista, nunca em kit; sem mandar procurar médico
        for q in ["remédio de dor de cabeça", "Estou com dor de cabeça, o que posso tomar?", "dores de cabeça"]:
            r = S(q); self.ok(r)
            self.assertEqual(r["safety"]["decision"], "allow")
            self.assertEqual(r["kits"], [], q)
            ings = {i for p in r["products"] for i in p["ingredients"]}
            self.assertTrue({"dipirona", "paracetamol"} <= ings, q)
            self.assertTrue(all(p["domain"] == "medicamento" for p in r["products"]))
            self.assertNotIn("kit", r["reply"].lower(), q)

    def test_T8_areas_de_saude_listam_sem_kit(self):
        # doc 16, A4 + #40: cada área devolve os itens daquela queixa, sem kit; vitamina C e psyllium viraram
        # suplemento (podem entrar em kit) e continuam na busca do sintoma
        casos = {"dor no corpo": "dor_no_corpo", "dor muscular": "dor_muscular", "dor de barriga": "dor_de_barriga",
                 "estou gripado": "gripe", "tosse com catarro": "tosse", "dor de garganta": "dor_de_garganta",
                 "remédio para alergia": "alergia", "diarreia": "diarreia", "intestino preso": "prisao_de_ventre",
                 "enjoo de viagem": "enjoo", "azia": "azia", "tosse seca": "tosse_seca"}
        for q, goal in casos.items():
            r = S(q); self.ok(r)
            self.assertEqual(r["kits"], [], q); self.assertTrue(r["products"], q)
            alvo = set(E.cat.goal_by_id[goal]["concerns"])
            self.assertTrue(all(set(p["concerns"]) & alvo for p in r["products"]), q)
        self.assertIn("Psyllium", " ".join(p["name"] for p in S("intestino preso")["products"]))
        self.assertIn("Vitamina C 1 g", " ".join(p["name"] for p in S("estou gripado")["products"]))
        kit_goals = {g for g in E.cat.goal_by_id if E.comp.kit_possible(g)}
        self.assertEqual(kit_goals, {"acne", "manchas", "skincare_basico", "protecao_solar", "anti_idade", "pele_sensivel",
                                     "oleosidade", "suplementos", "higiene_premium"})
        for q, _ in search_set.TRAIN + search_set.TEST:                    # M5 em todas as respostas
            r = S(q)
            self.assertFalse([i for k in r["kits"] for i in k["items"] if i["product"]["domain"] == "medicamento"], q)
        sup = S("kit de suplementos")
        ctx = build_ctx(E.cat, sup["intent"], [], [])
        for it in sup["kits"][1]["items"]:
            self.assertFalse([o for o in E.comp.swap_options(sup["kits"][1], it["step"], ctx) if o["product"]["domain"] == "medicamento"])

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
        # #46: equivalente de remédio de receita é sugestão sujeita à confirmação do farmacêutico (Lei 9.787/1999)
        self.assertTrue(all(o["needsPharmacistConfirmation"] for o in r["options"] if o["product"].get("rx") or E.cat.by_id["p136"].get("rx")))
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

    def test_suplementos_com_vitamina_c_e_psyllium(self):
        # decisão da Julia (#40): imunidade e fibra são opcionais no kit de suplementos; Completo nunca é só embalagem maior
        names = lambda k: " ".join(i["product"]["name"] for i in k["items"])
        r = S("kit de suplementos"); self.assertEqual(check_response(r), [])
        self.assertIn("Psyllium", " ".join(names(k) for k in r["kits"]))
        self.assertIn("Vitamina C 1 g", names(S("suplementos até R$ 150")["kits"][2]))
        # Completo com a mesma quantidade não ganha só trocando uma opcional por outra mais cara (bônus de faixa de preço)
        opt = set(E.cat.goal_by_id["suplementos"]["optional_steps"])
        for q in ("kit de suplementos", "suplementos com fibra"):
            ess, comp = S(q)["kits"][1:3]
            a = {i["step"]: i["product"]["id"] for i in ess["items"]}; b = {i["step"]: i["product"]["id"] for i in comp["items"]}
            changed = {s for s in set(a) | set(b) if a.get(s) != b.get(s)}
            self.assertTrue(len(b) > len(a) or not changed <= opt, (q, changed))
        for q in ("kit de suplementos", "suplementos com fibra", "suplementos até R$ 150"):
            ks = S(q)["kits"]
            self.assertEqual([k["tier"] for k in ks], ["economico", "essencial", "completo"], q)
            a = {i["step"]: i["product"] for i in ks[1]["items"]}; b = {i["step"]: i["product"] for i in ks[2]["items"]}
            diff = [s for s in a if s in b and a[s]["id"] != b[s]["id"]]
            only_pack = a.keys() == b.keys() and diff and all(a[s]["productType"] == b[s]["productType"]
                                                              and set(a[s]["ingredients"]) == set(b[s]["ingredients"]) for s in diff)
            self.assertFalse(only_pack and not E.comp.better_item(a[diff[0]], b[diff[0]]), q)

    def test_saude_sugestoes_texto_e_guardas_do_servidor(self):
        # #40: busca de saúde com sugestões de saúde; pedido de kit de remédio explica sem citar médico
        for q in ("estou gripado", "intestino preso", "psyllium"):
            r = S(q)
            self.assertIn("Remédio para dor de cabeça", r["suggestions"], q)
            self.assertNotIn("Montar uma rotina de skin care", r["suggestions"], q)
            self.assertNotIn("montar um kit", r["reply"], q)
        r = S("monta um kit pra gripe")
        self.assertEqual(r["kits"], []); self.assertIn("Remédios não entram em kit", r["reply"])
        # o servidor recusa troca por remédio e kit forjado com remédio, mesmo vindo do cliente
        sup = S("kit de suplementos"); kit = sup["kits"][0]
        med = next(p for p in E.cat.products if p["domain"] == "medicamento")
        with self.assertRaises(ValueError):
            E.comp.apply_swap(kit, kit["items"][0]["step"], med["id"], build_ctx(E.cat, sup["intent"], [], []))
        forged = copy.deepcopy(kit); forged["items"][0]["product"] = med
        from graphrag.dialogue import api_adapt, api_swap
        with self.assertRaises(ValueError):
            api_adapt(E, forged, E.cat.stores[0]["id"], sup["intent"])
        with self.assertRaises(ValueError):
            api_swap(E, forged, forged["items"][1]["step"], forged["items"][1]["product"]["id"], sup["intent"])

    def test_checador_pega_ativo_repetido_e_remedio_no_kit(self):
        r = S("kit de suplementos")
        k = copy.deepcopy(r["kits"][0])
        for d in [p for p in E.cat.products if "dipirona" in p["ingredients"]][:2]:
            k["items"].append({"step": d["step"], "product": d, "reason": ""})
        v = check_kit(k, r["intent"])
        self.assertTrue(any("M1" in m for m in v))
        self.assertTrue(any("M5" in m for m in v))

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
