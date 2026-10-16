# Kits Inteligentes — IA Commerce (Hackathon Pague Menos)

> **CONFIDENCIAL.** O enunciado do desafio e qualquer informação recebida são confidenciais. Manter este repositório **privado**. Não publicar, não identificar a empresa em locais públicos, não usar em portfólio, trabalho acadêmico ou processo seletivo. Prazo de submissão: **26/10/2026**.

Uma camada de **kits inteligentes** sobre a busca: a pessoa descreve a intenção em linguagem natural ("preciso de produtos para tratamento de acne até R$ 120") e recebe de 2 a 3 kits prontos, sem itens repetidos, com preços diferentes, editáveis e prontos para o carrinho. O catálogo individual continua logo abaixo.

Não é um chatbot. É busca por intenção + composição de kit + compra.

## Status atual

| Fase | Estado |
| --- | --- |
| Pré-documentação (briefing, PRD, UX/UI, arquitetura...) | escrita (docs 01–11); aguardando sua avaliação |
| Catálogo sintético (100 produtos) + ecossistema (8 lojas, estoque por loja, cashback, categorias) | gerado; 47 de 47 checagens passam |
| Visual do app (dados simulados) | segue o app real (prints): caminho de compra completo com abas, cesta, retirada por loja; 26 testes passando; visto só em Chromium |
| Fotos reais sem marca | script pronto; **falta rodar no seu computador** e revisar |
| Desenho do GraphRAG | só documento |
| **Treino/implementação do GraphRAG** | **NÃO iniciado — aguardando liberação** |

Limites conhecidos: o cliente HTTP do app nunca foi exercitado (não há servidor); a relevância do simulador é genérica; acessibilidade não foi medida. Detalhes em [docs/08](docs/08-validacao-e-qualidade.md).

## Mapa de pastas (módulos separados de propósito)

```
pague-menos-kits/
├── README.md              este arquivo
├── docs/                  toda a documentação, um arquivo por etapa
├── catalog/               banco de dados FICTÍCIO (gerador, dados, validador)
├── app/                   código principal: visual do app (React + TypeScript)
├── graphrag/              sistema GraphRAG (hoje só README; sem código de treino)
├── contracts/             formatos de dados trocados entre os módulos
└── tools/                 pontes explícitas e de mão única entre módulos
```

### Regras de separação

1. `catalog/` não importa nada de `app/` nem de `graphrag/`. Ele só produz arquivos de dados.
2. `app/` não importa nada de `catalog/` nem de `graphrag/`. Ele fala com um serviço de busca definido em `contracts/`. Hoje esse serviço é simulado; depois será trocado pelo GraphRAG sem refazer telas.
3. `graphrag/` só **lê** os arquivos exportados por `catalog/` (ingestão) e **expõe** o contrato de busca.
4. A única ponte entre módulos é `tools/export_app_mock.py` (catálogo para dados simulados do app), de mão única.

## Documentação (leia nesta ordem)

| # | Arquivo | Para que serve |
| --- | --- | --- |
| 01 | [docs/01-briefing.md](docs/01-briefing.md) | Desafio, restrições, critérios, entregáveis |
| 02 | [docs/02-PRD.md](docs/02-PRD.md) | Produto: problema, escopo, requisitos, métricas |
| 03 | [docs/03-UX-UI.md](docs/03-UX-UI.md) | Fluxos, telas, estados, tokens de design |
| 04 | [docs/04-arquitetura.md](docs/04-arquitetura.md) | Módulos, fluxo de dados, separação |
| 05 | [docs/05-catalogo-sintetico.md](docs/05-catalogo-sintetico.md) | Como o banco fictício é gerado e checado |
| 06 | [docs/06-graphrag-design.md](docs/06-graphrag-design.md) | Desenho do GraphRAG e do compositor de kits |
| 07 | [docs/07-seguranca-saude.md](docs/07-seguranca-saude.md) | Limites da IA em saúde |
| 08 | [docs/08-validacao-e-qualidade.md](docs/08-validacao-e-qualidade.md) | Como cada etapa é conferida |
| 09 | [docs/09-decisoes-tecnicas.md](docs/09-decisoes-tecnicas.md) | Decisões e premissas |
| 10 | [docs/10-integracao-proposta.md](docs/10-integracao-proposta.md) | Como se conectaria ao sistema real |
| 11 | [docs/11-pitch-e-entrega.md](docs/11-pitch-e-entrega.md) | Checklist de entrega e roteiro do pitch |
| 12 | [docs/12-app-real-e-ecossistema.md](docs/12-app-real-e-ecossistema.md) | App real hoje, o que integrar e opções de imagens |
| 13 | [docs/13-referencia-visual-app.md](docs/13-referencia-visual-app.md) | Referência visual a partir dos prints e o que o protótipo reproduz |
| — | [contracts/README.md](contracts/README.md) | Contratos entre módulos |

## Comandos rápidos

```bash
# 1. Gerar e validar o catálogo fictício
python3 catalog/generate_catalog.py
python3 catalog/validate_catalog.py

# 2. Ponte catálogo -> dados simulados do app
python3 tools/export_app_mock.py

# 3. Rodar o visual do app
cd app && npm install && npm run dev
# conferir tipos + build de produção
npm run build
```

## Dados

Todos os dados são **sintéticos**: marcas, nomes, preços, estoque e fórmulas são inventados. Nada vem de sistemas da empresa. Nenhum produto é medicamento. Os dados servem para demonstrar a arquitetura; não têm validação dermatológica.
