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
    ("tô com o pulso doendo de tanto digitar", ("concern", "dor_muscular", "dor_no_corpo")),   # trocou "pescoço travado" (23/10): o léxico passou a conhecer "pescoço travado" no #62
    ("remédio pra frieira", ("missing",)),
]
NOVO_ADJUST: list[tuple] = [
    ("kit de suplementos", "nada que tenha glúten", ("pref", "sem glúten")),
    ("kit de suplementos", "menos caro por favor", ("cheaper",)),
    ("kit de suplementos", "quero o mais caprichado", ("richer",)),
]

# --- AMPLO (23/10, a pedido da Julia: "a pesquisa estava ruim"): frases do dia a dia, com o que o GRAFO já acerta
# (controle: o RAG não pode estragar) e o que ele entende errado ou pela metade. Dividido por posição: a cada 3ª frase
# é TESTE (só mede); as outras ajustam o corte de confiança e o prompt.
AMPLO: list[tuple] = [
    ("quero cuidar da pele que vive melada", ("goal", "oleosidade")),
    ("minha testa tá sempre brilhando", ("goal", "oleosidade")),
    ("tô fanho e entupido", ("concern", "nariz_entupido", "gripe", "alergia")),
    ("treino pesado e fico todo dolorido", ("concern", "dor_muscular", "dor_no_corpo")),
    ("dor no joelho", ("concern", "dor_muscular", "dor_no_corpo")),
    ("tô com a cara cheia de bolinha", ("goal", "acne")),
    ("cara cheia de cravo", ("goal", "acne", "oleosidade")),
    ("minhas olheiras tão horríveis", ("concern", "olheiras")),
    ("preciso de algo pro sol da praia", ("goal", "protecao_solar")),
    ("tô com a barriga estufada e dura", ("concern", "gases", "prisao_de_ventre", "dor_de_barriga")),
    ("tô sem ânimo, cansada demais", ("goal", "suplementos")),
    ("preciso passar protetor mas odeio sensação de grude", ("goal", "protecao_solar")),
    ("queria algo pra tirar maquiagem", ("concern", "desmaquilagem", "limpeza_diaria")),
    ("cabelo seco e sem vida", ("step", "higiene_cabelo")),
    ("mau hálito", ("step", "higiene_oral")),
    ("suor excessivo", ("step", "desodorante")),
    ("rugas no rosto", ("goal", "anti_idade")),
    ("manchas do sol no rosto", ("goal", "manchas")),
    ("pele sensível que arde com tudo", ("goal", "pele_sensivel")),
    ("quero ficar mais bonita por dentro", ("goal", "suplementos")),
    ("meu ombro tá travado", ("concern", "dor_muscular", "dor_no_corpo")),
    ("vomitei a noite toda", ("concern", "enjoo")),
    ("tô com coriza e espirrando", ("concern", "alergia", "gripe", "nariz_entupido")),
    ("garganta ardendo", ("concern", "dor_de_garganta")),
    ("azia depois do almoço", ("concern", "azia")),
    ("queria um perfume bom", ("missing",)),
    ("pasta de dente pra dente sensível", ("step", "higiene_oral")),
    ("tô grávida e com enjoo", ("concern", "enjoo")),
    ("acordo com o nariz tapado toda manhã", ("concern", "nariz_entupido", "gripe", "alergia")),
    ("minha pele tá ressecada e repuxando", ("goal", "skincare_basico", "pele_sensivel")),
    ("tosse seca à noite", ("concern", "tosse_seca")),
    ("meu estômago não anda bem", ("concern", "azia", "dor_de_barriga")),
    ("garganta de lixa", ("concern", "dor_de_garganta")),
    ("dor de cabeça forte e a luz incomoda", ("goal", "dor_de_cabeca")),
    ("queria um creme pras mãos", ("missing",)),
    ("preciso de um remédio pra ansiedade", ("missing",)),
    ("minha pele vive com cara de cansada e sem brilho", ("goal", "anti_idade", "manchas", "skincare_basico")),
    ("tô com intestino travado", ("concern", "prisao_de_ventre")),
    ("meu cabelo tá caindo", ("step", "higiene_cabelo")),
    ("quero clarear as manchinhas que ficaram das espinhas", ("goal", "manchas", "acne")),
    ("tô com dor nas costas de tanto ficar sentada", ("concern", "dor_muscular", "dor_no_corpo")),
    ("preciso de protetor que não deixe a cara branca", ("goal", "protecao_solar")),
    ("diarreia desde ontem", ("concern", "diarreia")),
]
AMPLO_TEST = [c for i, c in enumerate(AMPLO) if i % 3 == 0]
AMPLO_TRAIN = [c for i, c in enumerate(AMPLO) if i % 3 != 0]

# --- RISCO (23/10, depois da revisão do #61): frases em que o GRAFO JÁ ACERTA e que têm palavra que o catálogo não conhece.
# É onde a conferência da DeepSeek poderia estragar uma resposta boa. Escolhidas assim: 15 candidatas escritas à mão,
# ficaram as 11 que o grafo sozinho acerta (as 4 que ele erra não entram aqui, para não medir o RAG com o que já o motivou); mais 3 escritas pelo revisor.
RISCO: list[tuple] = [
    ("sinto o corpo todo pesado e cansado", ("nomed",)),
    ("preciso de um xampu que não resseque meu cabelo", ("step", "higiene_cabelo")),
    ("quero comprar uns protetores pra viagem de férias", ("goal", "protecao_solar")),
    ("meu cabelo vive embaraçado e ressecado", ("step", "higiene_cabelo")),
    ("minha pele fica toda vermelhinha com o sol", ("goal", "pele_sensivel", "protecao_solar")),
    ("tô com uma coceirinha no nariz e espirro muito", ("concern", "alergia", "nariz_entupido", "gripe")),
    ("meu hálito amanhece bem pesado", ("step", "higiene_oral")),
    ("me dá um protetor leve pra usar no escritório", ("goal", "protecao_solar")),
    ("tô com a garganta meio áspera hoje", ("concern", "dor_de_garganta")),
    ("acordei com o estômago pesado depois da festa", ("concern", "azia", "dor_de_barriga", "gases")),
    ("quero me livrar dos cravinhos do nariz", ("goal", "acne", "oleosidade")),
    # as três abaixo foram escritas pelo REVISOR independente (não por mim) para tentar quebrar a conferência
    ("quero um sabonete pro meu marido que tem a pele melada", ("goal", "oleosidade", "acne")),
    ("minha pele tá puxando e vermelha", ("goal", "pele_sensivel", "skincare_basico")),
    ("tô sem pique pra malhar, preciso de algo", ("goal", "suplementos")),
    # da 3ª rodada do revisor, provadas na API real: a palavra desconhecida é um adjetivo NEGADO
    ("quero um protetor solar que não fique melado na pele", ("goal", "protecao_solar")),
    ("quero um hidratante leve que não deixe a pele melada", ("step", "hidratacao")),
]
