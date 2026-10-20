"""Conjunto de avaliação da BUSCA (o que aparece na lista de itens), com frases do dia a dia.

Cada caso: (frase, regra). Regras:
  ("step", id, ...)        todo item relevante tem uma dessas etapas
  ("type", "trecho", ...)  o tipo de produto contém um desses trechos (sem acento, minúsculo)
  ("ing", id, ...)         o produto contém esse ingrediente
  ("typeing", "trecho", id) tipo contém o trecho E o produto contém o ingrediente
  ("concern", id, ...)     o item trata uma dessas preocupações
  ("absent", id, ...)      NÃO existe esse produto no catálogo: a resposta tem de avisar; o que for listado só pode
                           ser da(s) etapa(s) vizinha(s) indicadas (ou nada)
  ("blocked",)             pedido de saúde: o motor tem de recusar
O que conta como relevante é definido aqui, só pelo cadastro (etapa, tipo, preocupação), independente do código do
motor. TRAIN serve para ajustar o léxico e os pesos; TEST só mede (nunca é consultado ao ajustar).
"""
from __future__ import annotations

TRAIN: list[tuple[str, tuple]] = [
    # --- higiene bucal
    ("quero cuidar da minha higiene bucal", ("step", "higiene_oral")),
    ("pasta de dente", ("step", "higiene_oral")),
    ("creme dental branqueador", ("step", "higiene_oral")),
    ("enxaguante bucal", ("step", "higiene_oral")),
    ("meus dentes são sensíveis", ("step", "higiene_oral")),
    ("mau hálito", ("step", "higiene_oral")),
    ("escova de dente", ("absent", "higiene_oral")),
    ("fio dental", ("absent", "higiene_oral")),
    # --- cabelo
    ("shampoo", ("step", "higiene_cabelo")),
    ("condicionador", ("step", "higiene_cabelo")),
    ("cabelo ressecado", ("step", "higiene_cabelo")),
    ("quero cuidar do meu cabelo", ("step", "higiene_cabelo")),
    ("máscara de hidratação para os fios", ("step", "higiene_cabelo")),
    ("cabelo com frizz", ("step", "higiene_cabelo")),
    ("tintura de cabelo", ("absent", "higiene_cabelo")),
    # --- corpo e desodorante
    ("gel de banho", ("step", "higiene_corpo")),
    ("sabonete para o corpo", ("step", "higiene_corpo")),
    ("esfoliante para o corpo", ("step", "higiene_corpo")),
    ("desodorante", ("step", "desodorante")),
    ("suor demais na axila", ("step", "desodorante")),
    ("desodorante sem alumínio", ("step", "desodorante")),
    ("hidratante para o corpo todo", ("absent", "higiene_corpo", "hidratacao")),
    ("creme para as mãos", ("absent",)),
    ("creme para os pés", ("absent",)),
    # --- sol
    ("protetor solar", ("step", "protecao_solar", "protecao_corporal")),
    ("filtro para ir à praia", ("step", "protecao_solar", "protecao_corporal")),
    ("protetor solar para o corpo", ("step", "protecao_corporal")),
    ("protetor solar facial fps 50", ("step", "protecao_solar")),
    ("protetor com cor", ("step", "protecao_solar")),
    ("repelente", ("absent",)),
    # --- pele
    ("espinhas no rosto", ("concern", "acne")),
    ("pele oleosa", ("concern", "oleosidade")),
    ("poros dilatados", ("concern", "poros")),
    ("manchas no rosto", ("concern", "manchas")),
    ("rugas", ("concern", "sinais_idade")),
    ("olheiras", ("concern", "olheiras")),
    ("pele seca", ("concern", "ressecamento")),
    ("pele sensível", ("concern", "sensibilidade")),
    ("tirar a maquiagem", ("concern", "desmaquilagem")),
    ("sabonete para o rosto", ("step", "limpeza")),
    ("esfoliar o rosto", ("step", "preparo")),
    ("hidratante facial", ("step", "hidratacao")),
    ("sérum de vitamina c", ("typeing", "serum", "vitamina_c")),
    ("retinol", ("ing", "retinol")),
    ("protetor labial", ("type", "labial")),
    ("batom", ("absent",)),
    ("base para o rosto", ("absent",)),
    # --- suplementos
    ("ômega 3", ("step", "omega3")),
    ("colágeno", ("step", "colageno")),
    ("magnésio", ("step", "magnesio")),
    ("vitamina d", ("step", "vitaminas")),
    ("multivitamínico", ("step", "vitaminas")),
    ("quero dormir melhor", ("step", "magnesio")),
    ("pele cabelo e unhas mais fortes", ("step", "colageno")),
    ("cansaço no dia a dia", ("step", "vitaminas", "magnesio", "omega3")),
    # --- fora do catálogo
    ("fralda", ("absent",)),
    ("perfume", ("absent",)),
    ("absorvente", ("absent",)),
    ("ração para cachorro", ("absent",)),
    ("preservativo", ("absent",)),
    ("esmalte", ("absent",)),
    # --- saúde (recusa)
    ("que remédio eu tomo pra dor de cabeça", ("blocked",)),
]

TEST: list[tuple[str, tuple]] = [
    ("quero uma boa higiene da boca", ("step", "higiene_oral")),
    ("creme dental com flúor", ("step", "higiene_oral")),
    ("dentes mais brancos", ("step", "higiene_oral")),
    ("enxaguante sem álcool", ("step", "higiene_oral")),
    ("escova de dentes macia", ("absent", "higiene_oral")),
    ("xampu para cabelo oleoso", ("step", "higiene_cabelo")),
    ("condicionador reparador", ("step", "higiene_cabelo")),
    ("cuidar dos fios", ("step", "higiene_cabelo")),
    ("sabonete líquido corporal", ("step", "higiene_corpo")),
    ("quero tomar banho com algo cremoso", ("step", "higiene_corpo")),
    ("antitranspirante", ("step", "desodorante")),
    ("cheiro de suor", ("step", "desodorante")),
    ("filtro solar para o rosto", ("step", "protecao_solar")),
    ("bloqueador para piscina", ("step", "protecao_solar", "protecao_corporal")),
    ("proteção contra o sol", ("step", "protecao_solar", "protecao_corporal")),
    ("cravos e espinhas", ("concern", "acne")),
    ("pele brilhando muito", ("concern", "oleosidade")),
    ("marcas escuras de acne", ("concern", "manchas")),
    ("linhas de expressão", ("concern", "sinais_idade")),
    ("olhos cansados", ("concern", "olheiras")),
    ("pele que repuxa", ("concern", "ressecamento")),
    ("pele reativa", ("concern", "sensibilidade")),
    ("água micelar", ("step", "limpeza")),
    ("gel de limpeza", ("step", "limpeza")),
    ("tônico facial", ("step", "preparo")),
    ("niacinamida", ("ing", "niacinamida")),
    ("óleo de peixe", ("step", "omega3")),
    ("colágeno hidrolisado", ("step", "colageno")),
    ("citrato de magnésio", ("step", "magnesio")),
    ("vitamina d3 e k2", ("step", "vitaminas")),
    ("quero relaxar à noite", ("step", "magnesio")),
    ("imunidade", ("step", "vitaminas")),
    ("lápis de olho", ("absent",)),
    ("fralda de bebê", ("absent",)),
    ("shampoo para bebê", ("absent", "higiene_cabelo")),
    ("camisinha", ("absent",)),
    ("protetor solar infantil", ("absent", "protecao_solar", "protecao_corporal")),
    ("perfume masculino", ("absent",)),
    ("preciso de um remédio para febre", ("blocked",)),
]


# Frases novas, escritas depois de o motor estar ajustado a TRAIN/TEST: gíria, erro de digitação, frase longa, pedido
# com duas coisas, preço e preferência. Rodar uma vez, olhar as falhas, corrigir de forma GERAL e então escrever
# outras frases (ao incorporar estas ao treino, elas deixam de ser cegas).
BLIND: list[tuple[str, tuple]] = [
    ("tô com a boca fedendo, o que eu uso", ("step", "higiene_oral")),
    ("preciso de uma pasta de dente boa", ("step", "higiene_oral")),
    ("quero comprar pasta de dente e shampoo", ("steps_all", "higiene_oral", "higiene_cabelo")),
    ("shampu para cabelo cacheado", ("step", "higiene_cabelo")),
    ("meu cabelo está horrível de seco", ("step", "higiene_cabelo")),
    ("quero deixar meu cabelo macio", ("step", "higiene_cabelo")),
    ("sabonete liquido pra tomar banho", ("step", "higiene_corpo")),
    ("tem sabonete em barra?", ("step", "limpeza", "higiene_corpo")),
    ("desodorante sem cheiro", ("step", "desodorante")),
    ("tem desodorante roll-on?", ("step", "desodorante")),
    ("protetor solar vegano", ("step", "protecao_solar", "protecao_corporal")),
    ("protetor solar até 60 reais", ("step", "protecao_solar", "protecao_corporal")),
    ("vou viajar para a praia, o que levar para o sol", ("step", "protecao_solar", "protecao_corporal")),
    ("protetor soalr facial", ("step", "protecao_solar")),
    ("minha pele está cheia de cravos", ("concern", "acne")),
    ("pele muito oleosa e com poros grandes", ("concern", "oleosidade", "poros")),
    ("quero tirar as manchas do rosto", ("concern", "manchas")),
    ("creme para rugas", ("concern", "sinais_idade")),
    ("pele ressecada no inverno", ("concern", "ressecamento")),
    ("minha pele irrita com tudo", ("concern", "sensibilidade")),
    ("quero um sérum bom para o rosto", ("type", "serum")),
    ("serum com acido hialuronico", ("typeing", "serum", "acido_hialuronico")),
    ("hidratante com ceramidas", ("ing", "ceramidas")),
    ("produto com niacinamida", ("ing", "niacinamida")),
    ("acido salicilico", ("ing", "acido_salicilico")),
    ("omega 3 vegano", ("step", "omega3")),
    ("preciso de colageno em capsula", ("step", "colageno")),
    ("tem vitamina d?", ("step", "vitaminas")),
    ("magnesio em po", ("step", "magnesio")),
    ("quero algo para ter mais energia", ("step", "vitaminas", "magnesio", "omega3")),
    ("não consigo dormir direito", ("step", "magnesio")),
    ("suplemento para a pele", ("step", "colageno", "omega3", "vitaminas")),
    ("quero um kit de suplementos", ("step", "omega3", "colageno", "magnesio", "vitaminas")),
    ("hidratante para as mãos", ("absent",)),
    ("preciso de cotonete", ("absent",)),
    ("fita adesiva", ("absent",)),
    ("tem protetor solar infantil?", ("absent", "protecao_solar", "protecao_corporal")),
    ("quero comprar uma escova de dentes", ("absent", "higiene_oral")),
    ("tem lâmina de barbear?", ("absent",)),
    ("tem remédio para dormir", ("blocked",)),
]


# Segunda rodada cega (frases mais difíceis: inglês, sinônimo, frase longa, duas coisas, jeito indireto).
BLIND2: list[tuple[str, tuple]] = [
    ("sunscreen para o rosto", ("step", "protecao_solar")),
    ("quero um body wash", ("step", "higiene_corpo")),
    ("preciso de um mouthwash", ("step", "higiene_oral")),
    ("toothpaste", ("step", "higiene_oral")),
    ("hair mask", ("step", "higiene_cabelo")),
    ("deodorant", ("step", "desodorante")),
    ("minha filha de 15 anos tem muita espinha, o que serve para ela", ("concern", "acne")),
    ("acordo com o rosto brilhando de tão oleoso", ("concern", "oleosidade")),
    ("quero clarear as marquinhas que ficaram depois que espremi cravo", ("concern", "manchas")),
    ("tenho 50 anos e quero diminuir as linhas do rosto", ("concern", "sinais_idade")),
    ("minha pele descama toda de seca", ("concern", "ressecamento")),
    ("tenho rosácea e minha pele vive vermelha", ("blocked",)),   # condição de saúde: o motor recusa por política
    ("preciso de algo pra limpar o rosto de manhã", ("step", "limpeza")),
    ("o que passo na pele depois de lavar o rosto", ("step", "hidratacao", "tratamento", "preparo")),
    ("quero tirar o brilho do nariz", ("concern", "oleosidade", "poros")),
    ("pasta de dente que clareia", ("step", "higiene_oral")),
    ("quero cuidar dos dentes e do cabelo", ("steps_all", "higiene_oral", "higiene_cabelo")),
    ("sabonete, shampoo e desodorante", ("steps_all", "higiene_corpo", "higiene_cabelo", "desodorante")),
    ("quero ômega 3 e magnésio", ("steps_all", "omega3", "magnesio")),
    ("colágeno e vitamina d", ("steps_all", "colageno", "vitaminas")),
    ("shampoo até 40 reais", ("step", "higiene_cabelo")),
    ("desodorante vegano", ("step", "desodorante")),
    ("hidratante sem fragrância para pele seca", ("step", "hidratacao")),
    ("gel de limpeza para pele oleosa até 50 reais", ("step", "limpeza")),
    ("tem algum suplemento para os ossos", ("step", "vitaminas")),
    ("quero melhorar meu sono", ("step", "magnesio")),
    ("estou sempre cansada, o que posso tomar de vitamina", ("blocked",)),   # "o que posso tomar" é pedido de indicação
    ("preciso de maquiagem para festa", ("absent",)),
    ("onde acho absorvente", ("absent",)),
    ("cadê o bloqueador solar infantil", ("absent", "protecao_solar", "protecao_corporal")),
    ("tem pomada para assadura", ("absent",)),
    ("quero comprar um tapete", ("absent",)),
    ("creme anti celulite", ("absent",)),
    ("serum para crescer cílios", ("absent", "tratamento")),   # a prateleira "sérum" aparece, mas com o aviso
    ("quero shampoo anticaspa", ("absent", "higiene_cabelo")),
    ("meu cabelo está caindo muito", ("step", "higiene_cabelo")),
    ("tem algo para a unha", ("absent",)),
    ("qual remédio tomo para ansiedade", ("blocked",)),
]


# Terceira rodada cega: jeito indireto e gíria, sem as palavras "óbvias" do catálogo.
BLIND3: list[tuple[str, tuple]] = [
    ("meu cabelo parece palha", ("step", "higiene_cabelo")),
    ("quero ficar cheirosa depois do banho", ("step", "higiene_corpo", "desodorante")),
    ("minha pele descasca quando esfria", ("concern", "ressecamento")),
    ("quero a pele lisinha", ("concern", "textura", "ressecamento")),
    ("pra quem trabalha na rua o dia todo", ("step", "protecao_solar", "protecao_corporal")),
    ("minha pele arde quando passo creme", ("concern", "sensibilidade")),
    ("tirar o cheiro do suvaco", ("step", "desodorante")),
    ("quero cuidar do meu sorriso", ("step", "higiene_oral")),
    ("cuidar da minha boca", ("step", "higiene_oral")),
    ("preciso dar uma melhorada no cabelo", ("step", "higiene_cabelo")),
    ("para a minha mãe de 60 anos que está com a pele cansada", ("concern", "sinais_idade")),
    ("pele de adolescente cheia de acne", ("concern", "acne")),
    ("quero ficar com a pele com viço", ("concern", "sinais_idade", "ressecamento", "textura", "manchas")),
    ("o que usar embaixo dos olhos", ("concern", "olheiras")),
    ("proteger a pele quando for ao parque", ("step", "protecao_solar", "protecao_corporal")),
    ("quero nutrir a pele por dentro", ("step", "colageno", "omega3", "vitaminas")),
    ("algo para dar uma energia", ("step", "vitaminas", "magnesio", "omega3")),
    ("meus fios estão quebrando", ("step", "higiene_cabelo")),
    ("pele com cara de cansada", ("concern", "sinais_idade", "olheiras")),
    ("sabonete que não resseca", ("step", "limpeza", "higiene_corpo")),
    ("coisa para o rosto não brilhar", ("concern", "oleosidade")),
    ("hidratar bastante a pele do rosto", ("concern", "ressecamento")),
    ("sorriso branco", ("step", "higiene_oral")),
    ("quero acabar com os cravos do nariz", ("concern", "acne", "poros")),
    ("produto para tratar a pele manchada pelo sol", ("concern", "manchas", "fotoprotecao")),
    ("tem algo natural e vegano para a pele", ("claim", "vegano")),
    ("quero comprar xampu e sabonete", ("steps_all", "higiene_cabelo", "higiene_corpo")),
    ("cuidar dos pés", ("absent",)),
]


# Quarta rodada cega: escrita por último, rodada UMA vez para estimar o desempenho em frases novas (não ajustar a ela).
BLIND4: list[tuple[str, tuple]] = [
    ("quero algo pra limpar os dentes direito", ("step", "higiene_oral")),
    ("cremi dental pra criança", ("absent", "higiene_oral")),
    ("shampoo e condicionador para cabelo pintado", ("steps_all", "higiene_cabelo")),
    ("meu cabelo quebra muito na ponta", ("step", "higiene_cabelo")),
    ("cuidar do cabelo, da boca e do corpo", ("steps_all", "higiene_cabelo", "higiene_oral", "higiene_corpo")),
    ("sabonete liquido barato", ("step", "limpeza", "higiene_corpo")),
    ("preciso de um desodorante forte pra academia", ("step", "desodorante")),
    ("protetor solar pra pele negra", ("step", "protecao_solar", "protecao_corporal")),
    ("fps 30 pra usar todo dia", ("step", "protecao_solar", "protecao_corporal")),
    ("tô com muita espinha na testa", ("concern", "acne")),
    ("pele grudenta e oleosa no verão", ("concern", "oleosidade")),
    ("manchas de melasma", ("concern", "manchas")),
    ("quero tirar as rugas da testa", ("concern", "sinais_idade")),
    ("hidratante pra pele que descama", ("step", "hidratacao")),
    ("creme para pele sensível sem perfume", ("concern", "sensibilidade")),
    ("limpar o rosto sem ressecar", ("step", "limpeza")),
    ("algo para os poros do nariz", ("concern", "poros", "acne", "oleosidade")),
    ("serum antioxidante", ("type", "serum")),
    ("creme de olhos com cafeína", ("concern", "olheiras")),
    ("lábios rachados no inverno", ("type", "labial")),
    ("preciso de ômega 3 e colágeno", ("steps_all", "omega3", "colageno")),
    ("tomar algo para as articulações", ("step", "colageno")),
    ("vitamina para o cabelo e as unhas", ("step", "colageno", "vitaminas")),
    ("quero dormir bem à noite", ("step", "magnesio")),
    ("suplemento vegano", ("claim", "vegano")),
    ("comprar protetor solar e hidratante", ("steps_all", "protecao_solar", "protecao_corporal", "hidratacao")),
    ("fio dental e pasta de dente", ("steps_all", "higiene_oral")),
    ("tem condicionador sem sulfato?", ("step", "higiene_cabelo")),
    ("água micelar pra tirar make", ("step", "limpeza")),
    ("cotonetes e algodão", ("absent",)),
    ("quero um batom vermelho", ("absent",)),
    ("onde fica a seção de brinquedos", ("absent",)),
    ("tem fralda geriátrica", ("absent",)),
    ("shampoo para cachorro", ("absent",)),
    ("qual o melhor remédio para gripe", ("blocked",)),
    ("posso tomar ômega 3 com remédio de pressão", ("blocked",)),
]


def relevant_ids(cat, rule) -> set[str]:
    from graphrag.text import norm
    kind, *vals = rule
    out = set()
    for p in cat.products:
        if p["domain"] == "medicamento":
            continue
        if kind == "step" and (p["step"] in vals or any(s in vals for s in p["coversSteps"])):
            out.add(p["id"])
        elif kind == "concern" and any(c in vals for c in p["concerns"]):
            out.add(p["id"])
        elif kind == "type" and any(v in norm(p["productType"]) for v in vals):
            out.add(p["id"])
        elif kind == "claim" and any(v in p["claims"] for v in vals):
            out.add(p["id"])
        elif kind == "any":
            out.add(p["id"])
        elif kind == "steps_all" and (p["step"] in vals or any(s in vals for s in p["coversSteps"])):
            out.add(p["id"])
        elif kind == "ing" and any(i in p["ingredients"] for i in vals):
            out.add(p["id"])
        elif kind == "typeing" and vals[0] in norm(p["productType"]) and vals[1] in p["ingredients"]:
            out.add(p["id"])
    return out
