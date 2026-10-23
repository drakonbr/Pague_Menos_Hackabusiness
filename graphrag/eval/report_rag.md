# Avaliação do RAG com DeepSeek (#33 e #38)

Frases que o grafo não entendia em 23/10 (graphrag/eval/rag_set.py). Acerto = regra do caso e nenhuma violação das invariantes.

| Conjunto | n | só o grafo | grafo + DeepSeek |
|---|---|---|---|
| TRAIN busca | 7 | 1/7 (0.0 s/frase) | 7/7 (1.5 s/frase) |
| TRAIN ajuste | 3 | 0/3 (0.0 s/frase) | 3/3 (1.6 s/frase) |
| TEST busca | 6 | 0/6 (0.0 s/frase) | 6/6 (1.5 s/frase) |
| TEST ajuste | 4 | 0/4 (0.0 s/frase) | 3/4 (1.2 s/frase) |
| NOVO busca | 5 | 0/5 (0.0 s/frase) | 5/5 (1.3 s/frase) |
| NOVO ajuste | 3 | 0/3 (0.0 s/frase) | 3/3 (1.3 s/frase) |

Erros (só o grafo): minha cabeça tá latejando; meu nariz não para de escorrer; suo muito embaixo do braço; to soltando pum demais; caganeira desde ontem; remédio pra unha encravada; tira tudo que tem cheiro; algo mais em conta; não quero ácido; a cabeça vai explodir; cabeça pesada e latejando; nariz pingando o dia todo; torci o pé; dei um mau jeito nas costas; quero um remédio pra calvície; tira o que tem álcool; não quero nada de origem animal; nada que arda; coisa mais top; nariz trancado não consigo respirar; barriga desarranjada; quero algo pra ficar menos cansado; pescoço travado; remédio pra frieira; nada que tenha glúten; menos caro por favor; quero o mais caprichado

Erros (grafo + DeepSeek): nada que arda

Chamadas à DeepSeek: 0 de 101 frases do conjunto de busca do motor (0%); 18 de 119 contando as frases deste RAG (15%). Meta do #34: abaixo de 15% no conjunto do motor.

Chamadas reais feitas nesta avaliação: 28 (com cache).
