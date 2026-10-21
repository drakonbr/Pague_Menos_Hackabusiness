# Ranking: treino x teste

Pesos calibrados no treino: {'bm25': 0.0, 'emb': 0.571, 'graph': 0.429}

| Configuração | nDCG@10 treino | P@5 treino | nDCG@10 teste | P@5 teste |
|---|---|---|---|---|
| somente BM25 | 0.398 | 0.3 | 0.6874 | 0.4857 |
| somente vetores | 0.8858 | 0.7375 | 0.9778 | 0.8 |
| somente grafo | 0.9306 | 0.75 | 0.9542 | 0.7714 |
| híbrido (pesos iniciais) | 0.8834 | 0.7 | 1.0 | 0.8143 |
| híbrido calibrado no treino | 0.9433 | 0.7375 | 1.0 | 0.8143 |

Treino: 16 frases. Teste: 14 frases, nunca usadas na calibração.
