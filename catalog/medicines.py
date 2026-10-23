"""Medicamentos para busca e kits (docs/16-prompt-medicamentos-e-ui.md).

Só DADOS (vocabulários e produtos); quem monta tudo é generate_catalog.py.

Princípios ativos e apresentações são os comuns no Brasil; marcas e laboratórios são FICTÍCIOS, como no resto do
catálogo (D-11). Preço e estoque também são inventados. A tarja (`rx`) segue o que é usual no varejo e está listada
no doc 16 para conferência; ela é só um dado do produto (selo "exige receita"), nunca uma mensagem.

Cada área de saúde (campo `line` = "med_<área>") tem pelo menos 6 produtos. Cada área vira um objetivo de kit com
etapas que são PAPÉIS (ex.: dipirona + paracetamol para dor de cabeça). Duas regras do compositor valem aqui
(aceitas pela Julia em 21/10): nunca o mesmo princípio ativo duas vezes no kit; nunca dois anti-inflamatórios juntos.
A segunda está nas interações abaixo; a primeira é verificada pelo compositor (ingrediente em comum).
"""
from __future__ import annotations

from itertools import combinations

MED_STEPS = {
    "analgesico_dipirona": "Dipirona",
    "analgesico_paracetamol": "Paracetamol",
    "antiinflamatorio": "Anti-inflamatório",
    "relaxante_muscular": "Relaxante muscular",
    "dor_topico": "Gel ou pomada para dor",
    "antiespasmodico": "Para cólica",
    "antigases": "Antigases",
    "antiacido": "Antiácido",
    "protetor_gastrico": "Protetor gástrico",
    "antigripal": "Antigripal",
    "descongestionante_nasal": "Nariz (soro e descongestionante)",
    "imunidade": "Vitamina C",
    "expectorante": "Expectorante",
    "antitussigeno": "Para tosse seca",
    "pastilha_garganta": "Pastilha para garganta",
    "spray_garganta": "Spray ou gargarejo para garganta",
    "antialergico": "Antialérgico",
    "antidiarreico": "Antidiarreico",
    "probiotico": "Probiótico",
    "reidratacao": "Reidratação oral",
    "laxante": "Laxante",
    "fibra": "Fibra",
    "antiemetico": "Contra enjoo",
}

MED_CONCERNS = {
    "dor_de_cabeca": "dor de cabeça",
    "enxaqueca": "enxaqueca",
    "febre": "febre",
    "dor_no_corpo": "dor no corpo",
    "dor_muscular": "dor muscular",
    "dor_de_barriga": "dor de barriga e cólica",
    "gases": "gases",
    "azia": "azia e má digestão",
    "gripe": "gripe e resfriado",
    "nariz_entupido": "nariz entupido",
    "tosse": "tosse com catarro",
    "tosse_seca": "tosse seca",
    "dor_de_garganta": "dor de garganta",
    "alergia": "alergia e rinite",
    "diarreia": "diarreia",
    "prisao_de_ventre": "prisão de ventre",
    "enjoo": "enjoo e náusea",
    # reposição de uso contínuo (medicamentos fictícios da persona): passam a ser achados pela busca
    "hipertensao": "pressão alta",
    "colesterol": "colesterol alto",
}

# id, nome, família, função, fotossensibilizante
A = "princípio ativo"
MED_INGREDIENTS = [
    ("dipirona", "Dipirona monoidratada", A, "analgésico e antitérmico", False),
    ("paracetamol", "Paracetamol", A, "analgésico e antitérmico", False),
    ("acido_acetilsalicilico", "Ácido acetilsalicílico", A, "analgésico, antitérmico e anti-inflamatório", False),
    ("cafeina_med", "Cafeína anidra", A, "potencializa o analgésico", False),
    ("isometepteno", "Mucato de isometepteno", A, "vasoconstritor para enxaqueca", False),
    ("ibuprofeno", "Ibuprofeno", A, "anti-inflamatório", False),
    ("naproxeno", "Naproxeno sódico", A, "anti-inflamatório", False),
    ("diclofenaco_potassico", "Diclofenaco potássico", A, "anti-inflamatório", False),
    ("diclofenaco_sodico", "Diclofenaco sódico", A, "anti-inflamatório", False),
    ("diclofenaco_dietilamonio", "Diclofenaco dietilamônio", A, "anti-inflamatório de uso local", False),
    ("nimesulida", "Nimesulida", A, "anti-inflamatório", False),
    ("orfenadrina", "Citrato de orfenadrina", A, "relaxante muscular", False),
    ("ciclobenzaprina", "Cloridrato de ciclobenzaprina", A, "relaxante muscular", False),
    ("carisoprodol", "Carisoprodol", A, "relaxante muscular", False),
    ("salicilato_metila", "Salicilato de metila", A, "alívio local da dor", False),
    ("mentol", "Mentol", A, "sensação refrescante no local", False),
    ("canfora", "Cânfora", A, "alívio local da dor", False),
    ("escopolamina", "Butilbrometo de escopolamina", A, "antiespasmódico", False),
    ("simeticona", "Simeticona", A, "antigases", False),
    ("hidroxido_aluminio", "Hidróxido de alumínio", A, "antiácido", False),
    ("hidroxido_magnesio", "Hidróxido de magnésio", A, "antiácido e laxante", False),
    ("bicarbonato_sodio", "Bicarbonato de sódio", A, "antiácido", False),
    ("carbonato_sodio", "Carbonato de sódio", A, "antiácido", False),
    ("acido_citrico", "Ácido cítrico", A, "efervescente", False),
    ("alginato_sodio", "Alginato de sódio", A, "forma barreira contra o refluxo", False),
    ("omeprazol", "Omeprazol", A, "reduz a acidez do estômago", False),
    ("pantoprazol", "Pantoprazol", A, "reduz a acidez do estômago", False),
    ("esomeprazol", "Esomeprazol", A, "reduz a acidez do estômago", False),
    ("fenilefrina", "Cloridrato de fenilefrina", A, "descongestionante", False),
    ("clorfeniramina", "Maleato de clorfeniramina", A, "antialérgico", False),
    ("acido_ascorbico", "Ácido ascórbico (vitamina C)", A, "vitamina C", False),
    ("cloreto_sodio", "Cloreto de sódio 0,9%", A, "lavagem nasal", False),
    ("nafazolina", "Cloridrato de nafazolina", A, "descongestionante nasal", False),
    ("oximetazolina", "Cloridrato de oximetazolina", A, "descongestionante nasal", False),
    ("ambroxol", "Cloridrato de ambroxol", A, "expectorante", False),
    ("acetilcisteina", "Acetilcisteína", A, "expectorante", False),
    ("bromexina", "Cloridrato de bromexina", A, "expectorante", False),
    ("carbocisteina", "Carbocisteína", A, "expectorante", False),
    ("guaco", "Guaco (Mikania glomerata)", A, "expectorante fitoterápico", False),
    ("dropropizina", "Dropropizina", A, "para tosse seca", False),
    ("levodropropizina", "Levodropropizina", A, "para tosse seca", False),
    ("amilmetacresol", "Amilmetacresol + álcool diclorobenzílico", A, "antisséptico para a garganta", False),
    ("flurbiprofeno", "Flurbiprofeno", A, "anti-inflamatório de uso na garganta", False),
    ("benzidamina", "Cloridrato de benzidamina", A, "anti-inflamatório de uso na garganta", False),
    ("loratadina", "Loratadina", A, "antialérgico", False),
    ("desloratadina", "Desloratadina", A, "antialérgico", False),
    ("cetirizina", "Dicloridrato de cetirizina", A, "antialérgico", False),
    ("fexofenadina", "Cloridrato de fexofenadina", A, "antialérgico", False),
    ("dexclorfeniramina", "Maleato de dexclorfeniramina", A, "antialérgico", False),
    ("loperamida", "Cloridrato de loperamida", A, "antidiarreico", False),
    ("racecadotrila", "Racecadotrila", A, "antidiarreico", False),
    ("nitazoxanida", "Nitazoxanida", A, "antiparasitário", False),
    ("saccharomyces_boulardii", "Saccharomyces boulardii", A, "probiótico", False),
    ("bacillus_clausii", "Bacillus clausii", A, "probiótico", False),
    ("sais_reidratacao", "Sais para reidratação oral", A, "reidratação", False),
    ("bisacodil", "Bisacodil", A, "laxante", False),
    ("picossulfato", "Picossulfato de sódio", A, "laxante", False),
    ("lactulose", "Lactulose", A, "laxante", False),
    ("macrogol", "Macrogol 3350", A, "laxante", False),
    ("psyllium", "Psyllium (Plantago ovata)", A, "fibra", False),
    ("dimenidrinato", "Dimenidrinato", A, "contra enjoo", False),
    ("piridoxina", "Piridoxina (vitamina B6)", A, "vitamina B6", False),
    ("ondansetrona", "Ondansetrona", A, "contra enjoo", False),
    ("metoclopramida", "Cloridrato de metoclopramida", A, "contra enjoo", False),
    ("domperidona", "Domperidona", A, "contra enjoo", False),
]

# Regra aceita: nunca dois anti-inflamatórios no mesmo kit (inclui gel, pastilha e AAS).
AINES = ["ibuprofeno", "naproxeno", "diclofenaco_potassico", "diclofenaco_sodico", "diclofenaco_dietilamonio",
         "nimesulida", "acido_acetilsalicilico", "flurbiprofeno", "benzidamina"]
EXPECTORANTES = ["ambroxol", "acetilcisteina", "bromexina", "carbocisteina", "guaco"]
ANTITUSSIGENOS = ["dropropizina", "levodropropizina"]

MED_INTERACTIONS = (
    [(a, b, "evitar", "Dois anti-inflamatórios no mesmo kit somam efeitos sem somar alívio.")
     for a, b in combinations(AINES, 2)]
    + [(a, b, "evitar", "Remédio que segura a tosse junto com expectorante prende o catarro.")
       for a in ANTITUSSIGENOS for b in EXPECTORANTES]
)

MED_WARNINGS: dict[str, str] = {}


def _goal(gid, label, concerns, required, optional, synonyms):
    return {"id": gid, "label": label, "concerns": concerns, "required_steps": required, "optional_steps": optional,
            "synonyms": synonyms}


MED_GOALS = [
    _goal("dor_de_cabeca", "Dor de cabeça e febre", ["dor_de_cabeca", "enxaqueca", "febre"],
          ["analgesico_dipirona", "analgesico_paracetamol"], [],
          ["dor de cabeça", "dor de cabeca", "dores de cabeça", "dores de cabeca", "cabeça doendo", "cabeca doendo",
           "cabeça latejando", "cabeca latejando", "enxaqueca", "cefaleia", "febre", "febril", "antitérmico",
           "antitermico", "analgésico", "analgesico"]),
    _goal("dor_no_corpo", "Dor no corpo", ["dor_no_corpo", "febre"],
          ["antiinflamatorio", "analgesico_paracetamol"], [],
          ["dor no corpo", "dores no corpo", "dor de corpo", "corpo doendo", "corpo dolorido", "mal estar",
           "mal-estar", "moído", "moido", "anti-inflamatório", "anti inflamatório", "antiinflamatório",
           "anti inflamatorio", "antiinflamatorio"]),
    _goal("dor_muscular", "Dor muscular", ["dor_muscular"],
          ["relaxante_muscular", "dor_topico"], ["antiinflamatorio"],
          ["dor muscular", "dores musculares", "dor nos músculos", "dor nos musculos", "músculo", "musculo",
           "torcicolo", "dor nas costas", "contratura", "contusão", "contusao", "pancada", "relaxante muscular",
           "dor na lombar", "lombar"]),
    _goal("dor_de_barriga", "Dor de barriga e cólica", ["dor_de_barriga", "gases"],
          ["antiespasmodico", "antigases"], [],
          ["dor de barriga", "dores de barriga", "cólica", "colica", "cólicas", "colicas", "cólica menstrual",
           "colica menstrual", "barriga inchada", "barriga estufada", "gases", "estufado", "estufada",
           "antiespasmódico", "antiespasmodico"]),
    _goal("azia", "Azia e má digestão", ["azia"],
          ["antiacido", "protetor_gastrico"], [],
          ["azia", "queimação", "queimacao", "má digestão", "ma digestao", "indigestão", "indigestao", "refluxo",
           "dor de estômago", "dor de estomago", "estômago", "estomago", "antiácido", "antiacido"]),
    _goal("gripe", "Gripe e resfriado", ["gripe", "nariz_entupido", "febre"],
          ["antigripal", "descongestionante_nasal"], ["imunidade"],
          ["gripe", "gripado", "gripada", "resfriado", "resfriada", "resfriado forte", "nariz entupido",
           "congestão nasal", "congestao nasal", "coriza", "nariz escorrendo", "antigripal"]),
    _goal("tosse", "Tosse com catarro", ["tosse"],
          ["expectorante", "pastilha_garganta"], [],
          ["tosse", "tosse com catarro", "catarro", "peito carregado", "xarope", "xarope para tosse", "expectorante"]),
    _goal("tosse_seca", "Tosse seca", ["tosse_seca"],
          ["antitussigeno", "pastilha_garganta"], [],
          ["tosse seca", "tosse irritativa", "tosse sem catarro"]),
    _goal("dor_de_garganta", "Dor de garganta", ["dor_de_garganta"],
          ["pastilha_garganta", "spray_garganta"], [],
          ["dor de garganta", "garganta inflamada", "garganta irritada", "garganta doendo", "garganta",
           "pastilha para garganta", "spray para garganta"]),
    _goal("alergia", "Alergia e rinite", ["alergia"],
          ["antialergico", "descongestionante_nasal"], [],
          ["alergia", "alergias", "rinite", "rinite alérgica", "rinite alergica", "espirro", "espirros",
           "espirrando", "antialérgico", "antialergico", "anti-histamínico", "antihistaminico"]),
    _goal("diarreia", "Diarreia", ["diarreia"],
          ["reidratacao", "probiotico"], ["antidiarreico"],
          ["diarreia", "diarréia", "intestino solto", "desarranjo", "dor de barriga com diarreia", "soro de reidratação",
           "soro de reidratacao", "probiótico", "probiotico", "antidiarreico"]),
    _goal("prisao_de_ventre", "Prisão de ventre", ["prisao_de_ventre"],
          ["laxante", "fibra"], [],
          ["prisão de ventre", "prisao de ventre", "intestino preso", "constipação", "constipacao", "laxante",
           "não consigo ir ao banheiro", "nao consigo ir ao banheiro"]),
    _goal("enjoo", "Enjoo e náusea", ["enjoo"],
          ["antiemetico", "reidratacao"], [],
          ["enjoo", "enjoado", "enjoada", "náusea", "nausea", "náuseas", "nauseas", "vômito", "vomito",
           "vomitando", "ânsia", "ansia", "enjoo de viagem", "enjoo no carro"]),
]

# ------------------------------------------------------------------ produtos
# Tupla no formato do gerador (16 campos) + extras (domain, rx):
# (marca, nome, tipo, etapa, linha, forma, tamanho, peles, preocupações, ingredientes,
#  fps, período, preço_reais, claims, avisos, cobre_etapas_extra, extras)
MED_PRODUCTS: list[tuple] = []
RX = "receita_simples"   # tarja vermelha, venda sob prescrição


def med(lab, name, ptype, step, area, form, size, concerns, ings, price, rx=None, domain="medicamento"):
    warn = ["consultar_se_medicacao"] if domain == "suplemento" else []      # mesmo aviso dos outros suplementos
    MED_PRODUCTS.append((lab, name, ptype, step, "med_" + area, form, size, "T", concerns, ings, None, "dia_noite",
                         price, [], warn, [], {"domain": domain, "rx": rx}))


# Laboratórios fictícios: Vitalis Farma, Farmanorte, Lab Genérico Sul, Lab Nova Via, Lab Aurora.
CAB = ["dor_de_cabeca", "febre"]
med("Vitalis Farma", "Dipirona 500 mg — 10 comprimidos", "dipirona em comprimidos", "analgesico_dipirona", "dor_de_cabeca",
    "box", "10 un", CAB + ["dor_no_corpo"], ["dipirona"], 7.90)
med("Lab Genérico Sul", "Dipirona 1 g (genérico) — 10 comprimidos", "dipirona em comprimidos", "analgesico_dipirona",
    "dor_de_cabeca", "box", "10 un", CAB + ["dor_no_corpo"], ["dipirona"], 11.90)
med("Farmanorte", "Dipirona Gotas 500 mg/mL — 20 mL", "dipirona em gotas", "analgesico_dipirona", "dor_de_cabeca",
    "dropper", "20 ml", CAB, ["dipirona"], 9.90)
med("Vitalis Farma", "Paracetamol 750 mg — 20 comprimidos", "paracetamol em comprimidos", "analgesico_paracetamol",
    "dor_de_cabeca", "box", "20 un", CAB + ["dor_no_corpo"], ["paracetamol"], 12.90)
med("Lab Nova Via", "Paracetamol 500 mg + Cafeína 65 mg — 20 comprimidos", "paracetamol com cafeína",
    "analgesico_paracetamol", "dor_de_cabeca", "box", "20 un", ["dor_de_cabeca", "enxaqueca"],
    ["paracetamol", "cafeina_med"], 19.90)
med("Farmanorte", "Paracetamol Gotas 200 mg/mL — 15 mL", "paracetamol em gotas", "analgesico_paracetamol",
    "dor_de_cabeca", "dropper", "15 ml", CAB, ["paracetamol"], 10.90)
med("Lab Aurora", "Dipirona 300 mg + Isometepteno 30 mg + Cafeína 30 mg — 20 comprimidos", "analgésico para enxaqueca",
    "analgesico_dipirona", "dor_de_cabeca", "box", "20 un", ["dor_de_cabeca", "enxaqueca"],
    ["dipirona", "isometepteno", "cafeina_med"], 24.90)
med("Lab Genérico Sul", "Ácido Acetilsalicílico 500 mg (genérico) — 20 comprimidos", "ácido acetilsalicílico em comprimidos",
    "antiinflamatorio", "dor_de_cabeca", "box", "20 un", CAB + ["dor_no_corpo"], ["acido_acetilsalicilico"], 8.90)

CORPO = ["dor_no_corpo"]
med("Vitalis Farma", "Ibuprofeno 400 mg — 10 cápsulas", "ibuprofeno em cápsulas", "antiinflamatorio", "dor_no_corpo",
    "caps", "10 un", CORPO + ["dor_de_cabeca", "febre", "dor_muscular"], ["ibuprofeno"], 14.90)
med("Lab Genérico Sul", "Ibuprofeno 600 mg (genérico) — 20 comprimidos", "ibuprofeno em comprimidos", "antiinflamatorio",
    "dor_no_corpo", "box", "20 un", CORPO + ["dor_muscular"], ["ibuprofeno"], 18.90, RX)
med("Farmanorte", "Ibuprofeno Gotas 50 mg/mL — 30 mL", "ibuprofeno em gotas", "antiinflamatorio", "dor_no_corpo",
    "dropper", "30 ml", CORPO + ["febre"], ["ibuprofeno"], 16.90)
med("Lab Nova Via", "Naproxeno Sódico 275 mg — 10 comprimidos", "naproxeno em comprimidos", "antiinflamatorio",
    "dor_no_corpo", "box", "10 un", CORPO + ["dor_muscular", "dor_de_cabeca"], ["naproxeno"], 17.90)
med("Lab Genérico Sul", "Naproxeno Sódico 550 mg (genérico) — 10 comprimidos", "naproxeno em comprimidos",
    "antiinflamatorio", "dor_no_corpo", "box", "10 un", CORPO + ["dor_muscular"], ["naproxeno"], 22.90, RX)
med("Lab Aurora", "Diclofenaco Potássico 50 mg — 20 comprimidos", "diclofenaco em comprimidos", "antiinflamatorio",
    "dor_no_corpo", "box", "20 un", CORPO + ["dor_muscular"], ["diclofenaco_potassico"], 21.90, RX)
med("Vitalis Farma", "Nimesulida 100 mg — 12 comprimidos", "nimesulida em comprimidos", "antiinflamatorio",
    "dor_no_corpo", "box", "12 un", CORPO + ["dor_de_garganta"], ["nimesulida"], 12.90, RX)

MUSC = ["dor_muscular"]
med("Vitalis Farma", "Dipirona 300 mg + Orfenadrina 35 mg + Cafeína 50 mg — 10 comprimidos", "relaxante muscular com analgésico",
    "relaxante_muscular", "dor_muscular", "box", "10 un", MUSC + ["dor_no_corpo"],
    ["dipirona", "orfenadrina", "cafeina_med"], 9.90)
med("Vitalis Farma", "Dipirona 300 mg + Orfenadrina 35 mg + Cafeína 50 mg — 36 comprimidos", "relaxante muscular com analgésico",
    "relaxante_muscular", "dor_muscular", "box", "36 un", MUSC + ["dor_no_corpo"],
    ["dipirona", "orfenadrina", "cafeina_med"], 27.90)
med("Lab Genérico Sul", "Ciclobenzaprina 5 mg (genérico) — 30 comprimidos", "ciclobenzaprina em comprimidos",
    "relaxante_muscular", "dor_muscular", "box", "30 un", MUSC, ["ciclobenzaprina"], 24.90, RX)
med("Lab Nova Via", "Ciclobenzaprina 10 mg — 30 comprimidos", "ciclobenzaprina em comprimidos", "relaxante_muscular",
    "dor_muscular", "box", "30 un", MUSC, ["ciclobenzaprina"], 32.90, RX)
med("Lab Aurora", "Diclofenaco Sódico 50 mg + Carisoprodol 125 mg + Paracetamol 300 mg + Cafeína 30 mg — 15 comprimidos",
    "relaxante muscular combinado", "relaxante_muscular", "dor_muscular", "box", "15 un", MUSC + ["dor_no_corpo"],
    ["diclofenaco_sodico", "carisoprodol", "paracetamol", "cafeina_med"], 29.90, RX)
med("Farmanorte", "Diclofenaco Dietilamônio Gel 11,6 mg/g — 60 g", "gel anti-inflamatório", "dor_topico", "dor_muscular",
    "tube", "60 g", MUSC, ["diclofenaco_dietilamonio"], 26.90)
med("Lab Nova Via", "Pomada de Salicilato de Metila, Mentol e Cânfora — 30 g", "pomada para dor muscular", "dor_topico",
    "dor_muscular", "tube", "30 g", MUSC, ["salicilato_metila", "mentol", "canfora"], 14.90)

BAR = ["dor_de_barriga"]
med("Vitalis Farma", "Butilbrometo de Escopolamina 10 mg — 20 drágeas", "escopolamina em drágeas", "antiespasmodico",
    "dor_de_barriga", "box", "20 un", BAR, ["escopolamina"], 16.90)
med("Farmanorte", "Butilbrometo de Escopolamina Gotas 10 mg/mL — 20 mL", "escopolamina em gotas", "antiespasmodico",
    "dor_de_barriga", "dropper", "20 ml", BAR, ["escopolamina"], 18.90)
med("Lab Aurora", "Escopolamina 10 mg + Dipirona 250 mg — 20 comprimidos", "escopolamina com dipirona", "antiespasmodico",
    "dor_de_barriga", "box", "20 un", BAR, ["escopolamina", "dipirona"], 22.90)
med("Lab Genérico Sul", "Simeticona 40 mg (genérico) — 20 comprimidos", "simeticona em comprimidos", "antigases",
    "dor_de_barriga", "box", "20 un", ["gases", "dor_de_barriga"], ["simeticona"], 8.90)
med("Farmanorte", "Simeticona Gotas 75 mg/mL — 15 mL", "simeticona em gotas", "antigases", "dor_de_barriga",
    "dropper", "15 ml", ["gases", "dor_de_barriga"], ["simeticona"], 12.90)
med("Lab Nova Via", "Simeticona 125 mg — 10 cápsulas", "simeticona em cápsulas", "antigases", "dor_de_barriga",
    "caps", "10 un", ["gases", "dor_de_barriga"], ["simeticona"], 14.90)

AZ = ["azia"]
med("Vitalis Farma", "Hidróxido de Alumínio + Hidróxido de Magnésio + Simeticona — suspensão 240 mL", "antiácido em suspensão",
    "antiacido", "azia", "bottle", "240 ml", AZ + ["gases"], ["hidroxido_aluminio", "hidroxido_magnesio", "simeticona"], 24.90)
med("Farmanorte", "Sal de Frutas (Bicarbonato de Sódio + Carbonato de Sódio + Ácido Cítrico) — 2 envelopes de 5 g",
    "antiácido efervescente", "antiacido", "azia", "powder", "10 g", AZ,
    ["bicarbonato_sodio", "carbonato_sodio", "acido_citrico"], 4.90)
med("Lab Nova Via", "Alginato de Sódio + Bicarbonato de Sódio — 12 sachês de suspensão", "antiácido para refluxo",
    "antiacido", "azia", "powder", "12 un", AZ, ["alginato_sodio", "bicarbonato_sodio"], 29.90)
med("Lab Genérico Sul", "Omeprazol 20 mg (genérico) — 28 cápsulas", "omeprazol em cápsulas", "protetor_gastrico", "azia",
    "caps", "28 un", AZ, ["omeprazol"], 15.90, RX)
med("Lab Aurora", "Pantoprazol 40 mg — 28 comprimidos", "pantoprazol em comprimidos", "protetor_gastrico", "azia",
    "box", "28 un", AZ, ["pantoprazol"], 39.90, RX)
med("Vitalis Farma", "Esomeprazol 40 mg — 28 comprimidos", "esomeprazol em comprimidos", "protetor_gastrico", "azia",
    "box", "28 un", AZ, ["esomeprazol"], 54.90, RX)

GR = ["gripe"]
med("Vitalis Farma", "Antigripal Paracetamol 400 mg + Fenilefrina 4 mg + Clorfeniramina 4 mg — 20 comprimidos",
    "antigripal em comprimidos", "antigripal", "gripe", "box", "20 un", GR + ["nariz_entupido", "febre"],
    ["paracetamol", "fenilefrina", "clorfeniramina"], 17.90)
med("Lab Nova Via", "Antigripal Dipirona 500 mg + Clorfeniramina 2 mg + Cafeína 30 mg — 20 cápsulas",
    "antigripal em cápsulas", "antigripal", "gripe", "caps", "20 un", GR + ["febre"],
    ["dipirona", "clorfeniramina", "cafeina_med"], 15.90)
med("Farmanorte", "Vitamina C 1 g Efervescente — 10 comprimidos", "vitamina C efervescente", "imunidade", "gripe",
    "box", "10 un", GR, ["acido_ascorbico"], 13.90, domain="suplemento")      # suplemento (#40): etapa opcional do kit de suplementos
med("Lab Genérico Sul", "Soro Fisiológico Nasal 0,9% — 30 mL", "solução nasal de cloreto de sódio", "descongestionante_nasal",
    "gripe", "dropper", "30 ml", GR + ["nariz_entupido", "alergia"], ["cloreto_sodio"], 6.90)
med("Vitalis Farma", "Nafazolina 0,5 mg/mL Solução Nasal — 30 mL", "descongestionante nasal em gotas",
    "descongestionante_nasal", "gripe", "dropper", "30 ml", GR + ["nariz_entupido"], ["nafazolina"], 7.90)
med("Lab Aurora", "Oximetazolina 0,5 mg/mL Spray Nasal — 20 mL", "descongestionante nasal em spray",
    "descongestionante_nasal", "gripe", "spray", "20 ml", GR + ["nariz_entupido"], ["oximetazolina"], 24.90)

TS = ["tosse"]
med("Vitalis Farma", "Ambroxol Xarope Adulto 30 mg/5 mL — 120 mL", "xarope expectorante", "expectorante", "tosse",
    "bottle", "120 ml", TS, ["ambroxol"], 16.90)
med("Lab Aurora", "Acetilcisteína 600 mg — 16 envelopes", "expectorante em envelopes", "expectorante", "tosse",
    "powder", "16 un", TS, ["acetilcisteina"], 44.90)
med("Farmanorte", "Bromexina Xarope Adulto 8 mg/5 mL — 120 mL", "xarope expectorante", "expectorante", "tosse",
    "bottle", "120 ml", TS, ["bromexina"], 18.90)
med("Lab Genérico Sul", "Carbocisteína Xarope Adulto 50 mg/mL (genérico) — 100 mL", "xarope expectorante", "expectorante",
    "tosse", "bottle", "100 ml", TS, ["carbocisteina"], 14.90)
med("Lab Nova Via", "Xarope de Guaco — 120 mL", "xarope fitoterápico", "expectorante", "tosse", "bottle", "120 ml",
    TS, ["guaco"], 12.90)
med("Vitalis Farma", "Dropropizina Xarope Adulto 3 mg/mL — 120 mL", "xarope para tosse seca", "antitussigeno", "tosse",
    "bottle", "120 ml", ["tosse_seca"], ["dropropizina"], 17.90)
med("Lab Aurora", "Levodropropizina Xarope 6 mg/mL — 120 mL", "xarope para tosse seca", "antitussigeno", "tosse",
    "bottle", "120 ml", ["tosse_seca"], ["levodropropizina"], 38.90, RX)

GAR = ["dor_de_garganta"]
med("Vitalis Farma", "Pastilhas Amilmetacresol + Álcool Diclorobenzílico Mel e Limão — 8 pastilhas",
    "pastilha antisséptica", "pastilha_garganta", "dor_de_garganta", "box", "8 un", GAR + ["tosse", "tosse_seca"],
    ["amilmetacresol"], 13.90)
med("Farmanorte", "Pastilhas Amilmetacresol + Álcool Diclorobenzílico Menta — 8 pastilhas", "pastilha antisséptica",
    "pastilha_garganta", "dor_de_garganta", "box", "8 un", GAR + ["tosse", "tosse_seca"], ["amilmetacresol"], 12.90)
med("Lab Aurora", "Flurbiprofeno 8,75 mg — 16 pastilhas", "pastilha anti-inflamatória", "pastilha_garganta",
    "dor_de_garganta", "box", "16 un", GAR, ["flurbiprofeno"], 29.90)
med("Lab Nova Via", "Benzidamina 3 mg — 12 pastilhas", "pastilha anti-inflamatória", "pastilha_garganta",
    "dor_de_garganta", "box", "12 un", GAR, ["benzidamina"], 19.90)
med("Vitalis Farma", "Benzidamina Spray 1,5 mg/mL — 30 mL", "spray para garganta", "spray_garganta", "dor_de_garganta",
    "spray", "30 ml", GAR, ["benzidamina"], 24.90)
med("Lab Genérico Sul", "Benzidamina Colutório 1,5 mg/mL (genérico) — 250 mL", "gargarejo para garganta", "spray_garganta",
    "dor_de_garganta", "bottle", "250 ml", GAR, ["benzidamina"], 21.90)

AL = ["alergia"]
med("Vitalis Farma", "Loratadina 10 mg — 12 comprimidos", "loratadina em comprimidos", "antialergico", "alergia",
    "box", "12 un", AL, ["loratadina"], 9.90)
med("Farmanorte", "Loratadina Xarope 1 mg/mL — 100 mL", "loratadina em xarope", "antialergico", "alergia", "bottle",
    "100 ml", AL, ["loratadina"], 14.90)
med("Lab Aurora", "Desloratadina 5 mg — 10 comprimidos", "desloratadina em comprimidos", "antialergico", "alergia",
    "box", "10 un", AL, ["desloratadina"], 27.90, RX)
med("Lab Genérico Sul", "Cetirizina 10 mg (genérico) — 10 comprimidos", "cetirizina em comprimidos", "antialergico",
    "alergia", "box", "10 un", AL, ["cetirizina"], 12.90, RX)
med("Lab Nova Via", "Fexofenadina 180 mg — 10 comprimidos", "fexofenadina em comprimidos", "antialergico", "alergia",
    "box", "10 un", AL, ["fexofenadina"], 34.90, RX)
med("Vitalis Farma", "Dexclorfeniramina 2 mg — 20 comprimidos", "dexclorfeniramina em comprimidos", "antialergico",
    "alergia", "box", "20 un", AL, ["dexclorfeniramina"], 11.90, RX)

DI = ["diarreia"]
med("Vitalis Farma", "Loperamida 2 mg — 12 comprimidos", "loperamida em comprimidos", "antidiarreico", "diarreia",
    "box", "12 un", DI, ["loperamida"], 11.90)
med("Lab Aurora", "Racecadotrila 100 mg — 9 cápsulas", "racecadotrila em cápsulas", "antidiarreico", "diarreia",
    "caps", "9 un", DI, ["racecadotrila"], 39.90, RX)
med("Lab Nova Via", "Nitazoxanida 500 mg — 6 comprimidos", "nitazoxanida em comprimidos", "antidiarreico", "diarreia",
    "box", "6 un", DI, ["nitazoxanida"], 42.90, RX)
med("Farmanorte", "Saccharomyces boulardii 200 mg — 12 cápsulas", "probiótico em cápsulas", "probiotico", "diarreia",
    "caps", "12 un", DI, ["saccharomyces_boulardii"], 34.90)
med("Vitalis Farma", "Bacillus clausii 2 bilhões — 5 flaconetes de 5 mL", "probiótico em flaconetes", "probiotico",
    "diarreia", "bottle", "25 ml", DI, ["bacillus_clausii"], 39.90)
med("Lab Genérico Sul", "Sais para Reidratação Oral — envelope 27,9 g", "soro de reidratação oral", "reidratacao",
    "diarreia", "powder", "27.9 g", DI + ["enjoo"], ["sais_reidratacao"], 3.90)
med("Farmanorte", "Soro de Reidratação Oral Pronto Sabor Coco — 500 mL", "soro de reidratação pronto", "reidratacao",
    "diarreia", "bottle", "500 ml", DI + ["enjoo"], ["sais_reidratacao"], 9.90)

PV = ["prisao_de_ventre"]
med("Vitalis Farma", "Bisacodil 5 mg — 20 drágeas", "laxante em drágeas", "laxante", "prisao_de_ventre", "box", "20 un",
    PV, ["bisacodil"], 12.90)
med("Lab Aurora", "Picossulfato de Sódio Gotas 7,5 mg/mL — 20 mL", "laxante em gotas", "laxante", "prisao_de_ventre",
    "dropper", "20 ml", PV, ["picossulfato"], 19.90)
med("Lab Genérico Sul", "Lactulose Xarope 667 mg/mL (genérico) — 120 mL", "laxante em xarope", "laxante",
    "prisao_de_ventre", "bottle", "120 ml", PV, ["lactulose"], 21.90)
med("Farmanorte", "Leite de Magnésia (Hidróxido de Magnésio) — suspensão 120 mL", "laxante em suspensão", "laxante",
    "prisao_de_ventre", "bottle", "120 ml", PV + ["azia"], ["hidroxido_magnesio"], 13.90)
med("Lab Nova Via", "Macrogol 3350 Pó para Solução Oral — 10 sachês", "laxante em pó", "laxante", "prisao_de_ventre",
    "powder", "10 un", PV, ["macrogol"], 34.90)
med("Vitalis Farma", "Psyllium (Plantago ovata) Pó — 10 sachês", "fibra em pó", "fibra", "prisao_de_ventre", "powder",
    "10 un", PV, ["psyllium"], 29.90, domain="suplemento")
med("Farmanorte", "Psyllium (Plantago ovata) Pó — 30 sachês", "fibra em pó", "fibra", "prisao_de_ventre", "powder",
    "30 un", PV, ["psyllium"], 69.90, domain="suplemento")

EN = ["enjoo"]
med("Vitalis Farma", "Dimenidrinato 100 mg — 10 comprimidos", "dimenidrinato em comprimidos", "antiemetico", "enjoo",
    "box", "10 un", EN, ["dimenidrinato"], 14.90)
med("Lab Aurora", "Dimenidrinato 50 mg + Piridoxina 10 mg — 10 comprimidos", "dimenidrinato com vitamina B6",
    "antiemetico", "enjoo", "box", "10 un", EN, ["dimenidrinato", "piridoxina"], 16.90)
med("Farmanorte", "Dimenidrinato Gotas 25 mg/mL — 20 mL", "dimenidrinato em gotas", "antiemetico", "enjoo", "dropper",
    "20 ml", EN, ["dimenidrinato"], 15.90)
med("Lab Genérico Sul", "Ondansetrona 4 mg (genérico) — 10 comprimidos orodispersíveis", "ondansetrona em comprimidos",
    "antiemetico", "enjoo", "box", "10 un", EN, ["ondansetrona"], 24.90, RX)
med("Lab Nova Via", "Metoclopramida 10 mg — 20 comprimidos", "metoclopramida em comprimidos", "antiemetico", "enjoo",
    "box", "20 un", EN, ["metoclopramida"], 8.90, RX)
med("Vitalis Farma", "Domperidona 10 mg — 30 comprimidos", "domperidona em comprimidos", "antiemetico", "enjoo", "box",
    "30 un", EN + ["azia"], ["domperidona"], 19.90, RX)

MED_HOW_TO = {s: "Siga as instruções da bula." for s in MED_STEPS}
# vitamina C efervescente e psyllium viraram suplemento (#40): modo de uso de suplemento, não de bula
MED_HOW_TO.update({"imunidade": "Dissolva 1 comprimido em um copo de água, conforme a embalagem.",
                   "fibra": "Misture 1 sachê em um copo de água e beba em seguida, conforme a embalagem."})
