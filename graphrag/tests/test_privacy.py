"""Privacidade por construção (doc 14): o motor não lê dados da pessoa e não devolve termos de saúde."""
import builtins
import json
import pathlib
import re
import unittest
from unittest import mock

import numpy as np

from graphrag import data as gdata
from graphrag.dialogue import Engine
from graphrag.lexicon import HEALTH_TERMS
from graphrag.text import norm

ENTRADAS_DE_SAUDE = [
    "preciso repor meu remédio de pressão", "meu remédio de colesterol está acabando", "tenho hipertensão e colesterol alto",
    "tem similar do meu remédio de pressão", "quero suplemento para baixar a pressão", "sou diabética, qual kit de higiene",
    "reposição dos meus medicamentos", "qual o frete do meu remédio de pressão", "tomo remédio de pressão, quero kit de suplementos",
]
TEXTOS = ("reply", "suggestions", "notes")


def texto_visivel(r: dict) -> str:
    parts = [r["reply"], " ".join(r["suggestions"]), " ".join(r["notes"]), json.dumps(r["safety"], ensure_ascii=False),
             json.dumps(r["context"], ensure_ascii=False)]
    return norm(" ".join(parts))


class TestPrivacidade(unittest.TestCase):
    def test_persona_fora_da_lista_de_leitura(self):
        self.assertNotIn("persona.json", gdata.ALLOWED_FILES)
        with self.assertRaises(AssertionError):
            gdata._load("persona.json")

    def test_motor_nunca_abre_persona(self):
        opened = []
        real_open, real_read, real_np = builtins.open, pathlib.Path.read_text, np.load

        def spy_open(f, *a, **k):
            opened.append(str(f)); return real_open(f, *a, **k)

        def spy_read(self, *a, **k):
            opened.append(str(self)); return real_read(self, *a, **k)

        def spy_np(f, *a, **k):
            opened.append(str(f)); return real_np(f, *a, **k)

        with mock.patch("builtins.open", spy_open), mock.patch.object(pathlib.Path, "read_text", spy_read), \
                mock.patch("numpy.load", spy_np):
            e = Engine.build()
            for q in ENTRADAS_DE_SAUDE + ["kit de suplementos", "rotina anti idade"]:
                e.search({"query": q})
            e.similars("p136", "s01")
        self.assertTrue(opened)
        self.assertFalse([p for p in opened if "persona" in p.lower()], "o motor abriu um arquivo de persona")

    def test_respostas_nao_repetem_termos_de_saude(self):
        e = Engine.build()
        for q in ENTRADAS_DE_SAUDE:
            ctx = None
            for turno in (q, "qual a entrega mais rápida", "tem similar"):
                r = e.search({"query": turno, **({"context": ctx} if ctx else {})})
                ctx = r["context"]
                txt = texto_visivel(r)
                for t in HEALTH_TERMS:
                    self.assertNotIn(norm(t), txt, f"'{t}' voltou na resposta a: {turno!r} (entrada {q!r})")

    def test_contexto_so_tem_ids_e_preferencias(self):
        e = Engine.build()
        r = e.search({"query": "meu remédio de pressão está acabando, quero kit de suplementos sem açúcar"})
        permitido = {"intent", "requested", "excluded", "kits", "lastAct", "turn", "focusTier", "focusProductId"}
        self.assertLessEqual(set(r["context"]), permitido)
        blob = json.dumps(r["context"], ensure_ascii=False)
        self.assertNotIn("remédio", blob); self.assertNotIn("pressão", blob)
        for k in r["context"]["kits"]:
            self.assertLessEqual(set(k), {"id", "tier", "title", "goal", "storeId", "rationale", "totalCents", "items"})

    def test_equivalentes_de_medicamento_nao_citam_nome_no_texto(self):
        e = Engine.build()
        r = e.search({"query": "tem similar", "focusProductId": "p136", "storeId": "s01"})
        self.assertEqual(r["act"], "similar"); self.assertEqual(r["action"]["type"], "show_similars")
        for nome in ("tensivalol", "lipostanol", "pressolan", "colemax"):
            self.assertNotIn(nome, norm(r["reply"]))
        self.assertTrue(r["action"]["options"])

    def test_servidor_nao_loga_a_frase(self):
        import inspect
        from graphrag.service import server
        self.assertIn("def log_message", inspect.getsource(server.Handler))
        self.assertIn("pass", inspect.getsource(server.Handler.log_message))

    def test_pacote_nao_importa_o_app(self):
        root = pathlib.Path(__file__).resolve().parents[1]
        for f in root.rglob("*.py"):
            txt = f.read_text(encoding="utf-8")
            self.assertIsNone(re.search(r"^\s*(from|import)\s+app\b", txt, re.M), f.name)


if __name__ == "__main__":
    unittest.main()
