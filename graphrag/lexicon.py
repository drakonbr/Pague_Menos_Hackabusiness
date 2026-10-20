"""Léxico escrito à mão: como as pessoas falam -> conceitos do grafo (preocupação, tipo de pele, preferência,
ingrediente, etapa). É conhecimento de domínio do projeto, não vem de modelo nem de dado real.

Duas funções:
  1. entrada do entendimento de frases (graphrag/nlu.py);
  2. fonte de frases para o treino dos vetores de palavras (graphrag/embed.py), para que gírias e variações
     fiquem perto do conceito certo no espaço vetorial.
"""
from __future__ import annotations

# ----------------------------------------------------------------- preocupações (id do catálogo -> falas)
CONCERN_ALIASES: dict[str, list[str]] = {
    "acne": ["acne", "espinha", "espinhas", "cravo", "cravos", "acneica", "acneico", "pele com espinha", "espremi cravo", "espremer cravo", "muita espinha", "tem espinha", "espinha na cara", "problema de acne", "cravo no nariz",
             "pele cheia de espinhas", "pele com acne", "marquinhas de espinha"],
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
                     "rotina anti idade"],
    "olheiras": ["olheira", "olheiras", "olhos cansados", "area dos olhos", "contorno dos olhos", "bolsa nos olhos"],
    "ressecamento": ["seca", "secas", "ressecada", "ressecado", "ressecamento", "pele repuxando", "repuxa", "hidratar",
                     "hidratacao", "hidratante", "pele seca", "desidratada", "descama", "descamando", "descamacao", "pele descama", "pele ressecada", "pele craquelada", "pele esticando"],
    "sensibilidade": ["sensivel", "sensiveis", "pele sensivel", "reativa", "pele reativa", "irritada facilmente",
                      "pele delicada", "irrita", "irritacao", "irritada", "irritado", "irritam", "arde", "ardendo", "ardencia",
                      "vermelhidao", "vermelha", "coceira", "pele que irrita", "irrita com tudo", "alergia na pele"],
    "fotoprotecao": ["protetor", "protetor solar", "filtro solar", "bloqueador", "fps", "praia", "piscina", "sol",
                     "proteger do sol", "proteger da luz", "protecao solar", "protecao uv"],
    "limpeza_diaria": ["limpar", "limpeza", "lavar o rosto", "sabonete facial", "gel de limpeza", "limpeza facial"],
    "textura": ["textura", "pele aspera", "aspereza", "pele lisa", "pele lisinha", "lisinha", "pele macia", "pele aveludada", "esfoliar", "esfoliante", "renovar a pele"],
    "desmaquilagem": ["demaquilar", "desmaquilante", "tirar maquiagem", "remover maquiagem", "agua micelar"],
    "nutricao": ["suplemento", "suplementos", "vitamina", "vitaminas", "nutricao", "bem estar", "omega", "omega 3",
                 "magnesio", "vitamina d", "multivitaminico"],
    "beleza_interna": ["colageno", "colageno hidrolisado", "beleza de dentro", "beleza de dentro para fora"],
    "higiene_diaria": ["higiene", "higiene pessoal", "banho", "higiene premium"],
    "cuidado_cabelo": ["cabelo", "cabelos", "shampoo", "xampu", "condicionador", "mascara capilar", "capilar",
                       "cabelo seco", "fios"],
    "higiene_oral": ["dente", "dentes", "creme dental", "pasta de dente", "enxaguante", "bucal", "boca", "escovar os dentes"],
    "cuidado_corporal": ["corpo", "corporal", "sabonete corporal", "gel de banho", "esfoliante corporal", "banho"],
    "desodorizacao": ["desodorante", "antitranspirante", "axila", "cheiro de suor"],
}

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
    "kit economico essencial alternativo orcamento ate 120 reais menor preco combinacao",
    "trocar um item do kit por outro mais barato da mesma etapa hidratante protetor serum",
    "sem fragrancia sem alcool vegano oil free preferencias do produto",
    "gravida amamentando evitar retinol consultar profissional de saude",
]

# ----------------------------------------------------------------- termos de saúde que NUNCA devem ser repetidos em respostas
HEALTH_TERMS = [
    "pressao", "hipertensao", "hipertens", "colesterol", "diabetes", "diagnostic", "doenca", "remedio de pressao",
    "anti hipertensivo", "anti-hipertensivo", "hipolipemiante", "estatina", "tensivalol", "lipostanol", "tensiv",
    "lipostan", "pressolan", "colemax",
]
