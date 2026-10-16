# 10 — Integração proposta com o e-commerce real

O desafio avalia se o que foi construído é plausível como ponto de partida real e se a troca de dados simulados por reais é viável sem reconstrução. Nenhuma credencial ou sistema da empresa foi usado; abaixo estão as **premissas** e os **pontos de troca**.

## Pontos de integração

| # | Sistema real (premissa) | Hoje (simulado) | Contrato | Como trocar |
| --- | --- | --- | --- | --- |
| 1 | Catálogo/PIM do e-commerce (produtos, atributos, categorias) | `catalog/data/products.json` | `Product` | Trocar a fonte da ingestão do GraphRAG por leitura do catálogo; mapear campos para o `Product` |
| 2 | Preço e promoção | `catalog/data/inventory.json` | `priceCents`, `listPriceCents` | Consulta ao serviço de preço por lote de ids, a cada busca |
| 3 | Estoque (por loja ou centro de distribuição) | `inventory.json` | `stockQty` | Consulta por CEP/loja; `stockQty` passa a ser o disponível para aquele cliente |
| 4 | Busca atual do app | tela de resultados simulada | `SearchService` | Chamar o motor de kits em paralelo à busca atual e exibir kits acima da lista existente (fallback: só a lista) |
| 5 | Carrinho | `app/src/state/cart` | itens com `productId` e quantidade | Chamar a API do carrinho existente; o kit vira N linhas com marcação do kit de origem |
| 6 | Checkout e pagamento | telas simuladas | fora do contrato | Redirecionar ao checkout existente; **a IA não toca em dados de pagamento** |
| 7 | Identidade e histórico | ausente | `SearchRequest` (campos extras) | Com consentimento, enviar histórico agregado para personalização (doc 02, fora do MVP) |
| 8 | Base de medicamentos | ausente | camada de segurança (doc 07) | Base validada por farmacêuticos; fora do escopo do MVP |

## Padrão de integração

```
App/Site existente ──▶ Gateway de IA Commerce (SearchService) ──▶ GraphRAG
                              │                                      │
                              ├── Catálogo (leitura)  ◀──────────────┤ ingestão agendada
                              ├── Preço/Estoque (consulta por lote) ◀┘ tempo real
                              └── Carrinho (escrita, API existente)
```

- **Adaptadores finos:** cada sistema real entra por um adaptador que devolve o formato do contrato; o motor não muda.
- **Sem estado no motor:** o kit viaja inteiro; carrinho e sessão ficam nos sistemas existentes.
- **Degradação segura:** se preço ou estoque falham, o motor não exibe kits (melhor sem kit do que com preço errado); a busca atual segue funcionando.
- **Feature flag:** kits ligados por experimento (grupo controle x grupo com kits) para medir impacto real (doc 02, métricas).

## Dados e privacidade

- Sem dados pessoais no motor na primeira versão.
- Personalização por histórico exigiria consentimento explícito, minimização de dados e registro de finalidade (LGPD).
- Registros de busca sem identificadores diretos; retenção curta.

## Requisitos operacionais (estimativa a validar)

| Tema | Meta inicial |
| --- | --- |
| Latência de resposta de busca com kits | até 3 s no percentil 95 (a medir) |
| Disponibilidade do motor | degradação para a busca atual sem queda do app |
| Reingestão do catálogo | diária ou por evento de mudança |
| Auditoria | registro de intenção, candidatos, kits descartados e motivo |

## Passos para um piloto real (proposta)

1. Mapear campos do catálogo real para `Product` e rodar a ingestão em ambiente de teste.
2. Ligar preço e estoque reais por lote.
3. Revisar com farmácia o escopo (só cosméticos) e os textos de aviso.
4. Piloto com feature flag em uma porcentagem pequena, medindo adição ao carrinho, conversão e ticket médio.
5. Só então avaliar a camada de medicamentos, com validação clínica.
