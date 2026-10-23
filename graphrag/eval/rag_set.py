"""Conjunto de avaliação do RAG com DeepSeek (#33): frases que o GRAFO não entende hoje (medido em 23/10).

Cada caso de busca: (frase, regra). Regras:
  ("goal", id, ...)      o objetivo entendido é um destes
  ("concern", id, ...)   o objetivo ou algum item mostrado trata uma destas preocupações
  ("step", id, ...)      algum item mostrado é de uma destas etapas
  ("missing",)           nada do catálogo serve: nenhum kit e nenhum produto
Ajustes no meio da conversa: (busca_base, frase, regra), com regra
  ("pref", p) preferência aplicada · ("skin", s) pele aplicada · ("cheaper",) orçamento abaixo do kit em foco
  (Essencial) · ("richer",) orçamento acima do mais caro · ("excl", prefixo) ingrediente excluído que começa com prefixo
  · ("any", regra, regra...) qualquer uma.
TRAIN serve para ajustar o prompt; TEST só mede. Ressalva honesta: dois erros do TEST ("tira o que tem álcool", "nada
que arda") revelaram defeitos do validador, corrigidos em 23/10, e um ajuste no prompt; por isso existe NOVO, escrito
depois das correções e rodado uma única vez, sem ajuste nenhum depois.
"""
from __future__ import annotations

TRAIN: list[tuple] = [
    ("minha cabeça tá latejando", ("goal", "dor_de_cabeca")),
    ("meu nariz não para de escorrer", ("concern", "gripe", "nariz_entupido", "alergia")),
    ("suo muito embaixo do braço", ("step", "desodorante")),
    ("to soltando pum demais", ("concern", "gases")),
    ("caganeira desde ontem", ("concern", "diarreia")),
    ("quero parar de fumar", ("missing",)),
    ("remédio pra unha encravada", ("missing",)),
]
TRAIN_ADJUST: list[tuple] = [
    ("pele oleosa", "tira tudo que tem cheiro", ("pref", "sem fragrância")),
    ("pele oleosa", "algo mais em conta", ("cheaper",)),
    ("pele oleosa", "não quero ácido", ("excl", "acido")),
]
TEST: list[tuple] = [
    ("a cabeça vai explodir", ("goal", "dor_de_cabeca")),
    ("cabeça pesada e latejando", ("goal", "dor_de_cabeca")),
    ("nariz pingando o dia todo", ("concern", "gripe", "nariz_entupido", "alergia")),
    ("torci o pé", ("concern", "dor_muscular", "dor_no_corpo")),
    ("dei um mau jeito nas costas", ("concern", "dor_muscular", "dor_no_corpo")),
    ("quero um remédio pra calvície", ("missing",)),
]
TEST_ADJUST: list[tuple] = [
    ("pele oleosa", "tira o que tem álcool", ("pref", "sem álcool")),
    ("pele oleosa", "não quero nada de origem animal", ("pref", "vegano")),
    ("pele oleosa", "nada que arda", ("any", ("skin", "sensível"), ("pref", "sem fragrância"), ("pref", "sem álcool"))),
    ("pele oleosa", "coisa mais top", ("richer",)),
]

NOVO: list[tuple] = [
    ("nariz trancado não consigo respirar", ("concern", "nariz_entupido", "gripe", "alergia")),
    ("barriga desarranjada", ("concern", "diarreia", "dor_de_barriga")),
    ("quero algo pra ficar menos cansado", ("goal", "suplementos")),
    ("pescoço travado", ("concern", "dor_muscular", "dor_no_corpo")),
    ("remédio pra frieira", ("missing",)),
]
NOVO_ADJUST: list[tuple] = [
    ("kit de suplementos", "nada que tenha glúten", ("pref", "sem glúten")),
    ("kit de suplementos", "menos caro por favor", ("cheaper",)),
    ("kit de suplementos", "quero o mais caprichado", ("richer",)),
]
