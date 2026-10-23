# 04 — Arquitetura

Status (21/10): os três módulos existem. `graphrag/` foi implementado do zero em 20/10 (docs 06, 14 e 15). O desenho abaixo continua valendo; onde a implementação mudou o plano, está marcado.

## Visão geral

```
                    ┌──────────────────────────────── app/ (React + TS) ───────────────────────────────┐
  pessoa ──frase──▶ │  Telas  ──▶  SearchService (interface do contrato)                               │
                    │                 ├─ HttpSearchService   (padrão: GraphRAG local, porta 8787)       │
                    │                 └─ MockSearchService   (reserva, se o servidor não responder)     │
                    └──────────────────────────────────────────────────────────────────────────────────┘
                                                      │  contracts/  (SearchRequest / SearchResponse / Kit)
                                                      ▼
   ┌───────────────────────────────────── graphrag/ (do zero) ─────────────────────────────────────────┐
   │ 1 Segurança ─▶ 2 Intenção ─▶ 3 Recuperação em grafo + vetor ─▶ 4 Dados vivos ─▶ 5 Compositor ─▶ 6 │
   │   (regras)     (extração)      (produtos candidatos)           (preço/estoque)    de kits    Texto│
   └──────────▲────────────────────────────────────────────────────────────────▲──────────────────────┘
              │ ingestão (só leitura)                                           │ consulta em tempo real
   ┌──────────┴───────────┐                                         ┌───────────┴───────────┐
   │ catalog/ (fictício)  │                                         │ inventário (simulado) │
   │ products, ingredients│                                         │ hoje: inventory.json  │
   │ interactions, goals  │                                         │ real: ERP / estoque   │
   └──────────────────────┘                                         └───────────────────────┘
```

## Módulos e responsabilidades

| Módulo | Faz | Não faz |
| --- | --- | --- |
| `catalog/` | Gera e valida o banco fictício; exporta arquivos | Não conhece o app nem o GraphRAG |
| `app/` | Telas, estado do carrinho, serviço de busca (interface + implementação simulada) | Não lê `catalog/`; não decide regra de kit em produção |
| `graphrag/` | Segurança, interpretação, recuperação, composição de kits, texto de justificativa | Não desenha telas; não inventa preço |
| `contracts/` | Define formatos | Não tem código |
| `tools/` | Pontes de mão única e checagens entre módulos | Não é importado por nenhum módulo |

### Regras de separação (checadas por `tools/check_separation.py`)

1. `catalog/` não referencia `app/` nem `graphrag/`.
2. `app/src` não referencia `catalog/` nem `graphrag/` (os dados simulados chegam como JSON gerado por `tools/export_app_mock.py`).
3. `graphrag/` só lê de `catalog/data/` e de um inventário; não escreve lá.
4. ~~`graphrag/` contém apenas README~~: valeu até 20/10 (fase pré-RAG). Hoje só é exigida com `check_separation.py --phase pre-rag`.

## Fluxo de uma busca (alvo)

1. **Segurança** (regras antes de qualquer modelo): pedido de medicamento, sintoma ou condição de saúde é bloqueado, sem kits.
2. **Intenção**: extrai objetivo(s), orçamento, tipo de pele e preferências em um objeto estruturado; o que faltar vira `missing`.
3. **Recuperação**: a partir dos objetivos, caminha no grafo (objetivo → preocupações → produtos; objetivo → etapas) e complementa com busca vetorial sobre a descrição para sinais em texto livre.
4. **Dados vivos**: junta preço e estoque do inventário. Produto sem estoque sai.
5. **Compositor de kits** (determinístico): escolhe um produto por etapa, respeitando regras K1 a K10 (doc 06) e gera econômico, essencial e completo.
6. **Texto**: o modelo escreve só a justificativa de cada item a partir de fatos estruturados; números vêm dos dados.
7. **Validação final**: confere as invariantes do contrato; kit que viola é descartado.

O modelo de linguagem **interpreta e explica**. Quem escolhe e confere é código.

> Como ficou (D-23): não há modelo de linguagem. A intenção vem de regras sobre o léxico mais um classificador Naive Bayes de ato de fala; a justificativa vem de modelos de frase. Antes do ranking, a busca escolhe a prateleira (`scope.py`, doc 15). O princípio continua: quem escolhe e confere é código.

## Dois serviços no app (desde 15/10)

- `SearchService`: motor de kits (GraphRAG local, com o simulado como reserva). Operações: `search`, `swapOptions`, `swap`, `adaptToStore`, `similars`.
- `CommerceService`: catálogo, lojas, estoque por loja, frete, categorias e vitrines. No sistema real, adaptadores para os serviços que já existem (doc 10); no protótipo, simulado a partir de `catalog/` pela ponte de mão única.

O app só fala com essas duas interfaces. As telas não importam nada de `services/mock/`.

## Fronteira app ↔ motor

O app só conhece `SearchService`. A implementação é escolhida por `VITE_SEARCH_BACKEND=auto|mock|http`; o padrão `auto` (`AutoSearchService`, D-26) tenta o GraphRAG em `/v1/health` e cai no simulado se ele não responder, inclusive no meio da sessão. O serviço é sem estado: o kit viaja inteiro nas chamadas de troca.

## Dados em tempo de execução

| Dado | Onde vive | Quando muda |
| --- | --- | --- |
| Cadastro do produto, ingredientes, regras | Grafo (ingerido do catálogo) | Reingestão |
| Descrição para busca semântica | Índice vetorial | Reingestão |
| Preço e estoque | Inventário, consultado a cada busca | Tempo real |
| Carrinho | Estado do app (simulado) | Sessão |

## Escolhas que estavam em aberto (fechadas em 20/10)

| Tema | Opções | Critério |
| --- | --- | --- |
| Grafo | Neo4j; Kùzu (embarcado); NetworkX em memória | Simplicidade de demonstrar e de explicar a migração |
| Vetores | Índice no próprio grafo; FAISS/Chroma local | Latência e dependências |
| Modelo | API de LLM ou modelo local | Custo, privacidade e qualidade em português |

Decidido (D-23): NetworkX em memória, vetores PPMI+SVD próprios em numpy, sem modelo de linguagem nem API externa. Neo4j fica como opção para produção. P-01 a P-03 estão fechadas no doc 09.

## Observabilidade proposta

Cada resposta carrega `requestId` e registra: intenção extraída, candidatos, kits descartados e motivo, tempo por etapa. Serve para depurar relevância e para a avaliação do doc 08.
