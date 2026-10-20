# tools/ — pontes e verificações entre módulos

Scripts que atravessam fronteiras de propósito. Ficam fora dos módulos para que `catalog/`, `app/` e `graphrag/` não se enxerguem.

| Script | O que faz | Direção |
| --- | --- | --- |
| `export_app_mock.py` | lê `catalog/data/*.json` e escreve `app/src/mocks/*.mock.json` (camelCase, preço e estoque juntos, lojas com estoque, comércio, categorias) e copia as fotos aprovadas para `app/public/img/` | catálogo → app, **só nesse sentido** |
| `check_separation.py` | falha se `catalog/` referenciar `app/` ou `graphrag/`, se `app/src` referenciar `catalog/` ou `graphrag/`, ou se `graphrag/` importar `app/`/`catalog/` ou escrever em `catalog/` (`--phase pre-rag` volta a exigir `graphrag/` vazio) | verificação |

```bash
python3 tools/export_app_mock.py
python3 tools/check_separation.py     # código 0 = separação respeitada
```

O GraphRAG já existe; a regra R4 (pasta vazia) só vale com `--phase pre-rag`. Decisão registrada em `docs/09-decisoes-tecnicas.md` (D-23).
