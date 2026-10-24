# Avaliação do RAG com DeepSeek (#33, #38, #61 e #62)

Frases que o grafo não entendia em 23/10 (graphrag/eval/rag_set.py). Acerto = regra do caso e nenhuma violação das invariantes. AMPLO = 43 frases do dia a dia (a cada 3ª é TESTE, nunca usada para ajustar o vocabulário). Depois do #62 o grafo sozinho já entende parte dos conjuntos antigos: compare com os números do dia 23/10 antes do vocabulário (grafo 1 de 18 nos conjuntos TRAIN, TEST e NOVO).

| Conjunto | n | só o grafo | grafo + DeepSeek |
|---|---|---|---|
| TRAIN busca | 7 | 1/7 (0.0 s/frase) | 7/7 (1.5 s/frase) |
| TRAIN ajuste | 3 | 0/3 (0.0 s/frase) | 3/3 (1.5 s/frase) |
| TEST busca | 6 | 0/6 (0.0 s/frase) | 6/6 (1.3 s/frase) |
| TEST ajuste | 4 | 0/4 (0.0 s/frase) | 3/4 (1.4 s/frase) |
| NOVO busca | 5 | 1/5 (0.0 s/frase) | 5/5 (1.4 s/frase) |
| NOVO ajuste | 3 | 0/3 (0.0 s/frase) | 3/3 (1.4 s/frase) |
| AMPLO ajuste | 28 | 28/28 (0.0 s/frase) | 28/28 (0.2 s/frase) |
| AMPLO teste | 15 | 13/15 (0.0 s/frase) | 14/15 (0.5 s/frase) |
| RISCO controle | 16 | 16/16 (0.0 s/frase) | 16/16 (1.3 s/frase) |

Frases que o grafo acertava e a DeepSeek estragou: nenhuma

Erros (só o grafo): minha cabeça tá latejando; meu nariz não para de escorrer; suo muito embaixo do braço; to soltando pum demais; caganeira desde ontem; remédio pra unha encravada; tira tudo que tem cheiro; algo mais em conta; não quero ácido; a cabeça vai explodir; cabeça pesada e latejando; nariz pingando o dia todo; torci o pé; dei um mau jeito nas costas; quero um remédio pra calvície; tira o que tem álcool; não quero nada de origem animal; nada que arda; coisa mais top; nariz trancado não consigo respirar; barriga desarranjada; quero algo pra ficar menos cansado; remédio pra frieira; nada que tenha glúten; menos caro por favor; quero o mais caprichado; quero cuidar da pele que vive melada; minha pele vive com cara de cansada e sem brilho

Erros (grafo + DeepSeek): nada que arda; minha pele vive com cara de cansada e sem brilho

Chamadas à DeepSeek por conjunto de busca do motor (sem gastar nada):

| Conjunto | frases | chamadas | taxa |
|---|---|---|---|
| TRAIN | 62 | 0 | 0% |
| TEST | 39 | 0 | 0% |
| BLIND | 40 | 4 | 10% |
| BLIND2 | 38 | 7 | 18% |
| BLIND3 | 28 | 7 | 25% |
| BLIND4 | 36 | 9 | 25% |
| MED | 16 | 0 | 0% |
| MED_BLIND | 24 | 6 | 25% |
| AMPLO (dia a dia) | 43 | 9 | 21% |
| **Total do motor** | 283 | 33 | 11.7% |

Cada chamada leva cerca de 1,3 s e custa uma fração de centavo; o cache evita repetir a mesma frase.

Chamadas reais feitas nesta avaliação: 52 (com cache).
