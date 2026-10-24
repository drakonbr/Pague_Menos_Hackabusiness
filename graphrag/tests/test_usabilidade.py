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

    def test_remedio_de_receita_vem_depois_na_busca_por_sintoma(self):   # #44, RDC 96/2008
        for q in ("remédio para enjoo", "estou com azia", "remédio para alergia", "tosse seca", "diarreia"):
            rx = ["R" if p.get("rx") else "o" for p in E.search({"query": q})["products"]]
            self.assertIn("o", rx, q)
            self.assertEqual("".join(rx), "".join(sorted(rx, key=lambda c: c == "R")), q)   # nenhum "o" depois de um "R"

    def test_quem_pede_o_remedio_de_receita_pelo_nome_o_ve_primeiro(self):
        r = E.search({"query": "metoclopramida"})
        self.assertTrue(r["products"] and r["products"][0].get("rx"))

    def test_remedio_nunca_tem_preco_riscado_no_motor(self):   # #45
        meds = [p for p in E.cat.products if p["domain"] == "medicamento"]
        self.assertTrue(meds)
        for p in meds:
            self.assertEqual(p["listPriceCents"], p["priceCents"], p["name"])

    def test_mais_barato_nao_poe_receita_na_frente(self):   # #44
        r1 = E.search({"query": "remédio para enjoo"})
        r2 = E.search({"query": "mais barato", "context": r1["context"]})
        rx = ["R" if p.get("rx") else "o" for p in r2["products"]]
        self.assertTrue(rx)
        self.assertEqual("".join(rx), "".join(sorted(rx, key=lambda c: c == "R")))

    def test_similares_de_remedio_sem_receita_nao_poem_receita_na_frente(self):
        otc = next(p for p in E.cat.products if p["domain"] == "medicamento" and not p.get("rx") and not p.get("equivalence"))
        rx = ["R" if o["product"].get("rx") else "o" for o in E.similars(otc["id"])["options"]]
        self.assertEqual("".join(rx), "".join(sorted(rx, key=lambda c: c == "R")))

    def test_ingestao_de_remedio_sem_receita_perde_preco_riscado_e_cashback(self):   # #45
        from graphrag.ingest import ingest_records
        import copy
        cat = copy.copy(E.cat)
        cat.products = list(E.cat.products)
        base = next(q for q in cat.products if q["domain"] == "medicamento" and not q.get("rx"))
        rec = {k: base[k] for k in ("id", "name", "brand", "line", "step", "coversSteps", "productType", "form", "size", "skinTypes",
                                    "concerns", "ingredients", "fps", "usagePeriod", "claims", "warnings", "description", "howToUse",
                                    "priceTier", "domain", "rx", "equivalence") if k in base}
        rec.update({"priceCents": base["priceCents"], "listPriceCents": base["priceCents"] * 2, "cashbackPct": 15, "stockQty": 5})
        ingest_records(cat, [rec])
        out = cat.by_id.get(base["id"]) or next(q for q in cat.products if q["id"] == base["id"])
        self.assertEqual(out["listPriceCents"], out["priceCents"])
        self.assertEqual(out["cashbackPct"], 0)


if __name__ == "__main__":
    unittest.main()
