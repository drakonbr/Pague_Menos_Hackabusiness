# 09 — Decisões técnicas e premissas

Formato: decisão, motivo, alternativas e consequência. `P-xx` = pendente.

## Decisões tomadas

| ID | Decisão | Motivo | Alternativa descartada | Consequência |
| --- | --- | --- | --- | --- |
| D-01 | Entrada em linguagem natural, saída estruturada (sem thread de chat); ajustada pela D-31 | O cliente pediu explicitamente que não seja mais um chatbot; a equipe queria busca "como conversa" | Chat com histórico de mensagens | Interface mais simples e diferenciada; perguntas de refinamento limitadas a uma por vez |
| D-02 | Escopo inicial só cosméticos e autocuidado (revogada pela D-32) | Rede vende medicamentos; regras clínicas sem validação não devem ser inventadas | Incluir medicamentos de venda livre | Menos abrangente, muito mais defensável; camada de medicamentos fica como proposta |
| D-03 | O modelo interpreta e explica; código escolhe e valida | Evitar preço, estoque e combinação inventados | Modelo compondo kits livremente | Resultado auditável; exige compositor determinístico |
| D-04 | Preço e estoque fora do grafo, consultados ao vivo | Mudam o tempo todo; precisam ser verdadeiros | Gravar preço no grafo | Uma consulta extra por busca; dados nunca velhos |
| D-05 | Quatro módulos separados (catálogo, app, GraphRAG, contratos) com ponte de mão única | Pedido explícito de não misturar | Monorepo com código compartilhado | Mais arquivos de documentação; troca de partes sem retrabalho |
| D-06 | Catálogo com cadastro e inventário em arquivos separados | Espelha sistemas reais diferentes | Um arquivo só | Integração real mais direta |
| D-07 | Hidratante com FPS cobre duas etapas (`coversSteps`) | Evita kit com dois produtos para a mesma função | Tratar como hidratante comum | Regra K1 fica correta e explicável |
| D-08 | App em React + TypeScript + Vite, CSS próprio, sem biblioteca de UI | Stack com que a equipe trabalha; controle total do visual; poucas dependências | Next.js; Tailwind; biblioteca de componentes | Build simples; mais CSS escrito à mão |
| D-09 | Serviço de busca como interface (`SearchService`) com implementação simulada | Trocar pelo GraphRAG sem refazer telas | Chamar o motor direto das telas | Contrato precisa ficar estável |
| D-10 | Serviço sem estado (o kit viaja inteiro) | Simplifica a demonstração e a integração | Sessão no servidor | Cargas um pouco maiores |
| D-11 | Dados 100% sintéticos, com marcas fictícias | Condição do desafio; evita risco jurídico | Copiar o catálogo público | Dados menos realistas |
| D-12 | Identidade visual própria de protótipo, sem marca da empresa | Confidencialidade e propriedade intelectual | Reproduzir a identidade da rede | Paleta e logotipo genéricos |
| D-13 | Documentação em arquivos `.md` por etapa dentro do repositório | Pedido explícito | Wiki externa | Documento junto do código e versionado |
| D-14 | Repositório privado | Exigência de confidencialidade do desafio | Repositório público para portfólio | Não usar o material em portfólio ou processo seletivo |
| D-15 | Imagens | Fotos reais **sem marca** (Pexels), escolhidas por formato de embalagem, revisadas uma a uma; catálogo continua fictício | Foto de marca real em produto inventado engana; trocar por produtos reais desfaria o catálogo fictício. Decisão da Julia em 15/10 |
| D-16 | Serviços do app | `CommerceService` (catálogo, lojas, estoque, frete) separado do `SearchService` (kits) | No sistema real, comércio são serviços que já existem; só os kits são novos (doc 10) |
| D-17 | Estoque por loja | Kits respeitam a loja escolhida; trocar de loja ajusta o kit trocando só o que falta (`adaptToStore`) | Retirada na loja é 49% dos pedidos (release 2T26); kit incompleto na loja não serve |
| D-18 | Nome da rede | Fora das telas; uma constante em `app/src/brand.ts` | Confidencialidade do desafio; pode ser trocado para apresentação interna |
| D-19 | Prints do app real | Não versionados; só o layout descrito no doc 13 | Mostram nome, endereço e CEP de uma pessoa |
| D-20 | Escopo do ecossistema | Caminho de compra completo (vitrines, categorias Dermo, produto, cesta com régua, entrega e retirada, pagamento simulado, pedidos, assinatura, cashback); medicamentos, receita, convênio e locker visíveis e desativados | Decisão da Julia em 15/10, a partir da avaliação do doc 12 |
| D-21 | Persona | O app abre logado como Renata Almeida (persona do grupo); sem conta real | Pedido da Julia em 20/10; a persona guia catálogo, conversa e testes |
| D-22 | Medicamentos (revogada pela D-32; a reposição continua) | Só reposição; o motor nunca recomenda, doseia ou nomeia; equivalentes só como dado, com confirmação do farmacêutico | Decisão da Julia em 20/10; coerente com o doc 07 |
| D-23 | Motor | GraphRAG do zero (networkx, PPMI+SVD, BM25, Naive Bayes), sem Ollama nem API externa | Decisão da Julia em 20/10; zero dependência de serviço pago e dados nunca saem da máquina |
| D-24 | Conversa | Sem estado no servidor: o cliente reenvia `context` (ids e preferências cosméticas) | Simples de testar; nada de pessoa guardado |
| D-25 | Privacidade | `persona.json` fora da leitura do motor, com teste que rastreia arquivos abertos | Dado de saúde fica no aparelho |
| D-26 | Fallback | `AutoSearchService`: tenta o GraphRAG local e cai no simulado | Demonstração não trava sem servidor |
| D-27 | Ontologia | Esquema estrito em Pydantic; grafo validado no treino e na ingestão; vocabulário fechado x aberto | Evita nó e aresta por acidente; doc 15 |
| D-28 | Ingestão | Determinística, sem LLM; resolução de entidades por texto normalizado; delta em `graphrag/artifacts/`, nunca em `catalog/` | Catálogo já é estruturado; mantém a decisão D-23 |
| D-29 | Streaming | `POST /v1/search-chat` (SSE) com texto por regras em pedaços; app ainda usa `/v1/search` | Contrato pronto para um gerador de texto futuro; sem espera artificial |
| D-30 | Rerank | MMR com lambda 0,9 só na lista de produtos | Medido: sem perda de relevância, ganho pequeno de variedade |
| D-31 | Busca e conversa | A barra de busca abre a tela de resultados (kits em cima, lista embaixo). Quando o ato de fala não é de busca (repor, entrega, trocar item, pergunta sobre produto), `Results.tsx` passa para a conversa (`Chat.tsx`) | Ajusta a D-01: com a persona (D-21) a conversa voltou, mas só onde a ação precisa de diálogo. Buscar continua devolvendo uma seleção de compra, não texto (doc 15) |
| D-32 | Medicamentos na busca e nos kits | Busca de remédio e de sintoma funciona como numa farmácia, com e sem receita; sem bloqueio e sem texto de encaminhamento; sem remédio no catálogo, só "Não está no banco de dados ainda." | Pedido da Julia em 21/10 (doc 16, respostas 1 e 2); revoga D-02 e D-22 e a política do doc 07 |
| D-33 | Modelo de medicamento | Princípio ativo = ingrediente; sintoma = preocupação; cada área de saúde = objetivo de kit com etapas que são papéis (dipirona, paracetamol, anti-inflamatório...) | Reaproveita grafo, vetores, escopo e compositor sem tipo novo na ontologia |
| D-34 | Regras dos kits de remédio | Nunca o mesmo princípio ativo duas vezes (compositor); nunca dois anti-inflamatórios, nem expectorante com remédio para tosse seca (interações `evitar`) | Aceita pela Julia em 21/10 (doc 16, resposta 3) |
| D-35 | Dados de medicamento | Princípios ativos e apresentações reais e comuns; marcas e laboratórios fictícios; nomes populares (Dorflex, Buscopan...) só como sinônimo de busca | Mantém o catálogo fictício (D-11) e aceita o jeito como as pessoas pedem |
| D-36 | Prateleira de saúde gerada do catálogo | Um conceito por queixa e por objetivo, calculado dos produtos (`ScopeResolver.health_concepts`) | Produto novo de uma área entra na busca sem editar conceito à mão |
| D-37 | Fallback seletivo | Gate de incerteza, guarda de parte do corpo, cota 100/h visível em `/v1/health`, ato "não consigo" = busca, sugestões por ranking e cache de gíria em `slang.py`; a DeepSeek continua só entendendo, nunca compondo kit | O fallback só era chamado quando o grafo admitia não entender; falsos positivos confiantes e cota silenciosa pioravam a busca sem aviso |
| D-38 | Catálogo ampliado | 297 produtos: 68 de higiene (6 por prateleira, incluindo creme para pentear, escovas, fio dental, talco, buchas, cotonetes e limpeza auricular) e 108 medicamentos em 16 áreas (antifúngico, antibiótico, antiviral e corticoide, 6 cada) | Pedido do usuário em 24/10; ids antigos preservados, remédio continua fora de kit e validação cobre as novas classes |

## Premissas

1. Nenhum dado, sistema ou credencial da empresa foi usado.
2. O catálogo real teria atributos equivalentes aos do catálogo sintético (tipo, ingredientes, tipo de pele, FPS); onde não tivesse, a ingestão precisaria enriquecer com extração a partir da descrição.
3. Preço e estoque estariam disponíveis por consulta em lote.
4. O app real aceitaria exibir um bloco de kits acima da lista de resultados.
5. Pagamento e carrinho continuam nos sistemas existentes.
6. Resultados de negócio (conversão, ticket médio) são hipóteses, não promessas.

## Pendências

| ID | Tema | Opções | Quando decidir |
| --- | --- | --- | --- |
| P-01 | Armazenamento do grafo | **decidido: NetworkX (D-23)**; Neo4j só em produção | — |
| P-02 | Embeddings e índice vetorial | **decidido: PPMI+SVD do zero (D-23)** | — |
| P-03 | Modelo de linguagem para intenção e justificativa | **decidido: sem modelo de linguagem; regras + Naive Bayes (D-23)**. Comparar com o documento prático de GraphRAG que a Julia vai enviar | Ao receber o documento |
| P-04 | Hospedagem do protótipo para o avaliador | serviço estático gratuito ou servidor próprio | Antes de 26/10 |
| P-05 | Imagens de produto | **decidido em D-15** | — |
