# 12 — App real hoje e o que integrar ao protótipo

Status: **pesquisa feita e decisões tomadas em 15/10/2026**: fotos reais sem marca (opção A), caminho de compra completo, prints do app enviados por você (doc 13). Implementação: telas e dados prontos; fotos aguardando o download no seu computador.
Escopo do protótipo: só cosméticos (doc 07). Nada aqui usa dados internos da empresa; tudo vem de fontes públicas listadas no fim.

## 1. O que está confirmado sobre o app hoje

| Área | O que existe | Fonte |
| --- | --- | --- |
| Peso do app | 63% das vendas do e-commerce; +77% no ano (2T26). Digital = 24,1% da receita bruta | Release 2T26 |
| Retirada e entrega | Clique & Retire = **49%** dos pedidos; Expressa até 2 h = 34%; Agendada = 17% (2T26). Mais de 80% dos pedidos entregues em até 2 h | Release 2T26 |
| Clique & Retire | sem taxa; retirada a partir de 2 h após pagamento; lojas e lockers; documento com foto; cancela se não retirar em 15 dias úteis | Política de frete |
| Escolha de loja | seleção de loja em lista e mapa; checkout com menos etapas (versão 4.32.0) | App Store |
| Estoque por loja | consultar disponibilidade na drogaria mais próxima | App Store |
| Cesta | "Régua de Frete Grátis na cesta" (4.24.0); frete grátis a partir de R$ 150 (clientes Ouro: R$ 99,99) | App Store; política de frete |
| Pagamento | Pix, Nupay (4.24.0 e 4.25.0), cartão; Apple Pay e Google Pay no site | App Store; site |
| Pedidos | lista de pedidos logo após a compra, com status de Pix e Nupay e filtros (4.25.0) | App Store |
| Economia | cupons, favoritos, Cashback, Programa de Fidelidade, "Desconto Só Meu", Farmácia Popular, PBM | App Store |
| Cashback | Carteira+: selo no produto com cashback; saldo na carteira para próximas compras (lançada em 2023) | ABC da Comunicação |
| Recorrência | Assinaturas: envios programados conforme o uso, sem custo | App Store |
| Saúde | Clinic Farma (teleconsulta com médicos, farmacêuticos e outros); lembrete de medicamentos (4.28.1); upload de receita e token de convênio (4.23.0) | App Store |
| Vitrines | novas vitrines na tela inicial (4.22.0); nova interface de promoções (4.31.2) | App Store |
| Categorias (site) | "Dermo e Beleza" → Rosto (Sabonetes e Géis de Limpeza, Água Micelar, Hidratante Facial, Sérum, Vitamina C, Retinol, Niacinamida...), **Pele por tipo** (Normais e Mistas, Oleosas e Acneicas, Secas e Sensíveis, Com Manchas), Protetores Solares Faciais (Com Cor, Bastão, Toque Seco, Mineral, Clareador) e **Kit Protetor Solar** | Site |
| Página de produto (site) | nome, marca, código; preço; quantidade; CEP com "Calcular"; seções APRESENTAÇÃO, BENEFÍCIOS, PARA QUE SERVE, COMO DEVO USAR, ADVERTÊNCIAS; sem estoque → "Avise-me" | Site |
| Kits atuais | nos exemplos vistos: combos fixos do fabricante, da mesma marca, às vezes com brinde; sem mostrar economia e sem trocar itens | Páginas de kit do site |
| Dores relatadas | avaliações citam navegação confusa para voltar, app pesado e produto sem estoque que só avisa na cesta | App Store (avaliações) |

**Não confirmado:** o desenho exato das telas do app (abas inferiores, ordem da home, cores atuais). As fontes públicas são texto; capturas da loja de apps não foram analisadas. A forma de chegar perto do visual real é usar prints do app tirados por você.

**Não usado de propósito:** a afirmação de um artigo de análise de que problemas de experiência do usuário desaceleraram o digital no 2T26. Ela não aparece no release oficial.

## 2. Vale integrar? Avaliação etapa por etapa

Critério: integra quando o kit muda o resultado daquela etapa ou quando a etapa é usada pela maioria dos pedidos. Deixa fora o que é regulado (medicamento) ou o que só seria cenário.

| Etapa real | Decisão | Por quê | Como fica ligado aos 100 produtos |
| --- | --- | --- | --- |
| Início com vitrines | **Integrar** | Lugar natural para "Kits para você" e para a busca por intenção | vitrines geradas do catálogo (mais vendidos simulados, promoções, kits prontos por objetivo) |
| Busca | **Integrar** (já existe) | É o ponto de entrada da ideia | busca por intenção + busca por texto |
| Categorias Dermo e Beleza | **Integrar** só a árvore de Dermo | O catálogo fictício cobre exatamente Rosto, Pele por tipo e Protetores | mapear `line`, `productType` e `skinTypes` para as subcategorias reais; outras categorias aparecem desativadas, com aviso de fora do protótipo |
| "Kit Protetor Solar" | **Substituir/estender** | Mostra o contraste entre kit fixo e kit montado pela necessidade | entrada "Kits inteligentes" dentro de Dermo e Beleza |
| Página de produto | **Integrar** | Sem ela o protótipo não parece o app | seções reais (Apresentação, Benefícios, Para que serve, Como devo usar, Advertências) vindas dos campos que já temos; "Avise-me" para os 5 sem estoque; bloco "Este produto está nestes kits" |
| Cesta + régua de frete grátis | **Integrar** | A régua conversa com kits: "complete o kit e ganhe frete grátis" | cálculo com os preços do inventário fictício |
| Clique & Retire com loja e estoque | **Integrar (prioridade)** | 49% dos pedidos. O kit só serve se estiver completo na loja escolhida | novo dado sintético: lojas fictícias e estoque por loja; o compositor passa a respeitar a loja |
| Entrega Expressa / Agendada | **Simular** | Mostra as opções reais; a regra de prazo não muda o kit | opções e preços fictícios |
| Pagamento (Pix, cartão, Nupay) | **Simular só a escolha** | Sem campo de cartão, sem dado real | já é assim hoje |
| Pedidos e status | **Simular** | Fecha o ciclo da demonstração | lista local de pedidos simulados |
| Cashback (selo e saldo) | **Simular, com premissa** | Mostra que o kit soma cashback; regras reais podem ter mudado desde 2023 | percentual fictício por produto; total do kit |
| Cupom, favoritos | **Simular leve** | Barato e familiar | favoritar kit; campo de cupom de demonstração |
| Assinatura | **Integrar como opção do kit** | Kit de rotina é recorrente por natureza; maior valor de negócio | "Receber este kit a cada 30/60 dias" (simulado) |
| Clinic Farma / farmacêutico | **Só como encaminhamento** | Casa com a tela de segurança (doc 07) | botão "Falar com um farmacêutico" leva a uma tela informativa simulada |
| Receita, convênio, Farmácia Popular, PBM, lembrete de medicamento | **Fora** | Medicamento e regulação; fora do escopo e do risco aceitável | itens visíveis no menu, desativados |
| Login e cadastro reais | **Fora** | Sem dado pessoal (doc 10) | sessão de convidado |
| Superapps, WhatsApp, retail media | **Fora** | Não mudam a experiência do kit no app | citados no pitch como canais futuros |

Resumo: vale integrar o caminho de compra inteiro (início → busca/categoria → produto/kit → cesta → retirada ou entrega → pagamento simulado → pedido). Ele passa a ser um ecossistema, não uma tela isolada. A peça nova mais importante é o **estoque por loja**: com 49% dos pedidos em retirada, um kit que não está completo na loja escolhida é um kit que não serve.

### Impacto na separação de módulos

- `catalog/`: novos dados sintéticos (lojas, estoque por loja, cashback, vitrines) e o banco de imagens com manifesto de licença.
- `contracts/`: `Product` ganha `images` e `cashbackPct`; `SearchRequest` ganha `storeId` opcional; `Kit` ganha disponibilidade por loja.
- `app/`: novas telas (categorias, produto, seleção de loja, pedidos) e a cesta com régua.
- `graphrag/`: não muda o desenho; estoque por loja continua fora do grafo (dado vivo).

## 3. Imagens reais: opções

Fato que limita: o ambiente de trabalho e a ponte com o seu computador não alcançam sites de imagens (bloqueio de rede testado em 15/10). O download precisa rodar no seu Windows, por um script em `tools/`, ou você libera os domínios nas configurações de rede.

| Opção | Como | A favor | Contra |
| --- | --- | --- | --- |
| **A. Fotos reais sem marca** (recomendada) | fotos de banco gratuito (Pexels, Unsplash) de frascos, tubos e potes sem rótulo legível, escolhidas por formato e tipo | parece real; não associa marca real a um produto inventado; Pexels e Unsplash não exigem atribuição | foto repetida entre produtos parecidos; nem sempre é foto de estúdio com fundo branco |
| B. Produtos reais do Open Beauty Facts | trocar as marcas fictícias por produtos reais com foto, mantendo preço e estoque fictícios | foto e nome batem; dado público | deixa de ser catálogo fictício; põe benefícios e preços inventados em marcas reais; fotos CC BY-SA (atribuição e mesma licença), sem cobrir marcas registradas; pouca cobertura de produtos brasileiros |
| C. Fotos reais de marcas reais em produtos fictícios | foto de um produto real no lugar do nosso | rápido | engana: "Aurora Dermo" com frasco de outra marca. Não recomendado |
| D. Imagens geradas com as nossas marcas fictícias | packshots gerados com o rótulo das marcas inventadas | casa perfeito com o catálogo | não é foto real, que foi o pedido |

Em qualquer opção, o banco de imagens fica em `catalog/images/` com um manifesto (`images.json`): arquivo, produto ou tipo atendido, fonte, autor, licença, data. O app recebe as imagens pela mesma ponte de mão única (`tools/export_app_mock.py`).

## Fontes

- [Farmácias Pague Menos na App Store](https://apps.apple.com/BR/app/id1172438313) (descrição, histórico de versões e avaliações)
- [Release de resultados 2T26](https://api.mziq.com/mzfilemanager/v2/d/2cf06553-5bc1-44cd-b75f-6f3cd49d155d/07b599d9-f09f-55c3-f459-f4b25268b0c5?origin=2)
- [Suno: digital passa de R$ 1 bilhão no 2T26](https://www.suno.com.br/noticias/?p=660357)
- [Política de frete](https://www.paguemenos.com.br/politica-de-frete)
- [Site, página inicial e menu](https://www.paguemenos.com.br/)
- [Exemplo de página de produto](https://www.paguemenos.com.br/protetor-solar-nivea-sun-facial-toque-seco-fps60-50ml/p) e [exemplo de kit](https://www.paguemenos.com.br/kit-protetor-solar-sunless-fps50-200g-mais-mini-protetor-facial-sunless-30g-gratis/p)
- [Carteira+ e cashback (2023)](https://www.abcdacomunicacao.com.br/pague-menos-lanca-a-carteira-e-e-primeira-rede-de-farmacias-a-oferecer-cashback-em-compras/)
- [Giro News: canais digitais no 2T25](https://gironews.com/farma-cosmeticos/venda-do-canais-digitais-da-pague-menos-registra-alta-de-568-na-comparacao-anual/)
- [Mercado & Consumo: novo app (2022)](https://mercadoeconsumo.com.br/2022/03/25/novo-app-da-pague-menos-permite-personalizacao-de-compras-pelos-clientes/)
- Licenças: [Open Beauty Facts](https://world.openbeautyfacts.org/terms-of-use), [Pexels](https://www.pexels.com/license/), [Unsplash](https://unsplash.com/license)

## 4. O que foi feito com esta avaliação (15/10)

| Item | Estado |
| --- | --- |
| Lojas fictícias (8, Fortaleza) e estoque por loja | gerados e validados (`catalog/generate_commerce.py`) |
| Kits respeitando a loja e ajuste ao trocar de loja | implementado no simulador; testes T13 e T14 |
| Cashback por produto e por kit | premissa fictícia; invariante I15 |
| Categorias Dermo e Beleza com os nomes do menu real | 27 categorias, todo produto em pelo menos uma |
| Telas do caminho de compra | ver doc 13 |
| Assinatura do kit | escolha na página do kit e na cesta; lista em Mais → Assinaturas |
| Banco de imagens | script de download e de atribuição prontos e testados com fotos falsas; **fotos reais pendentes** |
| Proposta "kit usa o motor Combine N" | só proposta; não implementado |


## Atualização de 20/10

A área de medicamentos, antes visível e desativada, agora existe só como **reposição** para a persona Renata (receita simulada, equivalentes, alerta de 7 dias). Ver [doc 14](14-persona-e-privacidade.md) e as decisões D-21 a D-26.
