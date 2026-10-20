"""Frases do dia a dia (português do Brasil) que ensinam aos vetores de palavras onde as GÍRIAS e os jeitos indiretos
de falar moram: cada linha junta um jeito de falar com as palavras do catálogo que ele significa.

É dado de treino escrito à mão. Para ampliar o reconhecimento sem programar: acrescente linhas aqui (jeito de falar +
palavras do produto) e rode `python -m graphrag.train`. Quanto mais variado, melhor o mapa.
"""
from __future__ import annotations

EXTRA_PARAPHRASES: list[str] = [
    # ---- higiene bucal
    "cuidar do sorriso dentes brancos creme dental branqueador higiene bucal",
    "sorriso bonito e dentes limpos pasta de dente creme dental enxaguante bucal",
    "boca fresquinha hálito bom enxaguante bucal sem álcool higiene bucal",
    "mau hálito bafo boca seca enxaguante bucal creme dental higiene bucal",
    "dentes amarelados manchados de café clarear dentes creme dental branqueador",
    "dente sensível dói com gelado creme dental dentes sensíveis higiene bucal",
    "gengiva sangrando cárie placa creme dental com flúor higiene bucal",
    "escovar os dentes todo dia depois das refeições creme dental flúor",
    "bochechar depois de escovar enxaguante antisséptico bucal",
    "hálito de onça manhã boca pastosa higiene bucal enxaguante",
    # ---- cabelo
    "cabelo parece palha ressecado quebradiço seco precisa de hidratação máscara capilar condicionador",
    "cabelo caindo fio fraco quebrando pontas duplas shampoo reparador condicionador máscara capilar",
    "cabelo opaco sem brilho sem vida shampoo condicionador reparador nutrição",
    "cabelo armado frizz bagunçado alinhar cabelo macio condicionador máscara hidratação",
    "cabelo oleoso na raiz lavar o cabelo shampoo antioleosidade",
    "cabelo com química descolorido danificado reparar fios máscara capilar reparadora",
    "deixar o cabelo cheiroso macio e brilhoso shampoo condicionador premium",
    "lavar a cabeça cuidar dos fios e do couro cabeludo shampoo xampu",
    "cabelo cacheado crespo definir cachos hidratar fios máscara capilar condicionador",
    "cabelo liso fino sem volume shampoo condicionador leve",
    # ---- banho e corpo
    "banho gostoso cheiroso sabonete líquido gel de banho hidratante corpo",
    "pele do corpo macia depois do banho sabonete corporal gel de banho cremoso",
    "esfoliar o corpo tirar a pele morta esfoliante corporal açúcar banho",
    "tomar banho sabonete que não resseca a pele gel de banho hidratante",
    "ficar cheirosa depois do banho sabonete líquido corporal gel de banho desodorante",
    "espuma de banho banho relaxante gel de banho sabonete corpo",
    "higiene do corpo lavar o corpo todo dia sabonete líquido corporal",
    # ---- desodorante
    "suor demais na axila suvaco molhado desodorante antitranspirante roll-on",
    "tirar o cheiro de suor odor corporal desodorante aerossol creme",
    "desodorante que dura o dia todo sem manchar a roupa sem alumínio",
    "axila escura irritada desodorante creme hidratante sem álcool",
    "transpiração excessiva calor suar muito desodorante antitranspirante",
    # ---- sol
    "ir à praia piscina sol forte protetor solar corporal fps 50 resistente à água",
    "trabalhar na rua o dia todo no sol protetor solar fps alto reaplicar",
    "ir ao parque ficar ao ar livre proteger a pele do sol protetor solar",
    "viajar de férias verão sol protetor solar rosto e corpo",
    "queimadura de sol pele vermelha do sol proteção solar fps",
    "passar protetor solar todo dia no rosto mesmo dentro de casa fps 50 toque seco",
    "protetor solar com cor base protetor pele manchada fps 60",
    "proteger do sol sem deixar branco pele negra protetor solar fluido",
    # ---- acne e oleosidade
    "rosto brilhando de tão oleoso testa e nariz brilhosos controle de oleosidade gel de limpeza oil free",
    "cravos no nariz poros entupidos pontos pretos limpeza profunda sérum salicílico",
    "espinha inflamada no queixo espremer cravo acne tratamento secativo gel antiacne",
    "adolescente cheia de espinhas acne juvenil gel de limpeza antiacne sabonete",
    "pele de adolescente oleosa acne poros sabonete facial gel de limpeza",
    "acabar com as espinhas e os cravos tratamento acne sérum secativo",
    "brilho excessivo na pele hidratante matificante toque seco oil free",
    # ---- manchas
    "marquinhas escuras depois da espinha manchas pós acne clarear uniformizar sérum vitamina c niacinamida",
    "pele manchada pelo sol melasma manchas escuras tratar sérum despigmentante protetor solar",
    "tirar manchas do rosto clarear a pele uniformizar o tom ácido tranexâmico",
    "pele com tom desigual iluminar a pele luminosidade vitamina c sérum iluminador",
    "viço na pele pele iluminada radiante vitamina c antioxidante hidratante",
    # ---- idade
    "rugas linhas de expressão pés de galinha diminuir linhas retinol peptídeos antissinais",
    "pele cansada flácida sem firmeza pele madura sinais da idade creme noturno firmador",
    "mãe de sessenta anos pele madura cuidados anti idade creme antissinais hidratante",
    "rejuvenescer a pele rotina anti idade completa limpeza sérum hidratante protetor",
    "pele com cara de cansada sem viço sinais de idade sérum antioxidante vitamina c",
    "olheiras fundas olhos cansados inchados embaixo dos olhos creme para a área dos olhos cafeína",
    "contorno dos olhos bolsas e olheiras gel para olhos anti olheiras",
    # ---- ressecamento e sensibilidade
    "pele seca que descama repuxa descascando no frio hidratante creme nutritivo ceramidas",
    "pele ressecada áspera craquelada precisa de hidratação intensa creme barreira",
    "pele lisinha macia hidratada hidratante facial ácido hialurônico textura",
    "pele áspera cheia de textura esfoliar renovar a pele esfoliante tônico ácido mandélico",
    "pele que arde quando passo creme sensível reativa irritada produtos sem fragrância calmantes",
    "pele vermelha irritada sensível calmante centella alantoína creme barreira",
    "pele delicada reage a tudo coceira vermelhidão sem perfume hipoalergênico",
    # ---- limpeza, maquiagem, tônico
    "lavar o rosto de manhã limpar a pele sabonete facial gel de limpeza espuma",
    "tirar a maquiagem demaquilar água micelar óleo de limpeza leite de limpeza",
    "limpar o rosto antes de dormir remover protetor solar e make água micelar",
    "tônico para o rosto depois de lavar preparar a pele tônico facial calmante",
    "máscara facial de argila limpeza profunda poros",
    # ---- lábios
    "lábios ressecados rachados protetor labial bálsamo labial hidratante com fps",
    # ---- suplementos
    "dormir melhor sono tranquilo relaxar à noite magnésio citrato dimalato",
    "não consigo dormir cabeça cansada ansiedade do dia a dia relaxamento magnésio à noite",
    "cãibras musculares tensão no corpo magnésio dimalato em pó",
    "ter mais energia disposição para o dia a dia cansaço vitaminas multivitamínico magnésio",
    "sempre cansada sem pique vitamina d multivitamínico complexo de vitaminas",
    "imunidade defesas do corpo vitamina d vitaminas suplemento",
    "ossos fortes vitamina d3 k2 cálcio suplemento",
    "pele cabelo e unhas mais fortes beleza de dentro para fora colágeno hidrolisado",
    "firmeza da pele de dentro para fora colágeno com vitamina c e ácido hialurônico",
    "unhas fracas quebradiças cabelo fraco colágeno suplemento",
    "coração e cérebro gordura boa ômega 3 epa dha óleo de peixe cápsulas",
    "ômega 3 vegano de algas para quem não come peixe suplemento",
    "nutrir o corpo por dentro suplementos vitaminas ômega colágeno magnésio",
    "kit de suplementos para a rotina diária ômega 3 colágeno magnésio vitamina d",
    # ---- itens que o catálogo não tem (para o mapa saber que ficam longe)
    "batom maquiagem base corretivo rímel sombra delineador perfume colônia",
    "fralda lenço umedecido bebê criança infantil mamadeira pomada assadura",
    "absorvente preservativo camisinha lubrificante higiene íntima",
    "ração cachorro gato pet petisco coleira antipulgas",
    "escova de dente fio dental palito interdental irrigador oral",
    "tintura de cabelo coloração progressiva chapinha secador escova de cabelo",
    "esmalte unha manicure alicate lixa cutícula acetona",
    "depilação cera lâmina de barbear espuma de barbear pós barba",
    "repelente inseticida mosquito pernilongo citronela",
    "termômetro curativo gaze esparadrapo álcool algodão cotonete",
]
