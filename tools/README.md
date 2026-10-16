# tools/ — pontes e verificações entre módulos

Scripts que atravessam fronteiras de propósito. Ficam fora dos módulos para que `catalog/`, `app/` e `graphrag/` não se enxerguem.

| Script | O que faz | Direção |
| --- | --- | --- |
| `export_app_mock.py` | lê `catalog/data/*.json` e escreve `app/src/mocks/*.mock.json` (camelCase, preço e estoque juntos, lojas com estoque, comércio, categorias) e copia as fotos aprovadas para `app/public/img/` | catálogo → app, **só nesse sentido** |
| `check_separation.py` | falha se `catalog/` referenciar `app/` ou `graphrag/`, se `app/src` referenciar `catalog/` ou `graphrag/`, ou se `graphrag/` tiver algo além do README na fase pré-RAG | verificação |

```bash
python3 tools/export_app_mock.py
python3 tools/check_separation.py     # código 0 = separação respeitada
```

Quando o GraphRAG for construído, `check_separation.py` deve ser atualizado para a fase seguinte (a regra R4 deixa de exigir `graphrag/` vazio). Isso será uma decisão registrada em `docs/09-decisoes-tecnicas.md`.
