"""Achados do teste de usabilidade (#47, #59): texto de suplemento e nomes de ingredientes."""
import unittest

from graphrag.composer import lower_name
from graphrag.dialogue import Engine

E = Engine.build()


class TestUsabilidade(unittest.TestCase):
    def test_nome_de_ingrediente_mantem_sigla_e_letra_de_vitamina(self):
        self.assertEqual(lower_name("Ômega 3 (EPA e DHA)"), "ômega 3 (EPA e DHA)")
        self.assertEqual(lower_name("Vitamina E"), "vitamina E")
        self.assertEqual(lower_name("Vitamina D3"), "vitamina D3")
        self.assertEqual(lower_name("Niacinamida"), "niacinamida")

    def test_justificativa_do_kit_nao_perde_a_sigla(self):
        r = E.search({"query": "kit de suplementos ômega 3, colágeno e magnésio"})
        textos = " ".join(i["reason"] for k in r["kits"] for i in k["items"])
        self.assertIn("EPA e DHA", textos)
        self.assertNotIn("epa e dha", textos)

    def test_suplemento_nao_traz_queixa_de_saude_na_descricao(self):   # RDC 243/2018
        sup = [p for p in E.cat.products if p["domain"] == "suplemento"]
        self.assertTrue(sup)
        for p in sup:
            self.assertNotIn("Foco em", p["description"], p["name"])
            self.assertNotRegex(p["description"].lower(), r"gripe|resfriado|pris[aã]o de ventre")

    def test_resposta_do_motor_nao_perde_a_sigla(self):
        r = E.search({"query": "o ômega 3 tem EPA e DHA?"})
        self.assertNotIn("epa e dha", r["reply"])

    def test_atalho_de_kit_da_pagina_do_produto_leva_a_kit(self):
        # espelha o atalho do ProductPage.tsx: cada (domínio, queixa) de produto que não é remédio tem de montar kit
        sem_kit = {"desmaquilagem", "textura", "olheiras"}
        nome = {"suplemento": "kit de suplementos", "higiene": "kit de higiene"}
        for p in E.cat.products:
            if p["domain"] == "medicamento" or not p["concerns"]:
                continue
            if p["domain"] in nome:
                q = nome[p["domain"]]
            elif p["concerns"][0] in sem_kit:
                q = "kit de skin care"
            else:
                q = f"cuidados para {E.cat.concerns.get(p['concerns'][0], p['concerns'][0])}"
            self.assertTrue(E.search({"query": q})["kits"], (p["id"], q))


if __name__ == "__main__":
    unittest.main()
