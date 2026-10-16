# 09 — Decisões técnicas e premissas

Formato: decisão, motivo, alternativas e consequência. `P-xx` = pendente.

## Decisões tomadas

| ID | Decisão | Motivo | Alternativa descartada | Consequência |
| --- | --- | --- | --- | --- |
| D-01 | Entrada em linguagem natural, saída estruturada (sem thread de chat) | O cliente pediu explicitamente que não seja mais um chatbot; a equipe queria busca "como conversa" | Chat com histórico de mensagens | Interface mais simples e diferenciada; perguntas de refinamento limitadas a uma por vez |
| D-02 | Escopo inicial só cosméticos e autocuidado | Rede vende medicamentos; regras clínicas sem validação não devem ser inventadas | Incluir medicamentos de venda livre | Menos abrangente, muito mais defensável; camada de medicamentos fica como proposta |
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
| P-01 | Armazenamento do grafo | Neo4j, Kùzu embarcado, NetworkX | Início da fase GraphRAG |
| P-02 | Embeddings e índice vetorial | modelo local ou API; FAISS/Chroma | Início da fase GraphRAG |
| P-03 | Modelo de linguagem para intenção e justificativa | API ou modelo local | Início da fase GraphRAG |
| P-04 | Hospedagem do protótipo para o avaliador | serviço estático gratuito ou servidor próprio | Antes de 26/10 |
| P-05 | Imagens de produto | **decidido em D-15** | — |
