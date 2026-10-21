"""Mede a qualidade da lista de itens da busca.  python3 graphrag/eval/search_quality.py [--falhas] [--so test]

Por frase: precisão = parte dos itens listados que são relevantes; acerto = ao menos 1 relevante; limpo = precisão
100% com ao menos 1 item. Para item que não existe no catálogo ("absent"): precisa vir o aviso (catalogNotice) e só
pode aparecer item das etapas vizinhas. Para remédio que não existe ("missing"): só "Não está no banco de dados ainda."
"""
from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from graphrag.dialogue import Engine                       # noqa: E402
from graphrag.concepts import MED_MISSING                  # noqa: E402
from graphrag.eval.search_set import (BLIND, BLIND2, BLIND3, BLIND4, MED, MED_BLIND, TEST, TRAIN,   # noqa: E402
                                      relevant_ids)


def avaliar(eng: Engine, casos, falhas: list):
    linhas = []
    for frase, regra in casos:
        r = eng.search({"query": frase})
        ids = [p["id"] for p in r.get("products", [])]
        kind = regra[0]
        if kind == "missing":
            ok = r["reply"] == MED_MISSING and not ids and not r.get("kits")
            linhas.append(("missing", ok, None))
        elif kind == "absent":
            viz = set(regra[1:])
            avisou = bool(r.get("catalogNotice"))
            fora = [i for i in ids if eng.cat.by_id[i]["step"] not in viz and not (set(eng.cat.by_id[i]["coversSteps"]) & viz)]
            ok = avisou and not fora
            linhas.append(("absent", ok, None))
        else:
            rel = relevant_ids(eng.cat, regra)
            prec = (sum(i in rel for i in ids) / len(ids)) if ids else 0.0
            cobre = True
            if kind == "steps_all":                      # pediu duas coisas: precisa vir das duas prateleiras
                cobre = all(any(eng.cat.by_id[i]["step"] == s for i in ids) for s in regra[1:])
            ok = bool(ids) and prec == 1.0 and cobre
            linhas.append((kind, ok, prec if cobre else min(prec, 0.5)))
        if not ok:
            falhas.append((frase, regra, r["act"], len(r.get("kits", [])), len(ids), bool(r.get("catalogNotice")),
                           [eng.cat.by_id[i]["name"][:26] for i in ids[:6]]))
    return linhas


def resumo(nome, linhas):
    pos = [x for x in linhas if x[0] not in ("absent", "missing")]
    ab = [x for x in linhas if x[0] == "absent"]
    bl = [x for x in linhas if x[0] == "missing"]
    prec = statistics.mean(x[2] for x in pos) if pos else 0
    print(f"{nome:<6} itens relevantes: precisão média {prec:.3f} · listas limpas {sum(x[1] for x in pos)}/{len(pos)}"
          f" · aviso de item inexistente {sum(x[1] for x in ab)}/{len(ab)} · remédio fora do banco {sum(x[1] for x in bl)}/{len(bl)}")
    return prec, sum(x[1] for x in pos) / max(1, len(pos))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--falhas", action="store_true"); ap.add_argument("--so", default="")
    a = ap.parse_args()
    eng = Engine.build()
    for nome, casos in (("treino", TRAIN), ("teste", TEST), ("cego", BLIND), ("cego2", BLIND2), ("cego3", BLIND3),
                        ("cego4", BLIND4), ("med", MED), ("medcego", MED_BLIND)):
        if a.so and a.so != nome:
            continue
        f: list = []
        resumo(nome, avaliar(eng, casos, f))
        if a.falhas:
            for x in f:
                print("   ✗", x)
