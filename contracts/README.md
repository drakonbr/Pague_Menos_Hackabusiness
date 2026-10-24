# contracts/ — formatos trocados entre os módulos

Este é o **único ponto de acoplamento** entre `app/`, `catalog/` e `graphrag/`. Quem mudar um formato aqui precisa atualizar os três lados. O app já tem uma cópia em TypeScript (`app/src/contracts/types.ts`); este documento é a fonte.

Convenções: JSON em `camelCase`, valores em **centavos inteiros** (`priceCents`), identificadores em `snake_case` para vocabulários (`protecao_solar`), idioma dos textos: português do Brasil.

## Vocabulários

| Nome | Valores |
| --- | --- |
| `StepId` | `limpeza`, `preparo`, `tratamento`, `hidratacao`, `protecao_solar`, `protecao_corporal`, `complemento`, além das etapas de suplementos e higiene premium (ver `catalog/data/steps.json`) |
| `GoalId` | `acne`, `manchas`, `skincare_basico`, `protecao_solar`, `anti_idade`, `pele_sensivel`, `oleosidade`, `suplementos`, `higiene_premium` e as áreas de saúde (doc 16): `dor_de_cabeca`, `dor_no_corpo`, `dor_muscular`, `dor_de_barriga`, `azia`, `gripe`, `tosse`, `tosse_seca`, `dor_de_garganta`, `alergia`, `diarreia`, `prisao_de_ventre`, `enjoo` |
| `SkinType` | `oleosa`, `mista`, `seca`, `normal`, `sensível` |
| `KitTier` | `economico`, `essencial`, `completo` (era `alternativo` até 23/10) |
| `AlertCode` | `fotossensibilizante`, `consultar_se_gestante`, `evitar_contato_olhos`, `nao_usar_pele_irritada`, `teste_de_sensibilidade`, `interacao_separar_periodos`, `sem_protetor_no_kit` |

## Product

Produto já combinado com preço e estoque (o catálogo guarda os dois em arquivos separados; quem exporta junta).

```json
{
  "id": "p023",
  "name": "Gel Secativo Antiacne",
  "brand": "Clara Pele",
  "line": "tratamento_acne",
  "step": "tratamento",
  "coversSteps": ["tratamento"],
  "productType": "gel secativo",
  "form": "tube",
  "size": { "value": 15, "unit": "g" },
  "skinTypes": ["oleosa"],
  "concerns": ["acne"],
  "ingredients": ["acido_salicilico", "enxofre"],
  "fps": null,
  "usagePeriod": "dia_noite",
  "claims": ["oil free"],
  "warnings": ["nao_usar_pele_irritada"],
  "description": "…",
  "howToUse": "…",
  "priceTier": "economico",
  "priceCents": 2190,
  "listPriceCents": 2190,
  "stockQty": 31
}
```

Regras: `priceCents` e `stockQty` vêm **sempre** do inventário; `fps` só existe em protetor; `coversSteps` contém `step`.

## SearchRequest

```json
{ "query": "Quero começar a cuidar da pele até R$ 120", "budgetCents": null, "skinType": null, "preferences": [] }
```

`budgetCents`, `skinType` e `preferences` são sobrescritas explícitas (chips editados, controle de orçamento, resposta à pergunta de refinamento). Quando ausentes (`undefined`, campo omitido), o motor extrai da frase. **`budgetCents: null` significa "sem limite" escolhido de forma explícita** e não é o mesmo que omitir o campo; `skinType: null` não força nada. No JSON do exemplo acima, `null` em orçamento portanto significa "sem limite".

## SearchResponse

```json
{
  "requestId": "r_001",
  "query": "Quero começar a cuidar da pele até R$ 120",
  "safety": { "decision": "allow" },
  "intent": {
    "goals": ["skincare_basico"],
    "primaryGoal": "skincare_basico",
    "budgetCents": 12000,
    "skinType": null,
    "preferences": [],
    "missing": ["skinType"]
  },
  "clarification": {
    "id": "skinType",
    "question": "Como é a sua pele?",
    "options": [{ "value": "oleosa", "label": "Oleosa" }, { "value": "seca", "label": "Seca" }]
  },
  "kitsStatus": "ok",
  "kits": [ "<Kit>", "<Kit>" ],
  "closestKit": null,
  "products": [ "<Product>" ],
  "notes": []
}
```

| Campo | Regra |
| --- | --- |
| `safety.decision` | `allow` ou `caution` (gestação: mostra aviso, mantém kits). `blocked`, `referral` e `alternativeQuery` saíram em 21/10 (doc 16) |
| `safety.category` | Só `gestacao_e_ativos` |
| `safety.message` | Texto do aviso; nunca manda procurar médico ou farmacêutico (invariante M2) |
| `intent.pregnancy` | Verdadeiro quando a frase menciona gestação ou amamentação; itens com `consultar_se_gestante` ficam de fora (I11) |
| `intent.missing` | Informações que melhorariam o resultado (`skinType`, `budget`) |
| `clarification` | No máximo uma pergunta por resposta; nunca bloqueia os kits |
| `kitsStatus` | `ok`, `partial` (menos de 2 kits relevantes), `none_in_budget`, `not_applicable` (bloqueado) |
| `closestKit` | Preenchido quando `none_in_budget`: o kit válido de menor preço |
| `products` | Resultados individuais ordenados por relevância; só com estoque |

## Kit

```json
{
  "id": "k_r001_economico",
  "tier": "economico",
  "title": "Econômico",
  "goal": "skincare_basico",
  "items": [
    { "step": "limpeza", "product": "<Product>", "reason": "Limpeza suave para uso diário.", "alternativesCount": 9 }
  ],
  "itemsTotalCents": 7745,
  "discountPct": 10,
  "discountCents": 775,
  "totalCents": 6970,
  "listTotalCents": 7990,
  "withinBudget": true,
  "alerts": [
    { "code": "fotossensibilizante", "severity": "atencao", "text": "…", "productIds": ["p048"] }
  ],
  "rationale": "Menor preço que cobre limpeza, hidratação e proteção solar."
}
```

Invariantes que o emissor garante e o app pode assumir:

1. Nenhuma etapa aparece em dois itens (`step` único; hidratante com FPS ocupa as etapas de `coversSteps`).
2. Todo `product.stockQty > 0`.
3. `totalCents` = `itemsTotalCents − discountCents` (veja "Desconto do kit" abaixo); `itemsTotalCents` é a soma exata dos `priceCents`.
4. Se `withinBudget` é verdadeiro, `totalCents <= intent.budgetCents`.
5. Nenhum par de ingredientes `evitar` entre itens que ficam na pele. Pares `separar` só com períodos de uso diferentes, e geram o alerta `interacao_separar_periodos`.
6. Se algum item é `fotossensibilizante` e não há proteção solar no kit, o alerta `sem_protetor_no_kit` é emitido.

## Campos novos (15/10): loja, cashback, categorias e imagens

- `Product`: `cashbackPct` (premissa), `salesRank` (simulado), `categoryIds`, `images[]` (`{ src, alt, credit: { source: "Pexels", photographer, photographerUrl, pageUrl } }`). `stockQty` é o estoque **central** (entrega agendada).
- `SearchRequest.storeId` e `Intent.storeId`: loja escolhida para retirada ou expressa. Com loja, todo item de todo kit tem estoque nela. Ausente ou `null` = estoque central.
- `Kit.cashbackCents` (soma por item, arredondada para baixo) e `Kit.storeId` (loja usada na checagem de estoque).

Invariantes novas:

15. `cashbackCents` = `floor(C × (100 − discountPct) / 100)`, onde C é a soma de `floor(priceCents × cashbackPct / 100)` dos itens (cashback sobre o que a pessoa paga, desde 23/10).
16. `kit.storeId` = `intent.storeId` do pedido que gerou o kit.
(A invariante 3, estoque, passa a usar o estoque da loja quando há loja.)

## Desconto do kit (23/10, item #30)

- `Kit.itemsTotalCents`: soma avulsa dos `priceCents` (o preço de cada item hoje). É a única âncora de preço riscado do kit no app (cartão, cesta e detalhe).
- `Kit.discountPct`: 0 com 1 item, 10 com 2, 12 com 3, 15 com 4 ou mais.
- `Kit.discountCents` = `floor((itemsTotalCents × discountPct + 50) / 100)`: meio centavo arredonda para cima, com aritmética inteira, igual no motor (Python) e no app (TS).
- `Kit.listTotalCents` continua sendo a soma dos preços de tabela, só para referência.

Invariante M3: com 2 itens ou mais, `totalCents < itemsTotalCents`, e o desconto segue a regra acima. O teste de paridade usa a mesma tabela de casos nos dois lados.

## Conversa, ações e privacidade (20/10)

`SearchRequest` ganha `context` (o `context` da resposta anterior; o motor não guarda estado) e `focusProductId` (só um id). `SearchResponse` ganha:

| Campo | Regra |
| --- | --- |
| `act` | Ato de fala entendido: `busca`, `refinar`, `trocar_item`, `pergunta_produto`, `repor_medicamento`, `similar`, `entrega_frete`, `saudacao`, `agradecimento`, `afirmacao`… (13 no total) |
| `reply` | Texto da resposta na conversa |
| `suggestions` | Frases curtas para tocar |
| `action` | `none`, `show_kits`, `show_products`, `open_refill`, `add_kit_to_cart`, `delivery_info`, `delivery_quote`, `swap_options`, `show_similars` (formas em `app/src/contracts/types.ts`) |
| `context` | `{ intent, requested, excluded, kits (ids compactos), lastAct, turn, focusTier?, focusProductId? }` |
| `rewrittenQuery` | Pedido de agora + o que a conversa já sabia, numa frase (`null` se bloqueado, reposição ou sem entendimento). Só rótulos do catálogo |

`Product` ganha `domain` (`dermo`, `suplemento`, `higiene`, `medicamento`), `rx` (`null` ou `receita_simples`) e `equivalence` (`{ group, presentation: referencia|generico|similar, active, dose }`).

Regras de privacidade do contrato:

1. Nada de saúde da pessoa viaja: nem condição, nem medicamento em uso. Só a frase, o `context` e ids.
2. Desde 21/10 (doc 16), produtos com `domain = medicamento` aparecem em `products` como os outros; desde 23/10 (#40) **nunca em `kits`** (invariante M5); `rx` (`null` ou `receita_simples`) é só um dado do produto. Princípio ativo repetido segue no checador (M1, para kit forjado) e nenhum texto manda procurar profissional (M2).
3. Remédio que o catálogo não tem: `reply` = "Não está no banco de dados ainda.", sem itens.

## RAG com DeepSeek (23/10)

- `SearchRequest.allowExternal` (opcional): `true` deixa o motor consultar o serviço de linguagem externo quando não entende; `false`, `null` ou qualquer valor que não seja exatamente `true` o desliga; ausente vale o padrão do servidor (`RAG_EXTERNAL_DEFAULT`, desligado na Vercel). O app envia o que a pessoa escolheu em Privacidade e dados.
- `/v1/health` traz `rag` (a DeepSeek está ligada?) e `ragCalls` (chamadas por motivo).
- `SearchResponse.rag` (opcional, `true`): o grafo não entendeu e a resposta saiu do pedido traduzido pela DeepSeek. Só para depuração e avaliação: o app não mostra nada diferente. `query` continua sendo o texto que a pessoa digitou.
- Todas as invariantes valem igual para essas respostas (kits continuam do compositor).

## Operações do serviço de busca

| Operação | Entrada | Saída |
| --- | --- | --- |
| `search` | `SearchRequest` | `SearchResponse` |
| `swapOptions` | `Kit`, `StepId`, `Intent` | Lista de `SwapOption`: `{ product, deltaCents, compatible, reason? }`, em ordem de relevância |
| `adaptToStore` | `Kit`, `storeId`, `Intent` | `{ kit, replaced[] }` trocando só os itens sem estoque na loja, ou `null` se o kit não fecha nela |
| `swap` | `Kit`, `StepId`, `productId`, `Intent` | `Kit` revalidado (total, alertas e invariantes recalculados) |
| `similars` | `productId`, `storeId` | `{ productId, domain, storeId, inStockHere, options[] }`; cada opção traz `kind` (`equivalente` ou `parecido`), `deltaCents`, `inStock`, `storeIdsWithStock`, `needsPharmacistConfirmation` (sempre `false` desde o doc 16; mantido por compatibilidade) |
| `delivery-quote` | `totalCents` | opções de entrega com taxa e total (item + frete) |

O serviço é **sem estado**: o kit e a intenção (`Intent`, vinda da última resposta de `search`) viajam inteiros entre app e serviço, então nada precisa ser guardado no servidor para a demonstração.

Em HTTP (proposta para o GraphRAG): `POST /v1/search`, `POST /v1/kits/swap-options`, `POST /v1/kits/swap`, `POST /v1/kits/adapt-to-store`, `POST /v1/similars`, `POST /v1/delivery-quote`, `GET /v1/health` e `POST /v1/search-chat` (SSE). Implementado em `graphrag/service/server.py` (porta 8787). `POST /v1/admin/ingest` existe só com `--allow-ingest`.

### `POST /v1/search-chat` (fluxo SSE)

Corpo = `SearchRequest` + `history?: string[]` (até 3 falas anteriores; usado só se não houver `context`). Resposta `text/event-stream` com os eventos `rewrite` → `sources` → `token`* → `done`; o `done` traz o mesmo corpo de `/v1/search` mais `latencyMs`. Entrada inválida: `400` JSON antes do fluxo. Detalhes e limites no [doc 15](../docs/15-graphrag-conversacional.md).

## Serviço de comércio (`CommerceService`)

Separado do motor de kits. No sistema real, são adaptadores para serviços que já existem (catálogo, lojas, estoque, frete); no protótipo, só a versão simulada.

| Operação | Saída |
| --- | --- |
| `home()` | vitrines, atalhos de kits, categorias, banners |
| `categories()` | árvore Dermo e Beleza com `productIds` |
| `product(id)`, `products(ids, sort)` | produtos; `sort` = `relevancia`, `mais_vendidos`, `menor_preco`, `maior_preco` (sem estoque no fim) |
| `storesFor(productIds)` | lojas por distância, com `availableIds` e `missingIds` |
| `delivery()` | modalidades (retirada, expressa, agendada), taxas e limite de frete grátis (premissas) |
| `labels()` | textos de avisos, preocupações e ingredientes |

## Carrinho e checkout

Simulados dentro do app (`app/src/state/cart`). Não fazem parte deste contrato. A proposta de integração real está no doc 10.

- `Safety.decision` ganhou `"urgent"` (#63): risco de vida ou sinal de alerta; `category` é `risco_de_vida` ou `sinal_de_alerta`; `reply` e `message` trazem o texto fixo, `products`, `kits` e `suggestions` vêm vazios. O servidor ignora qualquer campo `_client` do corpo (#64).
