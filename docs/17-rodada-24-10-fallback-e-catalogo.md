# 17 — Rodada 24/10: fallback seletivo e catálogo ampliado

Registro do que foi **decidido e feito** depois da rodada de avaliação do RAG (doc 15) e da ampliação de medicamentos (doc 16). Substitui os números de catálogo/testes dos docs anteriores quando houver divergência; o histórico continua nos docs 08 e 16.

Branches: `feat/fallback-seletivo` (fallback seletivo) e `feat/catalogo-ampliado` (catálogo, itens de higiene e esta documentação).

## 1. Fallback seletivo

O problema medido: o fallback só era chamado quando o grafo **admitia** que não entendeu. Quando ele entendia errado com confiança (ex.: “ardência para urinar” → pele sensível) ou quando a cota de 20/hora estourava, o app não avisava e a resposta piorava em silêncio. Mapear gíria não resolvia a cauda longa.

### Decisões

| ID | Decisão | Por quê |
| --- | --- | --- |
| D-37 | Fallback seletivo com gate de incerteza, guarda de parte do corpo, cota visível e sugestões por ranking | Corrigir falsos positivos confiantes e a degradação silenciosa sem abrir mão das invariantes; a DeepSeek continua só entendendo, nunca compondo kit |
| D-38 | Catálogo ampliado para **297 produtos**: 68 de higiene (6 por prateleira) e 108 medicamentos (100 de busca em 16 áreas + 8 de reposição) | Pedido do usuário; itens óbvios de higiene e novas classes (antifúngico, antibiótico, antiviral e corticoide) |

### O que entrou no motor

- **Cota**: padrão de **100 chamadas/hora por cliente** (`RAG_PER_CLIENT_HOUR`) e 1.500/dia. `/v1/health` traz `quota` com `perHour`, `usedHour`, `daily` e `usedDay`. Quando o teto estoura, a resposta ganha uma nota em `notes` em vez de degradar calada.
- **Gate de incerteza**: além de `_miss`, a conferência entra quando o ato é `desconhecido` ou quando há conflito entre parte do corpo e prateleira de pele.
- **Guarda de parte do corpo**: `urina`, `xixi`, `uretra`, `bexiga`, `ouvido`, `dente`, `gengiva` + prateleira de pele → tenta corrigir; se não corrigir, responde “Não está no banco de dados ainda.”, nunca um kit de pele. Exceção: se o próprio grafo resolveu para higiene (`meu ouvido ta sujo`), a guarda não se aplica.
- **Ato**: “não consigo cagar”, “meu nariz não para de escorrer” e afins viram `busca`, não `negacao`.
- **Sugestões**: quando o grafo não entende, os chips vêm dos objetivos mais próximos pelo ranking, não de lista fixa.
- **`slang.py`**: cache determinístico de fala popular/chula de alta frequência (“me caguei”, “me borrei”, “estou peidando”, “tosse de cachorro”, “coceira nos olhos”, “pele melada”, “torci o pé”...). É atalho, **não** a solução geral; a cauda longa continua no gate/fallback.
- **Higiene + “sujo”**: “meu ouvido ta sujo”, “limpeza de ouvido”, “meu pé ta sujo”, “minha mão ta suja” passam a ir para a prateleira de higiene. “Ouvido entupido”/“dor de ouvido” continuam remédio ausente.

### O que ficou pendente (de propósito)

- Retrieval de candidatos antes do LLM.
- Saída fechada com confiança e abstenção.
- Clarificação com chips no app (hoje o componente de clarificação só sabe perguntar tipo de pele).
- Feedback loop com frases reais anonimizadas.

## 2. Catálogo ampliado

### Números finais

| Item | Antes (21/10) | Agora (24/10) |
| --- | ---: | ---: |
| Produtos | 217 | **297** |
| Higiene | 12 | **68** |
| Medicamentos | 84 | **108** |
| Áreas de saúde | 12 | **16** |
| Checagens do catálogo | 76/76 | **83/83** |
| Nós do grafo | 599 | **759** |
| Arestas do grafo | 3.261 | **4.361** |
| Vocabulário dos vetores | 1.361 | **1.530** |
| Testes do GraphRAG | 95 | **173** |
| Testes do app | 46 | **103** |

### Higiene (68 itens, 6 por prateleira)

- **Corpo (26):** sabonetes, gel/óleo de banho, esfoliante, talco corporal e para pés, buchas, esponjas, cotonetes, lenços, algodão e **limpeza auricular** (spray, solução e lenços).
- **Cabelo (18):** shampoos (incluindo anticaspa), condicionador, máscara, **6 cremes para pentear/leave-in**, escovas e pentes.
- **Bucal (18):** cremes dentais, enxaguantes, **6 escovas de dente** e **6 fios/fitas dentais**.
- **Desodorante (6):** roll-on, aerossol, creme, stick e spray.

Os IDs antigos (p001–p217) foram preservados. Os 24 medicamentos novos são p218–p241; os 56 itens de higiene novos são p242–p297.

### Medicamentos (108 itens: 100 de busca em 16 áreas + 8 de reposição)

Além das 12 áreas originais, entraram 4 classes com **6 itens cada**:

| Classe | Itens | Exemplos |
| --- | ---: | --- |
| Antifúngico | 6 | clotrimazol, miconazol, cetoconazol, terbinafina, fluconazol, nistatina |
| Antibiótico | 6 | amoxicilina, azitromicina, cefalexina, ciprofloxacino, doxiciclina, metronidazol |
| Antiviral | 6 | aciclovir, penciclovir, valaciclovir, oseltamivir, famciclovir |
| Corticoide | 6 | hidrocortisona, betametasona, mometasona, prednisona, dexametasona, budesonida |

Regras mantidas: remédio **nunca entra em kit** (K13), os de prescrição levam `rx = receita_simples` e ficam fora de vitrines, e nenhum texto manda procurar médico ou farmacêutico (M2).

### Categorias e app

- `generate_commerce.py` ganhou as categorias “Antifúngicos”, “Antibióticos”, “Antivirais” e “Corticoides”.
- `hygiene_products.py` é a fonte dos itens novos; `generate_catalog.py` concatena os produtos **depois** dos existentes para não mudar ids.
- `tools/export_app_mock.py` exporta os 297 produtos, lojas, categorias e estoque por loja para o app.
- `app/tests/persona.test.ts` foi ajustado: “quero meu remédio” saiu da lista de pedidos que não são de remédio (com as novas classes, ele passou a ser um pedido de remédio de verdade).

## 3. Medições da rodada

- **Catálogo**: `python3 catalog/validate_catalog.py` → **83/83**.
- **GraphRAG**: `python3 -m unittest discover -s graphrag/tests -t .` → **173/173**.
- **App**: `npm test` → **103/103**; `npm run build` → ok.
- **Teste de fallback (25 frases)**: antes, com cota padrão, o fallback consertava 3 de 25; com a cota desligada, 8 de 25. Depois do gate + guardas + `slang.py`, as frases dentro do catálogo passaram a responder direto; as fora do catálogo (ardência para urinar, dor de ouvido, afta) passaram a dizer isso explicitamente.
- **Buscas novas verificadas**: “fio dental” 6, “escova de dente” 6, “creme para pentear” 6, “talco” 6, “antibiótico” 6, “micose” 6, “meu ouvido ta sujo” 6 (auricular).

## 4. Limites que continuam

- O fallback ainda não faz retrieval de candidatos nem escolha com confiança; a correção de falso positivo depende das guardas.
- As novas classes de medicamento são **busca**, não recomendação: não entram em kit e não têm validação clínica.
- “6 por tipo” foi implementado como **6 por prateleira de higiene** e **6 por classe nova de remédio**; subtipos (ex.: condicionador, enxaguante) têm menos.
- Os itens de limpeza auricular são sintéticos e não substituem orientação de profissional; o catálogo não tem produto para o canal auditivo interno.
- A cota vive na memória de cada instância; na Vercel, múltiplas instâncias e cold start furam o teto.
