# 02 — PRD: Kits inteligentes

Versão 0.1 · 15/10/2026 · Status: rascunho para avaliação

## 1. Problema

Observado em testes exploratórios no app atual (poucos testes, não é auditoria):

- Busca ampla ("quero fazer skin care") retornou 1.450 produtos, com itens de categorias fora da intenção.
- Busca com contexto e orçamento ("quero começar a cuidar da pele até R$ 120") retornou **nenhum resultado**.

Quem descreve uma necessidade em linguagem natural precisa navegar por centenas de itens e montar a rotina sozinho. Isso aumenta o esforço de escolha e a chance de desistir.

**Pergunta a investigar:** como reduzir o esforço de escolha e ajudar a pessoa a encontrar produtos adequados à intenção e ao orçamento?

## 2. Proposta

Uma **camada de kits inteligentes** no topo dos resultados de busca. Quando a intenção e as restrições são entendidas, a experiência mostra de 2 a 3 kits compactos. O catálogo individual continua logo abaixo.

Um kit é um conjunto **sem itens repetidos** (nenhuma etapa da rotina coberta duas vezes) que, junto, atende ao objetivo declarado dentro do orçamento, com preço total visível, e pode ser editado, trocado item a item ou adicionado ao carrinho de uma vez.

Formatos: **Econômico** (menor preço total que cumpre os requisitos), **Essencial** (seleção equilibrada e mais relevante para o objetivo), **Alternativo** (outra combinação relevante, com marcas ou atributos diferentes). Não forçar 3 quando o catálogo não sustenta opções realmente relevantes.

Não é um chatbot: a entrada é uma frase, a saída é uma seleção de compra.

## 3. Usuários e cenários

| Persona | Cenário | Resultado esperado |
| --- | --- | --- |
| Iniciante em skin care | "Quero começar a cuidar da pele até R$ 120" | Kit econômico e essencial com limpeza, hidratação e protetor |
| Pessoa com objetivo claro | "Preciso de produtos para tratamento de acne" | Kits com limpeza, tratamento e hidratação oil-free |
| Pessoa com orçamento apertado | Mesma busca com limite de R$ 80 | Kit econômico dentro do limite; mensagem clara se nada couber |
| Pessoa que quer comparar | Abre o kit e troca um item | Total recalculado; avisos de compatibilidade atualizados |
| Pedido de saúde | "Estou com dor de cabeça, o que tomo?" | Sem kit; explicação do limite e encaminhamento a profissional |

## 4. Escopo

### Dentro (MVP demonstrável)

- Busca em linguagem natural para skin care, tratamento cosmético, proteção solar.
- Interpretação de objetivo, orçamento, tipo de pele e preferências (ex.: vegano, sem fragrância).
- Kits econômico, essencial e alternativo, sem itens repetidos.
- Seleção de orçamento pelo usuário (controle de valor máximo que recompõe os kits).
- Detalhe do kit com troca de item, total e justificativa por item.
- Catálogo individual abaixo dos kits.
- Carrinho e checkout **simulados**.
- Camada de segurança para pedidos de saúde.

### Fora (explicitamente)

- Recomendação de medicamentos, doses, interações medicamentosas ou combinações terapêuticas.
- Integração real com catálogo, estoque, pagamento ou conta do cliente.
- Histórico de compra real do usuário (personalização por histórico é item de integração, doc 10).
- Login e cadastro.

## 5. Requisitos funcionais

| ID | Requisito | Verificação |
| --- | --- | --- |
| R1 | Aceitar uma frase em linguagem natural e exibir a intenção entendida (objetivo, orçamento, pele) em chips editáveis | Tela de resultados; casos de teste T1 a T6 (doc 08) |
| R2 | Exibir de 2 a 3 kits no topo, cada um com nome do formato, número de itens e preço total | Tela de resultados |
| R3 | Um kit nunca repete item nem cobre a mesma etapa duas vezes | Regra K1 (doc 06); checagem automática no GraphRAG |
| R4 | Todo item de kit tem estoque e preço vindos do inventário, nunca inventados | Regra K2; contrato de preço |
| R5 | O total do kit respeita o orçamento informado; se nada couber, dizer isso e mostrar o mais próximo | Estado "sem kit dentro do orçamento" |
| R6 | O usuário pode mudar o orçamento e ver os kits recompostos | Controle de orçamento |
| R7 | O usuário pode abrir um kit, trocar um item por alternativa compatível e ver o total recalculado | Tela de detalhe e folha de troca |
| R8 | Cada item do kit explica por que está ali | Detalhe do kit |
| R9 | Mostrar avisos (fotossensibilizante, gestação, interação) de forma visível antes de adicionar ao carrinho | Detalhe do kit |
| R10 | Adicionar o kit inteiro ou itens avulsos ao carrinho | Carrinho |
| R11 | Manter o catálogo individual abaixo dos kits | Tela de resultados |
| R12 | Pedidos de saúde, medicamento ou sintoma não geram kit; mostram explicação e encaminhamento | Estado de segurança; casos T7 a T9 |
| R13 | Quando faltar informação decisiva (ex.: tipo de pele), fazer no máximo uma pergunta de refinamento por vez, sem bloquear os kits | Cartão de pergunta |
| R14 | Checkout simulado até a confirmação, sinalizado como demonstração | Telas de checkout e confirmação |
| R15 | Trocar dados simulados por dados reais sem refazer telas | Contratos (doc 10 e `contracts/`) |

## 6. Requisitos não funcionais

- Mobile-first (390 px de largura de referência), utilizável no desktop.
- Contraste e alvos de toque acessíveis (mínimo 44 px nos botões principais).
- Texto em português do Brasil, valores em R$ com vírgula.
- Nenhum dado pessoal real armazenado.
- Preços e estoque nunca gerados por modelo de linguagem.

## 7. Métricas (hipóteses a validar, não resultados)

| Grupo | Métrica |
| --- | --- |
| Descoberta | Tempo até achar uma opção relevante; buscas sem resultado; relevância percebida |
| Engajamento | Cliques nos kits; abertura de detalhe; uso de troca |
| Negócio | Adição ao carrinho; conversão; ticket médio; itens por pedido |

Aumento de conversão e ticket médio são **hipóteses de negócio**, não ganhos garantidos. Validação proposta: teste com 5 a 8 pessoas em tarefas de skin care, comparação com a busca atual e, havendo ambiente real, experimento controlado.

## 8. Riscos

| Risco | Mitigação |
| --- | --- |
| Recomendar algo inadequado em saúde | Escopo sem medicamentos; lista de intenções bloqueadas; avisos por produto (doc 07) |
| Kit sem sentido (itens que se anulam) | Regras de interação e de etapas, checadas antes de exibir (doc 06) |
| Modelo inventar preço ou estoque | Preço e estoque só do inventário; o modelo escolhe, não escreve números |
| Parecer um chatbot | Saída estruturada, sem thread de mensagens, no máximo uma pergunta de refinamento |
| Dados sintéticos pouco realistas | Declarado como premissa; troca por catálogo real prevista |

## 9. Critérios de aceite do MVP

1. As 3 consultas do PDF e as de segurança (doc 08) produzem o resultado esperado.
2. Nenhum kit exibido repete etapa, passa do orçamento, inclui item sem estoque ou contém par de ingredientes marcado como `evitar`.
3. Do texto da busca até a confirmação do pedido simulado, sem ruptura de fluxo.
4. Documentação de arquitetura e integração permite apontar onde entram catálogo, preço, estoque e pagamento reais.
