# 03 — UX/UI

> **Atualização de 21/10 (doc 16):** a tela de segurança, o botão "Falar com um farmacêutico" e todo texto de encaminhamento saíram. Busca de remédio abre a tela de resultados como qualquer outra; o orçamento passou a abrir numa folha a partir do chip.
>
> **Atualização de 15/10 (noite):** o visual passou a seguir o app real, a partir dos prints. A referência atual de telas, tokens e diferenças está no **doc 13**; este documento continua valendo para princípios, copy, estados e o bloco de kits.

Módulo: `app/` (React + TypeScript, mobile-first). Status: **telas implementadas com dados simulados e vistas em navegador** (Chromium, 390×844 e 1280×900). Contraste AA medido e leitor de tela **não** foram testados; ver "Diferenças entre o desenho e o protótipo" no fim.

## Princípios

1. **Entrada em linguagem natural, saída estruturada.** A pessoa escreve uma frase; a tela devolve uma seleção de compra, não uma conversa.
2. **Kits no topo, catálogo logo abaixo.** Reduz esforço inicial sem tirar a exploração livre.
3. **Transparência.** A intenção entendida aparece em chips (tipo de pele e valor são editáveis; objetivo e preferências mudam ao editar a frase); cada item diz por que está no kit; o preço total é sempre visível.
4. **Controle.** Trocar item, mudar orçamento, ignorar os kits e comprar avulso estão sempre à mão.
5. **Segurança visível.** Avisos aparecem antes de adicionar ao carrinho; pedidos de saúde têm tela própria.
6. **Honestidade de protótipo.** Produtos, preços e checkout são simulados e dizem isso.

## Diferenciação de um chatbot (exigência do cliente)

| Chatbot convencional | Esta experiência |
| --- | --- |
| Thread de mensagens que cresce | Uma tela de resultados que se recompõe |
| Responde com texto | Responde com kits de compra editáveis |
| Quem pergunta faz o trabalho de comparar | Preço total, itens e alternativas já organizados |
| Pergunta várias coisas antes de ajudar | Mostra kits primeiro; no máximo uma pergunta de refinamento, sem bloquear |
| Inventa preço e disponibilidade | Preço e estoque só do inventário |

## Mapa de telas e fluxo

```
Início ──busca──▶ Resultados ──abrir kit──▶ Detalhe do kit ──trocar──▶ Folha de troca
   │                 │  ▲                        │
   │                 │  └── ajustar orçamento    ├──adicionar kit──▶ Carrinho ──▶ Checkout ──▶ Confirmação
   │                 │      ou responder pergunta│
   │                 └──adicionar produto avulso─┘
   └── pedido de saúde ──▶ Tela de segurança (sem kits)
```

| # | Tela | Papel |
| --- | --- | --- |
| 1 | Início | Campo de busca em linguagem natural, exemplos, atalhos de outras formas de busca |
| 2 | Resultados | Intenção em chips, orçamento, kits no topo, pergunta de refinamento, produtos individuais |
| 3 | Detalhe do kit | Itens por etapa, motivo de cada item, avisos, total, adicionar ao carrinho |
| 4 | Folha de troca | Alternativas da mesma etapa com diferença de preço e compatibilidade |
| 5 | Carrinho | Kits agrupados e itens avulsos, quantidades, subtotal |
| 6 | Checkout (simulado) | Entrega, pagamento, resumo |
| 7 | Confirmação | Número do pedido simulado e aviso de demonstração |
| 8 | Segurança | Explica o limite da IA e encaminha a um profissional |

## Estados que a interface precisa tratar

| Estado | Comportamento |
| --- | --- |
| Carregando | Esqueleto dos kits; o campo de busca continua utilizável |
| Kits completos (2 a 3) | Carrossel de cartões |
| Kits parciais (1) | Um cartão e nota "só encontramos uma combinação relevante"; sem forçar três |
| Nada dentro do orçamento | Mensagem direta, kit mais próximo com seu valor e botão "Subir orçamento para R$ X"; produtos individuais continuam |
| Falta tipo de pele | Cartão de pergunta com opções; kits já aparecem com a melhor suposição e sinalizam isso |
| Item sem estoque | Nunca aparece em kit; no catálogo individual, aparece desabilitado se for o caso |
| Pedido de saúde | Tela de segurança no lugar dos kits |
| Busca sem entendimento | Mostra produtos individuais mais próximos e sugere reformular |
| Carrinho vazio | Mensagem e atalho para o início |

## Cartão de kit (resultados)

Compacto, uma linha de leitura: **formato** (selo), **número de itens**, **preço total**, linha "dentro do orçamento" ou diferença, miniaturas dos itens e botão "Ver kit". Cores distintas por formato, mas o selo sempre traz o nome (não depender só de cor).

## Detalhe do kit

- Cabeçalho com formato, objetivo e total.
- Lista por etapa na ordem da rotina (limpeza, tratamento, hidratação, proteção).
- Cada item: miniatura, marca, nome, tamanho, preço, linha **"Por que está aqui"**, botão **Trocar**.
- Bloco de avisos (fotossensibilizante, gestação, separar períodos) logo acima do botão.
- Rodapé fixo: total e **Adicionar kit ao carrinho**; ação secundária para adicionar só alguns itens.

## Folha de troca

Lista de alternativas da mesma etapa, ordenadas por relevância; cada uma mostra preço, diferença em relação ao item atual (`+ R$ 10,00` ou `− R$ 4,00`), compatibilidade com o resto do kit e, se estourar o orçamento, um aviso. Itens incompatíveis aparecem desabilitados com o motivo.

## Controle de orçamento

Faixa de valores com atalhos (até R$ 80, R$ 120, R$ 200, sem limite) e ajuste fino. Mudar o valor recompõe os kits na hora. O valor extraído da frase aparece como chip e pode ser editado ali.

## Textos (tom)

Direto, calmo, sem exclamações. Exemplos:

- Topo da busca: "Descreva o que você precisa. Ex.: pele oleosa, até R$ 120."
- Kits: "Kits para o seu objetivo" / "Sugestões dentro do seu orçamento".
- Nada no orçamento: "Não encontramos um kit completo por até R$ 60. O mais próximo custa R$ 64,60."
- Segurança: "Esse tipo de pedido envolve saúde. Aqui eu só monto kits de cuidados com a pele. Para medicamentos e sintomas, converse com um farmacêutico ou médico."
- Rodapé de protótipo: "Demonstração. Produtos, preços e pagamento são simulados."

## Tokens de design (paleta de protótipo, não oficial)

| Token | Valor | Uso |
| --- | --- | --- |
| `--brand` | `#0B4FA8` | Ações principais, cabeçalho |
| `--brand-ink` | `#06306A` | Texto sobre fundo claro de marca |
| `--accent` | `#F26B21` | Preço e destaque de ação secundária |
| `--ok` | `#0E8A5F` | Dentro do orçamento, estoque |
| `--warn` | `#B26A00` | Avisos |
| `--danger` | `#B3261E` | Erros e bloqueios |
| `--bg` | `#F4F6FA` | Fundo |
| `--surface` | `#FFFFFF` | Cartões |
| `--line` | `#DDE3EE` | Bordas |
| `--text` | `#14213D` | Texto |
| `--muted` | `#5B6783` | Texto secundário |

Tipografia: pilha do sistema (`system-ui`), tamanhos 12/14/16/20/26. Raios 12 px e 20 px. Alvos de toque de 44 px ou mais nos botões principais.

Identidade: não usa marca, logotipo ou imagens da empresa. O cabeçalho mostra apenas o nome do protótipo em texto. Produtos usam um desenho de embalagem gerado por forma (tubo, frasco, pote, bastão, adesivo).

## Acessibilidade

Contraste mínimo AA nos textos; foco visível; chips e botões com rótulo textual; folha de troca e checkout navegáveis por teclado; `aria-live` para a mudança de total e de kits; nada depende só de cor.

## Rastreabilidade

Cada requisito do PRD aponta para uma tela aqui. Tabela completa de cobertura no doc 08.

## Diferenças entre o desenho e o protótipo

Registradas depois de ver as telas rodando. O que está acima é a intenção; o que está aqui é o que existe hoje.

| Ponto | Desenho | Protótipo |
| --- | --- | --- |
| Chips de objetivo e preferência | removíveis | só leitura; para mudar, edite a frase e busque de novo |
| Campo de busca ao ajustar o orçamento | refletiria o valor | mantém a frase original; o chip e o painel mostram o valor em uso (pode parecer contraditório, ex.: frase "até R$ 20" com painel em R$ 200) |
| Pergunta de tipo de pele | antes dos kits | depois dos kits, porque é opcional e empurrava o resultado para fora da tela |
| Título do kit | nome do kit | objetivo do pedido (ex.: "Controle de acne"); a faixa aparece na etiqueta |
| Imagens de produto | foto | miniatura em SVG por formato de embalagem e cor da marca fictícia |
| Checkout | simulado | simulado, sem campos de cartão; só nome, forma de receber e pagamento (Pix simulado ou na retirada) |
| Ao ajustar orçamento ou pele | recompõe na hora | mantém o resultado anterior esmaecido até a nova resposta chegar (350 ms de atraso simulado) |
| Acessibilidade | AA, teclado, `aria-live` | rótulos, foco visível, folha com `Esc` e `aria-modal`, `prefers-reduced-motion`; **sem medição de contraste e sem teste com leitor de tela** |

