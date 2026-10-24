# graphrag/ — sistema GraphRAG do zero

> **Status (20/10): implementado e treinado.** Sem Ollama: só Python, networkx e numpy. Dados sintéticos; repositório privado.
>
> **RAG com DeepSeek (23/10):** `llm.py`. Só entra quando o grafo não entende o pedido (nunca nas 101 frases do conjunto de busca; nunca num simples "não", numa pergunta com "?" nem no replay do histórico do chat); a DeepSeek traduz a frase para ids do catálogo, o que não existe é descartado e o grafo busca de novo com esses rótulos. Kits continuam do compositor. Quando o grafo responde mas vê palavra desconhecida, a DeepSeek só confere: a resposta do grafo muda apenas se ela EXPLICAR a palavra com algo do catálogo que o grafo não cobria (palavra negada nunca conta; nunca vira lista de remédios sem pedido de dor, remédio ou sintoma). Sem `DEEPSEEK_API_KEY` (ou com a API fora do ar), o motor responde como antes e avisa na partida e em `/v1/health` (`rag`, `ragCalls`). Avaliação: `python -m graphrag.eval.rag_eval --live` (relatório em `eval/report_rag.md`).

Recebe uma frase (e o contexto da conversa) e devolve resposta, kits e ação, seguindo `../contracts/README.md`. Pensado para a persona Renata Almeida (doc 14), mas serve a qualquer pedido dentro do catálogo.

## Peças

| Arquivo | Papel |
| --- | --- |
| `text.py`, `lexicon.py` | normalização e vocabulário (preocupações, ingredientes, etapas, preferências) |
| `data.py` | leitura do catálogo (lista permitida de arquivos; `persona.json` fora) |
| `graph.py` | grafo de conhecimento (networkx) e ativação espalhada |
| `embed.py` | vetores de palavras PPMI + SVD |
| `retrieval.py` | BM25 + vetores + grafo, com pesos calibrados |
| `nlu.py`, `nlu_corpus.py`, `corpus_extra.py` | ato de fala (Naive Bayes) e extração de entidades |
| `scope.py`, `concepts.py`, `spell.py` | escolha da prateleira antes do ranking e correção de digitação (doc 15) |
| `safety.py` | regras de segurança antes de tudo |
| `composer.py` | compositor de kits K1 a K12, troca de item, adaptação à loja |
| `dialogue.py` | motor de conversa (sem estado), similares, cotação de entrega |
| `ontology.py` | ontologia estrita (nós, arestas, esquema de entrada) em Pydantic |
| `ingest.py` | ingestão incremental com resolução de entidades (delta em `artifacts/`) |
| `rewrite.py`, `chat_stream.py` | reescrita pelo histórico e eventos SSE de `/v1/search-chat` |
| `service/server.py` | HTTP local (`/v1/search`, `/v1/search-chat`, `/v1/similars`, …) |
| `train.py` | gera `artifacts/` |
| `eval/` | calibração dos pesos, conjuntos de ranking e de busca, invariantes independentes, latência |
| `tests/` | 95 testes (motor, NLU, privacidade, ontologia, ingestão, streaming, escopo da busca, medicamentos) |

## Comandos (a partir da raiz do repositório)

```bash
pip install -r graphrag/requirements.txt
python3 -m graphrag.train                    # grafo, vetores, classificador
python3 graphrag/eval/calibrate.py           # pesos do ranking
python3 graphrag/eval/rerank_eval.py         # mede o rerank por diversidade
python3 graphrag/eval/latency.py             # latência em processo (--url para o SSE)
python3 -m graphrag.ingest novos.json        # ingestão incremental (--dry-run para só ver)
python3 -m unittest discover -s graphrag/tests -t .   # inclui as invariantes (eval/invariants.py)
python3 -m graphrag.service.server --port 8787
```

## Regras de separação

- Só **lê** `../catalog/data/` (lista permitida); nunca escreve lá; não importa nada de `../app/`.
- Nunca lê `persona.json`.
- Desde o doc 16, medicamento é busca e kit como qualquer produto; nenhuma resposta manda procurar médico ou farmacêutico (invariante M2).

`python3 ../tools/check_separation.py` confere as regras de importação e escrita.

## Limites

Conjunto de ranking pequeno (14 frases); entidades por regras; vetores treinados só no catálogo; premissas de reposição fictícias. Ver doc 14, seção 7.
