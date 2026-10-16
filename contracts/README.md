# contracts/ — formatos trocados entre os módulos

Este é o **único ponto de acoplamento** entre `app/`, `catalog/` e `graphrag/`. Quem mudar um formato aqui precisa atualizar os três lados. O app já tem uma cópia em TypeScript (`app/src/contracts/types.ts`); este documento é a fonte.

Convenções: JSON em `camelCase`, valores em **centavos inteiros** (`priceCents`), identificadores em `snake_case` para vocabulários (`protecao_solar`), idioma dos textos: português do Brasil.

## Vocabulários

| Nome | Valores |
| --- | --- |
| `StepId` | `limpeza`, `preparo`, `tratamento`, `hidratacao`, `protecao_solar`, `protecao_corporal`, `complemento` |
| `GoalId` | `acne`, `manchas`, `skincare_basico`, `protecao_solar`, `anti_idade`, `pele_sensivel`, `oleosidade` |
| `SkinType` | `oleosa`, `mista`, `seca`, `normal`, `sensível` |
| `KitTier` | `economico`, `essencial`, `alternativo` |
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
| `safety.decision` | `allow`, `caution` (mostra aviso, mantém kits) ou `blocked` (sem kits; ver doc 07) |
| `safety.category` | Quando não é `allow`: `medicamento`, `sintoma`, `condicao_de_saude`, `gestacao_e_ativos` |
| `safety.message`, `safety.referral` | Texto exibido e encaminhamento sugerido |
| `safety.alternativeQuery` | Só em `blocked`: consulta cosmética oferecida como alternativa (ex.: pedido sobre espinhas inflamadas → "tratamento de acne"). O app a mostra como botão |
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
  "totalCents": 6970,
  "listTotalCents": 6970,
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
3. `totalCents` é a soma exata dos `priceCents`.
4. Se `withinBudget` é verdadeiro, `totalCents <= intent.budgetCents`.
5. Nenhum par de ingredientes `evitar` entre itens que ficam na pele. Pares `separar` só com períodos de uso diferentes, e geram o alerta `interacao_separar_periodos`.
6. Se algum item é `fotossensibilizante` e não há proteção solar no kit, o alerta `sem_protetor_no_kit` é emitido.

## Campos novos (15/10): loja, cashback, categorias e imagens

- `Product`: `cashbackPct` (premissa), `salesRank` (simulado), `categoryIds`, `images[]` (`{ src, alt, credit: { source: "Pexels", photographer, photographerUrl, pageUrl } }`). `stockQty` é o estoque **central** (entrega agendada).
- `SearchRequest.storeId` e `Intent.storeId`: loja escolhida para retirada ou expressa. Com loja, todo item de todo kit tem estoque nela. Ausente ou `null` = estoque central.
- `Kit.cashbackCents` (soma por item, arredondada para baixo) e `Kit.storeId` (loja usada na checagem de estoque).

Invariantes novas:

15. `cashbackCents` = soma de `floor(priceCents × cashbackPct / 100)` dos itens.
16. `kit.storeId` = `intent.storeId` do pedido que gerou o kit.
(A invariante 3, estoque, passa a usar o estoque da loja quando há loja.)

## Operações do serviço de busca

| Operação | Entrada | Saída |
| --- | --- | --- |
| `search` | `SearchRequest` | `SearchResponse` |
| `swapOptions` | `Kit`, `StepId`, `Intent` | Lista de `SwapOption`: `{ product, deltaCents, compatible, reason? }`, em ordem de relevância |
| `adaptToStore` | `Kit`, `storeId`, `Intent` | `{ kit, replaced[] }` trocando só os itens sem estoque na loja, ou `null` se o kit não fecha nela |
| `swap` | `Kit`, `StepId`, `productId`, `Intent` | `Kit` revalidado (total, alertas e invariantes recalculados) |

O serviço é **sem estado**: o kit e a intenção (`Intent`, vinda da última resposta de `search`) viajam inteiros entre app e serviço, então nada precisa ser guardado no servidor para a demonstração.

Em HTTP (proposta para o GraphRAG): `POST /v1/search`, `POST /v1/kits/swap-options`, `POST /v1/kits/swap`, `POST /v1/kits/adapt-to-store`.

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
