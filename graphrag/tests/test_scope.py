"""Testes da qualidade de busca: prateleira (scope), aviso de item inexistente, correção de digitação e ajustes de lista."""
import unittest

from graphrag.dialogue import Engine
from graphrag.eval.invariants import check_response

E = Engine.build()


def S(q, ctx=None):
    return E.search({"query": q, "context": ctx} if ctx is not None else {"query": q})


def steps(r):
    return {p["step"] for p in r["products"]}


class TestShelf(unittest.TestCase):
    def test_higiene_bucal_so_traz_higiene_bucal(self):
        r = S("quero cuidar da minha higiene bucal")
        self.assertEqual(check_response(r), [])
        self.assertEqual(r["scope"]["kind"], "shelf")
        self.assertEqual(steps(r), {"higiene_oral"})
        self.assertEqual(r["kits"], [])          # prateleira de uma etapa só: lista, sem kit forçado

    def test_sem_enchimento(self):
        r = S("desodorante")
        self.assertTrue(r["products"] and steps(r) == {"desodorante"})

    def test_kit_quando_o_pedido_cobre_as_etapas(self):
        r = S("pele oleosa até R$ 100")
        self.assertEqual(len(r["kits"]), 3)
        self.assertGreater(len(r["products"]), 3)      # kits em cima, lista completa embaixo

    def test_medicamento_nunca_na_lista(self):
        for q in ["quero tudo para a dor", "higiene bucal", "suplementos"]:
            self.assertTrue(all(p["domain"] != "medicamento" for p in S(q)["products"]), q)


class TestAbsent(unittest.TestCase):
    def test_item_que_nao_existe_avisa(self):
        r = S("escova de dente")
        self.assertIn("Não temos escova de dente", r["catalogNotice"]["message"])
        self.assertEqual(r["catalogNotice"]["shelf"], "higiene bucal")
        self.assertTrue(r["products"])             # mostra a prateleira vizinha

    def test_sem_prateleira_vizinha_nao_inventa(self):
        r = S("batom")
        self.assertEqual(r["products"], [])
        self.assertIsNone(r["catalogNotice"]["shelf"])


class TestTypos(unittest.TestCase):
    def test_erro_de_digitacao_e_corrigido(self):
        r = S("protetor solar fasial")
        self.assertIn("facial", r.get("correctedQuery", ""))

    def test_plural_nao_vira_singular(self):
        r = S("preciso repor meus medicamentos")
        self.assertNotIn("correctedQuery", r)
        self.assertEqual(r["act"], "repor_medicamento")

    def test_seguranca_olha_o_texto_original(self):
        r = S("dor de cabeca, o que tomo")
        self.assertEqual(r["safety"]["decision"], "blocked")
        self.assertEqual(r["products"], [])


class TestAjusteDeLista(unittest.TestCase):
    def setUp(self):
        self.first = S("quero cuidar da minha higiene bucal")

    def test_mais_barato_ordena_a_mesma_lista(self):
        r = S("mais barato", self.first["context"])
        self.assertEqual(r["act"], "refinar")
        prices = [p["priceCents"] for p in r["products"]]
        self.assertEqual(prices, sorted(prices))
        self.assertEqual({p["id"] for p in r["products"]}, {p["id"] for p in self.first["products"]})

    def test_sem_alcool_filtra_dentro_da_prateleira(self):
        r = S("sem álcool", self.first["context"])
        self.assertTrue(r["products"] and steps(r) == {"higiene_oral"})
        self.assertLess(len(r["products"]), len(self.first["products"]))

    def test_orcamento_corta_a_lista(self):
        r = S("até R$ 25", self.first["context"])
        self.assertTrue(all(p["priceCents"] <= 2500 for p in r["products"]))

    def test_sugestao_monta_kit(self):
        r = S("Higiene premium", self.first["context"])
        self.assertEqual(len(r["kits"]), 3)


if __name__ == "__main__":
    unittest.main()
