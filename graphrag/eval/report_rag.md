# Avaliação do RAG com DeepSeek (#33, #38, #61 e #62)

Frases que o grafo não entendia em 23/10 (graphrag/eval/rag_set.py). Acerto = regra do caso e nenhuma violação das invariantes. AMPLO = 43 frases do dia a dia (a cada 3ª é TESTE, nunca usada para ajustar o vocabulário). Depois do #62 o grafo sozinho já entende parte dos conjuntos antigos: compare com os números do dia 23/10 antes do vocabulário (grafo 1 de 18 nos conjuntos TRAIN, TEST e NOVO).

| Conjunto | n | só o grafo | grafo + DeepSeek |
|---|---|---|---|
| TRAIN busca | 7 | 3/7 (0.0 s/frase) | 6/7 (0.9 s/frase) |
| TRAIN ajuste | 3 | 0/3 (0.0 s/frase) | 3/3 (1.8 s/frase) |
| TEST busca | 6 | 3/6 (0.0 s/frase) | 6/6 (0.8 s/frase) |
| TEST ajuste | 4 | 1/4 (0.1 s/frase) | 3/4 (1.2 s/frase) |
| NOVO busca | 5 | 1/5 (0.0 s/frase) | 5/5 (1.6 s/frase) |
| NOVO ajuste | 3 | 0/3 (0.0 s/frase) | 3/3 (1.6 s/frase) |
| AMPLO ajuste | 28 | 28/28 (0.0 s/frase) | 28/28 (0.2 s/frase) |
| AMPLO teste | 15 | 13/15 (0.0 s/frase) | 14/15 (0.4 s/frase) |
| RISCO controle | 16 | 16/16 (0.0 s/frase) | 16/16 (1.2 s/frase) |

Frases que o grafo acertava e a DeepSeek estragou: nenhuma

Erros (só o grafo): meu nariz não para de escorrer; suo muito embaixo do braço; to soltando pum demais; remédio pra unha encravada; tira tudo que tem cheiro; algo mais em conta; não quero ácido; torci o pé; dei um mau jeito nas costas; quero um remédio pra calvície; tira o que tem álcool; não quero nada de origem animal; nada que arda; nariz trancado não consigo respirar; barriga desarranjada; quero algo pra ficar menos cansado; remédio pra frieira; nada que tenha glúten; menos caro por favor; quero o mais caprichado; quero cuidar da pele que vive melada; minha pele vive com cara de cansada e sem brilho

Erros (grafo + DeepSeek): to soltando pum demais; nada que arda; minha pele vive com cara de cansada e sem brilho

Chamadas à DeepSeek por conjunto de busca do motor (sem gastar nada):

| Conjunto | frases | chamadas | taxa |
|---|---|---|---|
| TRAIN | 62 | 0 | 0% |
| TEST | 39 | 0 | 0% |
| BLIND | 40 | 3 | 8% |
| BLIND2 | 38 | 7 | 18% |
| BLIND3 | 28 | 6 | 21% |
| BLIND4 | 36 | 8 | 22% |
| MED | 16 | 0 | 0% |
| MED_BLIND | 24 | 4 | 17% |
| AMPLO (dia a dia) | 43 | 8 | 19% |
| **Total do motor** | 283 | 28 | 9.9% |

Cada chamada leva cerca de 1,3 s e custa uma fração de centavo; o cache evita repetir a mesma frase.

Chamadas reais feitas nesta avaliação: 41 (com cache).

## Conjunto cego blind5 (24/10, `python -m graphrag.eval.blind5_run [--live]`)

100 casos (80 buscas e 20 ajustes) escritos por um agente independente que não viu o código. A metade A (índices pares) serve para diagnosticar; a metade B (ímpares) nunca teve as falhas olhadas, só a contagem. Duas regras do arquivo estavam com a chave de pele sem acento ("sensivel"); foi corrigido nos dois lados da medição. Atenção: `rag_eval.py` reescreve este arquivo; esta seção é acrescentada à mão depois de rodá-lo.

| | só o grafo, antes | só o grafo, depois | grafo + DeepSeek, antes | grafo + DeepSeek, depois |
|---|---|---|---|---|
| A (50) | 33 | 41 | 40 | 43 |
| B (50, cega) | 34 | 36 | 41 | 43 |

Leitura honesta: com 50 casos por metade, +2 em B está dentro do ruído e não prova generalização; o ganho em A é em parte ajuste às frases dela. A revisão achou aliases soltos demais (que criavam falso positivo, como "filtro de linha" virando protetor solar e "caroço no seio" virando kit de acne) e aliases de saúde sensíveis; esses foram tirados, o que custou 4 pontos em A (45 para 41) e nada em B. Nos conjuntos antigos a DeepSeek não estragou nenhuma frase que o grafo acertava; algumas frases isoladas variam de uma rodada para outra (a DeepSeek não é determinística). Um banco de 327 jeitos de falar, gerado por outro agente e posto no treino dos vetores, não melhorou B (36 de 50), piorou um conjunto antigo e foi desfeito (decisão tomada olhando a contagem de B, o que é seleção de modelo em B). Falhas que sobram em A: alergia por comida, desmaquilagem à prova d'água, pele áspera, "cabelo caindo e unhas quebrando, falta de vitamina?", "pele descasca no inverno, repuxa depois do banho" e "teste de gravidez" (o motor devolve lista vazia, mas o caso não é reconhecido como "não temos"). Frases de alerta (sangue, língua inchada, rigidez no pescoço) continuam sem tratamento de urgência: é o item #63, que depende de decisão da Julia.
