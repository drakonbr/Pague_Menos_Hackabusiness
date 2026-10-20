import unittest

from graphrag.dialogue import Engine
from graphrag.nlu import ActClassifier
from graphrag.nlu_corpus import TEST, TRAIN

E = Engine.build()


class TestNLU(unittest.TestCase):
    def test_treino_e_teste_nao_se_misturam(self):
        a = {t for ts in TRAIN.values() for t in ts}; b = {t for ts in TEST.values() for t in ts}
        self.assertFalse(a & b)

    def test_acuracia_do_ato_no_teste(self):
        clf = ActClassifier().fit(TRAIN)
        ok = sum(clf.predict(t)[0] == act for act, ts in TEST.items() for t in ts)
        tot = sum(len(ts) for ts in TEST.values())
        self.assertGreaterEqual(ok / tot, 0.90, f"{ok}/{tot}")

    def test_entidades(self):
        u = E.nlu.understand("kit vegano para pele seca até R$ 150 sem retinol")
        self.assertEqual((u.skin, u.budget_cents), ("seca", 15000))
        self.assertIn("vegano", u.preferences); self.assertIn("retinol", u.excluded_ingredients)
        self.assertNotIn("retinol", u.requested_ingredients)

    def test_orcamento_por_extenso(self):
        self.assertEqual(E.nlu.understand("quero uniformizar manchas até cem reais").budget_cents, 10000)

    def test_gestacao(self):
        self.assertTrue(E.nlu.understand("estou amamentando, kit anti idade").pregnancy)

    def test_giria_cai_no_objetivo_certo(self):
        self.assertEqual(E.nlu.understand("pele que brilha muito no meio do dia").primary_goal, "oleosidade")

    def test_suplementos_e_higiene(self):
        self.assertEqual(E.nlu.understand("quero ômega 3, colágeno e magnésio").primary_goal, "suplementos")
        self.assertEqual(E.nlu.understand("shampoo e creme dental premium").primary_goal, "higiene_premium")

    def test_ato_com_contexto(self):
        self.assertEqual(E.nlu.understand("sem fragrância", has_context=True).act, "refinar")
        self.assertEqual(E.nlu.understand("troca o hidratante", has_context=True).act, "trocar_item")


if __name__ == "__main__":
    unittest.main()
