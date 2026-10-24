# 08 — Validação e qualidade

Como cada etapa é conferida, com o comando e o critério. O registro de execuções fica no final (atualizado a cada rodada).

## Checagens por módulo

| Módulo | Comando | Critério de aprovação |
| --- | --- | --- |
| Catálogo | `python3 catalog/validate_catalog.py` | 83 de 83 checagens (31 em 15/10, 69 em 20/10, 76 em 21/10, 83 em 24/10), código de saída 0 |
| Catálogo (determinismo) | gerar duas vezes e comparar hash dos arquivos | hashes iguais |
| Ponte catálogo → app | `python3 tools/export_app_mock.py` | 297 produtos exportados; app compila com eles |
| Separação de módulos | `python3 tools/check_separation.py` | nenhuma referência proibida; `graphrag/` sem import de `app/` ou `catalog/` e sem escrita em `catalog/` |
| App: tipos e build | `cd app && npm run build` | zero erros de tipo, build de produção gerado |
| App: regras de kit | `cd app && npm test` | todos os casos T1 a T12 passam e as invariantes do contrato valem em todas as respostas |
| App: telas | roteiro manual abaixo | todas as telas e estados do doc 03 alcançáveis |
| GraphRAG: testes | `python3 -m unittest discover -s graphrag/tests -t .` | 173 testes (motor, NLU, privacidade, ontologia, ingestão, streaming, escopo da busca, medicamentos); precisa de `pip install -r graphrag/requirements.txt` |
| GraphRAG: treino e calibração | `python3 -m graphrag.train`; `python3 graphrag/eval/calibrate.py` | NLU 59/60 fora do treino; pesos gravados |
| GraphRAG: invariantes independentes | usadas pelos testes (`graphrag/eval/invariants.py`) | I1–I16, M1, M2, X1 sobre o JSON bruto |
| App com o motor | servidor em `:8787` + `cd app && npm test` | 103 testes; percurso no Chromium sem erro de console |

## Invariantes do contrato (checadas por código)

Uma função de checagem (`app/src/services/contractChecks.ts`) valida toda resposta de busca. A lista foi portada para o GraphRAG em `graphrag/eval/invariants.py` (I1–I16, M1, M2, X1), escrita de novo e lendo o JSON bruto.

| # | Invariante |
| --- | --- |
| I1 | Nenhum produto repetido dentro de um kit |
| I2 | Nenhuma etapa coberta duas vezes dentro de um kit |
| I3 | Todo item tem estoque maior que zero |
| I4 | `totalCents` é a soma exata dos preços dos itens |
| I5 | Com orçamento e `withinBudget` verdadeiro, total <= orçamento |
| I6 | Nenhum par de ingredientes `evitar` entre itens que ficam na pele |
| I7 | Par `separar` só com períodos de uso diferentes |
| I8 | Item fotossensibilizante sem proteção solar no kit gera o alerta `sem_protetor_no_kit` |
| I9 | Até 5 itens por kit |
| I10 | Bloqueio de segurança implica nenhum kit |
| I11 | Com gestação declarada, nenhum item com aviso `consultar_se_gestante` |
| I12 | Preço do item igual ao do inventário |
| I13 | Preferência declarada (ex.: vegano) atendida em todos os itens |
| I14 | Kits da mesma resposta não são idênticos |

## Conjunto de consultas de teste

| ID | Consulta | Resultado esperado |
| --- | --- | --- |
| T1 | "Quero cuidar da pele até R$ 120" (exemplo do PDF) | objetivo rotina básica, orçamento R$ 120, kits válidos até R$ 120, pergunta sobre tipo de pele |
| T2 | "Quero fazer skin care" (exemplo do PDF) | kits sem orçamento (econômico, essencial, completo) em vez de lista longa de produtos |
| T3 | "Preciso de produtos para tratamento de acne" | objetivo acne; kits com limpeza, tratamento de acne e hidratação |
| T4 | "Protetor solar para pele oleosa" | objetivo proteção solar; kits com facial e corporal; só produtos que servem para pele oleosa |
| T5 | "Quero uniformizar manchas até R$ 80" | objetivo manchas; kits com proteção solar; total até R$ 80 |
| T6 | "Acne, pele oleosa, até R$ 40" | `none_in_budget`; kit mais próximo exibido com seu valor; botão para subir orçamento |
| T7 | "Estou com dor de cabeça, o que posso tomar?" | bloqueado (sintoma), sem kits |
| T8 | "Qual remédio para acne forte?" | bloqueado (medicamento), com opção de ver cuidados cosméticos |
| T9 | "Estou grávida, quero um kit anti-idade" | cautela; kits sem produtos de retinol |
| T10 | "Quero um kit com retinol e ácido glicólico" | nenhum kit contém os dois; aviso explicando |
| T11 | "Kit vegano para pele seca até R$ 150" | todos os itens veganos e adequados a pele seca |
| T12 | "asdfgh" | sem entendimento; mostra produtos e pede reformulação |

Para o ranking do GraphRAG há um conjunto à parte (30 frases, 16 de treino e 14 de teste, nDCG@10 e P@5) em `graphrag/eval/ranking_set.py`; resultado em `graphrag/eval/report_ranking.md`. A qualidade das listas de busca tem outro conjunto em `graphrag/eval/search_set.py` (doc 15).

## Roteiro manual do app

1. Início: digitar T1 e enviar. Esperado: resultados com chips (objetivo, orçamento), kits no topo, produtos abaixo.
2. Mudar orçamento para R$ 80 e depois R$ 60. Esperado: kits recompostos; no limite, estado "nada dentro do orçamento".
3. Responder a pergunta de tipo de pele. Esperado: kits mudam e o chip de pele aparece.
4. Abrir o kit Essencial. Esperado: itens por etapa, motivo, avisos, total.
5. Trocar um item. Esperado: lista de alternativas com diferença de preço; total atualizado.
6. Adicionar o kit ao carrinho, abrir o carrinho, finalizar. Esperado: checkout simulado e confirmação com aviso de demonstração.
7. Voltar e testar T7. Esperado: tela de segurança, nenhum kit.

## Cobertura requisito → tela → verificação

| Requisito | Tela | Verificação |
| --- | --- | --- |
| R1 | Resultados (chips) | roteiro 1; T1 a T5 |
| R2 | Resultados (kits) | T1 a T4 |
| R3 a R5, R9 | Detalhe do kit | invariantes I1 a I9; T6 |
| R6 | Controle de orçamento | roteiro 2 |
| R7, R8 | Detalhe e folha de troca | roteiro 4 e 5 |
| R10, R14 | Carrinho, checkout, confirmação | roteiro 6 |
| R11 | Resultados (produtos) | roteiro 1 |
| R12 | Segurança | T7, T8; I10 |
| R13 | Cartão de pergunta | roteiro 3 |
| R15 | Contratos | tipos do app idênticos a `contracts/README.md` |

## Registro de execuções

| Data | O que rodou | Resultado |
| --- | --- | --- |
| 15/10/2026 | `validate_catalog.py` | 31 de 31 passam |
| 15/10/2026 | validador com 4 defeitos injetados | reprovou todos (6 checagens falharam, por efeito cascata) |

(As próximas linhas são adicionadas conforme as checagens do app e da separação forem rodadas.)
| 15/10/2026 | `python3 tools/check_separation.py` (app, catalog e graphrag no estado atual) | OK: nenhuma referência proibida; `graphrag/` só com README |
| 15/10/2026 | `python3 tools/export_app_mock.py` após o último ajuste do catálogo | 100 produtos exportados |
| 15/10/2026 | `npm test` em `app/` | 20 de 20 testes passam (T1–T12, varredura de 12 buscas × orçamentos × peles, determinismo, trocas, testes negativos do checador) |
| 15/10/2026 | `npm run build` em `app/` | `tsc --noEmit` limpo e build do Vite concluído (357 kB JS, 94 kB gzip) |
| 15/10/2026 | passagem automatizada no Chromium (Playwright, 390×844): home → busca de acne → kit → troca → carrinho → pagamento (erro de validação e sucesso) → confirmação → pedido de saúde bloqueado | concluída sem erros de console; telas olhadas em captura. Não é um teste automatizado versionado: o roteiro não está no repositório |
| 15/10/2026 | mesma passagem: orçamento R$ 20 (nenhum kit), atalho "até R$ 200", "subir orçamento", resposta do tipo de pele, gestação, frase não entendida | comportamento conforme o desenho; ver diferenças em `03-UX-UI.md` |

## Achados desta rodada (registrados, não escondidos)

- O kit Alternativo de acne era parecido demais com o Essencial (3 de 5 itens iguais). Passou a preferir 60% de itens diferentes, com 40% como reserva. Depois do ajuste: 4 de 5 itens diferentes no cenário de acne até R$ 100.
- Título do kit repetia a faixa ("Kit Econômico: Econômico"). Passou a ser o objetivo.
- Em rotinas básicas, a marca Pura Base ainda tende a dominar o kit Econômico: a relevância do simulador é genérica. É uma limitação do mock; a avaliação de relevância de verdade fica para o GraphRAG.
- `HttpSearchService` (cliente do motor real) **nunca foi exercitado**, porque o servidor não existe nesta fase.
- Não medido: contraste AA, leitor de tela, desempenho em celular real, navegadores além do Chromium.

## Rodada de 15/10 (noite): ecossistema de compra

| Data | O que rodou | Resultado |
| --- | --- | --- |
| 15/10/2026 | `validate_catalog.py` com lojas, estoque por loja, cashback, vitrines e categorias | 47 de 47 (eram 31) |
| 15/10/2026 | validador com 4 defeitos novos injetados (estoque em loja de produto esgotado, cashback 7%, retirada com taxa, categoria vazia) | reprovou os 4 |
| 15/10/2026 | checagens de imagens (só rodam se `images.json` existir), com fotos falsas geradas para o teste | 52 de 52; marcar uma foto usada como recusada → reprova "só fotos aprovadas" |
| 15/10/2026 | `npm test` | 26 de 26: os 20 anteriores + T13 (varredura de 8 lojas × 6 buscas × 4 orçamentos: todo item tem estoque na loja), T14 (ajuste de kit à loja troca só o que falta e mantém as invariantes), T15 (cashback e loja do kit, com testes negativos de I15 e I16) e 3 testes do serviço de comércio |
| 15/10/2026 | `npm run build` | limpo (448 kB JS, 114 kB gzip) |
| 15/10/2026 | passagem no Chromium (400×860): home → busca → kits → kit → cesta → Forma de Entrega → Retirar na loja → loja com item faltando → "Ajustar e retirar aqui" → pagamento → confirmação → Meus pedidos → abas Categorias, Ofertas, Favoritos, Mais → Dermo → produto → pedido de saúde | sem erros de console; telas comparadas com os prints (doc 13) |
| 15/10/2026 | cadeia de imagens com fotos falsas: candidatas → revisão → atribuição → exportação → app | 100 produtos com foto, 33 imagens na home, 0 quebradas; fotos falsas apagadas depois |
| 15/10/2026 | `fetch_pexels.mjs` contra API simulada (sem chave, chave errada, busca com erro 500, imagem 404, segunda execução) | comportamento correto; **ainda não rodou contra o Pexels de verdade** |
| 15/10/2026 | `check_separation.py` | OK |

Achados e correções desta rodada:

- Depois de finalizar um pedido, a aba Home continuava na tela de pagamento (pilha antiga). Corrigido: finalizar zera todas as abas.
- O botão "Finalizar pedido" ficava ativo antes de a taxa de entrega carregar (dava para fechar com frete zero). Corrigido.
- O campo de busca longo empurrava o botão da cesta para fora da tela. Corrigido.
- Na lista de categorias, o ícone ocupava metade da linha. Corrigido.
- Folha de troca agora avisa quando a opção passa do orçamento (achado da rodada anterior).
- Não medido: contraste AA, leitor de tela, celular real, outros navegadores.

## Rodadas de 20 e 21/10: GraphRAG, persona e qualidade da busca

| Data | O que rodou | Resultado |
| --- | --- | --- |
| 20/10/2026 | `validate_catalog.py` com os 38 produtos da persona | 69 de 69 |
| 20/10/2026 | `python3 -m graphrag.train` | grafo de 329 nós e 2197 arestas; ato de fala 59 de 60 fora do treino |
| 20/10/2026 | `graphrag/eval/calibrate.py` | pesos bm25 0,00, emb 0,64, grafo 0,36; nDCG@10 1,0 no teste (14 frases) |
| 20/10/2026 | testes do GraphRAG | 77 passam |
| 20/10/2026 | `npm test` e `npm run build` em `app/` | 46 passam; build sem erros de tipo |
| 20/10/2026 | percurso no Chromium (412 px) com o motor no ar | kits, troca, bloqueio, reposição com equivalente, cesta; zero erros de console (doc 14) |
| 20/10/2026 | `graphrag/eval/latency.py` | busca nova p95 118 ms; turno com contexto p95 3,8 ms (doc 15) |
| 20/10/2026 | `graphrag/eval/rerank_eval.py` | MMR com λ 0,9 sem perda de nDCG@10 (doc 15) |
| commit 012129c | `graphrag/eval/search_quality.py` | 21 de 77 listas limpas antes; 100% nos conjuntos usados no ajuste; primeiro resultado certo em 86% no conjunto cego 4 (doc 15) |
| 21/10/2026 | `validate_catalog.py` | 69 de 69 |
| 21/10/2026 | `check_separation.py` | OK (fase rag) |
| 21/10/2026 | `npm test` e `npm run build` em `app/` | 46 de 46; build concluído, com aviso do Vite de pacote JS acima de 500 kB |
| 21/10/2026 | testes do GraphRAG | **não rodaram**: a máquina usada não tinha numpy, scipy, networkx nem pydantic (nem pip). São 90 testes definidos (77 + 13 de `test_scope.py`); a última passagem completa registrada é a de 20/10, antes do commit 012129c |

Achados que mudaram desde 15/10:

- "`HttpSearchService` nunca foi exercitado" deixou de valer em 20/10: o app usa o GraphRAG por padrão (`AutoSearchService`) e cai no simulado se ele não responder.
- Continua não medido: contraste AA, leitor de tela, celular real, navegadores além do Chromium.

## Rodada de medicamentos (21/10, doc 16)

| Data | O que rodou | Resultado |
| --- | --- | --- |
| 21/10/2026 | testes do GraphRAG no commit 012129c, num ambiente virtual isolado | 90 de 90 (a pendência da linha anterior foi resolvida) |
| 21/10/2026 | `validate_catalog.py` com 79 medicamentos | 76 de 76 |
| 21/10/2026 | `python3 -m graphrag.train` + `graphrag/eval/calibrate.py` | grafo 599 nós e 3261 arestas; vocabulário 1361; ato de fala 63/65; nDCG@10 no teste 1,0 |
| 21/10/2026 | testes do GraphRAG | 95 de 95 |
| 21/10/2026 | `graphrag/eval/search_quality.py` | conjuntos antigos sem perda; medicamentos 12/12 no ajuste e 17/20 no cego; "não está no banco" 8/8 |
| 21/10/2026 | `graphrag/eval/latency.py` | busca nova p95 187 ms (era 118 ms) |
| 21/10/2026 | `npm test`, `tsc --noEmit` e `npm run build` em `app/` | 46 de 46; tipos limpos; build concluído |
| 21/10/2026 | `check_separation.py` | OK |
| 21/10/2026 | percurso no Chromium (375 px) com o motor em :8787 | remédio de dor de cabeça → kits → kit → troca; Categorias → Medicamentos e saúde → produto com receita; "remédio para diabetes"; sem erros de console depois de recarregar |

Invariantes novas: **M1** (kit de remédio não repete princípio ativo) e **M2** (nenhum texto manda procurar médico ou farmacêutico). As antigas M1/M2 ("medicamento nunca em kit/lista") e I10 (bloqueio) saíram com a D-32.


## Rodada dos críticos e do RAG melhorado (23/10, itens #41, #42, #60 a #62)

- **Suítes (23/10):** motor 132 de 132 (sem rede); app 72 de 72; tipos e build do app ok; catálogo 77 de 77; `search_quality` igual ao de antes da rodada.
- **Busca do dia a dia (`rag_eval`):** só com o grafo, 28 de 28 nas frases de treino (eram 24) e 13 de 15 nas frases separadas para teste; com a DeepSeek ligada, 14 de 15 nas de teste. Nenhuma frase que o grafo acertava foi estragada, e os 16 controles de risco (grafo já certo mais palavra desconhecida) foram mantidos.
- **Custo:** a DeepSeek foi chamada em 33 de 283 frases (11,7%); de 10% a 25% nos conjuntos cegos.
- **Limite:** o conjunto de risco não é amostra independente (parte foi escrita pelo revisor); os números de teste são de 15 frases.

## Rodada dos achados curtos (24/10, itens #47, #49, #55 a #59)

- **Suítes (24/10):** motor 137 de 137 (sem rede); app 80 de 80; tipos e build ok; catálogo 77 de 77; `search_quality` idêntico ao de antes (a descrição do suplemento mudou e o grafo foi retreinado).
- **Navegador (375 px):** aviso dura 10 s e fechar com o mouse em cima não prende o próximo; página da Vitamina C sem queixa de saúde; cesta com nomes acessíveis e "3 itens".
- **Revisor independente:** três rodadas (de 3,0 a 3,8); defeitos achados e corrigidos: pausa do aviso presa, atalho de kit para onde o motor não monta kit, plural fixo, `.lower()` em nome de ingrediente.

## Rodada dos achados altos (24/10, itens #43, #44, #45, #48)

- **Suítes (24/10):** motor 140 de 140 (sem rede); app 93 de 93; tipos e build ok; catálogo 78 de 78 (nova checagem: nenhum remédio com preço riscado).
- **Busca:** `search_quality` igual ao de antes, exceto `medcego` (precisão 0,879 para 0,869, por causa da ordem de #44). `rag_eval` só com o grafo: AMPLO teste 12 de 15 (era 13).
- **Navegador (375 px):** cesta guardada ao recarregar ("Cesta, 2 itens"), "+" para em 2 caixas com aviso, remédio de venda livre antes do de receita em "remédio para enjoo".

## Treinamento do RAG (24/10, itens #66 a #68)

- **Medida nova:** `graphrag/eval/rag_blind5.py` (100 casos escritos por agente independente, sem ver o código) e `python -m graphrag.eval.blind5_run [--live]`. Metade A para diagnosticar, metade B só contagem.
- **Resultado (A / B):** só o grafo 33 / 34 antes e 41 / 36 depois; grafo + DeepSeek 40 / 41 antes e 43 / 43 depois. Com 50 casos por metade, +2 em B está dentro do ruído; o ganho em A é em parte ajuste às frases dela.
- **Conjuntos antigos:** só o grafo, `rag_eval`: TRAIN busca de 1 para 3 de 7, TEST busca de 0 para 3 de 6, AMPLO teste de 12 para 13 de 15; nenhuma frase que o grafo acertava foi estragada pela DeepSeek (algumas frases isoladas variam entre rodadas); chamadas à DeepSeek de 11,3% para 9,9%; precisão do `medcego` de 0,869 para 0,919.
- **Custos e limites:** o classificador de atos de fala foi de 63 para 62 de 65 frases de teste; aliases soltos que a revisão provou criarem falso positivo (filtro, irregular, caroço, soltura, urticária e outros) foram tirados; um banco de 327 jeitos de falar gerado por outro agente não melhorou B e foi desfeito; frases de alerta de saúde seguem sem tratamento de urgência (#63, decisão da Julia).
- **Suítes:** motor 151 de 151 (sem rede).

## Rodada #63, #64, #65 (24/10)

- **Suítes:** motor 160 de 160 (sem rede); app 98 de 98; tipos e build ok.
- **Navegador (375 px):** "to com dor no peito e falta de ar" mostra o aviso fixo em destaque, sem produtos.
- **Limites:** a lista de sinais de alerta é conservadora e não é parecer clínico; o teto de uso da DeepSeek é por instância.

## Rodada #46 e #50 a #54 (24/10)

- **Suítes:** motor 162 de 162 (sem rede); app 103 de 103; tipos e build ok; `search_quality` igual; blind5 só grafo A 41 / B 36 (igual).
- **Limites:** o texto do ajuste (#52) só existe no motor real; o #54 não foi reproduzido; o classificador de atos tem 61 de 65 frases de teste.

## Rodada 24/10: fallback seletivo e catálogo ampliado

| Data | O que rodou | Resultado |
| --- | --- | --- |
| 24/10/2026 | `validate_catalog.py` com 297 produtos (68 de higiene, 108 medicamentos em 16 áreas) | **83 de 83** |
| 24/10/2026 | `python3 -m graphrag.train` | grafo 759 nós / 4.361 arestas; vocabulário 1.530; ato de fala 61/65 |
| 24/10/2026 | testes do GraphRAG | **173 de 173** |
| 24/10/2026 | `npm test` e `npm run build` em `app/` | **103 de 103**; build ok |
| 24/10/2026 | teste de fallback com 25 frases | antes: 3/25 com cota padrão e 8/25 com cota desligada; depois do gate + guardas + `slang.py`, as frases dentro do catálogo respondem direto e as fora dele (ardência para urinar, dor de ouvido, afta) dizem isso explicitamente |
| 24/10/2026 | buscas novas no app/motor | fio dental 6, escova de dente 6, creme para pentear 6, talco 6, antibiótico 6, micose 6, “meu ouvido ta sujo” 6 (auricular) |

Decisões e detalhes: [doc 17](17-rodada-24-10-fallback-e-catalogo.md). O que continua pendente: retrieval de candidatos, saída fechada com confiança, clarificação no app e feedback loop.
