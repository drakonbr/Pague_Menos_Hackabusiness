#!/usr/bin/env python3
"""
Gerador do catálogo SINTÉTICO (fictício) de produtos.

- Determinístico: mesma saída a cada execução (seed fixa, data fixa).
- Nada aqui vem de dados reais da empresa. Marcas, nomes, preços e estoque são inventados.
- Escopo principal: skin care, tratamento cosmético e proteção solar (100 primeiros produtos).
- Ampliação da persona (persona_products.py): suplementos, higiene premium e 8 apresentações de 2
  medicamentos FICTÍCIOS (princípios ativos inventados), usados só para reposição, nunca em kits.
- Saídas em catalog/data/: products.json, inventory.json, ingredients.json,
  interactions.json, goals.json, warnings.json, catalog.sqlite

Separação de fontes de verdade (espelha uma integração real):
  products.json   = cadastro (vem do PIM/catálogo)
  inventory.json  = preço e estoque (vêm do ERP/estoque; mudam com frequência)
"""
from __future__ import annotations

import json
import random
import sqlite3
from pathlib import Path

import medicines as MED
import persona_products as PP
import hygiene_products as HG

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
SEED = 42
UPDATED_AT = "2026-10-15T00:00:00-03:00"

# --------------------------------------------------------------------------
# Vocabulários controlados
# --------------------------------------------------------------------------
STEPS = {
    "limpeza": "Limpeza",
    "preparo": "Tônico, esfoliante ou máscara",
    "tratamento": "Tratamento",
    "hidratacao": "Hidratação",
    "protecao_solar": "Proteção solar facial",
    "protecao_corporal": "Proteção solar corporal",
    "complemento": "Complemento (olhos e lábios)",
}

SKIN = {
    "O": "oleosa",
    "M": "mista",
    "S": "seca",
    "N": "normal",
    "Z": "sensível",
    "T": "todas",
}

CONCERNS = {
    "acne": "acne",
    "oleosidade": "oleosidade",
    "poros": "poros",
    "manchas": "manchas",
    "ressecamento": "ressecamento",
    "sinais_idade": "sinais de idade",
    "sensibilidade": "sensibilidade",
    "fotoprotecao": "proteção solar",
    "olheiras": "olheiras",
    "textura": "textura irregular",
    "limpeza_diaria": "limpeza diária",
    "desmaquilagem": "remoção de make e protetor",
}

# --------------------------------------------------------------------------
# Ingredientes, interações, avisos
# --------------------------------------------------------------------------
INGREDIENTS = [
    # id, nome, família, função, fotossensibilizante
    ("niacinamida", "Niacinamida", "vitamina", "controle de oleosidade, uniformização", False),
    ("acido_salicilico", "Ácido salicílico", "BHA", "esfoliação dentro dos poros", False),
    ("zinco_pca", "Zinco PCA", "mineral", "regulação de oleosidade", False),
    ("acido_azelaico", "Ácido azelaico", "ácido dicarboxílico", "uniformização e controle de acne", False),
    ("acido_hialuronico", "Ácido hialurônico", "umectante", "hidratação", False),
    ("ceramidas", "Ceramidas", "lipídio", "reforço da barreira da pele", False),
    ("pantenol", "Pantenol", "provitamina", "hidratação e conforto", False),
    ("vitamina_c", "Vitamina C", "antioxidante", "antioxidante, uniformização", False),
    ("vitamina_e", "Vitamina E", "antioxidante", "antioxidante", False),
    ("acido_tranexamico", "Ácido tranexâmico", "ativo clareador cosmético", "uniformização de manchas", False),
    ("retinol", "Retinol", "retinoide cosmético", "renovação e sinais de idade", True),
    ("bakuchiol", "Bakuchiol", "ativo vegetal", "alternativa ao retinol", False),
    ("acido_glicolico", "Ácido glicólico", "AHA", "esfoliação superficial", True),
    ("acido_mandelico", "Ácido mandélico", "AHA", "esfoliação suave", True),
    ("argila", "Argila", "mineral", "absorção de oleosidade", False),
    ("cha_verde", "Extrato de chá verde", "extrato vegetal", "calmante e antioxidante", False),
    ("centella_asiatica", "Centella asiática", "extrato vegetal", "calmante", False),
    ("alantoina", "Alantoína", "calmante", "conforto da pele", False),
    ("glicerina", "Glicerina", "umectante", "hidratação", False),
    ("tensoativo_suave", "Tensoativo suave", "limpeza", "limpeza suave", False),
    ("filtro_uv", "Filtros UVA/UVB", "filtro químico", "proteção solar", False),
    ("oxido_de_zinco", "Óxido de zinco", "filtro mineral", "proteção solar mineral", False),
    ("dioxido_titanio", "Dióxido de titânio", "filtro mineral", "proteção solar mineral", False),
    ("peptideos", "Peptídeos", "peptídeo", "firmeza e sinais de idade", False),
    ("cafeina", "Cafeína", "estimulante", "olheiras e inchaço", False),
    ("enxofre", "Enxofre", "mineral", "controle de oleosidade e acne", False),
    ("hidrocoloide", "Hidrocoloide", "curativo cosmético", "proteção da espinha", False),
    ("aloe_vera", "Aloe vera", "extrato vegetal", "hidratação leve", False),
    ("manteiga_karite", "Manteiga de karité", "emoliente", "nutrição", False),
]

# severity: "evitar" = nunca no mesmo kit; "separar" = só se um for de dia e outro de noite.
# Regra vale entre produtos que ficam na pele (não se aplica a limpeza, que é enxaguada).
INTERACTIONS = [
    ("retinol", "acido_glicolico", "evitar", "Esfoliante forte junto com retinol aumenta o risco de irritação."),
    ("retinol", "acido_mandelico", "evitar", "Esfoliante junto com retinol aumenta o risco de irritação."),
    ("retinol", "acido_salicilico", "evitar", "Ácido esfoliante junto com retinol aumenta o risco de irritação."),
    ("acido_glicolico", "acido_mandelico", "evitar", "Dois ácidos esfoliantes no mesmo kit é excesso de esfoliação."),
    ("acido_glicolico", "acido_salicilico", "evitar", "Dois ácidos esfoliantes no mesmo kit é excesso de esfoliação."),
    ("acido_mandelico", "acido_salicilico", "evitar", "Dois ácidos esfoliantes no mesmo kit é excesso de esfoliação."),
    ("retinol", "vitamina_c", "separar", "Usar vitamina C de dia e retinol à noite."),
    ("acido_glicolico", "vitamina_c", "separar", "Usar vitamina C de dia e o ácido à noite."),
    ("retinol", "acido_azelaico", "separar", "Usar em períodos diferentes para reduzir irritação."),
]

WARNINGS = {
    "fotossensibilizante": "Pode aumentar a sensibilidade ao sol. Use protetor solar durante o dia.",
    "consultar_se_gestante": "Contém ativo com restrição de uso na gestação e na amamentação.",
    "evitar_contato_olhos": "Evite o contato com os olhos.",
    "nao_usar_pele_irritada": "Não aplicar sobre pele machucada ou irritada.",
    "teste_de_sensibilidade": "Faça um teste em área pequena antes do primeiro uso.",
}

# --------------------------------------------------------------------------
# Objetivos (intenções) e etapas da rotina
# required: etapas que o kit precisa cobrir. optional: etapas que entram se o orçamento permitir.
# --------------------------------------------------------------------------
GOALS = [
    {
        "id": "acne",
        "label": "Controle de acne",
        "concerns": ["acne", "oleosidade", "poros"],
        "required_steps": ["limpeza", "tratamento", "hidratacao"],
        "optional_steps": ["protecao_solar", "preparo"],
        "synonyms": ["acne", "espinha", "espinhas", "cravo", "cravos", "pele acneica"],
    },
    {
        "id": "manchas",
        "label": "Uniformizar manchas",
        "concerns": ["manchas"],
        "required_steps": ["limpeza", "tratamento", "protecao_solar"],
        "optional_steps": ["hidratacao"],
        "synonyms": ["mancha", "manchas", "uniformizar", "clarear", "tom da pele", "pós-acne"],
    },
    {
        "id": "skincare_basico",
        "label": "Rotina básica de skin care",
        "concerns": ["limpeza_diaria", "ressecamento"],
        "required_steps": ["limpeza", "hidratacao", "protecao_solar"],
        "optional_steps": ["complemento"],
        "synonyms": ["skin care", "skincare", "cuidar da pele", "cuidado com a pele", "rotina", "começar a cuidar"],
    },
    {
        "id": "protecao_solar",
        "label": "Proteção solar",
        "concerns": ["fotoprotecao"],
        "required_steps": ["protecao_solar", "protecao_corporal"],
        "optional_steps": ["complemento"],
        "synonyms": ["protetor", "protetor solar", "filtro solar", "fps", "sol", "praia"],
    },
    {
        "id": "anti_idade",
        "label": "Cuidado antissinais",
        "concerns": ["sinais_idade", "olheiras"],
        "required_steps": ["limpeza", "tratamento", "hidratacao", "protecao_solar"],
        "optional_steps": ["complemento"],
        "synonyms": ["anti-idade", "antiidade", "antissinais", "rugas", "linhas de expressão", "envelhecimento"],
    },
    {
        "id": "pele_sensivel",
        "label": "Cuidado para pele sensível",
        "concerns": ["sensibilidade"],
        "required_steps": ["limpeza", "hidratacao", "protecao_solar"],
        "optional_steps": ["tratamento"],
        "synonyms": ["pele sensível", "sensível", "irritada", "reativa"],
    },
    {
        "id": "oleosidade",
        "label": "Controle de oleosidade",
        "concerns": ["oleosidade", "poros"],
        "required_steps": ["limpeza", "hidratacao", "protecao_solar"],
        "optional_steps": ["tratamento", "preparo"],
        "synonyms": ["oleosa", "oleosidade", "brilho", "pele oleosa"],
    },
]

# Ampliação para a persona (catalog/persona_products.py): vocabulários novos entram junto dos antigos.
STEPS.update(PP.EXTRA_STEPS)
CONCERNS.update(PP.EXTRA_CONCERNS)
INGREDIENTS.extend(PP.EXTRA_INGREDIENTS)
INGREDIENTS.extend(HG.HYGIENE_INGREDIENTS)
WARNINGS.update(PP.EXTRA_WARNINGS)
GOALS.extend(PP.EXTRA_GOALS)

# Medicamentos para busca e kits (catalog/medicines.py, doc 16).
STEPS.update(MED.MED_STEPS)
CONCERNS.update(MED.MED_CONCERNS)
INGREDIENTS.extend(MED.MED_INGREDIENTS)
INTERACTIONS.extend(MED.MED_INTERACTIONS)
WARNINGS.update(MED.MED_WARNINGS)
GOALS.extend(MED.MED_GOALS)

# --------------------------------------------------------------------------
# Produtos
# (marca, nome, tipo, etapa, linha, forma, tamanho, peles, preocupações, ingredientes,
#  fps, período, preço_reais, claims, avisos, cobre_etapas_extra)
# --------------------------------------------------------------------------
OF = "oil free"
NC = "não comedogênico"
SF = "sem fragrância"
VG = "vegano"
SA = "sem álcool"
MIN = "filtro mineral"
COR = "com cor"
TS = "toque seco"
AP = "resistente à água"
FOT = "fotossensibilizante"
GES = "consultar_se_gestante"
IRR = "nao_usar_pele_irritada"
OLH = "evitar_contato_olhos"
TST = "teste_de_sensibilidade"

P = []  # lista de tuplas


def add(*args):
    P.append(args)


# ---- LIMPEZA (14) ----
L, LN = "limpeza", "limpeza"
add("Clara Pele", "Gel de Limpeza Purificante", "gel de limpeza", L, LN, "tube", "150 ml", "OM", ["acne", "oleosidade", "poros"], ["acido_salicilico", "zinco_pca"], None, "dia_noite", 24.90, [OF, NC], [], [])
add("Clara Pele", "Sabonete Líquido Facial Oil Control", "sabonete líquido facial", L, LN, "bottle", "200 ml", "O", ["oleosidade", "poros"], ["zinco_pca", "cha_verde"], None, "dia_noite", 19.90, [OF, NC], [], [])
add("Pura Base", "Gel de Limpeza Facial Diário", "gel de limpeza", L, LN, "tube", "120 ml", "T", ["limpeza_diaria"], ["tensoativo_suave", "glicerina"], None, "dia_noite", 14.90, [SF], [], [])
add("Pura Base", "Água Micelar 5 em 1", "água micelar", L, LN, "bottle", "200 ml", "T", ["desmaquilagem", "limpeza_diaria"], ["glicerina"], None, "dia_noite", 17.90, [SF], [], [])
add("Bem Simples", "Espuma de Limpeza Facial", "espuma de limpeza", L, LN, "pump", "150 ml", "NM", ["limpeza_diaria"], ["tensoativo_suave", "pantenol"], None, "dia_noite", 16.90, [], [], [])
add("Aurora Dermo", "Gel de Limpeza Suave Pele Sensível", "gel de limpeza", L, LN, "tube", "200 ml", "Z", ["sensibilidade", "limpeza_diaria"], ["centella_asiatica", "alantoina"], None, "dia_noite", 54.90, [SF, NC], [], [])
add("Aurora Dermo", "Gel de Limpeza Anti-Acne", "gel de limpeza", L, LN, "tube", "150 ml", "O", ["acne", "oleosidade"], ["acido_salicilico", "niacinamida"], None, "dia_noite", 62.90, [OF, NC], [], [])
add("Vita Verde", "Sabonete Facial Chá Verde", "sabonete líquido facial", L, LN, "bottle", "150 ml", "OM", ["oleosidade", "limpeza_diaria"], ["cha_verde", "glicerina"], None, "dia_noite", 29.90, [VG], [], [])
add("Vita Verde", "Óleo de Limpeza Demaquilante", "óleo de limpeza", L, LN, "bottle", "100 ml", "SN", ["desmaquilagem", "ressecamento"], ["vitamina_e"], None, "noite", 44.90, [VG], [OLH], [])
add("Lume Lab", "Gel de Limpeza Niacinamida", "gel de limpeza", L, LN, "tube", "150 ml", "OM", ["oleosidade", "poros"], ["niacinamida"], None, "dia_noite", 39.90, [OF, NC], [], [])
add("Lume Lab", "Leite de Limpeza Hidratante", "leite de limpeza", L, LN, "bottle", "200 ml", "SZ", ["ressecamento", "sensibilidade"], ["ceramidas", "glicerina"], None, "dia_noite", 42.90, [SF], [], [])
add("Solare", "Gel de Limpeza Pós-Sol", "gel de limpeza", L, LN, "tube", "150 ml", "T", ["desmaquilagem", "limpeza_diaria"], ["aloe_vera", "tensoativo_suave"], None, "dia_noite", 31.90, [SA], [], [])
add("Pura Base", "Sabonete Facial Antiacne em Barra", "sabonete facial em barra", L, LN, "bar", "80 g", "O", ["acne", "oleosidade"], ["enxofre"], None, "dia_noite", 13.90, [], [], [])
add("Bem Simples", "Água Micelar Pele Oleosa", "água micelar", L, LN, "bottle", "200 ml", "O", ["oleosidade", "desmaquilagem"], ["zinco_pca", "glicerina"], None, "dia_noite", 21.90, [OF], [], [])

# ---- PREPARO: tônicos, esfoliantes, máscaras (8) ----
PR = "preparo"
add("Lume Lab", "Tônico Renovador Mandélico", "tônico esfoliante", PR, "preparo", "bottle", "120 ml", "MN", ["manchas", "textura"], ["acido_mandelico"], None, "noite", 59.90, [], [FOT, IRR], [])
add("Clara Pele", "Tônico Adstringente Sem Álcool", "tônico facial", PR, "preparo", "bottle", "200 ml", "O", ["poros", "oleosidade"], ["cha_verde", "zinco_pca"], None, "dia_noite", 22.90, [SA, OF], [], [])
add("Pura Base", "Tônico Facial Calmante", "tônico facial", PR, "preparo", "bottle", "200 ml", "TZ", ["sensibilidade"], ["centella_asiatica", "glicerina"], None, "dia_noite", 19.90, [SA, SF], [], [])
add("Aurora Dermo", "Solução Esfoliante Salicílica", "esfoliante químico", PR, "preparo", "bottle", "100 ml", "O", ["acne", "textura", "poros"], ["acido_salicilico"], None, "noite", 79.90, [OF], [IRR, TST], [])
add("Aurora Dermo", "Tônico Glicólico Noturno", "tônico esfoliante", PR, "preparo", "bottle", "100 ml", "MN", ["textura", "manchas"], ["acido_glicolico"], None, "noite", 89.90, [], [FOT, IRR, TST], [])
add("Vita Verde", "Tônico de Rosas Hidratante", "tônico facial", PR, "preparo", "bottle", "150 ml", "SN", ["ressecamento"], ["glicerina", "acido_hialuronico"], None, "dia_noite", 34.90, [VG, SA], [], [])
add("Bem Simples", "Esfoliante Facial Suave", "esfoliante físico", PR, "preparo", "tube", "100 g", "OM", ["textura"], ["argila"], None, "noite", 18.90, [], [IRR], [])
add("Lume Lab", "Máscara de Argila Purificante", "máscara de argila", PR, "preparo", "jar", "60 g", "O", ["oleosidade", "poros"], ["argila", "zinco_pca"], None, "noite", 36.90, [OF], [], [])

# ---- TRATAMENTO ACNE (14) ----
TR = "tratamento"
add("Clara Pele", "Gel Secativo Antiacne", "gel secativo", TR, "tratamento_acne", "tube", "15 g", "O", ["acne"], ["acido_salicilico", "enxofre"], None, "dia_noite", 21.90, [OF], [IRR], [])
add("Clara Pele", "Sérum Niacinamida + Zinco", "sérum", TR, "tratamento_acne", "dropper", "30 ml", "OM", ["acne", "oleosidade", "poros"], ["niacinamida", "zinco_pca"], None, "dia_noite", 39.90, [OF, NC], [], [])
add("Clara Pele", "Adesivos Hidrocoloide Anti-Espinha (24 un)", "adesivo hidrocoloide", TR, "tratamento_acne", "patch", "24 un", "T", ["acne"], ["hidrocoloide"], None, "noite", 22.90, [SF], [], [])
add("Pura Base", "Loção Secativa Pontual", "loção secativa", TR, "tratamento_acne", "bottle", "20 ml", "O", ["acne"], ["enxofre", "acido_salicilico"], None, "noite", 14.90, [], [IRR], [])
add("Pura Base", "Sérum Niacinamida 5%", "sérum", TR, "tratamento_acne", "dropper", "30 ml", "OM", ["oleosidade", "poros", "manchas"], ["niacinamida"], None, "dia_noite", 29.90, [OF], [], [])
add("Bem Simples", "Gel Antiacne Diário", "gel secativo", TR, "tratamento_acne", "tube", "30 g", "O", ["acne", "oleosidade"], ["acido_salicilico"], None, "dia_noite", 18.90, [OF], [IRR], [])
add("Aurora Dermo", "Sérum Ácido Azelaico Controle de Acne", "sérum", TR, "tratamento_acne", "dropper", "30 ml", "OMZ", ["acne", "manchas"], ["acido_azelaico", "niacinamida"], None, "dia_noite", 94.90, [NC], [TST], [])
add("Aurora Dermo", "Gel-Creme Regulador Anti-Acne", "gel-creme de tratamento", TR, "tratamento_acne", "tube", "40 g", "O", ["acne", "oleosidade"], ["acido_salicilico", "niacinamida", "zinco_pca"], None, "dia_noite", 79.90, [OF, NC], [IRR], [])
add("Lume Lab", "Sérum Salicílico + Niacinamida", "sérum", TR, "tratamento_acne", "dropper", "30 ml", "O", ["acne", "poros"], ["acido_salicilico", "niacinamida"], None, "dia_noite", 59.90, [OF], [IRR, TST], [])
add("Lume Lab", "Sérum Pós-Acne Uniformizador", "sérum", TR, "tratamento_acne", "dropper", "30 ml", "OM", ["acne", "manchas"], ["acido_azelaico", "acido_tranexamico"], None, "noite", 84.90, [NC], [TST], [])
add("Vita Verde", "Sérum Chá Verde Calmante Anti-Acne", "sérum", TR, "tratamento_acne", "dropper", "30 ml", "OZ", ["acne", "sensibilidade"], ["cha_verde", "centella_asiatica", "zinco_pca"], None, "dia_noite", 44.90, [VG, NC], [], [])
add("Vita Verde", "Gel de Centella Pós-Espinha", "gel calmante", TR, "tratamento_acne", "tube", "30 g", "Z", ["acne", "sensibilidade"], ["centella_asiatica", "pantenol"], None, "dia_noite", 38.90, [VG, SF], [], [])
add("Solare", "Sérum Oil Control Matificante", "sérum", TR, "tratamento_acne", "dropper", "30 ml", "O", ["oleosidade", "poros"], ["niacinamida", "zinco_pca"], None, "dia", 49.90, [OF, NC], [], [])
add("Aurora Dermo", "Sérum Anti-Cravos Salicílico", "sérum", TR, "tratamento_acne", "dropper", "30 ml", "O", ["poros", "acne"], ["acido_salicilico"], None, "noite", 69.90, [OF], [IRR, TST], [])

# ---- TRATAMENTO MANCHAS (10) ----
add("Pura Base", "Sérum Vitamina C 10%", "sérum", TR, "tratamento_manchas", "dropper", "30 ml", "T", ["manchas"], ["vitamina_c"], None, "dia", 34.90, [], [TST], [])
add("Pura Base", "Sérum Clareador Ácido Tranexâmico", "sérum", TR, "tratamento_manchas", "dropper", "30 ml", "NM", ["manchas"], ["acido_tranexamico", "niacinamida"], None, "dia_noite", 39.90, [], [], [])
add("Bem Simples", "Gel Uniformizador Niacinamida", "gel de tratamento", TR, "tratamento_manchas", "tube", "30 g", "T", ["manchas"], ["niacinamida"], None, "dia_noite", 24.90, [OF], [], [])
add("Lume Lab", "Sérum Vitamina C 15% Antioxidante", "sérum", TR, "tratamento_manchas", "dropper", "30 ml", "NM", ["manchas", "sinais_idade"], ["vitamina_c", "vitamina_e"], None, "dia", 69.90, [], [TST], [])
add("Lume Lab", "Sérum Tranexâmico + Niacinamida", "sérum", TR, "tratamento_manchas", "dropper", "30 ml", "T", ["manchas"], ["acido_tranexamico", "niacinamida"], None, "dia_noite", 74.90, [NC], [], [])
add("Aurora Dermo", "Sérum Despigmentante Noturno", "sérum", TR, "tratamento_manchas", "dropper", "30 ml", "T", ["manchas"], ["acido_azelaico", "acido_tranexamico"], None, "noite", 109.90, [NC], [TST], [])
add("Aurora Dermo", "Sérum Vitamina C Estabilizada 20%", "sérum", TR, "tratamento_manchas", "dropper", "30 ml", "NS", ["manchas", "sinais_idade"], ["vitamina_c", "vitamina_e"], None, "dia", 129.90, [], [TST], [])
add("Vita Verde", "Sérum Iluminador Vitamina C Natural", "sérum", TR, "tratamento_manchas", "dropper", "30 ml", "T", ["manchas"], ["vitamina_c", "vitamina_e"], None, "dia", 52.90, [VG], [TST], [])
add("Vita Verde", "Creme Uniformizador Noturno", "creme de tratamento", TR, "tratamento_manchas", "jar", "40 g", "NS", ["manchas"], ["niacinamida", "acido_tranexamico"], None, "noite", 58.90, [VG], [], [])
add("Solare", "Sérum Antimanchas Dia", "sérum", TR, "tratamento_manchas", "dropper", "30 ml", "T", ["manchas"], ["vitamina_c", "niacinamida"], None, "dia", 59.90, [NC], [], [])

# ---- TRATAMENTO ANTI-IDADE (10) ----
add("Pura Base", "Creme Antissinais com Peptídeos", "creme antissinais", TR, "anti_idade", "jar", "50 g", "NS", ["sinais_idade"], ["peptideos", "glicerina"], None, "dia_noite", 32.90, [], [], [])
add("Bem Simples", "Sérum Retinol 0,2% Iniciante", "sérum de retinol", TR, "anti_idade", "dropper", "30 ml", "NM", ["sinais_idade", "textura"], ["retinol"], None, "noite", 39.90, [], [FOT, GES, TST], [])
add("Lume Lab", "Sérum Retinol 0,5%", "sérum de retinol", TR, "anti_idade", "dropper", "30 ml", "NM", ["sinais_idade", "textura"], ["retinol", "vitamina_e"], None, "noite", 79.90, [], [FOT, GES, TST], [])
add("Lume Lab", "Sérum Bakuchiol Alternativo ao Retinol", "sérum", TR, "anti_idade", "dropper", "30 ml", "TZ", ["sinais_idade"], ["bakuchiol", "vitamina_e"], None, "dia_noite", 89.90, [VG, NC], [], [])
add("Aurora Dermo", "Creme Retinol + Ceramidas Noturno", "creme de retinol", TR, "anti_idade", "jar", "40 g", "NS", ["sinais_idade", "ressecamento"], ["retinol", "ceramidas"], None, "noite", 139.90, [], [FOT, GES, TST], [])
add("Aurora Dermo", "Sérum Peptídeos Firmador", "sérum", TR, "anti_idade", "dropper", "30 ml", "NSM", ["sinais_idade"], ["peptideos", "acido_hialuronico"], None, "dia_noite", 119.90, [NC], [], [])
add("Vita Verde", "Óleo Facial Antissinais", "óleo facial", TR, "anti_idade", "dropper", "30 ml", "S", ["sinais_idade", "ressecamento"], ["vitamina_e", "bakuchiol"], None, "noite", 64.90, [VG], [], [])
add("Vita Verde", "Creme Noturno Regenerador", "creme noturno", TR, "anti_idade", "jar", "50 g", "SN", ["sinais_idade", "ressecamento"], ["ceramidas", "peptideos"], None, "noite", 59.90, [VG], [], [])
add("Clara Pele", "Sérum Retinol Oil-Free", "sérum de retinol", TR, "anti_idade", "dropper", "30 ml", "OM", ["sinais_idade", "textura"], ["retinol", "niacinamida"], None, "noite", 54.90, [OF], [FOT, GES, TST], [])
add("Solare", "Sérum Antioxidante Dia", "sérum", TR, "anti_idade", "dropper", "30 ml", "T", ["sinais_idade", "manchas"], ["vitamina_c", "vitamina_e"], None, "dia", 74.90, [], [TST], [])

# ---- HIDRATAÇÃO (16) — as três últimas têm FPS e cobrem também a proteção solar ----
H = "hidratacao"
add("Pura Base", "Gel Hidratante Oil-Free", "gel hidratante", H, "hidratacao", "jar", "50 g", "OM", ["oleosidade", "poros"], ["glicerina", "acido_hialuronico"], None, "dia_noite", 17.90, [OF, NC], [], [])
add("Pura Base", "Creme Hidratante Facial Nutritivo", "creme hidratante", H, "hidratacao", "jar", "50 g", "SN", ["ressecamento"], ["glicerina", "pantenol"], None, "dia_noite", 19.90, [], [], [])
add("Bem Simples", "Hidratante Facial Dia e Noite", "creme hidratante", H, "hidratacao", "jar", "50 g", "T", ["ressecamento"], ["glicerina"], None, "dia_noite", 15.90, [], [], [])
add("Bem Simples", "Gel Hidratante Pele Oleosa", "gel hidratante", H, "hidratacao", "jar", "50 g", "O", ["oleosidade"], ["glicerina", "aloe_vera"], None, "dia_noite", 16.90, [OF], [], [])
add("Clara Pele", "Gel-Creme Oil-Free Anti-Brilho", "gel-creme hidratante", H, "hidratacao", "jar", "50 g", "O", ["oleosidade", "acne"], ["niacinamida", "zinco_pca", "acido_hialuronico"], None, "dia_noite", 32.90, [OF, NC], [], [])
add("Clara Pele", "Hidratante Matificante Pós-Tratamento", "hidratante matificante", H, "hidratacao", "tube", "50 g", "OM", ["acne", "oleosidade"], ["niacinamida", "pantenol"], None, "dia_noite", 38.90, [OF, NC], [], [])
add("Lume Lab", "Gel Hidratante Ácido Hialurônico", "gel hidratante", H, "hidratacao", "jar", "50 g", "T", ["ressecamento"], ["acido_hialuronico", "pantenol"], None, "dia_noite", 44.90, [SF], [], [])
add("Lume Lab", "Creme Barreira Ceramidas", "creme hidratante", H, "hidratacao", "jar", "50 g", "SZ", ["ressecamento", "sensibilidade"], ["ceramidas", "pantenol"], None, "dia_noite", 56.90, [SF, NC], [], [])
add("Aurora Dermo", "Hidratante Facial Calmante Pele Sensível", "creme hidratante", H, "hidratacao", "tube", "50 g", "Z", ["sensibilidade", "ressecamento"], ["centella_asiatica", "ceramidas", "alantoina"], None, "dia_noite", 74.90, [SF, NC], [], [])
add("Aurora Dermo", "Gel-Creme Oil-Free Dermatológico", "gel-creme hidratante", H, "hidratacao", "tube", "50 g", "OM", ["oleosidade", "acne"], ["niacinamida", "acido_hialuronico", "ceramidas"], None, "dia_noite", 69.90, [OF, NC, SF], [], [])
add("Aurora Dermo", "Creme Hidratante Rico Pele Seca", "creme hidratante", H, "hidratacao", "jar", "50 g", "S", ["ressecamento"], ["ceramidas", "manteiga_karite", "glicerina"], None, "dia_noite", 84.90, [SF], [], [])
add("Vita Verde", "Gel Hidratante Aloe e Chá Verde", "gel hidratante", H, "hidratacao", "jar", "50 g", "OMN", ["oleosidade", "ressecamento"], ["aloe_vera", "cha_verde", "glicerina"], None, "dia_noite", 27.90, [VG, OF], [], [])
add("Vita Verde", "Creme Hidratante Vegano Karité", "creme hidratante", H, "hidratacao", "jar", "50 g", "SN", ["ressecamento"], ["manteiga_karite", "glicerina"], None, "dia_noite", 36.90, [VG], [], [])
add("Solare", "Hidratante Facial FPS 30 Toque Seco", "hidratante com FPS", H, "hidratacao", "tube", "50 g", "OM", ["fotoprotecao", "oleosidade"], ["filtro_uv", "niacinamida"], 30, "dia", 59.90, [OF, TS], [], ["protecao_solar"])
add("Solare", "Creme Hidratante Antissinais FPS 50", "hidratante com FPS", H, "hidratacao", "jar", "50 g", "NS", ["fotoprotecao", "sinais_idade"], ["filtro_uv", "peptideos", "vitamina_e"], 50, "dia", 79.90, [], [], ["protecao_solar"])
add("Pura Base", "Hidratante Facial FPS 30", "hidratante com FPS", H, "hidratacao", "tube", "50 g", "T", ["fotoprotecao", "ressecamento"], ["filtro_uv", "glicerina"], 30, "dia", 29.90, [], [], ["protecao_solar"])

# ---- PROTEÇÃO SOLAR FACIAL (16) ----
S = "protecao_solar"
add("Pura Base", "Protetor Solar Facial FPS 50 Toque Seco", "protetor solar facial", S, "protetor_solar", "tube", "50 g", "OM", ["fotoprotecao", "oleosidade"], ["filtro_uv"], 50, "dia", 24.90, [OF, TS], [], [])
add("Pura Base", "Protetor Solar Facial FPS 30", "protetor solar facial", S, "protetor_solar", "tube", "50 g", "T", ["fotoprotecao"], ["filtro_uv"], 30, "dia", 19.90, [], [], [])
add("Bem Simples", "Protetor Solar Facial FPS 60 Oil-Free", "protetor solar facial", S, "protetor_solar", "tube", "50 g", "O", ["fotoprotecao", "oleosidade"], ["filtro_uv"], 60, "dia", 27.90, [OF, NC], [], [])
add("Bem Simples", "Protetor Solar Facial FPS 50 Gel", "protetor solar facial", S, "protetor_solar", "tube", "40 g", "O", ["fotoprotecao", "oleosidade"], ["filtro_uv", "aloe_vera"], 50, "dia", 22.90, [OF], [], [])
add("Clara Pele", "Protetor Solar Facial Anti-Acne FPS 50", "protetor solar facial", S, "protetor_solar", "tube", "50 g", "O", ["fotoprotecao", "acne", "oleosidade"], ["filtro_uv", "niacinamida"], 50, "dia", 36.90, [OF, NC, TS], [], [])
add("Clara Pele", "Protetor Solar FPS 70 Oil Control com Cor", "protetor solar facial", S, "protetor_solar", "tube", "40 g", "O", ["fotoprotecao", "oleosidade"], ["filtro_uv", "zinco_pca"], 70, "dia", 42.90, [OF, COR], [], [])
add("Solare", "Protetor Solar Facial FPS 60 Fluido Ultraleve", "protetor solar facial", S, "protetor_solar", "tube", "50 g", "T", ["fotoprotecao"], ["filtro_uv"], 60, "dia", 39.90, [NC], [], [])
add("Solare", "Protetor Solar Facial FPS 50 Toque Seco", "protetor solar facial", S, "protetor_solar", "tube", "50 g", "NM", ["fotoprotecao", "oleosidade"], ["filtro_uv"], 50, "dia", 44.90, [TS], [], [])
add("Solare", "Protetor Solar Facial FPS 70 Sensitive", "protetor solar facial", S, "protetor_solar", "tube", "50 g", "Z", ["fotoprotecao", "sensibilidade"], ["oxido_de_zinco", "dioxido_titanio"], 70, "dia", 59.90, [MIN, SF], [], [])
add("Solare", "Protetor Solar Facial FPS 50 com Cor", "protetor solar facial", S, "protetor_solar", "tube", "40 g", "T", ["fotoprotecao"], ["filtro_uv"], 50, "dia", 54.90, [COR], [], [])
add("Lume Lab", "Protetor Solar FPS 50 Antioxidante", "protetor solar facial", S, "protetor_solar", "tube", "50 g", "T", ["fotoprotecao", "manchas"], ["filtro_uv", "vitamina_e", "niacinamida"], 50, "dia", 69.90, [], [], [])
add("Aurora Dermo", "Protetor Solar Facial FPS 60 Dermatológico Toque Seco", "protetor solar facial", S, "protetor_solar", "tube", "50 g", "OM", ["fotoprotecao", "oleosidade"], ["filtro_uv", "niacinamida"], 60, "dia", 89.90, [OF, NC, TS], [], [])
add("Aurora Dermo", "Protetor Solar Mineral FPS 50 Pele Sensível", "protetor solar facial", S, "protetor_solar", "tube", "50 g", "Z", ["fotoprotecao", "sensibilidade"], ["oxido_de_zinco", "dioxido_titanio"], 50, "dia", 94.90, [MIN, SF], [], [])
add("Aurora Dermo", "Protetor Solar Antimanchas FPS 70 com Cor", "protetor solar facial", S, "protetor_solar", "tube", "40 g", "T", ["fotoprotecao", "manchas"], ["filtro_uv", "acido_tranexamico"], 70, "dia", 119.90, [COR], [], [])
add("Vita Verde", "Protetor Solar Facial FPS 50 Vegano", "protetor solar facial", S, "protetor_solar", "tube", "50 g", "NS", ["fotoprotecao"], ["filtro_uv", "vitamina_e"], 50, "dia", 46.90, [VG], [], [])
add("Vita Verde", "Protetor Solar Mineral Hidratante FPS 30", "protetor solar facial", S, "protetor_solar", "tube", "50 g", "SZ", ["fotoprotecao", "ressecamento"], ["oxido_de_zinco", "glicerina"], 30, "dia", 49.90, [VG, MIN], [], [])

# ---- PROTEÇÃO SOLAR CORPORAL (6) ----
C = "protecao_corporal"
add("Pura Base", "Protetor Solar Corporal FPS 30", "protetor solar corporal", C, "protetor_solar", "bottle", "200 ml", "T", ["fotoprotecao"], ["filtro_uv"], 30, "dia", 34.90, [], [], [])
add("Pura Base", "Protetor Solar Corporal FPS 50 Resistente à Água", "protetor solar corporal", C, "protetor_solar", "bottle", "200 ml", "T", ["fotoprotecao"], ["filtro_uv"], 50, "dia", 44.90, [AP], [], [])
add("Bem Simples", "Protetor Solar Corporal FPS 30 Econômico", "protetor solar corporal", C, "protetor_solar", "bottle", "200 ml", "T", ["fotoprotecao"], ["filtro_uv"], 30, "dia", 29.90, [], [], [])
add("Solare", "Protetor Solar Corporal FPS 50 Spray", "protetor solar corporal", C, "protetor_solar", "spray", "200 ml", "T", ["fotoprotecao"], ["filtro_uv"], 50, "dia", 59.90, [AP], [], [])
add("Solare", "Protetor Solar Corporal FPS 70 Toque Seco", "protetor solar corporal", C, "protetor_solar", "bottle", "200 ml", "T", ["fotoprotecao"], ["filtro_uv"], 70, "dia", 69.90, [TS, AP], [], [])
add("Vita Verde", "Protetor Solar Corporal FPS 50 Vegano", "protetor solar corporal", C, "protetor_solar", "bottle", "200 ml", "T", ["fotoprotecao"], ["filtro_uv", "aloe_vera"], 50, "dia", 52.90, [VG], [], [])

# ---- COMPLEMENTO: lábios e olhos (6) ----
K = "complemento"
add("Pura Base", "Protetor Labial FPS 30", "protetor labial", K, "protetor_solar", "stick", "4 g", "T", ["fotoprotecao", "ressecamento"], ["filtro_uv"], 30, "dia", 12.90, [], [], [])
add("Solare", "Protetor Labial FPS 50", "protetor labial", K, "protetor_solar", "stick", "4 g", "T", ["fotoprotecao", "ressecamento"], ["filtro_uv", "vitamina_e"], 50, "dia", 19.90, [], [], [])
add("Lume Lab", "Sérum Contorno dos Olhos Cafeína", "contorno dos olhos", K, "olhos_labios", "dropper", "15 ml", "T", ["olheiras"], ["cafeina", "acido_hialuronico"], None, "dia_noite", 49.90, [], [OLH], [])
add("Pura Base", "Gel para Olhos Anti-Olheiras", "contorno dos olhos", K, "olhos_labios", "tube", "15 g", "T", ["olheiras"], ["cafeina", "glicerina"], None, "dia_noite", 24.90, [], [OLH], [])
add("Vita Verde", "Bálsamo Labial Hidratante", "bálsamo labial", K, "olhos_labios", "stick", "4 g", "T", ["ressecamento"], ["manteiga_karite", "vitamina_e"], None, "dia_noite", 14.90, [VG], [], [])
add("Aurora Dermo", "Creme para Área dos Olhos Antissinais", "contorno dos olhos", K, "olhos_labios", "jar", "15 g", "T", ["sinais_idade", "olheiras"], ["peptideos", "cafeina"], None, "dia_noite", 99.90, [], [OLH], [])

# SKUs sem estoque (para testar disponibilidade na recomendação)
OUT_OF_STOCK = {"p012", "p047", "p076", "p088", "p093", "p114"}  # p114: magnésio bisglicinato (ruptura de suplemento)

# --------------------------------------------------------------------------
# Textos auxiliares
# --------------------------------------------------------------------------
HOW_TO = {
    "água micelar": "Aplique com algodão sobre o rosto e remova sem enxaguar.",
    "óleo de limpeza": "Massageie na pele seca, adicione água para emulsionar e enxágue.",
    "tônico facial": "Aplique com algodão ou com as mãos após a limpeza.",
    "tônico esfoliante": "Use à noite, 2 a 3 vezes por semana, e use protetor solar durante o dia.",
    "esfoliante químico": "Use à noite, 2 a 3 vezes por semana, e use protetor solar durante o dia.",
    "esfoliante físico": "Massageie suavemente com a pele úmida e enxágue. Use 1 a 2 vezes por semana.",
    "máscara de argila": "Aplique uma camada fina, aguarde 10 minutos e enxágue. Use 1 a 2 vezes por semana.",
    "adesivo hidrocoloide": "Aplique sobre a espinha com a pele limpa e seca e deixe agir por 6 a 8 horas.",
    "gel secativo": "Aplique pontualmente sobre a região, após a limpeza.",
    "loção secativa": "Aplique pontualmente sobre a região, após a limpeza.",
    "protetor solar facial": "Aplique generosamente 15 minutos antes da exposição e reaplique a cada 2 horas.",
    "protetor solar corporal": "Aplique generosamente 15 minutos antes da exposição e reaplique a cada 2 horas.",
    "hidratante com FPS": "Aplique pela manhã sobre o rosto limpo e reaplique a cada 2 horas se houver exposição ao sol.",
    "protetor labial": "Aplique nos lábios quantas vezes for necessário, principalmente antes de sair.",
    "bálsamo labial": "Aplique nos lábios quantas vezes for necessário.",
    "contorno dos olhos": "Aplique pequenas quantidades ao redor dos olhos com leves batidas.",
}
HOW_TO_STEP = {
    "limpeza": "Aplique sobre a pele úmida, massageie suavemente e enxágue.",
    "preparo": "Aplique após a limpeza, antes do tratamento.",
    "tratamento": "Aplique no rosto limpo, antes do hidratante.",
    "hidratacao": "Aplique sobre o rosto limpo, pela manhã e/ou à noite.",
    "protecao_solar": "Aplique generosamente 15 minutos antes da exposição e reaplique a cada 2 horas.",
    "protecao_corporal": "Aplique generosamente 15 minutos antes da exposição e reaplique a cada 2 horas.",
    "complemento": "Aplique conforme a necessidade.",
    "omega3": "Use a quantidade indicada na embalagem, junto a uma refeição.",
    "colageno": "Use a quantidade indicada na embalagem.",
    "magnesio": "Use a quantidade indicada na embalagem.",
    "vitaminas": "Use a quantidade indicada na embalagem, junto a uma refeição.",
    "higiene_corpo": "Use no banho, massageie e enxágue.",
    "higiene_cabelo": "Aplique nos cabelos molhados, massageie e enxágue.",
    "higiene_oral": "Use na higiene bucal diária, conforme a embalagem.",
    "desodorante": "Aplique nas axilas limpas e secas.",
    "reposicao": "Use somente conforme a sua receita.",
    **MED.MED_HOW_TO,
}


def join_pt(items: list[str]) -> str:
    items = list(items)
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " e " + items[-1]


def parse_size(txt: str) -> tuple[float, str]:
    v, u = txt.split(" ")
    return (float(v) if "." in v else int(v)), u


def build_products() -> tuple[list[dict], list[dict]]:
    rng = random.Random(SEED)
    ing_names = {i[0]: i[1] for i in INGREDIENTS}
    products: list[dict] = []
    inventory: list[dict] = []
    for n, row in enumerate(P + PP.EXTRA_PRODUCTS + MED.MED_PRODUCTS + HG.HIGIENE_PRODUCTS, start=1):
        (brand, name, ptype, step, line, form, size, skins, concerns, ings, fps, period,
         price, claims, warns, covers_extra) = row[:16]
        extras = row[16] if len(row) > 16 else {}
        domain = extras.get("domain", "dermo")
        pid = f"p{n:03d}"
        skin_list = ["todas"] if skins == "T" else [SKIN[c] for c in skins]
        warn_list = list(warns)
        for ing_id in ings:
            ing = next(i for i in INGREDIENTS if i[0] == ing_id)
            if ing[4] and "fotossensibilizante" not in warn_list:
                warn_list.insert(0, "fotossensibilizante")
        size_v, size_u = parse_size(size)

        skins_txt = "todos os tipos de pele" if skin_list == ["todas"] else "pele " + join_pt(skin_list)
        conc_txt = join_pt([CONCERNS[c] for c in concerns])
        ing_txt = join_pt([ing_names[i] for i in ings])
        if domain == "dermo":
            desc = f"{name}: produto do tipo {ptype}, da marca {brand}, indicado para {skins_txt}. Foco em {conc_txt}. Principais ativos: {ing_txt}."
        elif domain == "suplemento":
            # #47 (RDC 243/2018): suplemento só traz composição e uso, nunca queixa de saúde
            desc = f"{name}: suplemento alimentar ({ptype}) da marca {brand}. Componentes: {ing_txt}."
        elif domain == "higiene":
            desc = f"{name}: produto de higiene ({ptype}) da marca {brand}. Foco em {conc_txt}. Componentes: {ing_txt}."
        elif not extras.get("equivalence"):
            desc = f"{name}: medicamento ({ptype}) do laboratório {brand}. Princípio ativo: {ing_txt}. Para {conc_txt}."
            if extras.get("rx"):
                desc += " Venda sob prescrição."
        else:
            eq = extras["equivalence"]
            desc = (f"{name}: medicamento FICTÍCIO para demonstração ({ptype}), laboratório {brand}. "
                    f"Princípio ativo inventado: {eq['active']} {eq['dose']}. Apresentação: {eq['presentation']}. "
                    f"Reposição de uso contínuo.")
        if fps:
            desc += f" FPS {fps}."
        if claims:
            desc += " " + join_pt([c.capitalize() if k == 0 else c for k, c in enumerate(claims)]) + "."
        products.append({
            "id": pid,
            "name": name,
            "brand": brand,
            "line": line,
            "step": step,
            "covers_steps": [step] + covers_extra,
            "product_type": ptype,
            "form": form,
            "size": {"value": size_v, "unit": size_u},
            "skin_types": skin_list,
            "concerns": concerns,
            "ingredients": ings,
            "fps": fps,
            "usage_period": period,
            "claims": claims,
            "warnings": warn_list,
            "description": desc,
            "how_to_use": HOW_TO.get(ptype, HOW_TO_STEP[step]),
            "image": None,  # imagens reais ficam em data/images.json (ver catalog/images/README.md)
            "domain": domain,
            "rx": extras.get("rx"),
            "equivalence": extras.get("equivalence"),
        })
        cents = int(round(price * 100))
        promo = rng.random() < 0.15 and domain != "medicamento"   # #41/#45 (RDC 96/2008): remédio, com ou sem receita, nunca tem preço riscado nem "Super oferta"
        list_cents = int(round(price * 1.2 / 0.1)) * 10 if promo else cents
        if list_cents < cents:
            list_cents = cents
        stock = 0 if pid in OUT_OF_STOCK else rng.randint(4, 60)
        inventory.append({
            "id": pid,
            "price_cents": cents,
            "list_price_cents": list_cents,
            "stock_qty": stock,
            "updated_at": UPDATED_AT,
        })

    # faixa de preço por etapa (tercis)
    by_step: dict[str, list[dict]] = {}
    inv_by_id = {i["id"]: i for i in inventory}
    for p in products:
        by_step.setdefault(p["step"], []).append(p)
    for step, items in by_step.items():
        items_sorted = sorted(items, key=lambda x: inv_by_id[x["id"]]["price_cents"])
        n = len(items_sorted)
        for k, p in enumerate(items_sorted):
            p["price_tier"] = "economico" if k < n / 3 else ("intermediario" if k < 2 * n / 3 else "premium")
    return products, inventory


SCHEMA_SQL = """
CREATE TABLE products (
  id TEXT PRIMARY KEY, name TEXT NOT NULL, brand TEXT NOT NULL, line TEXT NOT NULL,
  step TEXT NOT NULL, product_type TEXT NOT NULL, form TEXT NOT NULL,
  size_value REAL NOT NULL, size_unit TEXT NOT NULL, fps INTEGER,
  usage_period TEXT NOT NULL, price_tier TEXT NOT NULL,
  description TEXT NOT NULL, how_to_use TEXT NOT NULL,
  domain TEXT NOT NULL, rx TEXT
);
CREATE TABLE product_equivalence (
  product_id TEXT PRIMARY KEY, equivalence_group TEXT NOT NULL, presentation TEXT NOT NULL,
  active TEXT NOT NULL, dose TEXT NOT NULL
);
CREATE TABLE product_covers_step (product_id TEXT, step TEXT, PRIMARY KEY (product_id, step));
CREATE TABLE product_skin_types (product_id TEXT, skin_type TEXT, PRIMARY KEY (product_id, skin_type));
CREATE TABLE product_concerns (product_id TEXT, concern TEXT, PRIMARY KEY (product_id, concern));
CREATE TABLE product_claims (product_id TEXT, claim TEXT, PRIMARY KEY (product_id, claim));
CREATE TABLE product_warnings (product_id TEXT, warning TEXT, PRIMARY KEY (product_id, warning));
CREATE TABLE ingredients (id TEXT PRIMARY KEY, name TEXT, family TEXT, function TEXT, photosensitizing INTEGER);
CREATE TABLE product_ingredients (product_id TEXT, ingredient_id TEXT, PRIMARY KEY (product_id, ingredient_id));
CREATE TABLE interactions (a TEXT, b TEXT, severity TEXT, reason TEXT, PRIMARY KEY (a, b));
CREATE TABLE inventory (
  product_id TEXT PRIMARY KEY, price_cents INTEGER NOT NULL, list_price_cents INTEGER NOT NULL,
  stock_qty INTEGER NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE goals (id TEXT PRIMARY KEY, label TEXT);
CREATE TABLE goal_concerns (goal_id TEXT, concern TEXT, PRIMARY KEY (goal_id, concern));
CREATE TABLE goal_steps (goal_id TEXT, step TEXT, required INTEGER, PRIMARY KEY (goal_id, step));
CREATE TABLE warning_texts (code TEXT PRIMARY KEY, text TEXT);
"""


def write_sqlite(products, inventory) -> None:
    path = DATA / "catalog.sqlite"
    if path.exists():
        path.unlink()
    con = sqlite3.connect(path)
    con.executescript(SCHEMA_SQL)
    cur = con.cursor()
    for p in products:
        cur.execute(
            "INSERT INTO products VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (p["id"], p["name"], p["brand"], p["line"], p["step"], p["product_type"], p["form"],
             p["size"]["value"], p["size"]["unit"], p["fps"], p["usage_period"], p["price_tier"],
             p["description"], p["how_to_use"], p["domain"], p["rx"]),
        )
        if p["equivalence"]:
            e = p["equivalence"]
            cur.execute("INSERT INTO product_equivalence VALUES (?,?,?,?,?)",
                        (p["id"], e["group"], e["presentation"], e["active"], e["dose"]))
        for s in p["covers_steps"]:
            cur.execute("INSERT INTO product_covers_step VALUES (?,?)", (p["id"], s))
        for s in p["skin_types"]:
            cur.execute("INSERT INTO product_skin_types VALUES (?,?)", (p["id"], s))
        for s in p["concerns"]:
            cur.execute("INSERT INTO product_concerns VALUES (?,?)", (p["id"], s))
        for s in p["claims"]:
            cur.execute("INSERT INTO product_claims VALUES (?,?)", (p["id"], s))
        for s in p["warnings"]:
            cur.execute("INSERT INTO product_warnings VALUES (?,?)", (p["id"], s))
        for s in p["ingredients"]:
            cur.execute("INSERT INTO product_ingredients VALUES (?,?)", (p["id"], s))
    for i in INGREDIENTS:
        cur.execute("INSERT INTO ingredients VALUES (?,?,?,?,?)", (i[0], i[1], i[2], i[3], int(i[4])))
    for a, b, sev, reason in INTERACTIONS:
        cur.execute("INSERT INTO interactions VALUES (?,?,?,?)", (a, b, sev, reason))
    for inv in inventory:
        cur.execute("INSERT INTO inventory VALUES (?,?,?,?,?)",
                    (inv["id"], inv["price_cents"], inv["list_price_cents"], inv["stock_qty"], inv["updated_at"]))
    for g in GOALS:
        cur.execute("INSERT INTO goals VALUES (?,?)", (g["id"], g["label"]))
        for c in g["concerns"]:
            cur.execute("INSERT INTO goal_concerns VALUES (?,?)", (g["id"], c))
        for s in g["required_steps"]:
            cur.execute("INSERT INTO goal_steps VALUES (?,?,1)", (g["id"], s))
        for s in g["optional_steps"]:
            cur.execute("INSERT INTO goal_steps VALUES (?,?,0)", (g["id"], s))
    for code, text in WARNINGS.items():
        cur.execute("INSERT INTO warning_texts VALUES (?,?)", (code, text))
    con.commit()
    con.close()


def dump(name: str, obj) -> None:
    (DATA / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    products, inventory = build_products()
    dump("products.json", products)
    dump("inventory.json", inventory)
    dump("ingredients.json", [
        {"id": i[0], "name": i[1], "family": i[2], "function": i[3], "photosensitizing": i[4]}
        for i in INGREDIENTS
    ])
    dump("interactions.json", [
        {"a": a, "b": b, "severity": sev, "reason": reason} for a, b, sev, reason in INTERACTIONS
    ])
    dump("goals.json", GOALS)
    dump("warnings.json", WARNINGS)
    dump("steps.json", STEPS)
    dump("concerns.json", CONCERNS)
    write_sqlite(products, inventory)
    print(f"OK: {len(products)} produtos, {len(INGREDIENTS)} ingredientes, "
          f"{len(INTERACTIONS)} interações, {len(GOALS)} objetivos -> {DATA}")
    # ecossistema (lojas, estoque por loja, cashback, categorias) por cima do catálogo
    import generate_commerce
    generate_commerce.main()
    # persona sintética (Renata) por cima do catálogo e das lojas
    import generate_persona
    generate_persona.main()


if __name__ == "__main__":
    main()
