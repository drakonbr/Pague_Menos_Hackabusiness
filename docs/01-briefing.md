# 01 — Briefing

Fontes: enunciado do desafio (.docx, Hacka Business · Rec'n'Play 2026) e a proposta de ideia (PDF "Kits inteligentes: da intenção à compra").

## O desafio (resumo)

Criar uma experiência de **IA Commerce** que transforme conversas e intenções em jornadas de **descoberta, recomendação e compra**, de forma simples, personalizada, segura e integrada.

Pergunta central do cliente: *e se o futuro do e-commerce começasse em uma conversa?*

## Restrições do cliente

| Restrição | Consequência para o projeto |
| --- | --- |
| Não é para construir mais um chatbot | A interface é uma busca por intenção que devolve kits; a conversa é só a forma de entrada |
| Rede de farmácias: saúde exige cuidado | Escopo inicial só cosméticos e autocuidado; guardrails explícitos (doc 07) |
| Sem dados do cliente | Catálogo sintético, preço/estoque simulados, pagamento simulado |
| Liberdade de stack | React + TypeScript (app), Python (catálogo), GraphRAG a definir |
| Precisa ser plausível como ponto de partida real | Contratos e pontos de troca documentados (docs 04 e 10) |
| Documentar decisões e premissas | doc 09 |
| Confidencialidade total | Repositório privado; nada em portfólio ou processo seletivo |

## O que a entrega precisa demonstrar

| Aspecto | Onde este projeto responde |
| --- | --- |
| Jornada ponta a ponta | Telas: início, resultados, kit, carrinho, checkout simulado (doc 03) |
| Experiência conversacional | Busca em linguagem natural com intenção interpretada e perguntas de refinamento (doc 03) |
| Motor de recomendação | GraphRAG + compositor de kits (doc 06) |
| Tratamento de segurança | Guardrails de saúde (doc 07) |
| Integração proposta | Doc 10 e contratos |

## Critérios de avaliação

Específicos: fluidez da jornada; qualidade e relevância da recomendação; tratamento responsável de saúde; personalização sem formulários; viabilidade de integração; **diferenciação de um chatbot convencional**.

Gerais: inovação, impacto, clareza da apresentação, viabilidade, qualidade da solução. Nota: 40% mentores, 60% bancas (com representantes da empresa).

## Entregáveis e prazo

1. Vídeo de pitch (até 5 min).
2. Protótipo funcional (acesso em funcionamento).
3. Repositório de código, privado.

Submissão: **26/10/2026**. Mentoria online: 21 a 23/10.

## A ideia da equipe (do PDF)

- **Problema observado** (testes exploratórios no app atual, poucos testes, sem auditoria completa): busca ampla ("quero fazer skin care") retornou 1.450 produtos, com itens fora da intenção principal; busca com contexto e orçamento ("quero começar a cuidar da pele até R$ 120") não retornou resultado.
- **Solução:** camada de kits inteligentes no topo dos resultados, de 2 a 3 kits (econômico, essencial, completo), catálogo individual logo abaixo.
- **Como a IA funciona:** intenção → extração (objetivo, orçamento, preferências) → recuperação (catálogo, preço, estoque) → ranking → interface. RAG como base do MVP; GraphRAG opcional.
- **Segurança:** não montar combinações terapêuticas; medicamentos exigem camada validada.
- **Validação:** 5 a 8 participantes, comparação com a busca atual, depois experimento controlado. Ganhos de conversão e ticket médio são **hipóteses**.

## Decisão de interpretação (registrada)

A equipe pediu "pesquisa como se estivesse conversando com um chat". O PDF fala em "sem abrir um chat". Resolução adotada (ver doc 09, D-01): **entrada em linguagem natural, saída estruturada.** Sem thread de mensagens; a interface mostra a intenção entendida em chips, faz no máximo uma pergunta de refinamento por vez e entrega kits. Isso mantém o ar conversacional pedido e a diferenciação de chatbot exigida pelo cliente.
