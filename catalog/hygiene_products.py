"""Produtos de higiene adicionais (6 por prateleira: corpo, cabelo, bucal e desodorante).

Só DADOS; quem monta o catálogo é generate_catalog.py. Tudo fictício: marcas, nomes, preços e
estoque inventados. Estes itens entram DEPOIS dos produtos existentes para não mudar os ids
antigos (p001–p217), que a persona e o app já usam.
"""
from __future__ import annotations

VG = "vegano"
SF = "sem fragrância"

HIG = {"domain": "higiene"}
HIGIENE_PRODUCTS: list[tuple] = []

# Ingredientes/materiais usados só por estes itens (o gerador junta em INGREDIENTS).
# id, nome, família, função, fotossensibilizante
HYGIENE_INGREDIENTS = [
    ("nylon", "Nylon", "material", "cerdas e fio dental", False),
    ("plastico_reciclado", "Plástico reciclado", "material", "corpo de escovas e pentes", False),
    ("talco_mineral", "Talco mineral", "mineral", "absorção de umidade", False),
    ("amido_milho", "Amido de milho", "vegetal", "absorção de umidade", False),
    ("menta_extrato", "Extrato de menta", "extrato vegetal", "frescor", False),
    ("fibra_vegetal", "Fibra vegetal", "material", "esfoliação corporal", False),
    ("esponja_sintetica", "Esponja sintética", "material", "espuma e limpeza", False),
    ("algodao", "Algodão", "material", "higiene e limpeza", False),
]


def add(*args):
    HIGIENE_PRODUCTS.append((*args, HIG))


# ---- CORPO (3 novos; a prateleira passa a ter 6) ----
add("Noble Banho", "Sabonete em Barra Hidratante", "sabonete em barra", "higiene_corpo", "higiene", "bar", "120 g", "T",
    ["higiene_diaria", "cuidado_corporal"], ["glicerina", "manteiga_karite"], None, "dia_noite", 12.90,
    [VG, "sem parabenos"], [], [])
add("Noble Banho", "Gel de Banho Relaxante Lavanda", "gel de banho", "higiene_corpo", "higiene", "bottle", "300 ml", "T",
    ["higiene_diaria", "cuidado_corporal"], ["glicerina"], None, "dia_noite", 32.90, [SF], [], [])
add("Noble Banho", "Óleo de Banho Nutritivo", "óleo de banho", "higiene_corpo", "higiene", "bottle", "200 ml", "T",
    ["cuidado_corporal"], ["manteiga_karite", "oleo_argan"], None, "dia_noite", 49.90, [VG], [], [])

# ---- CABELO (3 novos; a prateleira passa a ter 6) ----
add("Noble Banho", "Shampoo Anticaspa Equilíbrio", "shampoo anticaspa", "higiene_cabelo", "higiene", "bottle", "300 ml",
    "T", ["cuidado_cabelo"], ["zinco_pca", "enxofre"], None, "dia_noite", 39.90, ["sem sulfato"], [], [])
add("Noble Banho", "Shampoo Hidratante Óleo de Argan", "shampoo", "higiene_cabelo", "higiene", "bottle", "300 ml", "T",
    ["cuidado_cabelo"], ["oleo_argan", "queratina"], None, "dia_noite", 42.90, ["sem sulfato"], [], [])
add("Noble Banho", "Máscara Capilar Reconstrução", "máscara capilar", "higiene_cabelo", "higiene", "jar", "250 g", "T",
    ["cuidado_cabelo"], ["queratina", "oleo_argan", "manteiga_karite"], None, "noite", 64.90, [VG], [], [])

# ---- BUCAL (3 novos; a prateleira passa a ter 6) ----
add("Sorriso Pleno", "Creme Dental Branqueador Carvão", "creme dental", "higiene_oral", "higiene", "tube", "90 g", "T",
    ["higiene_oral"], ["fluoreto"], None, "dia_noite", 19.90, ["com flúor"], [], [])
add("Sorriso Pleno", "Creme Dental Dentes Sensíveis", "creme dental", "higiene_oral", "higiene", "tube", "90 g", "T",
    ["higiene_oral"], ["fluoreto"], None, "dia_noite", 23.90, ["com flúor"], [], [])
add("Sorriso Pleno", "Enxaguante Bucal Menta Sem Álcool", "enxaguante bucal", "higiene_oral", "higiene", "bottle", "500 ml",
    "T", ["higiene_oral"], ["fluoreto"], None, "dia_noite", 26.90, ["sem álcool"], [], [])

# ---- DESODORANTE (3 novos; a prateleira passa a ter 6) ----
add("Noble Banho", "Desodorante Stick Sem Alumínio", "desodorante stick", "desodorante", "higiene", "stick", "50 g", "T",
    ["desodorizacao"], ["aloe_vera"], None, "dia", 22.90, ["sem alumínio"], [], [])
add("Noble Banho", "Desodorante Spray 48h", "desodorante aerossol", "desodorante", "higiene", "spray", "150 ml", "T",
    ["desodorizacao"], ["aloe_vera"], None, "dia", 27.90, ["sem alumínio"], [], [])
add("Noble Banho", "Desodorante Creme Pele Sensível", "desodorante em creme", "desodorante", "higiene", "jar", "55 g", "T",
    ["desodorizacao"], ["manteiga_karite"], None, "dia", 29.90, ["sem alumínio", SF], [], [])

# ---- Creme de cabelo / leave-in (6) ----
add("Noble Banho", "Creme para Pentear Hidratante", "creme para pentear", "higiene_cabelo", "higiene", "bottle", "200 ml",
    "T", ["cuidado_cabelo"], ["queratina", "oleo_argan"], None, "dia_noite", 29.90, [SF], [], [])
add("Noble Banho", "Creme para Pentear Antifrizz", "creme para pentear", "higiene_cabelo", "higiene", "bottle", "200 ml",
    "T", ["cuidado_cabelo"], ["oleo_argan"], None, "dia_noite", 34.90, [SF], [], [])
add("Noble Banho", "Leave-in Protetor Térmico", "leave-in", "higiene_cabelo", "higiene", "spray", "150 ml", "T",
    ["cuidado_cabelo"], ["queratina"], None, "dia_noite", 39.90, [SF], [], [])
add("Noble Banho", "Creme para Pentear Cachos Definidos", "creme para pentear", "higiene_cabelo", "higiene", "jar",
    "250 g", "T", ["cuidado_cabelo"], ["manteiga_karite"], None, "dia_noite", 36.90, [VG], [], [])
add("Noble Banho", "Creme para Pentear Sem Enxágue", "creme para pentear", "higiene_cabelo", "higiene", "bottle", "200 ml",
    "T", ["cuidado_cabelo"], ["glicerina"], None, "dia_noite", 24.90, [SF], [], [])
add("Noble Banho", "Creme para Pentear Reparador", "creme para pentear", "higiene_cabelo", "higiene", "bottle", "200 ml",
    "T", ["cuidado_cabelo"], ["queratina", "oleo_argan"], None, "dia_noite", 44.90, [SF], [], [])

# ---- Escovas de dente (6) ----
add("Sorriso Pleno", "Escova de Dente Macia", "escova de dente", "higiene_oral", "higiene", "box", "1 un", "T",
    ["higiene_oral"], ["nylon"], None, "dia_noite", 12.90, [], [], [])
add("Sorriso Pleno", "Escova de Dente Média", "escova de dente", "higiene_oral", "higiene", "box", "1 un", "T",
    ["higiene_oral"], ["nylon"], None, "dia_noite", 9.90, [], [], [])
add("Sorriso Pleno", "Escova de Dente Extra Macia", "escova de dente", "higiene_oral", "higiene", "box", "1 un", "T",
    ["higiene_oral"], ["nylon"], None, "dia_noite", 14.90, [], [], [])
add("Sorriso Pleno", "Escova de Dente Compacta", "escova de dente", "higiene_oral", "higiene", "box", "1 un", "T",
    ["higiene_oral"], ["nylon"], None, "dia_noite", 11.90, [], [], [])
add("Sorriso Pleno", "Escova de Dente com Cerdas Macias (2 un)", "escova de dente", "higiene_oral", "higiene", "box",
    "2 un", "T", ["higiene_oral"], ["nylon"], None, "dia_noite", 19.90, [], [], [])
add("Sorriso Pleno", "Escova de Dente Elétrica", "escova de dente", "higiene_oral", "higiene", "box", "1 un", "T",
    ["higiene_oral"], ["nylon", "plastico_reciclado"], None, "dia_noite", 89.90, [], [], [])

# ---- Escovas de cabelo e pentes (6) ----
add("Noble Banho", "Escova de Cabelo Desembaraçadora", "escova de cabelo", "higiene_cabelo", "higiene", "box", "1 un",
    "T", ["cuidado_cabelo"], ["nylon", "plastico_reciclado"], None, "dia_noite", 29.90, [], [], [])
add("Noble Banho", "Escova de Cabelo Ventilada", "escova de cabelo", "higiene_cabelo", "higiene", "box", "1 un", "T",
    ["cuidado_cabelo"], ["nylon", "plastico_reciclado"], None, "dia_noite", 34.90, [], [], [])
add("Noble Banho", "Escova de Cabelo Oval", "escova de cabelo", "higiene_cabelo", "higiene", "box", "1 un", "T",
    ["cuidado_cabelo"], ["nylon", "plastico_reciclado"], None, "dia_noite", 39.90, [], [], [])
add("Noble Banho", "Pente Garfo", "pente", "higiene_cabelo", "higiene", "box", "1 un", "T", ["cuidado_cabelo"],
    ["plastico_reciclado"], None, "dia_noite", 12.90, [], [], [])
add("Noble Banho", "Pente Fino", "pente", "higiene_cabelo", "higiene", "box", "1 un", "T", ["cuidado_cabelo"],
    ["plastico_reciclado"], None, "dia_noite", 9.90, [], [], [])
add("Noble Banho", "Escova de Cabelo para Cachos", "escova de cabelo", "higiene_cabelo", "higiene", "box", "1 un", "T",
    ["cuidado_cabelo"], ["nylon", "plastico_reciclado"], None, "dia_noite", 32.90, [], [], [])

# ---- Fio dental (6) ----
add("Sorriso Pleno", "Fio Dental 50 m", "fio dental", "higiene_oral", "higiene", "box", "1 un", "T", ["higiene_oral"],
    ["nylon"], None, "dia_noite", 14.90, [], [], [])
add("Sorriso Pleno", "Fita Dental 25 m", "fita dental", "higiene_oral", "higiene", "box", "1 un", "T", ["higiene_oral"],
    ["nylon"], None, "dia_noite", 16.90, [], [], [])
add("Sorriso Pleno", "Fio Dental com Cera", "fio dental", "higiene_oral", "higiene", "box", "1 un", "T",
    ["higiene_oral"], ["nylon"], None, "dia_noite", 17.90, [], [], [])
add("Sorriso Pleno", "Fio Dental Sabor Menta", "fio dental", "higiene_oral", "higiene", "box", "1 un", "T",
    ["higiene_oral"], ["nylon", "menta_extrato"], None, "dia_noite", 15.90, [], [], [])
add("Sorriso Pleno", "Fio Dental Expandível", "fio dental", "higiene_oral", "higiene", "box", "1 un", "T",
    ["higiene_oral"], ["nylon"], None, "dia_noite", 19.90, [], [], [])
add("Sorriso Pleno", "Fio Dental Deslizante", "fio dental", "higiene_oral", "higiene", "box", "1 un", "T",
    ["higiene_oral"], ["nylon"], None, "dia_noite", 18.90, [], [], [])

# ---- Talco (6) ----
add("Noble Banho", "Talco Corporal Clássico", "talco corporal", "higiene_corpo", "higiene", "bottle", "100 g", "T",
    ["cuidado_corporal"], ["talco_mineral"], None, "dia_noite", 12.90, [SF], [], [])
add("Noble Banho", "Talco para Pés Antiodor", "talco para pés", "higiene_corpo", "higiene", "bottle", "100 g", "T",
    ["cuidado_corporal"], ["talco_mineral", "menta_extrato"], None, "dia_noite", 15.90, [SF], [], [])
add("Noble Banho", "Talco Corporal com Amido de Milho", "talco corporal", "higiene_corpo", "higiene", "bottle", "100 g", "T",
    ["cuidado_corporal"], ["amido_milho"], None, "dia_noite", 14.90, [SF], [], [])
add("Noble Banho", "Talco Refrescante Menta", "talco corporal", "higiene_corpo", "higiene", "bottle", "100 g", "T",
    ["cuidado_corporal"], ["talco_mineral", "menta_extrato"], None, "dia_noite", 16.90, [SF], [], [])
add("Noble Banho", "Talco para Pés com Aloe", "talco para pés", "higiene_corpo", "higiene", "bottle", "100 g", "T",
    ["cuidado_corporal"], ["talco_mineral", "aloe_vera"], None, "dia_noite", 17.90, [SF], [], [])
add("Noble Banho", "Talco Corporal Suave", "talco corporal", "higiene_corpo", "higiene", "bottle", "100 g", "T",
    ["cuidado_corporal"], ["amido_milho"], None, "dia_noite", 13.90, [SF], [], [])

# ---- Buchas e esponjas (4) ----
add("Noble Banho", "Bucha Vegetal", "bucha", "higiene_corpo", "higiene", "box", "1 un", "T", ["cuidado_corporal"],
    ["fibra_vegetal"], None, "dia_noite", 9.90, [VG], [], [])
add("Noble Banho", "Esponja de Banho", "esponja de banho", "higiene_corpo", "higiene", "box", "1 un", "T",
    ["cuidado_corporal"], ["esponja_sintetica"], None, "dia_noite", 7.90, [], [], [])
add("Noble Banho", "Luva Esfoliante", "luva esfoliante", "higiene_corpo", "higiene", "box", "1 un", "T",
    ["cuidado_corporal"], ["fibra_vegetal"], None, "dia_noite", 14.90, [], [], [])
add("Noble Banho", "Bucha Natural com Corda", "bucha", "higiene_corpo", "higiene", "box", "1 un", "T",
    ["cuidado_corporal"], ["fibra_vegetal"], None, "dia_noite", 12.90, [VG], [], [])

# ---- Cotonetes e lenços (4) ----
add("Noble Banho", "Cotonetes 75 un", "cotonete", "higiene_corpo", "higiene", "box", "75 un", "T", ["higiene_diaria"],
    ["algodao"], None, "dia_noite", 8.90, [], [], [])
add("Noble Banho", "Lenços Umedecidos 50 un", "lenço umedecido", "higiene_corpo", "higiene", "box", "50 un", "T",
    ["higiene_diaria"], ["algodao", "aloe_vera"], None, "dia_noite", 12.90, [], [], [])
add("Noble Banho", "Algodão em Bolas 50 g", "algodão em bolas", "higiene_corpo", "higiene", "box", "50 g", "T",
    ["higiene_diaria"], ["algodao"], None, "dia_noite", 7.90, [], [], [])
add("Noble Banho", "Lenços Faciais 100 un", "lenço facial", "higiene_corpo", "higiene", "box", "100 un", "T",
    ["higiene_diaria"], ["algodao"], None, "dia_noite", 9.90, [], [], [])

# ---- Limpeza de ouvido (6) ----
add("Noble Banho", "Spray de Limpeza Auricular", "spray auricular", "higiene_corpo", "higiene", "spray", "30 ml", "T",
    ["higiene_diaria", "cuidado_corporal"], ["glicerina", "aloe_vera"], None, "dia_noite", 29.90, [SF], [], [])
add("Noble Banho", "Solução de Limpeza de Ouvido", "solução auricular", "higiene_corpo", "higiene", "dropper", "15 ml",
    "T", ["higiene_diaria", "cuidado_corporal"], ["glicerina"], None, "dia_noite", 24.90, [SF], [], [])
add("Noble Banho", "Lenços de Limpeza Auricular", "lenço auricular", "higiene_corpo", "higiene", "box", "30 un", "T",
    ["higiene_diaria", "cuidado_corporal"], ["algodao"], None, "dia_noite", 14.90, [], [], [])
add("Noble Banho", "Spray Auricular Suave", "spray auricular", "higiene_corpo", "higiene", "spray", "30 ml", "T",
    ["higiene_diaria", "cuidado_corporal"], ["glicerina"], None, "dia_noite", 27.90, [SF], [], [])
add("Noble Banho", "Solução Auricular com Aloe", "solução auricular", "higiene_corpo", "higiene", "dropper", "15 ml",
    "T", ["higiene_diaria", "cuidado_corporal"], ["glicerina", "aloe_vera"], None, "dia_noite", 22.90, [SF], [], [])
add("Noble Banho", "Lenços Umedecidos para Ouvido", "lenço auricular", "higiene_corpo", "higiene", "box", "30 un", "T",
    ["higiene_diaria", "cuidado_corporal"], ["algodao", "aloe_vera"], None, "dia_noite", 16.90, [], [], [])
