# Kits Inteligentes — IA Commerce (Hackathon Pague Menos)

> **CONFIDENCIAL.** O enunciado do desafio e qualquer informação recebida são confidenciais. Manter este repositório **privado**. Não publicar, não identificar a empresa em locais públicos, não usar em portfólio, trabalho acadêmico ou processo seletivo. Prazo de submissão: **26/10/2026**.

Uma camada de **kits inteligentes** sobre a busca: a pessoa descreve a intenção em linguagem natural ("preciso de produtos para tratamento de acne até R$ 120") e recebe de 2 a 3 kits prontos, sem itens repetidos, com preços diferentes, editáveis e prontos para o carrinho. O catálogo individual continua logo abaixo.

Não é um chatbot. É busca por intenção + composição de kit + compra.

## Status atual (21/10)

| Fase | Estado |
| --- | --- |
| Documentação (docs 01–16) | escrita e revisada em 21/10; o doc 16 é o prompt e o registro da rodada de medicamentos |
| Catálogo sintético | 291 produtos (skin care, higiene, suplementos e 108 medicamentos em 16 áreas), 8 lojas, estoque por loja; 83 de 83 checagens |
| **GraphRAG do zero** | **implementado e treinado**, com medicamentos (grafo de 750 nós, vetores PPMI+SVD, BM25, Naive Bayes de ato de fala 61/65 fora do treino); 172 de 172 testes em 24/10 |
| App | logado como a persona Renata; busca de remédio e sintoma com kits; reposição; 46 testes; visto só em Chromium |
| Fotos reais sem marca | **pendente**: emissão de chave da Pexels pausada; o app mostra desenhos de embalagem |
| Hospedagem do protótipo | **pendente** (P-04, doc 09); a entrega pede acesso em funcionamento |

Limites conhecidos: conjunto de ranking pequeno (14 frases), entidades por regras, premissas de reposição fictícias, nenhuma regra clínica validada, acessibilidade não medida. Detalhes no [doc 14](docs/14-persona-e-privacidade.md) e no [doc 08](docs/08-validacao-e-qualidade.md).

## Mapa de pastas (módulos separados de propósito)

```
pague-menos-kits/
├── README.md              este arquivo
├── docs/                  toda a documentação, um arquivo por etapa
├── catalog/               banco de dados FICTÍCIO (gerador, dados, validador)
├── app/                   código principal: visual do app (React + TypeScript)
├── graphrag/              sistema GraphRAG do zero (grafo, vetores, NLU, compositor, servidor local)
├── contracts/             formatos de dados trocados entre os módulos
└── tools/                 pontes explícitas e de mão única entre módulos
```

### Regras de separação

1. `catalog/` não importa nada de `app/` nem de `graphrag/`. Ele só produz arquivos de dados.
2. `app/` não importa nada de `catalog/` nem de `graphrag/`. Ele fala com um serviço de busca definido em `contracts/`: o GraphRAG local (HTTP) ou, se o servidor não responder, o motor simulado.
3. `graphrag/` só **lê** os arquivos permitidos de `catalog/` (nunca `persona.json`) e **expõe** o contrato de busca.
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
| 14 | [docs/14-persona-e-privacidade.md](docs/14-persona-e-privacidade.md) | Persona Renata, conversa, reposição e privacidade |
| 15 | [docs/15-graphrag-conversacional.md](docs/15-graphrag-conversacional.md) | Ontologia, ingestão incremental, busca em fluxo (SSE), latência |
| 16 | [docs/16-prompt-medicamentos-e-ui.md](docs/16-prompt-medicamentos-e-ui.md) | Prompt, decisões e checklist da rodada de medicamentos e interface |
| — | [contracts/README.md](contracts/README.md) | Contratos entre módulos |

## Comandos rápidos

```bash
# 1. Gerar e validar o catálogo fictício
python3 catalog/generate_catalog.py
python3 catalog/validate_catalog.py

# 2. Ponte catálogo -> dados simulados do app
python3 tools/export_app_mock.py

# 3. Treinar e servir o GraphRAG (porta 8787)
pip install -r graphrag/requirements.txt
python3 -m graphrag.train
python3 -m graphrag.service.server --port 8787

# 4. Rodar o app (usa o GraphRAG se estiver no ar)
cd app && npm install && npm run dev
# conferir tipos + build de produção
npm run build
```

## Dados

Todos os dados são **sintéticos**: marcas, nomes, preços, estoque e fórmulas são inventados. Nada vem de sistemas da empresa. Os itens de reposição têm nomes genéricos fictícios e só servem à tela de reposição; nenhuma recomendação de medicamento. Os dados servem para demonstrar a arquitetura; não têm validação dermatológica.
