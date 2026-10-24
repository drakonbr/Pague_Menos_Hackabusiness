# catalog/ — banco de dados FICTÍCIO

Catálogo sintético de 297 produtos: 100 de skin care, tratamento cosmético e proteção solar; 6 dermocosméticos anti-idade; 15 suplementos; 68 itens de higiene (6 por prateleira, incluindo creme para pentear, escovas, fio dental, talco, buchas, cotonetes e limpeza auricular); 8 itens de reposição fictícios; e 108 medicamentos (100 de busca em 16 áreas de saúde, incluindo antifúngicos, antibióticos, antivirais e corticoides em `medicines.py`). **Todos os dados são inventados.** Itens de reposição só servem à tela de reposição; o motor nunca os recomenda.

Este módulo é independente: não importa nada de `app/` nem de `graphrag/`. Ele só gera arquivos de dados.

## Conteúdo

| Arquivo | O que é |
| --- | --- |
| `generate_catalog.py` | Gerador determinístico (seed fixa) |
| `validate_catalog.py` | 83 checagens automáticas; sai com código 1 se algo falhar |
| `persona_products.py`, `generate_persona.py` | produtos p101–p138 e `data/persona.json` (dados da persona; ficam no aparelho e o motor não os lê) |
| `hygiene_products.py` | 56 itens de higiene adicionais (p242–p297), incluindo escovas, fio dental, creme para pentear, talco, buchas e limpeza auricular |
| `data/products.json` | Cadastro dos produtos (equivale ao PIM/catálogo real) |
| `data/inventory.json` | Preço e estoque por produto (equivale ao ERP/estoque real) |
| `data/ingredients.json` | Ingredientes (família, função, fotossensibilizante) |
| `data/interactions.json` | Pares de ingredientes que não combinam (`evitar`) ou pedem períodos diferentes (`separar`) |
| `data/goals.json` | Objetivos de compra, etapas obrigatórias/opcionais e sinônimos |
| `data/warnings.json` | Texto dos avisos exibidos ao consumidor |
| `data/steps.json` | Etapas da rotina |
| `data/catalog.sqlite` | Mesmos dados em SQLite (para consultas e para a ingestão) |

## Como rodar

```bash
python3 catalog/generate_catalog.py     # gera os arquivos em catalog/data/
python3 catalog/validate_catalog.py     # confere (83 checagens)
```

Rodar o gerador duas vezes produz arquivos idênticos.

## Por que preço e estoque ficam em arquivo separado

Num sistema real, o cadastro do produto muda pouco e o preço/estoque mudam o tempo todo, em sistemas diferentes. Manter a separação aqui deixa a troca por dados reais direta: `products.json` vira a leitura do catálogo e `inventory.json` vira a consulta de preço/estoque. Ver `docs/10-integracao-proposta.md`.

## Marcas fictícias

Aurora Dermo (premium dermocosmética), Lume Lab (ativos, faixa intermediária), Solare (sol), Clara Pele (foco em pele oleosa e acne), Vita Verde (vegana), Pura Base (linha própria, preço baixo), Bem Simples (preço mais baixo). Qualquer semelhança com marcas reais é coincidência.

## Detalhes completos

`docs/05-catalogo-sintetico.md`.

## Ecossistema e imagens (15/10)

- `generate_commerce.py` roda junto com `generate_catalog.py` e cria lojas, estoque por loja, cashback, vitrines e categorias (doc 05).
- `images/`: banco de fotos reais sem marca. `fetch_pexels.mjs` baixa candidatas (no seu computador), a revisão marca `aprovada`/`recusada`, e `assign_images.py` grava `data/images.json`. Ver `images/README.md`.

