# 05 — Catálogo sintético

Módulo: `catalog/`. Status: **gerado e validado** (138 produtos, 69 de 69 checagens). Os 100 primeiros são os de skin care; **p101 a p138** (20/10) atendem a persona Renata: 12 suplementos e 12 itens de higiene premium (3 por tipo), 6 dermocosméticos anti-idade e 8 itens de reposição (genéricos fictícios, `rx`, `equivalence`, estoque por loja forçado a zero em alguns casos para exercitar equivalentes). Geração em `catalog/persona_products.py` e `generate_persona.py`; a persona vive em `data/persona.json` e nunca é lida pelo motor.

## Objetivo

Dar ao GraphRAG e ao app uma base realista, **sem usar nenhum dado do cliente**. O desafio permite base sintética construída a partir das categorias do catálogo público; aqui nenhum dado foi copiado: marcas, nomes, preços, estoque e fórmulas são inventados.

## O que tem

| Etapa da rotina | Produtos | Exemplos de tipo |
| --- | --- | --- |
| `limpeza` | 14 | gel, espuma, água micelar, óleo, sabonete |
| `preparo` | 8 | tônico, esfoliante químico, máscara de argila |
| `tratamento` | 34 | sérum, gel secativo, adesivo, retinol, vitamina C (linhas acne, manchas, anti-idade) |
| `hidratacao` | 16 | gel, creme, gel-creme, 3 hidratantes com FPS |
| `protecao_solar` | 16 | protetor facial (toque seco, com cor, mineral, vegano) |
| `protecao_corporal` | 6 | loção, spray |
| `complemento` | 6 | protetor labial, contorno dos olhos, bálsamo |
| **Total** | **100** | |

A tabela cobre os 100 de skin care. Os 38 da persona (p101–p138) estão descritos no status acima.

Preços de R$ 12,90 a R$ 139,90 nos 100 de skin care (até R$ 169,90 no catálogo todo). Sete marcas fictícias com posicionamentos diferentes (premium, intermediária, vegana, linha própria, preço mais baixo). Cada etapa central (limpeza, tratamento, hidratação, proteção solar) tem produtos nas três faixas (`economico`, `intermediario`, `premium`, calculadas por tercil de preço dentro da etapa). É isso que permite montar kits de preços diferentes.

## Modelo de dados

### Produto (`products.json`)

| Campo | Significado |
| --- | --- |
| `id` | `p001` a `p138` (p101–p138 da persona) |
| `step` | Etapa principal da rotina |
| `covers_steps` | Etapas que o produto cobre. Hidratante com FPS cobre `hidratacao` e `protecao_solar` |
| `product_type`, `form` | Tipo (gel, sérum...) e forma da embalagem (usada para o desenho do placeholder no app) |
| `skin_types` | `oleosa`, `mista`, `seca`, `normal`, `sensível` ou `todas` |
| `concerns` | Preocupações atendidas (acne, oleosidade, poros, manchas, ressecamento, sinais de idade, sensibilidade, proteção solar, olheiras...) |
| `ingredients` | Ids de ingredientes |
| `fps` | Só em protetores (e obrigatório neles) |
| `usage_period` | `dia`, `noite` ou `dia_noite` |
| `claims` | Ex.: oil free, não comedogênico, vegano, filtro mineral |
| `warnings` | Códigos de aviso (`fotossensibilizante`, `consultar_se_gestante`...) |
| `description`, `how_to_use` | Texto usado na busca semântica e na tela |
| `price_tier` | Faixa dentro da etapa |

### Preço e estoque (`inventory.json`)

`price_cents`, `list_price_cents` (preço de tabela, maior que o preço em ~15% dos produtos), `stock_qty`, `updated_at`. Seis produtos têm estoque central zero de propósito (p012, p047, p076, p088, p093 e p114), para exercitar a regra "só recomendar o que há em estoque".

### Conhecimento de domínio

- `ingredients.json`: 29 ingredientes, com marca de fotossensibilizante.
- `interactions.json`: 9 pares. `evitar` = nunca no mesmo kit (ex.: retinol com ácido glicólico). `separar` = só se um for de dia e o outro de noite (ex.: vitamina C com retinol). A regra vale entre produtos que ficam na pele; limpezas são enxaguadas e ficam de fora.
- `goals.json`: 7 objetivos (acne, manchas, rotina básica, proteção solar, antissinais, pele sensível, oleosidade), cada um com etapas obrigatórias, opcionais, preocupações-alvo e sinônimos em português.
- `warnings.json`: texto de cada aviso.

Esses arquivos de domínio viram nós e arestas do grafo (doc 06).

## Como é gerado

`python3 catalog/generate_catalog.py`. Determinístico: seed 42 e data de atualização fixa. Duas execuções produzem os mesmos arquivos. A tabela de produtos está escrita à mão no gerador (uma linha por produto), e os textos de descrição e modo de uso são montados por modelo de frase a partir dos campos.

## Como é conferido

`python3 catalog/validate_catalog.py` roda 69 checagens (eram 31 em 15/10; cresceram com lojas, imagens e a persona) e sai com código 1 se alguma falhar:

| Grupo | O que confere |
| --- | --- |
| Estrutura | tamanho entre 130 e 145, ids únicos, par (marca, nome) único, inventário cobre todos os produtos |
| Campos | obrigatórios preenchidos; etapa, período, pele e faixa dentro dos vocabulários; ingredientes e avisos existem |
| Preço e estoque | centavos inteiros e positivos; preço de tabela >= preço; há itens sem estoque; faixa ampla (mais barato até R$ 15,00, mais caro de R$ 120,00 para cima) |
| FPS | só em protetores, obrigatório neles, valor entre 15 e 100 |
| Segurança do texto | sem "remédio", "medicamento", "antibiótico", "cura" etc.; ingrediente fotossensibilizante gera aviso; retinol gera aviso de gestação |
| Interações | só citam ingredientes existentes; severidade válida |
| Viabilidade | as 3 faixas de preço existem com estoque nas etapas centrais; o kit mais barato de cada objetivo custa até R$ 100; mínimo de 4 tratamentos relevantes para acne, manchas e antissinais |
| SQLite | contagens e integridade batem com o JSON |

Estimativa do validador para o kit mínimo (soma do item mais barato em estoque de cada etapa obrigatória; é uma estimativa, não um kit composto): acne R$ 44,70; manchas R$ 58,70; rotina básica R$ 49,70; proteção solar R$ 49,80; pele sensível R$ 49,70; oleosidade R$ 49,70; antissinais R$ 89,60. O exemplo do PDF ("começar a cuidar da pele até R$ 120") é viável. O compositor do app chega a valores diferentes quando um produto cobre duas etapas (rotina básica Econômica: R$ 44,80 com hidratante com FPS, contra R$ 49,70 da estimativa) e confirma o de acne (R$ 44,70).

O validador foi testado com defeitos injetados (FPS em produto sem filtro, texto com "remédio", aviso removido, id duplicado) e reprovou todos.

## Ecossistema (`generate_commerce.py`, roda junto com o gerador)

| Arquivo | Conteúdo |
| --- | --- |
| `stores.json` | 8 lojas fictícias no Recife, perto da persona (bairros reais só para o mapa; ruas inventadas), porte grande/média/pequena, horário |
| `store_stock.json` | estoque de cada produto em cada loja (1.104 linhas: 138 × 8). Lojas pequenas têm menos itens e menos premium; produto esgotado no centro é zero em todas |
| `commerce.json` | cashback por produto (0, 2, 3, 5 ou 10%; 27 produtos com cashback), ranking de vendas simulado, modalidades de entrega com taxas (premissas), frete grátis a partir de R$ 150, vitrines e atalhos de kits |
| `categories.json` | árvore "Dermo e Beleza" com os nomes do menu público (Rosto, Pele por tipo, Protetores Solares Faciais/Corporais, Cosméticos Veganos...), já resolvida em ids; "Bastão" ficou de fora por não ter produto |
| `images.json` | só depois da revisão das fotos (ver `catalog/images/README.md`) |

Disponibilidade (21/10): as lojas têm de 64 a 122 dos 138 produtos com estoque; todos os objetivos fecham em todas as lojas pela regra do validador, mas um kit específico pode não estar completo numa loja (no teste de acne, 7 de 8 lojas tinham algum item faltando), e é isso que a tela de retirada mostra.

## Limites

- Dados fictícios; fórmulas e concentrações não foram revisadas por profissional de saúde ou dermatologia.
- Descrições geradas por modelo de frase: bons para demonstrar a busca, não para publicar.
- Sem imagens: o app desenha um placeholder por forma de embalagem.
- Escopo propositalmente sem medicamentos (doc 07).

## Onde entram os dados reais

Ver `docs/10-integracao-proposta.md`: `products.json` vira leitura do catálogo do e-commerce; `inventory.json` vira consulta de preço e estoque em tempo real; o formato exportado para o app já segue o contrato em `contracts/`.
