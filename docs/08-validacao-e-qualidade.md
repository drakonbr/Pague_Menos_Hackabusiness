# 08 — Validação e qualidade

Como cada etapa é conferida, com o comando e o critério. O registro de execuções fica no final (atualizado a cada rodada).

## Checagens por módulo

| Módulo | Comando | Critério de aprovação |
| --- | --- | --- |
| Catálogo | `python3 catalog/validate_catalog.py` | 31 de 31 checagens, código de saída 0 |
| Catálogo (determinismo) | gerar duas vezes e comparar hash dos arquivos | hashes iguais |
| Ponte catálogo → app | `python3 tools/export_app_mock.py` | 100 produtos exportados; app compila com eles |
| Separação de módulos | `python3 tools/check_separation.py` | nenhuma referência proibida; `graphrag/` só com README |
| App: tipos e build | `cd app && npm run build` | zero erros de tipo, build de produção gerado |
| App: regras de kit | `cd app && npm test` | todos os casos T1 a T12 passam e as invariantes do contrato valem em todas as respostas |
| App: telas | roteiro manual abaixo | todas as telas e estados do doc 03 alcançáveis |
| GraphRAG | (fase futura) `eval/` | metas do doc 06 |

## Invariantes do contrato (checadas por código)

Uma função de checagem (`app/src/services/contractChecks.ts`) valida toda resposta de busca. A mesma lista será portada para a avaliação do GraphRAG.

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
| T2 | "Quero fazer skin care" (exemplo do PDF) | kits sem orçamento (econômico, essencial, alternativo) em vez de lista longa de produtos |
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

Para o GraphRAG, cada caso ganha lista de produtos esperados e metas de recuperação (Recall@k), medidas na fase de avaliação.

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
