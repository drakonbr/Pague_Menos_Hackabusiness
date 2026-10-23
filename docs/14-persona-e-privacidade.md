# 14 — Persona Renata Almeida, conversa e privacidade

Rodada de 20/10. O grupo criou a persona **Renata Almeida** (PDF do grupo, não versionado). Esta rodada treina o GraphRAG do zero para atendê-la, amplia o catálogo com produtos viáveis para ela e deixa o app **logado como ela**.

## 1. A persona

49 anos, Recife (Madalena), renda de R$ 4.500, casada, dois filhos adolescentes, treina 3x por semana. Hipertensão leve e colesterol alto, com dois medicamentos de uso contínuo. Compra dermocosméticos anti-idade, suplementos (Ômega 3, Colágeno, Magnésio) e higiene premium. Prefere o celular, quer ver o **preço total** (item + frete + entrega), gosta de recomendações relacionadas que não exponham dados de saúde e se preocupa com privacidade.

Objetivos: nunca ficar sem o remédio, poucos toques, opções parecidas. Dores: frete caro e lento, falta de estoque, mau uso de dado de saúde.

Imagem da persona: `docs/assets/persona-renata.svg` (desenho original, não é foto de pessoa).

## 2. Da necessidade à funcionalidade

| Necessidade da Renata | O que o protótipo faz | Onde |
| --- | --- | --- |
| Conversar na barra de busca, do jeito dela | Barra de busca abre uma conversa; 13 atos de fala; o contexto viaja a cada turno | `graphrag/nlu.py`, `dialogue.py`, `app/src/screens/Chat.tsx` |
| Rotina anti-idade, suplementos, higiene premium | Kits Econômico, Essencial e Completo para esses domínios, com troca de item e ajuste por orçamento | `graphrag/composer.py` |
| Preço total, não só o do item | "Total com entrega" mostra item + frete por modalidade; frete grátis sobre o limite | ação `delivery_quote` |
| Nunca ficar sem o remédio | Tela **Meus medicamentos**: unidades restantes, alerta de 7 dias, reposição em poucos toques | `Refill.tsx` |
| Estoque zerado na loja | A reposição mostra onde há estoque e **equivalentes** (mesmo princípio ativo e dose) | `/v1/similars` |
| Recomendação sem expor saúde | Similares de cosméticos por grafo; os de medicamento saem só como dado estruturado | `dialogue.similars` |
| Privacidade | Tela Privacidade explica o que fica no aparelho; o motor nunca recebe dado de saúde | doc 07, `test_privacy.py` |

## 3. Medicamentos: só reposição (revisto em 21/10)

> Desde o doc 16 (D-32), remédio é busca e kit como qualquer produto, sem bloqueio nem texto de farmacêutico. A reposição abaixo continua igual, só sem a confirmação "com o farmacêutico". A privacidade do item 4 continua valendo: o motor não lê a lista de remédios da pessoa; ele só recebe o que ela digita.

Decisão da Julia: **reposição, sem recomendar**.

- O motor **nunca** sugere medicamento, dose, diagnóstico ou troca de tratamento. Pedido assim é bloqueado (`safety.py`), mesmo dentro do fluxo de reposição.
- Os itens da reposição (nomes genéricos fictícios, `rx = receita_simples`) existem só no catálogo para a tela de reposição. Não entram em kits, em busca livre, em sugestões nem em texto de resposta.
- Equivalentes (`equivalence`: grupo, apresentação referência/genérico/similar, ativo, dose) são devolvidos como **dados**; a tela mostra "A troca só vale com a confirmação do farmacêutico e conforme a sua receita".
- A receita é **simulada**: nenhum documento real é enviado. Frete grátis, 5% e alerta de 7 dias são premissas fictícias.

## 4. Privacidade por construção

1. Os dados de saúde da persona (`catalog/data/persona.json`) **ficam no aparelho**. O motor não os lê; um teste rastreia os arquivos abertos e falha se `persona.json` aparecer.
2. O app envia só a frase, o `context` (intenção cosmética, ids de kit) e ids de produto. Nunca condição, medicamento ou histórico.
3. ~~Respostas não contêm termos de saúde nem nomes de medicamentos~~: substituída em 21/10 (doc 16) por "nenhuma resposta manda procurar médico ou farmacêutico" (invariante M2, testada). A busca de remédio nomeia o remédio e a queixa que a pessoa digitou.
4. Repositório privado, empresa não identificada em lugar público, dados só sintéticos, sem criar contas, sem pagamento real.

## 5. Como o GraphRAG foi feito (do zero, sem Ollama nem modelo externo)

| Peça | Como é | Artefato |
| --- | --- | --- |
| Grafo de conhecimento | networkx; 329 nós e 2197 arestas, incluindo `EQUIVALENT_TO` e `SIMILAR_TO` | `artifacts/graph.json` |
| Vetores de palavras | PPMI + SVD sobre 762 frases geradas do catálogo; vocabulário de 488 | `artifacts/embeddings.npz` |
| BM25 | texto de cada produto | `retrieval.py` |
| Ativação espalhada | parte das entidades citadas e se espalha pelo grafo | `graph.py` |
| Nota híbrida | `w_bm25·bm25 + w_emb·emb + w_graph·grafo`, pesos calibrados por subida de coordenadas: bm25 0,00, emb 0,64, grafo 0,36 | `artifacts/weights.json` |
| Ato de fala | Naive Bayes treinado em 198 frases | `artifacts/nlu_model.json` |
| Entidades | regras sobre léxico (preocupação, pele, ingrediente pedido/excluído, etapa, orçamento, gestação, nível do kit) | `nlu.py`, `lexicon.py` |
| Compositor | regras determinísticas K1 a K12 | `composer.py` |
| Conversa | sem estado no servidor; o cliente reenvia o `context` | `dialogue.py` |

Treinar de novo: `python3 -m graphrag.train` e `python3 graphrag/eval/calibrate.py`. Servir: `python3 -m graphrag.service.server --port 8787`. Se o servidor não responder, o app cai no motor simulado e o selo "Motor" da conversa mostra qual está respondendo.

## 6. Resultados medidos

| Medida | Resultado |
| --- | --- |
| Classificador de ato de fala, frases fora do treino | 59 de 60 (98,3%) |
| Testes do motor, NLU, privacidade, ontologia, ingestão e streaming | 77 passam (os 26 novos são da rodada do [doc 15](15-graphrag-conversacional.md)) |
| Testes do app | 46 passam; build de produção sem erros de tipo |
| Validação do catálogo | 69 de 69 |
| Invariantes independentes (I1 a I16, M1, M2, X1), lendo o JSON bruto | passam |
| Percurso no navegador (Chromium, 412 px): kits, troca, pergunta de produto, bloqueio, "pode adicionar", reposição com equivalente e receita simulada, cesta | funciona; zero erros de console |

## 7. Limites honestos

- O conjunto de ranking tem só 14 frases; serve para calibrar, não para afirmar qualidade geral.
- As entidades são extraídas por regras: frase fora do vocabulário cai no ato mais próximo ou pede reformulação.
- Os vetores vêm de 762 frases geradas do próprio catálogo: bons para este catálogo, fracos fora dele.
- Fotos: o banco de imagens continua pendente (emissão de chave da Pexels pausada); o app mostra desenhos de embalagem.
- Premissas de reposição (frete, desconto, alerta) são fictícias e não validadas com a rede.
- Nenhuma regra clínica foi validada por profissional de saúde.
- Visto só em Chromium; acessibilidade não medida.
