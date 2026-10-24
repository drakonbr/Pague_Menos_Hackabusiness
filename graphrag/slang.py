"""Fala popular/chula das 13 áreas de saúde do catálogo.

Isto NÃO é a solução geral para frases desconhecidas: é um cache determinístico
para os jeitos de falar mais frequentes no balcão, que evita uma chamada de LLM
e garante resposta estável nos casos óbvios. O caso geral continua no fallback
seletivo (gate de incerteza + guardas + sugestões).

Não existe dataset público que cubra gíria e vulgaridade de farmácia em pt-BR
sem problema de licença (SemClinBr é não comercial, MedPT não declara licença,
HPO Cultural é focado em doenças raras). Esta lista é curadoria interna, curta
e revisada; cada termo aponta para uma preocupação que já existe no catálogo.
Termos fora das 13 áreas ficam de fora de propósito.
"""
from __future__ import annotations

import re

# Usos figurados de "caguei" não são diarreia: "me caguei de medo", "caguei pra isso".
FIGURATIVE = re.compile(r"\b(me\s+)?caguei\s+(de\s+(medo|rir)|pra\s+|para\s+|e\s+andei)", re.I)

SLANG: dict[str, list[str]] = {
    "diarreia": [
        "me caguei", "me caguei todo", "me caguei toda",
        "me borrei", "borrei nas calcas",
        "caguei mole", "estou cagando mole", "to cagando mole",
        "coco mole", "fezes moles", "diarreia braba", "diarreia forte",
    ],
    "prisao_de_ventre": [
        "nao consigo cagar", "nao consigo fazer coco", "preso pra cagar",
        "coco duro", "fezes duras", "dificuldade para evacuar", "nao solto nada",
    ],
    "gases": [
        "estou peidando", "peidando muito", "to peidando",
        "soltando pum", "pum demais", "peidos",
    ],
    "enjoo": [
        "estomago embrulhado", "vontade de vomitar", "barriga embrulhada",
    ],
    "dor_de_garganta": [
        "garganta arranhando", "garganta raspando", "dor ao engolir",
    ],
    "tosse": [
        "tosse de cachorro", "tosse do cachorro", "tosse canina",
        "tosse com secrecao", "tosse grossa",
    ],
    "alergia": [
        "coceira nos olhos", "olhos cocando", "olho cocando",
    ],
    "dor_muscular": [
        "torci o pe", "torcao", "entorse", "mau jeito", "dei um mau jeito",
        "puxei um musculo",
    ],
    "nariz_entupido": [
        "nariz nao para de escorrer", "nariz vive escorrendo", "nariz fica escorrendo",
    ],
    "oleosidade": [
        "pele que vive melada", "pele melada", "rosto melado",
    ],
    "nutricao": [
        "menos cansado", "menos cansada", "mais disposicao", "sem energia",
    ],
}
