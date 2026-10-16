# catalog/images — banco de imagens reais (sem marca)

Fotos reais de embalagens de cosméticos **sem marca legível**, de bancos gratuitos, escolhidas por formato de embalagem (`form` do produto). O catálogo continua fictício: nenhuma foto mostra produto de marca real.

## Fluxo

1. **Baixar candidatas** (no seu computador; o ambiente de nuvem não alcança o Pexels):
   ```powershell
   $env:PEXELS_API_KEY = "sua-chave"     # gratuita em https://www.pexels.com/api/
   node catalog/images/fetch_pexels.mjs  # ou só alguns grupos: node catalog/images/fetch_pexels.mjs tube jar
   ```
   Grava `raw/<grupo>/pexels-<id>.jpg` e `candidates.json` (fonte, fotógrafo, licença, data). Pode rodar de novo; o que já existe é pulado.
2. **Revisar**: cada candidata é olhada; sai a que tem marca, texto legível, pessoa identificável ou não parece a embalagem do grupo. O resultado fica no campo `review` (`aprovada` ou `recusada: motivo`).
3. **Atribuir**: um script determinístico liga cada produto a uma foto aprovada do seu formato e grava `catalog/data/images.json`.
4. **Exportar** para o app por `tools/export_app_mock.py` (mão única, como o resto do catálogo).

## Licença

[Pexels License](https://www.pexels.com/license/): uso livre, inclusive comercial; atribuição não obrigatória. As diretrizes da API pedem link visível para o Pexels e crédito ao fotógrafo quando possível. O app mostra isso numa tela de créditos. Não é permitido sugerir que pessoas ou marcas nas fotos endossam o produto, por isso fotos com marca são recusadas na revisão.

## Status

Script testado contra um servidor que imita a API (chave ausente, chave errada, busca com erro, imagem quebrada, segunda execução). **Ainda não rodou contra o Pexels de verdade.**
