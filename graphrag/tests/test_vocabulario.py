"""Fala do dia a dia que o grafo agora entende sozinho (24/10, treinamento do RAG). Frases próprias, nenhuma do conjunto blind5."""
import unittest

from graphrag.dialogue import Engine

E = Engine.build()
E.rag = None            # só o grafo: sem DeepSeek, sem rede


def goal(q, ctx=None):
    r = E.search({"query": q, **({"context": ctx} if ctx else {})})
    return r["intent"].get("primaryGoal"), r


class TestVocabulario(unittest.TestCase):
    def test_cabeca_e_barriga_ditas_do_jeito_de_casa(self):
        for q, concern in (("minha cabeça tá martelando desde ontem", "dor_de_cabeca"),
                           ("minha barriga tá solta", "diarreia"), ("caganeira desde cedo", "diarreia"), ("soltinho o dia todo", "diarreia")):
            r = E.search({"query": q})
            self.assertTrue(r["products"], q)
            self.assertTrue(all(concern in x["concerns"] for x in r["products"][:3]), (q, [x["name"] for x in r["products"][:3]]))

    def test_alias_novo_nao_cria_falso_positivo(self):   # revisor: "filtro de linha" virava protetor solar, "caroço no seio" kit de acne
        for q in ("filtro de linha", "filtro para café", "caroço no seio", "carocinho na virilha", "soltura de ponto", "barriga mole de gordura",
                  "a conta veio irregular", "caidinha de amor", "não sai nada de água da torneira", "cagando sangue", "urticária e língua inchada", "cabeça explodindo e rigidez no pescoço"):
            r = E.search({"query": q})
            self.assertEqual((r["kits"], r["products"]), ([], []), q)

    def test_sem_acido_so_exclui_esfoliante_e_respeita_ingrediente_nomeado(self):
        _, r0 = goal("rotina para acne")
        for q, esperado in (("sem ácido por favor", {"acido_salicilico", "acido_glicolico", "acido_mandelico"}),
                            ("sem ácido tranexâmico", {"acido_tranexamico"}), ("sem ácidos graxos", set())):
            ex = set(goal(q, r0["context"])[1]["context"].get("excluded") or [])
            self.assertEqual(ex & {"acido_salicilico", "acido_glicolico", "acido_mandelico", "acido_tranexamico", "acido_azelaico"}, esperado, q)

    def test_pele_dita_do_jeito_de_casa(self):
        for q, concern in (("carocinhos no queixo que não saem", "acne"), ("pele descascando nas bochechas", "ressecamento"),
                           ("pele flácida depois dos 50", "sinais_idade"), ("qualquer coisa que passo no rosto irrita", "sensibilidade")):
            r = E.search({"query": q})
            shown = r["products"] or [i["product"] for k in r["kits"] for i in k["items"]]
            self.assertTrue(shown, q)
            self.assertGreaterEqual(sum(concern in p["concerns"] for p in shown) * 2, len(shown), (q, concern))

    def test_bochecha_nao_vira_enxaguante(self):
        r = E.search({"query": "vermelhidão nas bochechas"})
        self.assertFalse(any(p["step"] == "higiene_oral" for p in r["products"]))

    def test_depois_do_banho_nao_vira_pedido_de_banho(self):
        _, r = goal("pele repuxando depois do banho")
        self.assertNotEqual(r["intent"].get("primaryGoal"), "higiene_premium")

    def test_nada_com_ingrediente_e_sem_acido(self):
        _, r0 = goal("rotina para acne")
        _, r = goal("não quero nada com retinol", r0["context"])
        self.assertIn("retinol", " ".join(r["context"].get("excluded") or []))
        _, r = goal("sem ácido, minha pele reagiu", r0["context"])
        self.assertTrue(any(x.startswith("acido") for x in (r["context"].get("excluded") or [])))

    def test_ajuste_de_preco_dito_do_jeito_de_casa(self):
        _, base = goal("rotina para manchas")
        for q in ("dá pra reduzir o valor?", "tá muito caro isso"):
            _, r = goal(q, base["context"])
            self.assertIsNotNone(r["intent"].get("budgetCents"), q)
        _, r = goal("quero uma opção mais top", base["context"])
        tots = [k["totalCents"] for k in base["kits"]]
        self.assertTrue(r["intent"].get("budgetCents") is not None and r["intent"]["budgetCents"] > max(tots))


if __name__ == "__main__":
    unittest.main()
