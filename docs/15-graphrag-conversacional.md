# 15 — GraphRAG conversacional: ontologia, ingestão e busca em fluxo

Rodada de 20/10 (tarde). Parte do que o Gemini sugeriu como prompt para "backend GraphRAG de barra de pesquisa conversacional" foi aplicada; parte ficou de fora de propósito (seção 6).

## 1. Ontologia (`graphrag/ontology.py`)

Esquema estrito em Pydantic. O grafo atual (329 nós, 2197 arestas) passa em `validate_graph` e o treino falha se sair da ontologia. O esquema também é gravado em `graphrag/artifacts/ontology.schema.json`.

**Nós** (12): `product`, `brand`, `ptype`, `domain`, `step`, `concern`, `ingredient`, `warning`, `skin`, `claim`, `goal`, `equiv`.
Vocabulário **fechado** (só vem do catálogo-base): etapa, preocupação, ingrediente, aviso, tipo de pele, domínio, objetivo. Vocabulário **aberto** (a ingestão pode criar): marca, tipo de produto, alegação.

**Arestas** (15, cada uma só liga um par de tipos):

| Aresta | Liga | Aresta | Liga |
| --- | --- | --- | --- |
| `OF_BRAND` | produto → marca | `TARGETS` | objetivo → preocupação |
| `OF_TYPE` | produto → tipo | `REQUIRES` | objetivo → etapa |
| `IN_DOMAIN` | produto → domínio | `CONFLICTS_WITH` | ingrediente → ingrediente |
| `COVERS` | produto → etapa | `IN_EQUIV_GROUP` | produto → grupo de equivalência |
| `ADDRESSES` | produto → preocupação | `EQUIVALENT_TO` | produto → produto (só medicamento) |
| `CONTAINS` | produto → ingrediente | `SIMILAR_TO` | produto → produto (calculada) |
| `SUITS` | produto → tipo de pele | `HAS_CLAIM` / `HAS_WARNING` | produto → alegação / aviso |

Preço e estoque não são nós (consulta viva).

## 2. Ingestão incremental (`graphrag/ingest.py`)

```bash
python3 -m graphrag.ingest novos_produtos.json --dry-run   # mostra o que aconteceria
python3 -m graphrag.ingest novos_produtos.json             # grava em graphrag/artifacts/delta_products.json
python3 -m graphrag.service.server --allow-ingest          # opcional: POST /v1/admin/ingest com o motor no ar
```

- **Entrada**: lista de `ProductRecord` (campos do contrato `Product`). Registro fora do esquema é recusado com o motivo; um registro ruim não derruba o lote.
- **Resolução de entidades**: vocabulário fechado casa por id ou rótulo sem acento nem caixa (se não casar, recusa); vocabulário aberto casa por texto normalizado (`ESSÊNCIA NUTRI` = `Essência Nutri`, sem marca duplicada) e cria nó só se for realmente novo. Produto com mesma marca e nome é o mesmo produto: sem `id`, atualiza o existente; com `id` diferente, é recusado como duplicata. Reenviar o mesmo lote não muda nada.
- **Escrita**: só em `graphrag/artifacts/delta_products.json` (nunca em `catalog/`). O motor sobe com catálogo-base + delta; `Engine.ingest` aplica o mesmo delta sem reiniciar. Um teste confere que o motor atualizado em memória fica **idêntico** (nós, arestas, pesos, produtos) a um motor reconstruído do zero a partir do delta.
- **Vetores**: não são retreinados na ingestão. O vetor do produto novo é a média das palavras que o vocabulário já conhece; as desconhecidas saem em `oovTokens`. `python3 -m graphrag.train` incorpora as novas.
- **Medicamento ingerido** continua fora de busca livre e de kits (testado).
- A ingestão aqui é **determinística, sem modelo de linguagem**: o catálogo já é estruturado, então "extrair" é validar e resolver. Extração por LLM só faria sentido para texto solto (bulas, descrições de fornecedor), que não é o caso.

## 3. Busca em fluxo (`POST /v1/search-chat`, SSE)

Corpo: o mesmo de `/v1/search` mais `history` opcional (até 3 falas anteriores da pessoa; sem `context`, o motor reexecuta essas falas para reconstruir o estado). Eventos, nesta ordem:

| Evento | Conteúdo |
| --- | --- |
| `rewrite` | `rewrittenQuery` (ex.: "Cuidado antissinais, sem retinol, até R$ 331,08") e `act` |
| `sources` | cartões prontos: `kits[]` (itens com preço), `products[]` (id, nome, marca, preço, estoque) |
| `token` | pedaços da resposta (vários) |
| `done` | resposta completa (igual a `/v1/search`: `context`, `action`, `suggestions`, `safety`...) + `latencyMs` |

Erro de validação (query vazia, maior que 500 caracteres, `history` fora do formato) volta como **400 JSON** antes de abrir o fluxo.

**Honestidade sobre o "streaming"**: o texto da resposta é montado por regras, não gerado por modelo; fica pronto junto com os cartões. O fluxo existe para a tela desenhar o chip e os cartões primeiro e a resposta aos poucos, e deixa o contrato pronto para o dia em que um modelo gerar o texto. Não há espera artificial entre eventos. O app ainda **não** consome esse endpoint (usa `/v1/search`).

## 4. Reescrita pelo histórico e rerank

- **Reescrita** (`rewrite.py`): junta o pedido atual ao que a conversa já sabia. A recuperação usa o estado estruturado (`context`), que é mais exato que reescrever texto; a frase serve para mostrar o que foi buscado. Usa só rótulos do catálogo, nunca o texto digitado.
- **Rerank** (`Retriever.rerank_mmr`, relevância marginal máxima): medido em `graphrag/eval/rerank_eval.py` nas 30 frases do conjunto de ranking. Com λ = 0,9: nDCG@10 igual ao sem rerank (treino 0,8637 contra 0,8636; teste 1,0 contra 1,0) e tipos distintos no top 5 de 3,5 para 3,57. Com λ = 0,7 a relevância já cai um pouco (teste 0,99) e com λ = 0,5 cai bastante (teste 0,89). O ganho é **pequeno** e foi ligado em 0,9 só na lista de produtos.

## 5. Latência (`graphrag/eval/latency.py`)

Máquina de desenvolvimento, 18 frases × 5 repetições, uma pessoa por vez, catálogo de 138 produtos:

| Medida | p50 | p95 | máx |
| --- | --- | --- | --- |
| Busca nova em processo | 2,4 ms | 118 ms | 160 ms |
| Turno com contexto | 0,3 ms | 3,8 ms | 101 ms |
| SSE até o 1º evento | 3,7 ms | 114 ms | 181 ms |

A frase mais lenta ("rotina anti idade premium até R$ 400, sem retinol") leva cerca de 200 ms: é o compositor de kits com orçamento. Não paralelizei vetor e grafo: em Python (GIL) threads não aceleram estas contas, e o total já é pequeno. Com catálogo real (milhares de produtos) isto precisa ser remedido.

## 6. O que do prompt do Gemini ficou de fora, e por quê

| Sugestão | Decisão |
| --- | --- |
| Extração de entidades por LLM com *Structured Outputs* | **Não**: decisão de 20/10 de não usar modelo externo nem Ollama; o catálogo já é estruturado; extração por LLM pode inventar nó; dado confidencial não deve sair da máquina. Substituída por esquema Pydantic + resolução de entidades |
| Resposta gerada por LLM em streaming | **Não**: o texto determinístico garante, com teste, que nenhuma resposta traz termo de saúde nem nome de medicamento (doc 14) |
| Rerank por LLM | **Não**: trocado por MMR medido |
| FastAPI, PostgreSQL com pgvector e Apache AGE, Neo4j, ChromaDB | **Não** agora: o servidor usa a biblioteca padrão, networkx e numpy (D-23). Para produção, o contrato `/v1/search-chat` e a ontologia valem para qualquer banco |
| Busca em paralelo | Medida, não implementada (seção 5) |

## 7. Defeitos achados e corrigidos nesta rodada

Ao testar termos curtos na barra (o prompt pede isso), 5 de 40 caíam no ato errado: "ômega 3", "creme dental", "sabonete" e "limpeza" viravam *trocar item* e "sérum" virava *pergunta sobre produto*, todos sem nada para trocar. Agora, sem conversa anterior e sem pista de que a pessoa aponta para algo ("troque", "esse", "?"), um termo solto é uma busca nova. Também: quando nenhum kit fecha com as preferências, a resposta antes misturava produtos de outras etapas ("ômega 3 vegano" trazia hidratante); agora mostra só produtos do objetivo e diz que não fechou um kit.

## 8. Limites

- As 40 frases curtas foram escolhidas por mim; não são um conjunto de teste independente. Cinco foram corrigidas e viraram teste de regressão; "dormir melhor" continua sendo lido como negação (sem sinônimo no léxico).
- O conjunto de ranking continua pequeno (30 frases, 14 de teste).
- Ingestão: produtos novos não ganham foto, categoria nem estoque por loja, a menos que venham no registro; o app (mock estático) não os enxerga até exportar.
- A API de ingestão não tem autenticação; por isso só liga com `--allow-ingest` e em `127.0.0.1`.
