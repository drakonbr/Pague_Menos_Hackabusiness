"""Léxico escrito à mão: como as pessoas falam -> conceitos do grafo (preocupação, tipo de pele, preferência,
ingrediente, etapa). É conhecimento de domínio do projeto, não vem de modelo nem de dado real.

Duas funções:
  1. entrada do entendimento de frases (graphrag/nlu.py);
  2. fonte de frases para o treino dos vetores de palavras (graphrag/embed.py), para que gírias e variações
     fiquem perto do conceito certo no espaço vetorial.
"""
from __future__ import annotations

import re

# ----------------------------------------------------------------- preocupações (id do catálogo -> falas)
CONCERN_ALIASES: dict[str, list[str]] = {
    "acne": ["acne", "espinha", "espinhas", "cravo", "cravos", "acneica", "acneico", "pele com espinha", "espremi cravo", "espremer cravo", "muita espinha", "tem espinha", "espinha na cara", "problema de acne", "cravo no nariz",
             "pele cheia de espinhas", "pele com acne", "marquinhas de espinha",
                    "carocinhos no rosto", "bolinhas no rosto", "bolinhas na cara", "pele cheia de carocinhos", "carocinhos na testa", "carocinhos no queixo", "carocinhos na cara"],
    "oleosidade": ["oleosa", "oleosas", "oleosidade", "brilho", "brilha", "brilhando", "brilhosa", "pele brilhosa",
                   "pele que brilha", "engordurada", "gordurosa", "pele oleosa", "brilho a tarde", "excesso de brilho", "rosto brilhando", "brilhar", "nao brilhar", "tao oleoso", "oleoso", "brilho do nariz", "brilho no nariz", "brilho na testa", "pele gordurosa"],
    "poros": ["poro", "poros", "poros dilatados", "poros abertos", "poros visiveis"],
    "manchas": ["mancha", "manchas", "manchinha", "manchinhas", "pele manchada", "escurecimento", "tom desigual",
                "uniformizar", "uniformizador", "clarear", "clareador", "pos acne", "marcas de espinha",
                "manchas escuras", "manchas de sol", "clarear marquinhas", "marquinhas", "marcas de cravo", "tirar manchas", "tirar as manchas", "marcas escuras", "marcas de acne",
                "marcas da acne", "manchas de acne", "manchas da acne", "cicatriz de espinha", "marquinhas escuras"],
    "sinais_idade": ["ruga", "rugas", "linha de expressao", "linhas de expressao", "pes de galinha", "anti idade",
                     "antiidade", "anti-idade", "antissinais", "antisinais", "envelhecimento", "envelhecer", "flacidez",
                     "firmeza", "rejuvenescer", "pele madura", "viço", "vico", "pele com vico", "pele sem vico", "cara de cansada", "pele com cara de cansada", "pele apagada", "pele sem brilho", "pele opaca", "sinais da idade", "sinais de idade", "pele cansada", "linhas do rosto", "linhas finas", "diminuir linhas", "linhas no rosto", "linha de expressao", "enrugada", "pele enrugada", "marcas de expressao", "pele flacida",
                     "rotina anti idade",
                    "pele caida", "flacida", "pele flacida", "depois dos 40", "depois dos 50", "depois dos 30", "passou dos 40", "pele sem vida", "pele sem viço", "sem viço", "sem vico"],
    "olheiras": ["olheira", "olheiras", "olhos cansados", "area dos olhos", "contorno dos olhos", "bolsa nos olhos"],
    "ressecamento": ["seca", "secas", "ressecada", "ressecado", "ressecamento", "pele repuxando", "repuxa", "hidratar",
                     "hidratacao", "hidratante", "pele seca", "desidratada", "descama", "descamando", "descamacao", "pele descama", "pele ressecada", "pele craquelada", "pele esticando",
                    "descasca", "descascando", "pele descascando", "pele descasca", "pele puxando", "pele repuxando no inverno", "pele estalando"],
    "sensibilidade": ["sensivel", "sensiveis", "pele sensivel", "reativa", "pele reativa", "irritada facilmente",
                      "pele delicada", "irrita", "irritacao", "irritada", "irritado", "irritam", "arde", "ardendo", "ardencia",
                      "vermelhidao", "vermelha", "coceira", "pele que irrita", "irrita com tudo", "alergia na pele",
                    "bochechas vermelhas", "vermelhidao nas bochechas", "qualquer coisa irrita", "qualquer cosmetico", "reage a tudo", "pele reage", "pele que reage", "irrita com qualquer coisa", "coça com qualquer"],
    "fotoprotecao": ["protetor", "protetor solar", "filtro solar", "bloqueador", "fps", "praia", "piscina", "sol",
                     "proteger do sol", "proteger da luz", "protecao solar", "protecao uv",
                    "branquinha"],
    "limpeza_diaria": ["limpar", "limpeza", "lavar o rosto", "sabonete facial", "gel de limpeza", "limpeza facial"],
    "textura": ["textura", "pele aspera", "aspereza", "pele lisa", "pele lisinha", "lisinha", "pele macia", "pele aveludada", "esfoliar", "esfoliante", "renovar a pele",
                    "pele irregular", "pele craquelada"],
    "desmaquilagem": ["demaquilar", "desmaquilante", "tirar maquiagem", "remover maquiagem", "agua micelar",
                    "demaquilante", "dupla limpeza", "tirar a maquiagem", "tirar a make"],
    "nutricao": ["suplemento", "suplementos", "vitamina", "vitaminas", "nutricao", "bem estar", "omega", "omega 3",
                 "magnesio", "vitamina d", "multivitaminico",
                 # fala do dia a dia (#62): cansaço e falta de ânimo levam a suplementos
                 "sem animo", "desanimo", "desanimada", "desanimado", "cansaco", "fadiga", "sem disposicao", "sem pique",
                    "falta de vitamina", "falta de vitaminas", "deficiencia de vitamina"],
    "beleza_interna": ["colageno", "colageno hidrolisado", "beleza de dentro", "beleza de dentro para fora",
                    "unhas fracas", "unha fraca", "unhas quebradicas"],
    "higiene_diaria": ["higiene", "higiene pessoal", "banho", "higiene premium"],
    "cuidado_cabelo": ["cabelo", "cabelos", "shampoo", "xampu", "condicionador", "mascara capilar", "capilar",
                       "cabelo seco", "fios"],
    "higiene_oral": ["dente", "dentes", "creme dental", "pasta de dente", "enxaguante", "bucal", "boca", "escovar os dentes"],
    "cuidado_corporal": ["corpo", "corporal", "sabonete corporal", "gel de banho", "esfoliante corporal", "banho"],
    "desodorizacao": ["desodorante", "antitranspirante", "axila", "cheiro de suor"],
    # ---- saúde (doc 16): o objetivo vem dos sinônimos em goals.json; aqui, a preocupação específica
    "dor_de_cabeca": ["dor de cabeca", "dores de cabeca", "cabeca doendo", "cabeca latejando", "cefaleia",
                    "pontada na cabeca", "cabeca pesada", "cabeca martelando", "cabeca pulsando"],
    "enxaqueca": ["enxaqueca", "enxaquecas", "crise de enxaqueca"],
    "febre": ["febre", "febril", "temperatura alta", "estou quente", "antitermico"],
    "dor_no_corpo": ["dor no corpo", "dores no corpo", "corpo doendo", "corpo dolorido", "mal estar", "moido"],
    "dor_muscular": ["dor muscular", "dores musculares", "torcicolo", "dor nas costas", "contratura", "lombar", "contusao", "pancada",
                    "dor no joelho", "dor nos joelhos", "dor na coluna", "dor no ombro", "dor nos ombros", "dor no braco", "dor na perna", "dor nas pernas", "dor nas juntas", "dor nas articulacoes", "dor no quadril", "dor no tornozelo", "dor no pescoco", "dor no cotovelo", "dor no punho", "dor no pulso"],
    "dor_de_barriga": ["dor de barriga", "colica", "colicas", "colica menstrual", "barriga doendo"],
    "gases": ["gases", "barriga inchada", "barriga estufada", "estufado", "estufada", "flatulencia"],
    "azia": ["azia", "queimacao", "ma digestao", "indigestao", "refluxo", "dor de estomago",
                    "dor no estomago", "estomago doendo", "queimacao no estomago"],
    "gripe": ["gripe", "gripado", "gripada", "resfriado", "resfriada"],
    "nariz_entupido": ["nariz entupido", "congestao nasal", "coriza", "nariz escorrendo", "sinusite", "fanho", "fanha", "voz fanha"],
    "tosse": ["tosse", "tosse com catarro", "catarro", "peito carregado"],
    "tosse_seca": ["tosse seca", "tosse irritativa", "tosse sem catarro",
                    "tosse que nao sai nada", "tossindo seco"],
    "dor_de_garganta": ["dor de garganta", "garganta inflamada", "garganta irritada", "garganta doendo"],
    "alergia": ["alergia", "alergias", "rinite", "rinite alergica", "espirro", "espirros", "espirrando",
                    "coceira depois de comer", "coceira apos comer",
                    "coca muito depois"],
    "diarreia": ["diarreia", "intestino solto", "desarranjo",
                    "soltinho", "barriga solta", "caganeira", "disenteria", "desarranjo intestinal", "toda hora no banheiro", "correndo pro banheiro"],
    "prisao_de_ventre": ["prisao de ventre", "intestino preso", "constipacao", "constipada", "constipado"],
    "enjoo": ["enjoo", "enjoado", "enjoada", "nausea", "nauseas", "vomito", "vomitando", "ansia de vomito"],
    "hipertensao": ["pressao alta", "hipertensao", "remedio de pressao", "remedio para pressao"],
    "colesterol": ["colesterol", "colesterol alto", "remedio de colesterol"],
}


# Fala do dia a dia (#62). A palavra solta ("travado", "tapado") serve a assuntos demais ("poros tapados", "pia tapada"), e
# ensiná-la ao vocabulário a faz parecer palavra de nariz na busca por semelhança. Então não entra como alias: canon_state REESCREVE
# "parte do corpo + até 2 palavras quaisquer + estado" para um jeito que o grafo já entende, antes de qualquer outra etapa.
_BODY = ("ombro", "ombros", "pescoco", "costas", "coluna", "joelho", "joelhos", "mandibula", "braco", "bracos", "perna", "pernas",
         "mao", "maos", "pe", "pes", "quadril", "punho", "pulso", "cotovelo", "tornozelo", "nuca", "lombar")
STATE_WORDS = frozenset(_BODY) | {"intestino", "barriga", "nariz", "cabeca"}   # entendidas pela regra abaixo, mesmo sem estar no vocabulário
_GUT = ("intestino", "barriga")
_STATE_RULES = [  # (partes, estados, reescrita)
    (_BODY, ("travado", "travada", "travados", "travadas", "travou", "duro", "dura"), "{p} dor muscular"),
    (_GUT, ("travado", "travada", "trancado", "trancada"), "intestino preso"),
    (("nariz",), ("tapado", "tapada", "congestionado", "congestionada"), "nariz entupido"),
    (("nariz",), ("escorrendo", "pingando", "escorre", "correndo"), "nariz escorrendo"),
    (("cabeca",), ("latejando", "latejante", "pesada", "martelando", "pulsando", "pulsante"), "dor de cabeca"),
    (("barriga",), ("solta", "soltinha"), "diarreia"),
    (("perna", "pernas", "pe", "pes"), ("inchada", "inchadas", "inchado", "inchados"), "pernas inchadas"),   # #65: circulação, fora do catálogo
]
_STATE_RES = [(re.compile(r"\b(%s)\s+((?:[a-z]+\s+){0,2}?)(?:%s)\b" % ("|".join(p), "|".join(st))), out) for p, st, out in _STATE_RULES]
_NEG = frozenset("nao nem sem nunca jamais".split())


def canon_state(text: str) -> str:
    """"meu ombro tá bem travado" -> "meu ombro dor muscular"; "nariz meio tapado" -> "nariz entupido"."""
    text = re.sub(r"\s+", " ", re.sub(r"[,;]+", " ", text))
    for rx, out in _STATE_RES:
        # com "não", "sem", "nem" no meio a pessoa diz o contrário ("meu nariz não está tapado"): não reescreve
        text = rx.sub(lambda m, out=out: m.group(0) if _NEG & set(m.group(2).split()) else out.format(p=m.group(1)), text)
    return text

# ----------------------------------------------------------------- tipos de pele
SKIN_ALIASES: dict[str, list[str]] = {
    "oleosa": ["oleosa", "oleosas", "oleosidade", "brilha", "brilhosa", "engordurada", "gordurosa"],
    "mista": ["mista", "mistas", "zona t", "oleosa no meio e seca nas bochechas"],
    "seca": ["seca", "secas", "ressecada", "repuxando", "desidratada"],
    "normal": ["normal", "pele normal", "equilibrada"],
    "sensível": ["sensivel", "sensiveis", "reativa", "delicada"],
}

# ----------------------------------------------------------------- preferências (-> claim do catálogo)
PREFERENCE_ALIASES: dict[str, list[str]] = {
    "vegano": ["vegano", "vegana", "veganos", "veganas", "sem origem animal", "100 vegano", "cruelty free vegano"],
    "sem fragrância": ["sem fragrancia", "sem perfume", "sem cheiro", "sem aroma", "sem essencia", "nao perfumado"],
    "sem álcool": ["sem alcool", "livre de alcool", "alcool free"],
    "oil free": ["oil free", "oilfree", "sem oleo", "livre de oleo", "sem oleosidade extra"],
    "filtro mineral": ["mineral", "filtro mineral", "filtro fisico", "protetor mineral", "protetor fisico"],
    "com cor": ["com cor", "colorido", "base", "tom de pele", "com tonalidade"],
    "toque seco": ["toque seco", "acabamento seco", "nao deixa oleoso", "matte", "matificante", "fosco"],
    "não comedogênico": ["nao comedogenico", "nao entope poros", "nao tapa poros"],
    "resistente à água": ["resistente a agua", "a prova dagua", "a prova d agua", "resiste a agua"],
    "sem parabenos": ["sem parabeno", "sem parabenos", "livre de parabenos"],
    "sem sulfato": ["sem sulfato", "livre de sulfato"],
    "sem alumínio": ["sem aluminio", "livre de aluminio"],
    "sem glúten": ["sem gluten", "livre de gluten"],
    "sem açúcar": ["sem acucar", "zero acucar"],
}

# ----------------------------------------------------------------- ingredientes pedidos (apelidos)
INGREDIENT_ALIASES: dict[str, list[str]] = {
    "retinol": ["retinol", "retinoide", "vitamina a"],
    "vitamina_c": ["vitamina c", "vit c", "acido ascorbico"],
    "acido_hialuronico": ["acido hialuronico", "hialuronico", "hialuronato"],
    "niacinamida": ["niacinamida", "vitamina b3"],
    "acido_salicilico": ["acido salicilico", "salicilico", "bha"],
    "acido_glicolico": ["acido glicolico", "glicolico", "aha"],
    "acido_mandelico": ["acido mandelico", "mandelico"],
    "acido_azelaico": ["acido azelaico", "azelaico"],
    "acido_tranexamico": ["acido tranexamico", "tranexamico"],
    "ceramidas": ["ceramida", "ceramidas"],
    "peptideos": ["peptideo", "peptideos"],
    "bakuchiol": ["bakuchiol"],
    "cafeina": ["cafeina"],
    "omega3_epa_dha": ["omega 3", "omega3", "epa", "dha", "oleo de peixe"],
    "omega3_algas": ["omega vegano", "omega de algas", "omega 3 vegano"],
    "colageno_hidrolisado": ["colageno", "colageno hidrolisado"],
    "magnesio_dimalato": ["magnesio dimalato", "dimalato"],
    "magnesio_bisglicinato": ["magnesio bisglicinato", "bisglicinato"],
    "magnesio_citrato": ["citrato de magnesio", "magnesio citrato"],
    "vitamina_d3": ["vitamina d", "vitamina d3", "d3"],
    "vitamina_k2": ["vitamina k", "k2"],
    "queratina": ["queratina"],
    "oleo_argan": ["argan", "oleo de argan"],
    "fluoreto": ["fluor", "fluoreto"],
    # ---- princípios ativos de medicamentos (doc 16) e nomes populares com que as pessoas pedem
    "dipirona": ["dipirona", "dipirona sodica", "dipirona monoidratada", "metamizol", "novalgina"],
    "paracetamol": ["paracetamol", "acetaminofeno", "tylenol"],
    "acido_acetilsalicilico": ["acido acetilsalicilico", "aas", "aspirina"],
    "isometepteno": ["isometepteno", "neosaldina"],
    "ibuprofeno": ["ibuprofeno", "advil", "alivium"],
    "naproxeno": ["naproxeno", "flanax"],
    "diclofenaco_potassico": ["diclofenaco potassico", "cataflam"],
    "diclofenaco_dietilamonio": ["diclofenaco gel", "diclofenaco dietilamonio", "gel de diclofenaco"],
    "nimesulida": ["nimesulida"],
    "orfenadrina": ["orfenadrina", "dorflex"],
    "ciclobenzaprina": ["ciclobenzaprina"],
    "carisoprodol": ["carisoprodol", "tandrilax"],
    "salicilato_metila": ["salicilato de metila", "gelol"],
    "escopolamina": ["escopolamina", "butilbrometo de escopolamina", "buscopan"],
    "simeticona": ["simeticona", "luftal"],
    "omeprazol": ["omeprazol"],
    "pantoprazol": ["pantoprazol"],
    "esomeprazol": ["esomeprazol"],
    "alginato_sodio": ["alginato", "gaviscon"],
    "bicarbonato_sodio": ["sal de frutas", "sal de fruta", "bicarbonato"],
    "fenilefrina": ["fenilefrina", "cimegripe"],
    "clorfeniramina": ["clorfeniramina", "benegrip"],
    "acido_ascorbico": ["vitamina c efervescente", "redoxon", "cewin"],
    "cloreto_sodio": ["soro fisiologico", "soro nasal"],
    "nafazolina": ["nafazolina", "sorine", "neosoro"],
    "oximetazolina": ["oximetazolina", "afrin"],
    "ambroxol": ["ambroxol", "mucosolvan"],
    "acetilcisteina": ["acetilcisteina", "fluimucil"],
    "bromexina": ["bromexina", "bisolvon"],
    "carbocisteina": ["carbocisteina", "mucofan"],
    "guaco": ["guaco", "xarope de guaco"],
    "dropropizina": ["dropropizina", "vibral"],
    "levodropropizina": ["levodropropizina", "antux"],
    "amilmetacresol": ["amilmetacresol", "strepsils"],
    "flurbiprofeno": ["flurbiprofeno"],
    "benzidamina": ["benzidamina", "ciflogex"],
    "loratadina": ["loratadina", "claritin"],
    "desloratadina": ["desloratadina", "desalex"],
    "cetirizina": ["cetirizina", "zyrtec"],
    "fexofenadina": ["fexofenadina", "allegra"],
    "dexclorfeniramina": ["dexclorfeniramina", "polaramine"],
    "loperamida": ["loperamida", "imosec"],
    "racecadotrila": ["racecadotrila", "tiorfan"],
    "nitazoxanida": ["nitazoxanida", "annita"],
    "saccharomyces_boulardii": ["saccharomyces", "floratil"],
    "bacillus_clausii": ["bacillus clausii", "enterogermina"],
    "sais_reidratacao": ["soro de reidratacao", "sais de reidratacao", "soro caseiro", "pedialyte"],
    "bisacodil": ["bisacodil", "dulcolax"],
    "picossulfato": ["picossulfato", "guttalax"],
    "lactulose": ["lactulose"],
    "hidroxido_magnesio": ["leite de magnesia", "hidroxido de magnesio"],
    "macrogol": ["macrogol", "muvinlax"],
    "psyllium": ["psyllium", "plantago", "metamucil"],
    "dimenidrinato": ["dimenidrinato", "dramin"],
    "ondansetrona": ["ondansetrona", "vonau"],
    "metoclopramida": ["metoclopramida", "plasil"],
    "domperidona": ["domperidona", "motilium"],
}

# ----------------------------------------------------------------- categoria de produto -> etapa
# (regex sobre texto normalizado, etapa). Ordem importa: o primeiro que casa vence.
STEP_PATTERNS: list[tuple[str, str]] = [
    (r"\b(omega|oleo de peixe)\b", "omega3"),
    (r"\bcolageno\b", "colageno"),
    (r"\bmagnesio\b", "magnesio"),
    (r"\b(vitamina d|vitamina k|multivitaminico|multi vitaminico|vitaminas)\b", "vitaminas"),
    (r"\b(shampoo|xampu|condicionador|mascara capilar|capilar)\b", "higiene_cabelo"),
    (r"\b(creme dental|pasta de dente|enxaguante|bucal|escova de dente)\b", "higiene_oral"),
    (r"\b(desodorante|antitranspirante)\b", "desodorante"),
    (r"\b(sabonete corporal|sabonete liquido corporal|gel de banho|esfoliante corporal|banho)\b", "higiene_corpo"),
    (r"\b(protetor|filtro|bloqueador)\b.*\b(corpo|corporal)\b|\b(corpo|corporal)\b.*\b(protetor|filtro|bloqueador)\b", "protecao_corporal"),
    (r"\b(protetor labial|labial|balsamo|olhos|olheira|olheiras|contorno)\b", "complemento"),
    (r"\b(protetor|filtro solar|bloqueador|fps)\b", "protecao_solar"),
    (r"\b(hidratante|hidratacao|creme hidratante|gel hidratante|hidratar)\b", "hidratacao"),
    (r"\b(serum|serums|tratamento|retinol|vitamina c|niacinamida|adesivo|gel secativo|secativo|antiacne|anti acne|creme noturno)\b", "tratamento"),
    (r"\b(tonico|esfoliante|mascara|argila)\b", "preparo"),
    (r"\b(sabonete|gel de limpeza|espuma de limpeza|limpeza|micelar|demaquilante|limpar)\b", "limpeza"),
]

# palavras que indicam que a pessoa quer UM TIPO de produto (lista), não um kit
SINGLE_PRODUCT_CUES = ["so o", "somente o", "apenas o", "so a", "somente a", "apenas a", "um ", "uma ", "tem ",
                       "mostra", "mostrar", "me mostra", "quais", "lista"]

# ----------------------------------------------------------------- frases extras para o treino dos vetores
# Cada linha liga falas do dia a dia aos conceitos do catálogo. Quanto mais variado, melhor o espaço.
PARAPHRASE_CORPUS: list[str] = [
    "pele que brilha no meio do dia e fica oleosa precisa de controle de oleosidade e poros menos visiveis",
    "tenho pele brilhosa e cheia de cravos nos poros quero um gel de limpeza e sabonete oil free",
    "espinhas e cravos acne pele acneica precisa limpeza secativo salicilico hidratante oil free",
    "marquinhas escuras que ficaram da espinha manchas pos acne uniformizar o tom vitamina c acido tranexamico niacinamida",
    "manchas de sol manchas escuras clareador uniformizador serum vitamina c e protetor solar todos os dias",
    "rugas linhas de expressao pes de galinha pele madura firmeza retinol peptideos antissinais creme noturno",
    "rotina anti idade completa limpeza serum antioxidante hidratante firmador protetor solar fps",
    "pele cansada com sinais de idade sérum vitamina c peptideos ceramidas acido hialuronico creme para a noite",
    "olheiras e olhos cansados creme para a area dos olhos cafeina peptideos contorno dos olhos",
    "pele seca que repuxa precisa de hidratacao creme nutritivo ceramidas karite acido hialuronico",
    "pele sensivel e reativa irrita facil produtos sem fragrancia calmantes centella alantoina",
    "protetor solar para o rosto todos os dias fps 50 toque seco fluido ultraleve sem deixar oleoso",
    "protetor solar para o corpo praia piscina resistente a agua fps 50 spray",
    "filtro solar mineral oxido de zinco dioxido de titanio para pele sensivel",
    "quero comecar a cuidar da pele rotina basica limpeza hidratante e protetor solar simples e barato",
    "skin care iniciante kit economico sabonete facial hidratante protetor",
    "retinol a noite vitamina c de manha nao usar juntos separar periodos acido glicolico evitar",
    "suplemento de omega 3 epa dha capsulas todos os dias junto com refeicao",
    "omega 3 vegano de algas para quem nao come peixe",
    "colageno hidrolisado em po ou capsulas beleza de dentro para fora pele cabelo unhas",
    "magnesio dimalato bisglicinato citrato capsulas ou po para a noite",
    "vitamina d3 e k2 suplemento multivitaminico mulher 45 mais",
    "suplementos vitaminas minerais bem estar rotina saudavel pratica sem mudar a rotina",
    "higiene premium banho sabonete liquido corporal gel de banho hidratante karite",
    "shampoo e condicionador reparador premium queratina argan cabelo seco mascara capilar",
    "creme dental branqueador dentes sensiveis enxaguante bucal sem alcool flúor",
    "desodorante roll on sem aluminio creme hidratante aerossol pele sensivel",
    "medicamento de uso continuo reposicao receita similar generico referencia equivalente mesma dose",
    "repor meu medicamento acabando pouco estoque similar disponivel na loja mais proxima",
    "entrega expressa retirar na loja em ate 60 minutos frete gratis acima de 150 reais",
    "frete caro anula o desconto preco total justo produto mais entrega",
    "kit economico essencial completo orcamento ate 120 reais menor preco combinacao",
    "trocar um item do kit por outro mais barato da mesma etapa hidratante protetor serum",
    "sem fragrancia sem alcool vegano oil free preferencias do produto",
    "gravida amamentando evitar retinol restricao na gestacao",
    # ---- medicamentos (doc 16)
    "dor de cabeca latejando enxaqueca cefaleia analgesico dipirona paracetamol antitermico febre",
    "febre alta corpo quente antitermico dipirona gotas paracetamol gotas",
    "dor no corpo corpo moido mal estar anti inflamatorio ibuprofeno naproxeno paracetamol",
    "dor muscular torcicolo dor nas costas lombar relaxante muscular orfenadrina ciclobenzaprina gel diclofenaco pomada",
    "dor de barriga colica gases barriga inchada estufada escopolamina antiespasmodico simeticona antigases",
    "azia queimacao refluxo ma digestao estomago antiacido sal de frutas omeprazol pantoprazol protetor gastrico",
    "gripe resfriado nariz entupido coriza antigripal descongestionante soro nasal vitamina c efervescente",
    "tosse com catarro peito carregado xarope expectorante ambroxol acetilcisteina bromexina guaco",
    "tosse seca irritativa xarope para tosse seca dropropizina levodropropizina pastilha",
    "dor de garganta garganta inflamada pastilha spray gargarejo benzidamina flurbiprofeno",
    "alergia rinite espirro coceira no nariz antialergico loratadina desloratadina cetirizina fexofenadina",
    "diarreia intestino solto desarranjo soro de reidratacao probiotico loperamida",
    "prisao de ventre intestino preso constipacao laxante lactulose bisacodil fibra psyllium",
    "enjoo nausea vomito enjoo de viagem dimenidrinato ondansetrona metoclopramida soro de reidratacao",
    "remedio medicamento comprimido capsula gotas xarope pomada farmacia generico com receita sem receita",
]
