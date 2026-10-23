"""Ampliação do catálogo para a persona Renata Almeida (docs/14-persona-renata.md).

Só DADOS (vocabulários e produtos); quem monta tudo é generate_catalog.py.
Tudo é fictício. Nada aqui vem da empresa nem de bula, fabricante ou marca real.

Necessidades da persona → o que foi acrescentado (ids p101 em diante, os 100 antigos não mudam):
  rotina de skincare anti-idade   6 produtos (limpeza, tratamento, olhos, hidratação, protetor)
  suplementos (ômega 3, colágeno, magnésio, vitaminas)   12 produtos
  higiene premium (corpo, cabelo, bucal, desodorante)    12 produtos
  reposição de medicamento contínuo   8 apresentações de 2 medicamentos FICTÍCIOS
                                      (referência, genérico, similar; princípios ativos inventados)

Regras de conteúdo (conferidas em validate_catalog.py):
  - suplemento: sem alegação terapêutica; sempre com o aviso `consultar_se_medicacao`;
  - medicamento: domínio próprio (`domain = medicamento`), com `rx`, fora de qualquer kit,
    nomes e princípios ativos inventados, texto "fictício para demonstração".
"""
from __future__ import annotations

# ------------------------------------------------------------------ vocabulários novos
EXTRA_STEPS = {
    "omega3": "Ômega 3",
    "colageno": "Colágeno",
    "magnesio": "Magnésio",
    "vitaminas": "Vitaminas",
    "higiene_corpo": "Banho e corpo",
    "higiene_cabelo": "Cabelo",
    "higiene_oral": "Higiene bucal",
    "desodorante": "Desodorante",
    "reposicao": "Reposição de medicamento contínuo",
}

EXTRA_CONCERNS = {
    "nutricao": "nutrição e bem-estar",
    "beleza_interna": "beleza de dentro para fora",
    "higiene_diaria": "higiene diária",
    "cuidado_cabelo": "cuidado com o cabelo",
    "higiene_oral": "higiene bucal",
    "cuidado_corporal": "cuidado com o corpo",
    "desodorizacao": "desodorização",
    "reposicao": "reposição de medicamento de uso contínuo",
}

# id, nome, família, função, fotossensibilizante
EXTRA_INGREDIENTS = [
    ("omega3_epa_dha", "Ômega 3 (EPA e DHA)", "ácido graxo", "suplemento alimentar de ômega 3", False),
    ("omega3_algas", "Ômega 3 de algas (DHA)", "ácido graxo vegetal", "suplemento alimentar de ômega 3 vegetal", False),
    ("colageno_hidrolisado", "Colágeno hidrolisado", "proteína", "suplemento alimentar de colágeno", False),
    ("magnesio_dimalato", "Magnésio dimalato", "mineral", "suplemento alimentar de magnésio", False),
    ("magnesio_bisglicinato", "Magnésio bisglicinato", "mineral", "suplemento alimentar de magnésio", False),
    ("magnesio_citrato", "Magnésio citrato", "mineral", "suplemento alimentar de magnésio", False),
    ("vitamina_d3", "Vitamina D3", "vitamina", "suplemento alimentar de vitamina D", False),
    ("vitamina_k2", "Vitamina K2", "vitamina", "suplemento alimentar de vitamina K", False),
    ("multivitaminico", "Complexo multivitamínico", "vitaminas e minerais", "suplemento alimentar multivitamínico", False),
    ("oleo_argan", "Óleo de argan", "óleo vegetal", "nutrição de cabelo e pele", False),
    ("queratina", "Queratina", "proteína", "reposição de massa do fio", False),
    ("fluoreto", "Fluoreto", "mineral", "higiene bucal", False),
    ("tensivalol_potassico", "Tensivalol potássico (fictício)", "substância fictícia", "princípio ativo inventado para a demonstração", False),
    ("lipostanol_calcico", "Lipostanol cálcico (fictício)", "substância fictícia", "princípio ativo inventado para a demonstração", False),
]

EXTRA_WARNINGS = {
    "consultar_se_medicacao": (
        "Suplemento alimentar: se você usa medicamento contínuo, confira na embalagem as interações informadas."),
    "receita_obrigatoria": "Venda sob receita. Neste protótipo a receita é simulada.",
    "confirmar_troca_com_farmaceutico": "Troca por outra apresentação conforme a sua receita.",
}

EXTRA_GOALS = [
    {
        "id": "suplementos",
        "label": "Suplementos e vitaminas",
        "concerns": ["nutricao", "beleza_interna"],
        "required_steps": ["omega3", "colageno", "magnesio"],
        "optional_steps": ["vitaminas", "imunidade", "fibra"],      # imunidade e fibra: vitamina C efervescente e psyllium (#40)
        "synonyms": ["suplemento", "suplementos", "vitamina", "vitaminas", "omega", "ômega", "omega 3", "ômega 3",
                     "colageno", "colágeno", "magnesio", "magnésio"],
    },
    {
        "id": "higiene_premium",
        "label": "Higiene premium",
        "concerns": ["higiene_diaria", "cuidado_cabelo", "higiene_oral", "cuidado_corporal", "desodorizacao"],
        "required_steps": ["higiene_corpo", "higiene_cabelo", "higiene_oral"],
        "optional_steps": ["desodorante"],
        "synonyms": ["higiene", "higiene premium", "banho", "shampoo", "xampu", "condicionador", "creme dental",
                     "pasta de dente", "desodorante", "cabelo", "produtos de higiene"],
    },
]

# ------------------------------------------------------------------ produtos
# Tupla no formato do gerador (16 campos) + 1 dicionário de atributos extras:
# (marca, nome, tipo, etapa, linha, forma, tamanho, peles, preocupações, ingredientes,
#  fps, período, preço_reais, claims, avisos, cobre_etapas_extra, extras)
# extras: domain (padrão "dermo"), rx, equivalence {group, presentation, active, dose}
OF = "oil free"
NC = "não comedogênico"
SF = "sem fragrância"
VG = "vegano"
FOT = "fotossensibilizante"
GES = "consultar_se_gestante"
TST = "teste_de_sensibilidade"
OLH = "evitar_contato_olhos"
MED = "consultar_se_medicacao"

EXTRA_PRODUCTS = []


def add(*args, **extras):
    EXTRA_PRODUCTS.append((*args, extras))


# ---- ANTI-IDADE: skincare premium para a rotina da persona (6) ----
add("Aurora Dermo", "Gel de Limpeza Antissinais Suave", "gel de limpeza", "limpeza", "limpeza", "tube", "150 ml", "NSM",
    ["sinais_idade", "limpeza_diaria"], ["ceramidas", "glicerina", "tensoativo_suave"], None, "dia_noite", 59.90,
    [SF, NC], [], [])
add("Aurora Dermo", "Sérum Vitamina C + Peptídeos Antissinais", "sérum", "tratamento", "anti_idade", "dropper", "30 ml",
    "NSM", ["sinais_idade", "manchas"], ["vitamina_c", "peptideos", "vitamina_e"], None, "dia", 149.90, [NC], [TST], [])
add("Lume Lab", "Creme Noturno Retinol + Peptídeos Premium", "creme de retinol", "tratamento", "anti_idade", "jar",
    "50 g", "NS", ["sinais_idade", "textura"], ["retinol", "peptideos", "ceramidas"], None, "noite", 169.90, [],
    [FOT, GES, TST], [])
add("Aurora Dermo", "Hidratante Antissinais Ácido Hialurônico + Ceramidas", "creme hidratante", "hidratacao",
    "hidratacao", "jar", "50 g", "NSM", ["sinais_idade", "ressecamento"],
    ["acido_hialuronico", "ceramidas", "peptideos"], None, "dia_noite", 89.90, [SF], [], [])
add("Solare", "Protetor Solar Facial FPS 60 Antissinais", "protetor solar facial", "protecao_solar", "protetor_solar",
    "tube", "50 g", "NSM", ["fotoprotecao", "sinais_idade"], ["filtro_uv", "vitamina_e", "peptideos"], 60, "dia",
    94.90, [NC], [], [])
add("Lume Lab", "Creme Área dos Olhos Antissinais Peptídeos", "contorno dos olhos", "complemento", "olhos_labios",
    "jar", "15 g", "T", ["sinais_idade", "olheiras"], ["peptideos", "cafeina", "acido_hialuronico"], None, "dia_noite",
    119.90, [], [OLH], [])

# ---- SUPLEMENTOS (12) ----
SUP = {"domain": "suplemento"}
add("Essência Nutri", "Ômega 3 1000 mg EPA/DHA", "suplemento de ômega 3 em cápsulas", "omega3", "suplementos", "caps",
    "60 un", "T", ["nutricao"], ["omega3_epa_dha"], None, "dia", 39.90, ["sem glúten"], [MED], [], **SUP)
add("Essência Nutri", "Ômega 3 Alta Concentração", "suplemento de ômega 3 em cápsulas", "omega3", "suplementos", "caps",
    "120 un", "T", ["nutricao"], ["omega3_epa_dha", "vitamina_e"], None, "dia", 79.90, ["sem glúten"], [MED], [], **SUP)
add("Vita Verde", "Ômega 3 Vegano de Algas", "suplemento de ômega 3 em cápsulas", "omega3", "suplementos", "caps",
    "60 un", "T", ["nutricao"], ["omega3_algas"], None, "dia", 89.90, [VG, "sem glúten"], [MED], [], **SUP)

add("Essência Nutri", "Colágeno Hidrolisado em Pó Neutro", "suplemento de colágeno em pó", "colageno", "suplementos",
    "powder", "300 g", "T", ["beleza_interna"], ["colageno_hidrolisado"], None, "dia", 69.90, ["sem açúcar"], [MED], [],
    **SUP)
add("Essência Nutri", "Colágeno Hidrolisado em Cápsulas", "suplemento de colágeno em cápsulas", "colageno",
    "suplementos", "caps", "120 un", "T", ["beleza_interna"], ["colageno_hidrolisado"], None, "dia", 59.90,
    ["sem açúcar"], [MED], [], **SUP)
add("Lume Lab", "Colágeno com Vitamina C e Ácido Hialurônico em Pó", "suplemento de colágeno em pó", "colageno",
    "suplementos", "powder", "250 g", "T", ["beleza_interna"], ["colageno_hidrolisado", "vitamina_c", "acido_hialuronico"],
    None, "dia", 99.90, ["sem açúcar"], [MED], [], **SUP)

add("Essência Nutri", "Magnésio Dimalato", "suplemento de magnésio em cápsulas", "magnesio", "suplementos", "caps",
    "60 un", "T", ["nutricao"], ["magnesio_dimalato"], None, "dia", 34.90, ["sem glúten"], [MED], [], **SUP)
add("Essência Nutri", "Magnésio Bisglicinato", "suplemento de magnésio em cápsulas", "magnesio", "suplementos", "caps",
    "60 un", "T", ["nutricao"], ["magnesio_bisglicinato"], None, "noite", 54.90, ["sem glúten"], [MED], [], **SUP)
add("Vita Verde", "Citrato de Magnésio em Pó", "suplemento de magnésio em pó", "magnesio", "suplementos", "powder",
    "200 g", "T", ["nutricao"], ["magnesio_citrato"], None, "noite", 44.90, [VG, "sem açúcar"], [MED], [], **SUP)

add("Essência Nutri", "Vitamina D3 2000 UI", "suplemento de vitamina D em cápsulas", "vitaminas", "suplementos",
    "caps", "60 un", "T", ["nutricao"], ["vitamina_d3"], None, "dia", 24.90, ["sem glúten"], [MED], [], **SUP)
add("Essência Nutri", "Vitamina D3 + K2", "suplemento de vitaminas D e K em cápsulas", "vitaminas", "suplementos",
    "caps", "60 un", "T", ["nutricao"], ["vitamina_d3", "vitamina_k2"], None, "dia", 49.90, ["sem glúten"], [MED], [],
    **SUP)
add("Essência Nutri", "Multivitamínico Mulher 45+", "suplemento multivitamínico em comprimidos", "vitaminas",
    "suplementos", "caps", "60 un", "T", ["nutricao"], ["multivitaminico"], None, "dia", 64.90, [], [MED], [], **SUP)

# ---- HIGIENE PREMIUM (12) ----
HIG = {"domain": "higiene"}
add("Noble Banho", "Sabonete Líquido Corporal Óleos Naturais", "sabonete líquido corporal", "higiene_corpo", "higiene",
    "bottle", "300 ml", "T", ["higiene_diaria", "cuidado_corporal"], ["glicerina", "oleo_argan"], None, "dia_noite",
    34.90, [VG, "sem parabenos"], [], [], **HIG)
add("Noble Banho", "Gel de Banho Hidratante Karité", "gel de banho", "higiene_corpo", "higiene", "bottle", "300 ml",
    "T", ["higiene_diaria", "cuidado_corporal"], ["manteiga_karite", "glicerina"], None, "dia_noite", 39.90,
    ["sem parabenos"], [], [], **HIG)
add("Noble Banho", "Esfoliante Corporal Açúcar e Karité", "esfoliante corporal", "higiene_corpo", "higiene", "jar",
    "200 g", "T", ["cuidado_corporal"], ["manteiga_karite"], None, "noite", 44.90, [VG], [], [], **HIG)
add("Noble Banho", "Shampoo Reparador Premium", "shampoo", "higiene_cabelo", "higiene", "bottle", "300 ml", "T",
    ["cuidado_cabelo"], ["queratina", "oleo_argan"], None, "dia_noite", 49.90, ["sem sulfato"], [], [], **HIG)
add("Noble Banho", "Condicionador Reparador Premium", "condicionador", "higiene_cabelo", "higiene", "bottle", "300 ml",
    "T", ["cuidado_cabelo"], ["queratina", "oleo_argan"], None, "dia_noite", 49.90, ["sem sulfato"], [], [], **HIG)
add("Noble Banho", "Máscara Capilar Nutrição Intensa", "máscara capilar", "higiene_cabelo", "higiene", "jar", "250 g",
    "T", ["cuidado_cabelo"], ["manteiga_karite", "oleo_argan"], None, "noite", 69.90, [VG], [], [], **HIG)
add("Sorriso Pleno", "Creme Dental Branqueador Premium", "creme dental", "higiene_oral", "higiene", "tube", "90 g", "T",
    ["higiene_oral"], ["fluoreto"], None, "dia_noite", 24.90, ["com flúor"], [], [], **HIG)
add("Sorriso Pleno", "Creme Dental para Dentes Sensíveis", "creme dental", "higiene_oral", "higiene", "tube", "90 g",
    "T", ["higiene_oral"], ["fluoreto"], None, "dia_noite", 22.90, ["com flúor"], [], [], **HIG)
add("Sorriso Pleno", "Enxaguante Bucal Sem Álcool", "enxaguante bucal", "higiene_oral", "higiene", "bottle", "500 ml",
    "T", ["higiene_oral"], ["fluoreto"], None, "dia_noite", 29.90, ["sem álcool"], [], [], **HIG)
add("Noble Banho", "Desodorante Roll-on Sem Alumínio", "desodorante roll-on", "desodorante", "higiene", "bottle",
    "55 ml", "T", ["desodorizacao"], ["aloe_vera"], None, "dia", 19.90, ["sem alumínio"], [], [], **HIG)
add("Noble Banho", "Desodorante Creme Hidratante", "desodorante em creme", "desodorante", "higiene", "jar", "55 g",
    "T", ["desodorizacao"], ["manteiga_karite"], None, "dia", 24.90, ["sem alumínio", VG], [], [], **HIG)
add("Noble Banho", "Desodorante Aerossol Pele Sensível", "desodorante aerossol", "desodorante", "higiene", "spray",
    "150 ml", "T", ["desodorizacao"], ["aloe_vera"], None, "dia", 29.90, ["sem alumínio", SF], [], [], **HIG)

# ---- REPOSIÇÃO DE MEDICAMENTO CONTÍNUO (8 apresentações de 2 medicamentos FICTÍCIOS) ----
# Princípios ativos e marcas inventados. Não são medicamentos reais. A IA nunca recomenda estes itens:
# eles só aparecem na reposição de quem já os usa (lista do próprio cliente, guardada no aparelho).
def med(brand, name, ptype, size, price, presentation, group, active, dose, ing, *, stock_note=None):
    concern = {"tensivalol_50": "hipertensao", "lipostanol_20": "colesterol"}[group]
    add(brand, name, ptype, "reposicao", "reposicao_" + group, "box", size, "T", ["reposicao", concern], [ing], None, "dia",
        price, [], ["receita_obrigatoria", "confirmar_troca_com_farmaceutico"], [],
        domain="medicamento", rx="receita_simples",
        equivalence={"group": group, "presentation": presentation, "active": active, "dose": dose})


med("Lab Aurora", "Tensiv 50 mg (referência)", "comprimido de uso contínuo", "30 un", 68.90, "referencia",
    "tensivalol_50", "Tensivalol potássico", "50 mg", "tensivalol_potassico")
med("Lab Genérico Sul", "Tensivalol potássico 50 mg (genérico) — 30 comprimidos", "comprimido de uso contínuo", "30 un",
    31.90, "generico", "tensivalol_50", "Tensivalol potássico", "50 mg", "tensivalol_potassico")
med("Lab Genérico Sul", "Tensivalol potássico 50 mg (genérico) — 60 comprimidos", "comprimido de uso contínuo", "60 un",
    58.90, "generico", "tensivalol_50", "Tensivalol potássico", "50 mg", "tensivalol_potassico")
med("Lab Nova Via", "Pressolan 50 mg (similar)", "comprimido de uso contínuo", "30 un", 39.90, "similar",
    "tensivalol_50", "Tensivalol potássico", "50 mg", "tensivalol_potassico")

med("Lab Aurora", "Lipostan 20 mg (referência)", "comprimido de uso contínuo", "30 un", 92.90, "referencia",
    "lipostanol_20", "Lipostanol cálcico", "20 mg", "lipostanol_calcico")
med("Lab Genérico Sul", "Lipostanol cálcico 20 mg (genérico) — 30 comprimidos", "comprimido de uso contínuo", "30 un",
    44.90, "generico", "lipostanol_20", "Lipostanol cálcico", "20 mg", "lipostanol_calcico")
med("Lab Genérico Sul", "Lipostanol cálcico 20 mg (genérico) — 60 comprimidos", "comprimido de uso contínuo", "60 un",
    82.90, "generico", "lipostanol_20", "Lipostanol cálcico", "20 mg", "lipostanol_calcico")
med("Lab Nova Via", "Colemax 20 mg (similar)", "comprimido de uso contínuo", "30 un", 52.90, "similar",
    "lipostanol_20", "Lipostanol cálcico", "20 mg", "lipostanol_calcico")

# Estoque central zerado de propósito (para a demonstração da "ruptura"): nenhum extra nasce sem estoque,
# a ruptura da persona é POR LOJA (generate_commerce.FORCED_STORE_STOCK).
EXTRA_OUT_OF_STOCK: set[str] = set()
