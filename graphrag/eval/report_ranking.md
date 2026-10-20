# Ranking: treino x teste

Pesos calibrados no treino: {'bm25': 0.0, 'emb': 0.64, 'graph': 0.36}

| Configuração | nDCG@10 treino | P@5 treino | nDCG@10 teste | P@5 teste |
|---|---|---|---|---|
| somente BM25 | 0.4499 | 0.35 | 0.6892 | 0.4857 |
| somente vetores | 0.8277 | 0.625 | 0.9651 | 0.7714 |
| somente grafo | 0.8419 | 0.6625 | 0.9542 | 0.7714 |
| híbrido (pesos iniciais) | 0.801 | 0.6375 | 1.0 | 0.8143 |
| híbrido calibrado no treino | 0.8636 | 0.6625 | 1.0 | 0.8143 |

Treino: 16 frases. Teste: 14 frases, nunca usadas na calibração.
