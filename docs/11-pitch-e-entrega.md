# 11 — Pitch e checklist de entrega

Prazo de submissão: **26/10/2026**, pela plataforma. Mentoria online: 21 a 23/10.

## Entregáveis

| Entregável | Especificação | Estado |
| --- | --- | --- |
| Vídeo de pitch | Até 5 minutos: problema, solução, resultado | a fazer |
| Protótipo funcional | Acesso à solução em funcionamento | app e motor prontos (GraphRAG local, com o simulado de reserva); **falta hospedar** (P-04) |
| Repositório de código | Link, **configuração privada** | estrutura pronta; manter privado |

## Checklist antes de enviar

- [ ] Repositório privado e sem dados do cliente
- [ ] Nenhum material do desafio em local público, portfólio ou trabalho acadêmico
- [ ] Protótipo abre sem instalação (link) e a jornada completa funciona
- [x] README explica como rodar
- [ ] Documentação 01 a 15 atualizada com o que foi de fato construído
- [ ] Testes do GraphRAG rodados de novo depois do commit de qualidade da busca (`python3 -m unittest discover -s graphrag/tests -t .`)
- [ ] Decidir se o protótipo hospedado leva o GraphRAG no ar ou só o simulado, e dizer isso no vídeo
- [ ] Vídeo com até 5 minutos, áudio claro, mostra a jornada ponta a ponta
- [ ] Busca de remédio demonstrada no vídeo (doc 16, A3 e A6)
- [ ] Integração proposta mostrada (doc 10)

## Roteiro do pitch (5 minutos)

| Tempo | Conteúdo | Mostrar |
| --- | --- | --- |
| 0:00 a 0:40 | O problema: busca com 1.450 resultados e busca com contexto sem resultado | As duas buscas observadas, com a ressalva de serem testes exploratórios |
| 0:40 a 1:20 | A ideia: do prompt à compra em kits, não mais um chatbot | Slide de diferenciação (tabela do doc 03) |
| 1:20 a 3:10 | Demonstração ponta a ponta, como a Renata (doc 14) | rotina anti-idade na barra → kits → ajustar orçamento → abrir kit → trocar item → cesta com total e frete → retirada em loja com estoque → pagamento simulado; depois Meus medicamentos (reposição com equivalente, sem recomendar) |
| 3:10 a 3:50 | Remédio na busca e privacidade | "remédio de dor de cabeça" → kit dipirona + paracetamol (sem repetir princípio ativo, sem juntar dois anti-inflamatórios); remédio fora do banco; dado de saúde da pessoa fica no aparelho |
| 3:50 a 4:30 | Como funciona por dentro | Diagrama GraphRAG: intenção, grafo, dados vivos, compositor, validação; feito do zero, sem LLM nem API externa |
| 4:30 a 5:00 | Integração e validação | Pontos de troca (doc 10) e plano de teste com 5 a 8 pessoas; métricas como hipóteses |

## Critérios do cliente × onde a entrega responde

| Critério | Resposta |
| --- | --- |
| Fluidez da jornada | Um fluxo contínuo da frase ao pedido simulado |
| Qualidade e relevância | Kits por objetivo, tipo de pele, orçamento, sem itens repetidos |
| Saúde responsável | Escopo, zonas, bloqueio e encaminhamento (doc 07) |
| Personalização sem formulário | Intenção extraída da frase; no máximo uma pergunta, opcional |
| Viabilidade de integração | Contratos, adaptadores e passos de piloto (doc 10) |
| Diferença de um chatbot | Saída estruturada e editável, sem thread de mensagens |

## Cuidado com a confidencialidade

O enunciado proíbe publicar o conteúdo, identificar a empresa, manter repositório público ou usar o material em portfólio, trabalho acadêmico ou processo seletivo. A propriedade intelectual do produto final é da empresa parceira. Descumprir desclassifica a equipe.
