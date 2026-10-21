"""Conceitos de prateleira: como as pessoas CHAMAM cada coisa que existe (ou não existe) na farmácia.

Escrito à mão, em português do Brasil do dia a dia. Cada conceito diz:
  - frases: jeitos de falar (sem acento, minúsculo; plural não precisa repetir);
  - steps / types / concerns: onde no catálogo isso mora (etapa, tipo de produto, preocupação);
  - absent=True: a farmácia do catálogo NÃO tem isso; `near` indica a prateleira vizinha para sugerir.

Como estender (custo baixo, sem treino):
  1. produto de um tipo novo: nada a fazer, o tipo vira conceito sozinho (ver scope.auto_concepts);
  2. um jeito novo de falar: acrescentar a frase aqui;
  3. um departamento novo (ex.: bebê): acrescentar conceitos com `absent` ou com as etapas dele.
Frases mais longas vencem as mais curtas ("protetor solar para o corpo" ganha de "corpo").
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Concept:
    id: str
    label: str                       # como aparece nas respostas ("escova de dente")
    phrases: tuple[str, ...]
    steps: tuple[str, ...] = ()
    types: tuple[str, ...] = ()      # trechos do tipo de produto (sem acento)
    concerns: tuple[str, ...] = ()
    absent: bool = False
    near: tuple[str, ...] = ()       # etapas vizinhas para sugerir quando o item não existe
    shelf: str = ""                  # nome da prateleira para texto ("higiene bucal")


def C(id, label, phrases, **kw) -> Concept:
    return Concept(id, label, tuple(phrases), **kw)


SUPP = ("omega3", "colageno", "magnesio", "vitaminas")

CONCEPTS: list[Concept] = [
    # ------------------------------------------------------------------ higiene em geral (os quatro departamentos juntos)
    C("higiene", "higiene pessoal", ["higiene", "higiene pessoal", "higiene premium", "kit de higiene", "higiene completa",
                                     "higiene do dia a dia", "cuidados pessoais", "cuidado pessoal"],
      steps=("higiene_corpo", "higiene_cabelo", "higiene_oral", "desodorante"), shelf="higiene pessoal"),
    # ------------------------------------------------------------------ higiene bucal
    C("oral", "higiene bucal", ["sorriso", "cuidar do sorriso", "cuidar do meu sorriso", "sorriso bonito", "sorriso branco", "mouthwash", "toothpaste", "dentes limpos", "escovar os dentes", "escovacao", "gengiva", "gengivas", "carie", "caries", "placa bacteriana", "tartaro", "higiene bucal", "higiene da boca", "cuidar da boca", "saude bucal", "cuidado bucal",
                               "cuidados com a boca", "boca", "bucal", "dente", "dentes", "dental", "dentario"],
      steps=("higiene_oral",), shelf="higiene bucal"),
    C("creme_dental", "creme dental", ["toothpaste", "pasta que clareia", "pasta de dente que clareia", "pasta dental branqueadora", "dentifrice", "pasta de dente", "pasta dental", "creme dental", "creme de dente", "dentifricio",
                                       "pasta de dentes", "pasta com fluor", "creme dental com fluor", "creme dental branqueador"],
      steps=("higiene_oral",), types=("creme dental",), shelf="higiene bucal"),
    C("enxaguante", "enxaguante bucal", ["mouthwash", "mouth wash", "enxaguatorio bucal", "antisseptico para a boca", "enxaguante", "enxaguante bucal", "antisseptico bucal", "bochecho", "colutorio",
                                         "enxaguatorio"],
      steps=("higiene_oral",), types=("enxaguante",), shelf="higiene bucal"),
    C("clarear_dentes", "clareamento dos dentes", ["dentes brancos", "dentes mais brancos", "branquear os dentes",
                                                  "clarear os dentes", "clareamento dental", "clareamento dos dentes",
                                                  "dente branco", "sorriso branco"],
      steps=("higiene_oral",), types=("creme dental",), shelf="higiene bucal"),
    C("halito", "mau hálito", ["mau halito", "halito", "bafo", "bafo de onca", "halitose"],
      steps=("higiene_oral",), shelf="higiene bucal"),
    C("dente_sensivel", "dentes sensíveis", ["dentes sensiveis", "dente sensivel", "sensibilidade nos dentes",
                                             "sensibilidade dental"],
      steps=("higiene_oral",), types=("creme dental",), shelf="higiene bucal"),
    C("escova_dente", "escova de dente", ["escova de dente", "escova de dentes", "escova dental", "escovinha de dente",
                                          "escova eletrica", "escova de dente macia", "escova macia", "refil de escova"],
      absent=True, near=("higiene_oral",), shelf="higiene bucal"),
    C("fio_dental", "fio dental", ["fio dental", "fita dental", "fio de dental", "palito de dente", "palito dental",
                                   "escova interdental", "irrigador oral", "irrigador"],
      absent=True, near=("higiene_oral",), shelf="higiene bucal"),
    C("aparelho_dental", "protetor bucal e acessórios", ["protetor bucal", "placa de dormir", "alinhador", "aparelho nos dentes",
                                                        "limpador de lingua", "raspador de lingua"],
      absent=True, near=("higiene_oral",), shelf="higiene bucal"),

    # ------------------------------------------------------------------ cabelo
    C("cabelo", "cabelo", ["hair", "hair care", "cabelo opaco", "cabelo sem vida", "cabelo estragado", "cabelo quebrando", "cabelos ressecados", "cabelo caindo muito", "cabelo muito caindo", "cabelo caindo demais", "cabelo ralo", "cabelo bagunçado", "madeixas", "cabelo", "cabelos", "fio", "fios", "capilar", "cuidar do cabelo", "cuidar dos fios",
                          "cuidado capilar", "cabelo seco", "cabelo ressecado", "cabelo danificado", "cabelo quimicamente tratado",
                          "frizz", "cabelo com frizz", "ponta dupla", "pontas duplas", "cabelo oleoso", "cabelo crespo",
                          "cabelo cacheado", "cabelo liso", "queda de cabelo", "cabelo caindo", "cabelo fraco",
                          "cabelo quebradico", "brilho no cabelo", "couro cabeludo", "oleosidade no cabelo"],
      steps=("higiene_cabelo",), shelf="cabelo"),
    C("shampoo", "shampoo", ["shampoo para cabelo cacheado", "xampu para cabelo cacheado", "shampoo de cabelo", "shampoo para cabelo seco", "shampoo para cabelos", "lavar a cabeca", "shampoo", "xampu", "shampu", "sampoo", "xampo", "shampoo para cabelo oleoso", "xampu para cabelo oleoso", "lavar o cabelo",
                            "lavar os cabelos", "shampoo reparador", "xampu reparador", "shampoo sem sulfato", "xampu sem sulfato"],
      steps=("higiene_cabelo",), types=("shampoo",), shelf="cabelo"),
    C("condicionador", "condicionador", ["conditioner", "condicionador de cabelo", "condicionador", "condicionador reparador", "creme de pentear", "desembaracante",
                                         "desembaracador"],
      steps=("higiene_cabelo",), types=("condicionador",), shelf="cabelo"),
    C("mascara_capilar", "máscara capilar", ["hair mask", "mascara capilar hidratante", "hidratar o cabelo", "deixar o cabelo macio", "cabelo macio", "cabelos macios", "mascara hidratante para cabelo", "mascara capilar", "mascara de cabelo", "mascara para o cabelo", "mascara para cabelo",
                                             "mascara de hidratacao para os fios", "mascara de hidratacao para o cabelo",
                                             "hidratacao capilar", "cronograma capilar", "creme de tratamento capilar",
                                             "mascara de nutricao capilar", "mascara de reconstrucao"],
      steps=("higiene_cabelo",), types=("mascara capilar",), shelf="cabelo"),
    C("tintura", "tintura e coloração de cabelo", ["tintura", "tintura de cabelo", "tinta de cabelo", "coloracao", "coloracao de cabelo",
                                                    "tinta para cabelo", "descolorante", "pintar o cabelo", "pintar cabelo",
                                                    "progressiva", "alisamento", "alisante", "relaxamento capilar", "botox capilar",
                                                    "luzes no cabelo"],
      absent=True, near=("higiene_cabelo",), shelf="cabelo"),
    C("acessorio_cabelo", "gel, spray e acessórios de cabelo", ["gel de cabelo", "pomada de cabelo", "pomada capilar", "laquê",
                                                              "lacque", "spray fixador", "creme para pentear", "escova de cabelo",
                                                              "pente", "secador", "chapinha", "prancha", "touca", "presilha",
                                                              "elastico de cabelo", "grampo", "leave in", "leave-in",
                                                              "oleo capilar", "oleo de cabelo", "oleo para cabelo",
                                                              "ampola capilar", "ampola de cabelo"],
      absent=True, near=("higiene_cabelo",), shelf="cabelo"),
    C("anticaspa", "shampoo anticaspa", ["caspa", "anticaspa", "shampoo anticaspa", "xampu anticaspa", "seborreia"],
      absent=True, near=("higiene_cabelo",), shelf="cabelo"),

    # ------------------------------------------------------------------ banho e corpo
    C("banho", "banho", ["body wash", "shower gel", "banho gostoso", "tomar um banho", "sabonete de corpo", "banho", "tomar banho", "banho relaxante", "chuveiro", "gel de banho", "banho cremoso", "ducha",
                         "sabonete liquido", "sabonete liquido corporal", "sabonete corporal", "sabonete para o corpo",
                         "sabonete de banho", "sabonete do corpo", "lavar o corpo", "higiene do corpo", "higiene corporal"],
      steps=("higiene_corpo",), types=("sabonete liquido corporal", "gel de banho"), shelf="banho e corpo"),
    C("corpo", "cuidado com o corpo", ["corpo", "corporal", "cuidar do corpo", "cuidado com o corpo", "pele do corpo"],
      steps=("higiene_corpo",), shelf="banho e corpo"),
    C("esfoliante_corpo", "esfoliante corporal", ["esfoliante corporal", "esfoliante para o corpo", "esfoliar o corpo",
                                                  "esfoliacao corporal", "esfoliante de corpo", "esfoliante do corpo",
                                                  "esfoliante de acucar", "bucha"],
      steps=("higiene_corpo",), types=("esfoliante corporal",), shelf="banho e corpo"),
    C("hidratante_corpo", "hidratante corporal", ["hidratante corporal", "hidratante para o corpo", "hidratante para o corpo todo",
                                                  "hidratante de corpo", "creme corporal", "locao corporal", "locao hidratante",
                                                  "manteiga corporal", "manteiga de karite corporal", "oleo corporal",
                                                  "creme para o corpo", "creme hidratante para o corpo", "hidratar o corpo",
                                                  "oleo para o corpo", "pele do corpo seca", "creme para o corpo todo"],
      absent=True, near=("higiene_corpo",), shelf="banho e corpo"),
    C("maos", "creme para as mãos", ["creme para as maos", "creme de maos", "creme para maos", "hidratante para as maos",
                                     "hidratante de maos", "maos ressecadas", "maos secas", "cuidar das maos", "maos",
                                     "cuticula", "cuticulas", "base fortalecedora", "esmalte", "esmaltes",
                                     "acetona", "removedor de esmalte", "alicate", "lixa de unha", "cortador de unha",
                                     "manicure", "unhas postica"],
      absent=True, shelf="mãos e unhas"),
    C("pes", "creme para os pés", ["creme para os pes", "creme de pes", "creme para pes", "hidratante para os pes", "pes rachados",
                                   "calcanhar", "calcanhares", "calo", "calos", "lixa de pe", "cuidar dos pes", "pes ressecados",
                                   "chulé", "chule", "pes", "pedicure", "frieira", "assadura nos pes"],
      absent=True, shelf="pés"),
    C("depilacao", "depilação e barbear", ["creme anti celulite", "celulite", "anticelulite", "anti celulite", "gordura localizada", "estrias", "creme para estrias", "creme para celulite", "flacidez do corpo", "modelador corporal", "depilacao", "depilar", "cera depilatoria", "creme depilatorio", "lamina de barbear",
                                           "aparelho de barbear", "gilete", "barbear", "espuma de barbear", "pos barba",
                                           "pos-barba", "barba", "barbeador", "aparelho de depilar", "depilador"],
      absent=True, shelf="depilação"),
    C("desodorante", "desodorante", ["deodorant", "deo", "roll on", "rollon", "antiperspirante", "anti transpirante", "cheiro nas axilas", "desodorante", "desodorantes", "antitranspirante", "antitranspirantes", "axila", "axilas",
                                     "suvaco", "sovaco", "suor", "suor demais", "suor excessivo", "transpiracao", "cheiro de suor",
                                     "mau cheiro", "odor corporal", "desodorante roll on", "desodorante rollon",
                                     "desodorante em creme", "desodorante aerossol", "desodorante spray", "transpirar",
                                     "cheiro no corpo", "suor nas axilas", "suar", "suando"],
      steps=("desodorante",), shelf="desodorantes"),

    # ------------------------------------------------------------------ sol
    C("solar_corpo", "protetor solar corporal", ["sunscreen para o corpo", "body sunscreen", "protetor solar para o corpo", "protetor solar corporal", "protetor corporal",
                                                 "filtro solar corporal", "bloqueador corporal", "protetor para o corpo",
                                                 "filtro solar para o corpo", "bloqueador solar para o corpo", "protetor solar do corpo",
                                                 "protetor solar de corpo", "filtro para o corpo"],
      steps=("protecao_corporal",), shelf="proteção solar"),
    C("solar_rosto", "protetor solar facial", ["sunscreen para o rosto", "sunscreen facial", "sunscreen para rosto", "facial sunscreen", "protetor solar para o rosto", "protetor solar facial", "protetor facial", "filtro solar facial", "bloqueador facial",
                                               "filtro para o rosto", "protetor para o rosto", "protetor solar para o rosto",
                                               "filtro solar para o rosto", "bloqueador para o rosto", "protetor solar de rosto",
                                               "filtro solar para rosto", "protetor solar para rosto", "protetor solar do rosto",
                                               "bloqueador solar facial", "fps facial", "protetor com cor", "protetor colorido",
                                               "protetor solar com cor", "base com protetor", "protetor solar toque seco",
                                               "protetor mineral", "protetor solar mineral", "filtro mineral",
                                               "protetor solar oil free", "protetor solar fps 50", "protetor solar facial fps 50",
                                               "protetor solar fps 30", "protetor solar fps 60", "protetor solar fps 70"],
      steps=("protecao_solar",), shelf="proteção solar"),
    C("solar", "protetor solar", ["trabalhar na rua", "trabalha na rua", "trabalho na rua", "ao ar livre", "parque", "ir ao parque", "proteger a pele", "proteja a pele", "pegar sol", "tomar sol", "muito sol", "sol forte", "ficar no sol", "ao sol", "no sol", "dia todo na rua", "passeio ao ar livre", "sunscreen", "sun screen", "sunblock", "protetor solar fps", "protecao uva", "solar", "protetor solar", "protetores solares", "filtro solar", "bloqueador solar", "bloqueador", "protetor",
                                  "protecao solar", "protecao contra o sol", "protecao uv", "fps", "praia", "piscina",
                                  "proteger do sol", "para ir a praia", "ir a praia", "ficar no sol", "contra o sol",
                                  "raios uv", "uv", "bronzeado", "queimadura de sol", "protecao solar fps"],
      steps=("protecao_solar", "protecao_corporal"), shelf="proteção solar"),
    C("solar_infantil", "protetor solar infantil", ["protetor solar infantil", "protetor solar para crianca", "protetor solar baby",
                                                     "filtro solar infantil", "protetor solar bebe", "protetor solar de bebe",
                                                     "protetor solar kids", "protetor solar para bebe"],
      absent=True, near=("protecao_solar", "protecao_corporal"), shelf="proteção solar"),
    C("pos_sol", "bronzeador e pós-sol", ["bronzeador", "autobronzeante", "auto bronzeante", "pos sol", "pos-sol", "after sun",
                                           "oleo bronzeador", "bronzeamento"],
      absent=True, near=("protecao_solar", "protecao_corporal"), shelf="proteção solar"),
    C("repelente", "repelente", ["repelente", "repelente de insetos", "citronela", "mosquito", "pernilongo", "dengue",
                                  "inseticida", "antimosquito", "mosquitos", "pernilongos"],
      absent=True, shelf="repelentes"),

    # ------------------------------------------------------------------ rosto: limpeza, tônico, esfoliante, olhos, lábios
    C("limpeza_rosto", "limpeza facial", ["cleanser", "facial cleanser", "limpar o rosto de manha", "limpar o rosto pela manha", "lavar o rosto pela manha", "limpar o rosto antes de dormir", "limpar o rosto", "limpeza do rosto", "limpeza facial", "lavar o rosto", "sabonete facial",
                                          "sabonete para o rosto", "sabonete de rosto", "sabonete do rosto", "gel de limpeza",
                                          "espuma de limpeza", "leite de limpeza", "limpar a pele", "limpeza de pele",
                                          "lavar o rosto de manha", "limpar o rosto a noite", "agua micelar", "micelar"],
      steps=("limpeza",), shelf="limpeza facial"),
    C("mancha_acne", "manchas de acne", ["marcas de acne", "marcas escuras de acne", "manchas de acne", "manchas da acne",
                                          "marcas da espinha", "marcas de espinha", "marquinhas de espinha", "cicatriz de acne",
                                          "cicatrizes de acne", "pos acne", "manchas pos acne", "marcas da acne", "manchinhas de espinha"],
      concerns=("manchas",), shelf="manchas"),
    C("demaquilante", "remoção de maquiagem", ["tirar a maquiagem", "tirar maquiagem", "remover maquiagem", "remover a maquiagem",
                                                "demaquilante", "desmaquilante", "demaquilar", "tirar make", "tirar a make",
                                                "remover make", "tirar protetor solar", "oleo de limpeza"],
      concerns=("desmaquilagem",), shelf="limpeza facial"),
    C("sabonete", "sabonete", ["sabonete", "sabonetes", "sabonete em barra", "sabonete liquido"],
      steps=("limpeza", "higiene_corpo"), types=("sabonete",), shelf="sabonetes"),
    C("esfoliante_rosto", "esfoliante facial", ["esfoliar o rosto", "esfoliante facial", "esfoliacao facial", "esfoliar a pele",
                                                "esfoliar", "esfoliante", "renovar a pele", "renovacao celular", "peeling",
                                                "tonico esfoliante", "esfoliante quimico", "esfoliante fisico"],
      steps=("preparo",), types=("esfoliante", "tonico esfoliante"), shelf="esfoliantes e tônicos"),
    C("tonico", "tônico facial", ["tonico", "tonico facial", "tonicos", "adstringente"], steps=("preparo",),
      types=("tonico",), shelf="esfoliantes e tônicos"),
    C("mascara_facial", "máscara facial", ["mascara facial", "mascara de argila", "argila", "mascara para o rosto", "mascara de rosto"],
      steps=("preparo",), types=("mascara de argila",), shelf="esfoliantes e tônicos"),
    C("hidratante_rosto", "hidratante facial", ["moisturizer", "moisturiser", "face cream", "hidratante facial", "hidratante para o rosto", "hidratante de rosto", "creme facial",
                                                "creme para o rosto", "hidratante do rosto", "hidratar o rosto", "hidratante",
                                                "hidratantes", "gel hidratante", "creme hidratante", "hidratacao facial",
                                                "creme de rosto", "hidratante para a pele", "hidratar a pele",
                                                "hidratante com fps", "hidratante facial com fps"],
      steps=("hidratacao",), shelf="hidratantes"),
    C("olhos", "área dos olhos", ["embaixo dos olhos", "debaixo dos olhos", "abaixo dos olhos", "em volta dos olhos", "ao redor dos olhos", "eye cream", "olheira", "olheiras", "area dos olhos", "contorno dos olhos", "contorno de olhos", "bolsa nos olhos",
                                  "bolsas nos olhos", "olhos cansados", "creme para os olhos", "creme para olhos", "olhos inchados",
                                  "pes de galinha"],
      steps=("complemento",), types=("olhos",), concerns=("olheiras",), shelf="área dos olhos"),
    C("labios", "cuidado labial", ["lip balm", "lip", "protetor labial", "balsamo labial", "labios ressecados", "labio rachado", "labios rachados",
                                    "hidratante labial", "labios", "labio", "manteiga de cacau", "cacau labial"],
      steps=("complemento",), types=("labial",), shelf="lábios"),
    C("maquiagem", "maquiagem", ["maquiagem para festa", "make para festa", "makeup", "cilios", "cilios postiços", "crescer cilios", "serum para cilios", "serum de cilios", "alongar cilios", "cilios mais longos", "volume nos cilios", "batom", "batons", "gloss", "base liquida", "base para o rosto", "base de maquiagem", "po compacto", "corretivo", "rimel", "mascara de cilios",
                                 "sombra", "sombras", "lapis de olho", "lapis", "delineador", "blush", "iluminador", "maquiagem",
                                 "make", "makeup", "paleta", "cilios postico", "cilios", "sobrancelha", "lapis de sobrancelha",
                                 "pincel de maquiagem", "pincel", "esponja de maquiagem", "primer", "fixador de maquiagem",
                                 "contorno facial", "bronzer"],
      absent=True, shelf="maquiagem"),
    C("perfume", "perfume", ["perfume", "perfumes", "colonia", "deo colonia", "deocolonia", "fragrancia", "body splash", "perfume masculino",
                              "perfume feminino", "eau de toilette", "eau de parfum", "perfumaria", "essencia", "aromatizador"],
      absent=True, shelf="perfumaria"),

    # ------------------------------------------------------------------ suplementos (jeitos de falar)
    C("omega3", "ômega 3", ["fish oil", "omega 3", "omega3", "omega", "oleo de peixe", "oleo de peixe em capsulas", "epa", "dha", "epa dha",
                            "gordura boa", "omega vegano", "omega de algas", "omega 3 vegano"],
      steps=("omega3",), shelf="suplementos"),
    C("colageno", "colágeno", ["vitamina para o cabelo", "vitamina para as unhas", "vitamina para cabelo e unhas", "vitamina para o cabelo e as unhas", "nutrir a pele por dentro", "pele por dentro", "por dentro", "de dentro para fora", "collagen", "colageno", "colageno hidrolisado", "colageno em po", "colageno em capsulas", "colageno hidrolisado em po",
                               "beleza de dentro", "beleza de dentro para fora", "pele cabelo e unhas", "pele cabelo unhas",
                               "cabelo e unhas", "cabelos e unhas", "unhas fracas", "unhas quebradicas", "firmeza da pele",
                               "pele e unhas", "pele e cabelo mais fortes", "suplemento para a pele", "suplemento para pele", "vitamina para a pele", "vitamina para pele",
                               "suplemento para o cabelo", "suplemento para cabelo", "suplemento para as unhas", "suplemento para beleza", "pele cabelo e unhas mais fortes", "unhas e cabelos",
                               "unhas mais fortes", "cabelo pele e unha", "cabelo unha e pele", "articulacao", "articulacoes",
                               "juntas", "cartilagem", "colageno com vitamina c", "peptideos de colageno"],
      steps=("colageno",), shelf="suplementos"),
    C("magnesio", "magnésio", ["magnesium", "melhorar meu sono", "melhorar o sono", "sono ruim", "dormir mal", "dificuldade para dormir", "nao consigo dormir", "dormir direito", "noites mal dormidas", "acordar varias vezes", "magnesio", "citrato de magnesio", "magnesio dimalato", "magnesio bisglicinato", "dimalato", "bisglicinato",
                               "dormir", "dormir melhor", "sono", "sono melhor", "sono tranquilo", "insonia", "relaxar", "relaxamento",
                               "descansar", "descanso", "noite tranquila", "cabeca cansada", "tensao muscular", "caimbra", "caibra",
                               "caimbras", "relaxar a noite", "relaxar a noite", "relaxar a mente", "calma", "ficar calmo",
                               "musculos", "musculo", "cansaco muscular", "tomar a noite"],
      steps=("magnesio",), shelf="suplementos"),
    C("vitaminas", "vitaminas", ["vitamin d", "vitamina d para os ossos", "suplemento para os ossos", "ossos e dentes", "fortalecer os ossos", "suplemento para ossos", "saude dos ossos", "vitamins", "vitamina d", "vitamina d3", "vitamina k", "vitamina k2", "vitaminas d e k", "d3 e k2", "d3", "k2",
                                 "multivitaminico", "multi vitaminico", "polivitaminico", "vitaminas", "vitamina", "vitamina do sol",
                                 "ossos", "ossos fortes", "imunidade", "sistema imune", "sistema imunologico", "defesas do corpo",
                                 "complexo b", "vitamina b", "vitamina e", "vitamina a"],
      steps=("vitaminas",), shelf="suplementos"),
    C("energia", "energia e disposição", ["estou cansada", "estou cansado", "sempre cansada", "sempre cansado", "sem disposicao", "preguica", "exausta", "exausto", "cansaco", "fadiga", "energia", "disposicao", "mais energia", "falta de energia", "sem energia", "cansaco no dia a dia", "cansaco do dia a dia", "mais disposicao",
                                          "mais disposicao no dia a dia", "pique", "mais pique", "indisposicao", "desanimo"],
      steps=("vitaminas", "magnesio", "omega3"), shelf="suplementos"),
    C("suplemento", "suplementos", ["supplement", "supplements", "suplemento para a saude", "suplemento", "suplementos", "suplemento alimentar", "suplementos alimentares", "kit de suplementos",
                                    "bem estar", "saude e bem estar", "vida saudavel"],
      steps=SUPP, shelf="suplementos"),
    C("proteina", "proteínas e esportivos", ["protein", "whey protein", "whey", "whey protein", "proteina", "creatina", "bcaa", "pre treino", "pre-treino",
                                              "hipercalorico", "barra de proteina", "termogenico", "queimador de gordura",
                                              "emagrecer", "emagrecimento", "perder peso", "perda de peso", "dieta", "shake",
                                              "massa muscular", "ganhar massa", "inibidor de apetite", "fome", "cha emagrecedor",
                                              "gelatina", "colageno bovino"],
      absent=True, shelf="suplementos esportivos"),
    C("infantil", "linha infantil", ["bebe", "bebes", "infantil", "infantis", "crianca", "criancas", "kids", "nenem", "recem nascido",
                                     "pediatrico", "baby", "para meu filho", "para minha filha", "para filho"],
      absent=True, shelf="linha infantil"),
    C("higiene_intima", "higiene íntima", ["absorvente", "absorventes", "coletor menstrual", "protetor diario", "tampao", "sabonete intimo",
                                            "higiene intima", "preservativo", "preservativos", "camisinha", "camisinhas", "lubrificante",
                                            "gel lubrificante", "teste de gravidez"],
      absent=True, shelf="higiene íntima"),
    C("fraldas", "fraldas e bebê", ["pomada de assadura", "pomada para assadura", "pomada assadura", "fralda", "fraldas", "lenco umedecido", "lencos umedecidos", "pomada para assadura", "assadura",
                                     "mamadeira", "chupeta", "leite em po", "formula infantil", "papinha"],
      absent=True, shelf="bebê"),
    C("pet", "produtos para pets", ["racao", "ração", "cachorro", "cachorros", "gato", "gatos", "pet", "pets", "petisco", "areia de gato",
                                      "antipulgas", "coleira", "shampoo para cachorro", "banho e tosa"],
      absent=True, shelf="pet"),
    C("casa", "casa e utilidades", ["tapete", "cortina", "travesseiro", "cobertor", "toalha de banho", "mesa", "cadeira", "panela", "prato", "copo", "talheres", "geladeira", "fogao", "microondas", "televisao", "celular", "carregador", "fone de ouvido", "notebook", "pilha", "pilhas", "bateria", "lampada", "vela", "desinfetante", "detergente", "sabao em po",
                                     "amaciante", "papel higienico", "papel toalha", "esponja de cozinha", "saco de lixo",
                                     "sabao", "limpeza da casa", "agua sanitaria", "alvejante", "guardanapo"],
      absent=True, shelf="casa"),
    C("saude_aparelhos", "aparelhos e primeiros socorros", ["cotonete", "cotonetes", "hastes flexiveis", "haste flexivel", "algodao", "bolinha de algodao", "discos de algodao", "fita adesiva", "fita micropore", "micropore", "tesoura", "pinca", "cortador", "termometro", "esfigmomanometro", "aparelho de pressao", "glicosimetro",
                                                          "curativo", "curativos", "band aid", "bandaid", "gaze", "esparadrapo",
                                                          "agua oxigenada", "alcool 70", "alcool em gel", "alcool gel", "mascara cirurgica",
                                                          "luva", "luvas", "seringa", "teste de covid", "teste rapido", "inalador",
                                                          "nebulizador", "bolsa termica"],
      absent=True, shelf="primeiros socorros"),
    # ------------------------------------------------------------------ medicamentos que o catálogo ainda não tem (doc 16)
    # resposta fixa: "Não está no banco de dados ainda." (shelf = MED_SHELF)
    C("med_ausente", "esse medicamento", ["diabetes", "insulina", "glicose alta", "ansiedade", "depressao", "antidepressivo",
                                          "calmante", "remedio para dormir", "remedio pra dormir", "remedio de dormir",
                                          "tarja preta", "antibiotico", "antibioticos", "amoxicilina", "azitromicina",
                                          "cefalexina", "anticoncepcional", "pilula anticoncepcional", "pilula do dia seguinte",
                                          "pilula", "sildenafila", "tadalafila", "impotencia", "tireoide", "levotiroxina",
                                          "asma", "bombinha", "colirio", "gotas para os olhos", "conjuntivite", "herpes",
                                          "aciclovir", "micose", "antifungico", "frieira", "candidiase", "vermifugo", "verme",
                                          "vermes", "albendazol", "piolho", "corticoide", "prednisona", "dexametasona",
                                          "infeccao urinaria", "cistite", "otite", "dor de ouvido", "dor de dente",
                                          "labirintite", "tontura", "gota", "acido urico", "osteoporose", "anemia"],
      absent=True, shelf="medicamentos"),
]

CONCEPT_BY_ID = {c.id: c for c in CONCEPTS}
GENERIC = {"suplemento", "higiene", "oral", "cabelo", "corpo", "solar", "energia", "remedio", "dor"}
MED_SHELF = "medicamentos"
MED_MISSING = "Não está no banco de dados ainda."   # perdem para um conceito mais específico da mesma família
NEGATORS = {"sem", "nao", "nada", "livre", "evitar", "evita", "tire", "tira"}
ARTICLES = {"o", "a", "os", "as", "um", "uma", "de", "do", "da"}
