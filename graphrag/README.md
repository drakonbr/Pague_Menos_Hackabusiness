# graphrag/ — sistema GraphRAG

> **Status: NÃO INICIADO.** Esta pasta contém só este README de propósito. Nenhum grafo, índice, embedding ou código de treino existe ainda. A construção começa quando for liberada ("pode continuar, sem treinamento do RAG ainda" foi a instrução para a fase atual).

## O que vai morar aqui

O motor que recebe uma frase e devolve kits, seguindo o contrato em `../contracts/README.md`:

1. Segurança (regras antes de qualquer modelo)
2. Extração de intenção
3. Recuperação em grafo + busca vetorial
4. Junção com preço e estoque vivos
5. Compositor de kits (regras K1 a K12)
6. Justificativas fundamentadas
7. Validação das invariantes

Desenho completo: `../docs/06-graphrag-design.md`. Segurança: `../docs/07-seguranca-saude.md`. Como será avaliado: `../docs/08-validacao-e-qualidade.md`.

## Regras de separação

- Só **lê** `../catalog/data/` (ingestão) e um inventário; nunca escreve lá.
- Não importa nada de `../app/`.
- Expõe o contrato `search`, `swapOptions`, `swap`.

## Estrutura prevista

```
ingest/  retrieval/  composer/  safety/  llm/  service/  eval/
```

## Verificação desta fase

`python3 ../tools/check_separation.py` falha se aparecer aqui qualquer coisa além deste README durante a fase "pré-RAG".
