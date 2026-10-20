"""Ontologia estrita e ingestão incremental: valida, resolve entidades, não duplica, não escreve em catalog/."""
import copy
import json
import pathlib
import tempfile
import unittest

from pydantic import ValidationError

from graphrag.data import DATA_DIR
from graphrag.dialogue import Engine
from graphrag.graph import nid
from graphrag.ontology import ProductRecord, validate_graph

NOVO = {
    "name": "Ômega 3 Algas Vegano 1000 mg", "brand": "ESSÊNCIA NUTRI", "line": "suplementos", "step": "omega3",
    "coversSteps": ["omega3"], "productType": "suplemento de ômega 3 em cápsulas", "form": "caps",
    "size": {"value": 60, "unit": "un"}, "skinTypes": ["Todas"], "concerns": ["Nutrição e bem-estar"], "ingredients": [],
    "claims": ["Vegano", "sem glúten", "sem corantes"], "warnings": ["consultar_se_medicacao"],
    "description": "Suplemento de ômega 3 de origem vegetal (algas), cápsulas de 1000 mg, rotina diária.",
    "howToUse": "Use a quantidade indicada na embalagem.", "priceTier": "premium", "priceCents": 8990, "stockQty": 40,
    "domain": "suplemento",
}


def fresh() -> Engine:
    return Engine.build(delta_path=pathlib.Path(tempfile.mkdtemp()) / "sem_delta.json")


def count(e: Engine, kind: str) -> int:
    return sum(1 for n in e.graph.g.nodes if n.startswith(kind + ":"))


class TestOntologia(unittest.TestCase):
    def test_grafo_base_respeita_a_ontologia(self):
        self.assertEqual(validate_graph(fresh().graph.g), [])

    def test_ontologia_pega_aresta_ilegal_e_no_sem_tipo(self):
        g = copy.deepcopy(fresh().graph.g)
        a, b = nid("product", "p001"), nid("brand", "Clara Pele")
        g.add_edge(a, b, type="CONTAINS")                     # produto não CONTÉM marca
        g.add_edge(a, "nada:x", type="OF_BRAND")             # destino inexistente
        g.add_edge(a, b, type="INVENTADA")
        errs = validate_graph(g)
        self.assertEqual(len(errs), 4, errs)      # ilegal, tipo inventado, destino sem tipo e destino inexistente

    def test_todos_os_produtos_do_catalogo_passam_no_esquema_de_entrada(self):
        e = fresh()
        campos = set(ProductRecord.model_fields)
        for p in e.cat.products:
            ProductRecord.model_validate({k: v for k, v in p.items() if k in campos})

    def test_esquema_recusa_registros_incoerentes(self):
        ruins = [
            {**NOVO, "priceCents": 0},
            {**NOVO, "coversSteps": ["colageno"]},                       # não contém a etapa principal
            {**NOVO, "listPriceCents": 10},                             # preço de lista menor que o preço
            {**NOVO, "campoInventado": 1},                              # campo fora do esquema
            {**NOVO, "fps": 3},                                         # fps fora da faixa
            {**NOVO, "domain": "medicamento"},                          # medicamento sem rx nem equivalência
            {**NOVO, "rx": "receita_simples"},                          # rx fora de medicamento
            {**NOVO, "form": "bola"},
        ]
        for r in ruins:
            with self.assertRaises(ValidationError, msg=str(r)[:80]):
                ProductRecord.model_validate(r)


class TestIngestao(unittest.TestCase):
    def test_cria_resolve_marca_e_nao_duplica_nos(self):
        e = fresh()
        marcas, claims, prods, nos = count(e, "brand"), count(e, "claim"), len(e.cat.products), e.graph.g.number_of_nodes()
        rep = e.ingest([NOVO], persist=False)
        r = rep.results[0]
        self.assertEqual((r.status, r.id), ("created", "p139"), r.reasons)
        self.assertEqual(count(e, "brand"), marcas, "'ESSÊNCIA NUTRI' deveria resolver para a marca que já existe")
        self.assertTrue(any("marca" in x and "Essência Nutri" in x for x in r.resolved), r.resolved)
        self.assertEqual(count(e, "claim"), claims + 1)                 # só 'sem corantes' é novo; 'Vegano' e 'sem glúten' resolvem
        self.assertEqual(len(e.cat.products), prods + 1)
        self.assertEqual(e.graph.g.number_of_nodes(), nos + 2)          # o produto + a alegação nova
        self.assertEqual(validate_graph(e.graph.g), [])

    def test_idempotente_e_sem_id_atualiza_o_mesmo_produto(self):
        e = fresh()
        e.ingest([NOVO], persist=False)
        nos, arestas, prods = e.graph.g.number_of_nodes(), e.graph.g.number_of_edges(), len(e.cat.products)
        rep = e.ingest([NOVO, {**NOVO, "id": "p139"}], persist=False)
        self.assertEqual([r.status for r in rep.results], ["unchanged", "unchanged"])
        self.assertEqual((e.graph.g.number_of_nodes(), e.graph.g.number_of_edges(), len(e.cat.products)), (nos, arestas, prods))
        rep = e.ingest([{**NOVO, "priceCents": 7990}], persist=False)
        self.assertEqual(rep.results[0].status, "updated")
        self.assertEqual(e.cat.by_id["p139"]["priceCents"], 7990)
        self.assertEqual(len(e.cat.products), prods)

    def test_duplicata_com_outro_id_e_recusada(self):
        e = fresh()
        e.ingest([NOVO], persist=False)
        rep = e.ingest([{**NOVO, "id": "p500"}], persist=False)
        self.assertEqual(rep.results[0].status, "rejected")
        self.assertIn("duplicata de p139", rep.results[0].reasons[0])

    def test_vocabulario_fechado_recusa_sem_tocar_no_grafo(self):
        e = fresh()
        antes = (len(e.cat.products), e.graph.g.number_of_nodes(), e.graph.g.number_of_edges())
        ruins = [{**NOVO, "ingredients": ["ingrediente_que_nao_existe"]}, {**NOVO, "concerns": ["fofura"]},
                 {**NOVO, "step": "etapa_nova", "coversSteps": ["etapa_nova"]}, {**NOVO, "warnings": ["aviso_novo"]},
                 {**NOVO, "storeStock": {"s99": 3}}]
        rep = e.ingest(ruins, persist=False)
        self.assertEqual([r.status for r in rep.results], ["rejected"] * len(ruins), [r.reasons for r in rep.results])
        self.assertEqual((len(e.cat.products), e.graph.g.number_of_nodes(), e.graph.g.number_of_edges()), antes)

    def test_um_registro_ruim_nao_derruba_o_lote(self):
        e = fresh()
        rep = e.ingest([{**NOVO, "priceCents": -5}, NOVO], persist=False)
        self.assertEqual([r.status for r in rep.results], ["rejected", "created"])

    def test_produto_novo_e_encontrado_na_busca(self):
        e = fresh()
        e.ingest([NOVO], persist=False)
        r = e.search({"query": "ômega 3 de algas 1000 mg"})
        self.assertIn("p139", [p["id"] for p in r["products"]])

    def test_incremental_em_memoria_igual_a_reconstruir_do_zero(self):
        delta = pathlib.Path(tempfile.mkdtemp()) / "delta.json"
        a = fresh()
        outro = {**NOVO, "name": "Colágeno Verisol Sachê", "step": "colageno", "coversSteps": ["colageno"],
                 "productType": "suplemento de colágeno em sachê", "form": "powder", "claims": ["sem açúcar"],
                 "description": "Colágeno hidrolisado em sachê, sabor neutro, para a rotina de beleza de dentro para fora.",
                 "storeStock": {"s01": 7}}
        a.ingest([NOVO, outro], persist=True, delta_path=delta)
        b = Engine.build(delta_path=delta)
        self.assertEqual(sorted(a.graph.g.nodes), sorted(b.graph.g.nodes))
        key = lambda g: sorted((u, v, d["type"], round(d.get("weight", 0), 6)) for u, v, d in g.edges(data=True))   # noqa: E731
        self.assertEqual(key(a.graph.g), key(b.graph.g))
        self.assertEqual(a.cat.by_id, b.cat.by_id)
        self.assertEqual(b.cat.store_stock["s01"]["p140"], 7)
        # o delta é determinístico e só tem os registros resolvidos
        txt = delta.read_text(encoding="utf-8")
        self.assertEqual([p["id"] for p in json.loads(txt)["products"]], ["p139", "p140"])

    def test_nao_escreve_em_catalog(self):
        antes = {p.name: (p.stat().st_mtime_ns, p.stat().st_size) for p in DATA_DIR.iterdir() if p.is_file()}
        e = fresh()
        e.ingest([NOVO], persist=True, delta_path=pathlib.Path(tempfile.mkdtemp()) / "d.json")
        depois = {p.name: (p.stat().st_mtime_ns, p.stat().st_size) for p in DATA_DIR.iterdir() if p.is_file()}
        self.assertEqual(antes, depois)

    def test_medicamento_ingerido_nunca_aparece_em_busca_nem_kit(self):
        e = fresh()
        med = {**NOVO, "name": "Cardivex 10 mg (genérico) 30 comprimidos", "brand": "Lab Nova Via", "line": "reposicao_cardivex_10",
               "step": "reposicao", "coversSteps": ["reposicao"], "productType": "comprimido de uso contínuo", "form": "box",
               "concerns": ["reposicao"], "claims": [], "warnings": ["receita_obrigatoria", "confirmar_troca_com_farmaceutico"],
               "description": "Medicamento FICTÍCIO de demonstração para a tela de reposição; princípio ativo inventado.",
               "howToUse": "Use somente conforme a sua receita.", "domain": "medicamento", "rx": "receita_simples",
               "equivalence": {"group": "cardivex_10", "presentation": "generico", "active": "Cardivex", "dose": "10 mg"},
               "step_": None}
        med.pop("step_")
        rep = e.ingest([med], persist=False)
        self.assertEqual(rep.results[0].status, "created", rep.results[0].reasons)
        self.assertEqual(validate_graph(e.graph.g), [])
        for q in ["cardivex", "comprimido de uso contínuo", "kit de suplementos", "reposição", "rotina anti idade"]:
            r = e.search({"query": q})
            vistos = [p["id"] for p in r["products"]] + [i["product"]["id"] for k in r["kits"] for i in k["items"]]
            self.assertNotIn("p139", vistos, q)


if __name__ == "__main__":
    unittest.main()
