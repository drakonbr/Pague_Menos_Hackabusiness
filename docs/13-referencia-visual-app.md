# 13 — Referência visual do app real e como o protótipo a segue

Status: **telas implementadas e vistas no navegador** (Chromium, 400×860), a partir de 10 prints do app tirados em 15/10/2026.

Os prints mostram nome, endereço e CEP de uma pessoa real. Por isso **não foram versionados** neste repositório; este documento descreve só o layout. Se precisar dos prints, eles ficam com você.

## Tokens tirados dos prints

Cores medidas nos pixels dos prints (não estimadas a olho):

| Token | Valor | Onde aparece |
| --- | --- | --- |
| `--brand` | `#0100BE` | cabeçalho da home, botões, aba ativa, segmentado "Todas as lojas" |
| `--brand-dark` | `#0C0C90` | nome da marca no cartão, botão redondo de cesta |
| `--brand-soft` | `#EAF1F9` | faixa de "Relevância" e "Filtros" |
| `--logo` | `#F23F5F` | quadrado do logotipo e cruz das lojas |
| `--price` / `--tag-ink` | `#E4183C` | preço em destaque e texto das etiquetas de promoção |
| `--tag-bg` | `#FFEAE8` | fundo das etiquetas ("Super oferta", "Combine 3 com 30% OFF") |
| `--ok` | `#0C7824` | "Descontos ativados", "Aberta", "Promoção ativada!" |
| `--bg` | `#F7F7F7` a `#F9F9F9` | fundo das telas |

Tipografia: Roboto (Android). O logotipo real não foi copiado: o protótipo usa um quadrado vermelho com cruz branca, símbolo genérico de farmácia.

## Telas com print e o que o protótipo reproduz

| Tela real (print) | Elementos | No protótipo |
| --- | --- | --- |
| Home | cabeçalho azul arredondado; logo + "Boa noite, Nome!" + cesta; busca branca sobreposta com câmera e microfone; linha de endereço com CEP; 2 atalhos ("Busque produtos usando sua receita" com selo Novo, "Configure alertas de medicamentos"); carrossel de banners; "Categorias" com "Exibir tudo" e blocos; "Aproveite as Melhores Ofertas para Você!" com "Super oferta" | Igual na estrutura. Saudação "visitante". Endereço → localização simulada. O 1º atalho vira **"Monte um kit pelo que você precisa" (Novo)**; receita aparece desativada. Banners do kit inteligente e da retirada. Nova faixa "Kits inteligentes para você" |
| Barra de abas | Home, Categorias, Ofertas, Favoritos, Mais | Igual |
| Busca (foco) | campo com "Cancelar"; atalhos Buscar por áudio, Buscar com receita (Novo), Ler código de barras; "Buscas recentes" com "Limpar busca" e X | Igual; os 3 atalhos ficam desativados (fora do protótipo); acrescenta aviso da busca por necessidade e exemplos |
| Resultados | voltar, campo com a busca e X, cesta com contador; faixa azul-clara com "Relevância ▾" e "Filtros"; "N produtos encontrados" em itálico; grade 2 colunas: etiqueta vermelha, coração, foto, nome em 2 linhas, MARCA em itálico azul, botão redondo de cesta, preço vermelho | Igual; **acima da faixa entra o bloco de kits** (chips de intenção, loja usada, orçamento, carrossel de kits) |
| Ofertas | título; cartão verde "Descontos ativados – Todos os Descontos só meu foram ativados"; grade de ofertas por marca/linha com "% OFF", validade e "Exibir itens" | Cartão verde igual; abaixo, grade de produtos em oferta (não há ofertas por linha no catálogo fictício) |
| Categorias | lista com ícones: Medicamentos e saúde, Dermo e beleza, Mamães e bebês, Vida saudável, Higiene pessoal, Conveniência, Marcas exclusivas, Pet shop | Igual; só Dermo e beleza abre, as outras indicam "fora do protótipo" |
| Favoritos (vazio) | barra azul com busca e cesta; coração sorrindo; "Ah não! Lista de favoritos vazia"; "Ir para ofertas" | Igual (ilustração redesenhada); com itens, mostra kits salvos e produtos |
| Cesta vazia | "Minha cesta"; cesta cinza; "Ops! Sua cesta esta vazia"; "Continuar comprando"; "Top de vendas!" | Igual |
| Cesta | "Pacote 1 – Vendido e entregue por …"; item com etiqueta, lixeira, "↓28%", preço riscado, preço, "R$ x/1und", quantidade; "Promoção ativada!" verde; "Resumo pacote 1" (Subtotal, Descontos, Total); **"Faltam R$ x para frete grátis."** com barra; "Aplicado para o cep … Alterar"; resumo fixo com "Seguir para entrega" e "Continuar comprando" | Igual; **linha de kit** agrupa os itens, mostra economia, cashback e assinatura (comprar uma vez / a cada 30 / 60 dias) |
| Forma de Entrega | abas Entrega, Retirar na loja, Locker; endereço "Principal" com Editar | Igual; Locker desativado; Entrega mostra Expressa (sai da loja mais próxima com a cesta completa) e Agendada (centro de distribuição) |
| Retirar na loja | "Lojas próximas à" + bairro/CEP + Alterar; segmentado **"Todas as lojas / Com estoque"**; "30 resultados" + "Abrir mapa"; cartão da loja: nome, "24 Horas.", "Aberta · 00:00 às 23:59", endereço, chips "+ Próxima", distância, **"Retirar em até 60 minutos"** | Igual, com 8 lojas fictícias; **cada loja diz "Cesta completa" ou "Falta 1 item"**; escolher loja incompleta abre "Ajustar para esta loja" (troca só o que falta); mapa esquemático |

## Telas sem print (aproximação, mesmo padrão visual)

Página de produto, página do kit, pagamento, confirmação, Meus pedidos, Assinaturas, Carteira, menu "Mais", lojas e créditos. A página de produto segue as seções públicas do site: APRESENTAÇÃO, BENEFÍCIOS, PARA QUE SERVE, COMO DEVO USAR, ADVERTÊNCIAS; sem estoque, mostra "Indisponível" e "Avise-me quando chegar" (simulado, sem coletar dados).

## O que os prints ensinaram (além do layout)

- **Retirada em 60 minutos**, não em 2 horas como diz a política de frete. O protótipo usa o texto do app.
- **A régua de frete grátis varia por CEP.** No print, faltavam R$ 373,03 com R$ 19,47 na cesta (limite de cerca de R$ 392,50 naquele CEP), contra R$ 150 da política pública. O protótipo usa R$ 150 como premissa e diz isso no ícone de informação.
- **O app já tem promoções de combinação** ("Combine 3 com 30% OFF", "Leve 3 e Pague", "Compre 3 ganhe desconto"). É um gancho de negócio: um kit inteligente pode usar esse motor de promoção para ter desconto de kit. Fica como proposta (doc 12), não implementado.
- **"Desconto de laboratório"** e "Descontos só meu" são mecânicas reais de preço; não foram simuladas.

## Diferenças que permanecem

| Ponto | App real | Protótipo |
| --- | --- | --- |
| Nome da rede nas telas | presente | ausente (constante em `app/src/brand.ts`) |
| Endereço e CEP | do cliente | localização simulada em Fortaleza |
| Fotos | fotos dos produtos | fotos reais sem marca (após a revisão); antes disso, desenho provisório com "foto pendente" |
| Ofertas | por marca/linha, com validade | por produto |
| Locker, receita, áudio, código de barras, alertas de medicamento | ativos | visíveis e desativados |
