"""Conjunto de avaliação do ranking: frases do dia a dia + o que conta como produto RELEVANTE.

A relevância é definida por uma regra simples sobre o cadastro (preocupação ou etapa do produto), escrita aqui e
independente do código de recuperação. TREINO calibra os pesos; TESTE só mede (nunca entra na calibração).
Cada item: (frase, regra) com regra = ("concern", id) | ("step", id[, id...]).
"""
from __future__ import annotations

TRAIN = [
    ("pele que brilha muito no meio do dia", ("concern", "oleosidade")),
    ("cheia de cravos e espinhas no queixo", ("concern", "acne")),
    ("marquinhas escuras que ficaram da espinha", ("concern", "manchas")),
    ("rugas e linhas de expressão ao redor dos olhos", ("concern", "sinais_idade")),
    ("minha pele repuxa depois do banho", ("concern", "ressecamento")),
    ("qualquer produto arde no meu rosto", ("concern", "sensibilidade")),
    ("preciso de bloqueador para ir à praia", ("step", "protecao_solar", "protecao_corporal")),
    ("óleo de peixe em cápsulas", ("step", "omega3")),
    ("beleza de dentro para fora para pele e unhas", ("step", "colageno")),
    ("quero branquear os dentes", ("step", "higiene_oral")),
    ("shampoo para fios ressecados", ("step", "higiene_cabelo")),
    ("tirar o cheiro de suor da axila", ("step", "desodorante")),
    ("magnésio para tomar à noite", ("step", "magnesio")),
    ("poros abertos no nariz", ("concern", "poros")),
    ("pele áspera e cheia de textura", ("concern", "textura")),
    ("gel de banho cremoso", ("step", "higiene_corpo")),
]

TEST = [
    ("pele brilhosa a tarde toda", ("concern", "oleosidade")),
    ("espinhas inflamadas na testa", ("concern", "acne")),
    ("manchas escuras de sol no rosto", ("concern", "manchas")),
    ("pele madura com sinais da idade", ("concern", "sinais_idade")),
    ("olhos cansados e olheiras fundas", ("concern", "olheiras")),
    ("hidratante para pele desidratada", ("concern", "ressecamento")),
    ("pele reativa e delicada", ("concern", "sensibilidade")),
    ("filtro solar fps alto para o rosto", ("step", "protecao_solar")),
    ("ômega 3 vegano de algas", ("step", "omega3")),
    ("colágeno hidrolisado em pó", ("step", "colageno")),
    ("creme dental para dentes sensíveis", ("step", "higiene_oral")),
    ("condicionador reparador premium", ("step", "higiene_cabelo")),
    ("vitamina d3 com k2", ("step", "vitaminas")),
    ("sabonete líquido corporal", ("step", "higiene_corpo")),
]


def relevant_ids(cat, rule) -> set[str]:
    kind, *vals = rule
    out = set()
    for p in cat.products:
        if p["domain"] == "medicamento":
            continue
        if kind == "concern" and vals[0] in p["concerns"]:
            out.add(p["id"])
        if kind == "step" and (p["step"] in vals or any(s in vals for s in p["coversSteps"])):
            out.add(p["id"])
    return out
