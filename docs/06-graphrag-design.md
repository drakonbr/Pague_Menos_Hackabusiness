# 06 — Desenho do GraphRAG e do compositor de kits

> **21/10 (doc 16):** medicamentos entram no grafo, nos vetores, na busca e nos kits; a camada de segurança não bloqueia mais. Ver D-32 a D-36.
>
> **Status (20/10): implementado do zero em `graphrag/`**, sem Ollama nem modelo externo: grafo em networkx, vetores PPMI+SVD, BM25, ativação espalhada, classificador Naive Bayes de ato de fala e compositor K1 a K12. Onde este desenho previa modelo de linguagem para intenção e justificativa, a versão atual usa regras + classificador treinado e textos por modelo de frase. Resultados e limites no [doc 14](14-persona-e-privacidade.md).

## Por que grafo e não só RAG

RAG simples recupera trechos parecidos com a pergunta. Um kit precisa de **relações**: este ingrediente conflita com aquele, este objetivo exige estas etapas, este produto atende aquela preocupação para aquele tipo de pele. Relações são nós e arestas. O grafo responde "o que combina com o quê"; a busca vetorial cobre o que a pessoa disse em texto livre ("pele que brilha à tarde").

## Esquema do grafo

### Nós

| Nó | Origem | Propriedades principais |
| --- | --- | --- |
| `Product` | `products.json` | id, nome, tipo, forma, fps, período de uso, descrição |
| `Brand` | `products.json` | nome |
| `Ingredient` | `ingredients.json` | nome, família, função, fotossensibilizante |
| `Concern` | vocabulário | acne, oleosidade, manchas... |
| `Goal` | `goals.json` | rótulo, sinônimos |
| `Step` | `steps.json` | etapa da rotina |
| `SkinType` | vocabulário | oleosa, mista, seca, normal, sensível |
| `Claim` | `products.json` | oil free, vegano, filtro mineral... |
| `Warning` | `warnings.json` | código e texto |

### Arestas

| Aresta | Significado |
| --- | --- |
| `(Product)-[:OF_BRAND]->(Brand)` | marca |
| `(Product)-[:CONTAINS]->(Ingredient)` | composição |
| `(Product)-[:ADDRESSES]->(Concern)` | preocupação atendida |
| `(Product)-[:SUITS]->(SkinType)` | tipo de pele (ou todos) |
| `(Product)-[:COVERS]->(Step)` | etapas que preenche (hidratante com FPS cobre duas) |
| `(Product)-[:HAS_CLAIM]->(Claim)` / `[:HAS_WARNING]->(Warning)` | atributos e avisos |
| `(Ingredient)-[:CONFLICTS_WITH {severity, reason}]->(Ingredient)` | `evitar` ou `separar` |
| `(Goal)-[:TARGETS]->(Concern)` | o que o objetivo busca resolver |
| `(Goal)-[:REQUIRES {required}]->(Step)` | etapas obrigatórias e opcionais |

**Preço e estoque não entram no grafo.** São consultados ao vivo (contrato do inventário), porque mudam o tempo todo e não podem ficar velhos nem ser inventados.

## Pipeline de consulta

| # | Etapa | Como | Saída |
| --- | --- | --- | --- |
| 1 | Segurança | Regras e lista de intenções bloqueadas, antes de qualquer modelo (doc 07) | `safety.decision` |
| 2 | Intenção | Modelo com saída em esquema fixo; plano B por sinônimos de `goals.json` | objetivos, orçamento, pele, preferências, `missing` |
| 3 | Recuperação | Objetivo → preocupações → produtos; filtro por pele e preferências; reforço por busca vetorial na descrição | candidatos por etapa |
| 4 | Dados vivos | Junta preço e estoque; remove sem estoque | candidatos com preço |
| 5 | Composição | Compositor determinístico (abaixo) | kits |
| 6 | Justificativa | Modelo escreve `reason` e `rationale` a partir de fatos do grafo; nenhum número livre | textos |
| 7 | Validação | Confere invariantes do contrato; descarta kit inválido | resposta |

## Regras do compositor de kits

| Regra | Descrição |
| --- | --- |
| K1 | Nenhum produto repetido; nenhuma etapa coberta duas vezes; nenhum tipo de produto repetido |
| K2 | Só produtos com estoque, com preço do inventário |
| K3 | Total dentro do orçamento quando há orçamento. O total já tem o desconto do kit (#30): 10% com 2 itens, 12% com 3, 15% com 4 ou mais; o kit sai sempre mais barato que os itens avulsos |
| K4 | Pares `evitar` nunca no mesmo kit; pares `separar` só se os períodos de uso forem diferentes (vale para produtos que ficam na pele, não para limpeza) |
| K5 | Produto fotossensibilizante exige proteção solar no kit; se não couber, alerta `sem_protetor_no_kit` |
| K6 | Tipo de pele: produto serve se lista o tipo ou "todas"; com tipo desconhecido, preferir os de "todas" e perguntar |
| K7 | Preferência declarada (vegano, sem fragrância, sem álcool) é filtro duro |
| K8 | Etapas obrigatórias do objetivo sempre cobertas; opcionais entram no Essencial se o orçamento permitir |
| K9 | No máximo 5 itens por kit |
| K10 | Formatos (#31, 23/10): sempre **Econômico < Essencial < Completo** no preço. **Econômico** = menor total que cumpre K1 a K9. **Completo** = mais itens (etapas opcionais) e, no empate, maior relevância, até 2,4× o Econômico ou o orçamento; pode repetir itens do Essencial. **Essencial** = maior relevância com preço entre os dois, e o Completo precisa ter mais itens ou relevância maior. Sem meio-termo (ex.: só kits de 2 itens), o Essencial é o mais relevante e o Completo é a mesma cesta em versão superior: cada item igual ou do mesmo tipo com preço maior e dose maior lida do nome (mesmos ativos) ou FPS estritamente maior, ex.: dipirona 500 mg → 1 g; sabor, embalagem maior ou marca de referência não contam. Se não houver, sai o Completo do passo principal; e um 2º kit sem nada a mais que o Econômico é rotulado Essencial. O texto do Completo diz o que ele tem a mais que o Essencial (itens a mais, versões superiores ou maior relevância). Invariante M4 confere a ordem. Até 22/10 a terceira faixa era o Alternativo (marcas diferentes do Essencial) |
| K11 | Gestação ou amamentação declarada: produtos com aviso `consultar_se_gestante` saem dos kits, a resposta vem com `safety.decision = caution` e o aviso de cautela (doc 07) |
| K12 | Pedido explícito de combinação que viola K4 (ex.: retinol com ácido glicólico): o kit respeita a regra, usa um dos dois e a resposta explica por quê em `notes` |

Relevância (a calibrar com o conjunto de teste do doc 08): sobreposição de preocupações do objetivo, adequação ao tipo de pele, preferências atendidas, coerência de linha/marca no kit e faixa de preço da etapa.

Busca da combinação: por etapa, ordena candidatos e explora combinações com poda (beam search); o espaço é pequeno (poucas etapas, dezenas de candidatos), então o resultado é exato o bastante para demonstração. Se um dia precisar, o mesmo problema vira programação inteira sem mudar as regras.

## Troca de item (`swap`)

Dado o kit e a etapa, lista candidatos da mesma etapa (mesma regra K1 a K9 contra o resto do kit), com diferença de preço e compatibilidade; ao trocar, recalcula total e alertas e revalida invariantes.

## O que significa "treinar" aqui

Não há treinamento de pesos de modelo. A fase de preparação inclui:

1. Ingerir `catalog/data` no grafo e conferir contagens.
2. Gerar embeddings das descrições e montar o índice.
3. Escrever e testar o esquema de extração de intenção e os prompts de justificativa.
4. Implementar o compositor e rodar o conjunto de testes (doc 08).
5. Calibrar pesos de relevância com os casos de teste.

Como ficou: o passo 3 virou o treino do Naive Bayes de ato de fala (`artifacts/nlu_model.json`) e regras de entidade; não há prompts. Os pesos do passo 5 estão em `artifacts/weights.json`.

## Avaliação

Métricas e conjunto de consultas em `docs/08-validacao-e-qualidade.md`. Metas iniciais: **0** violações de K1 a K9 em qualquer resposta; 100% dos preços e estoques iguais ao inventário; consultas do PDF resolvidas como esperado; texto sem números fora dos dados.

Medido: ver o registro do doc 08, os resultados dos docs 14 e 15 e `graphrag/eval/report_ranking.md`.

## Estrutura real de `graphrag/`

O plano previa subpastas (`ingest/`, `retrieval/`, `composer/`, `safety/`, `llm/`). Ficou mais simples: um arquivo por peça e nenhuma pasta `llm/`, porque não há modelo de linguagem (D-23).

```
graphrag/
├── text.py, lexicon.py, spell.py              normalização, vocabulário, correção de digitação
├── data.py                                    leitura do catálogo (lista permitida; persona.json fora)
├── ontology.py, ingest.py                     ontologia Pydantic e ingestão incremental
├── graph.py, embed.py                         grafo networkx e vetores PPMI+SVD
├── retrieval.py                               BM25 + vetores + grafo, rerank MMR
├── scope.py, concepts.py                      escolha da prateleira antes do ranking
├── nlu.py, nlu_corpus.py, corpus_extra.py     ato de fala (Naive Bayes) e entidades
├── safety.py                                  regras de segurança antes de tudo
├── composer.py                                kits K1 a K12, troca, adaptação à loja
├── dialogue.py, rewrite.py, chat_stream.py    conversa sem estado, reescrita, SSE
├── train.py, artifacts/                       treino e saídas (grafo, vetores, pesos, modelo NLU)
├── service/server.py                          HTTP local (porta 8787)
├── eval/                                      calibração, conjuntos de ranking e busca, invariantes, latência
└── tests/                                     testes unitários
```

## Limitações assumidas

Catálogo sintético; relevância calibrada em poucos casos; extração de intenção em português coloquial pode errar (por isso `missing` e chips editáveis); regras de interação são simplificadas e **não** substituem revisão por profissional de saúde.
