# app/ — Kits inteligentes (protótipo de interface)

React 19 + TypeScript + Vite. Mobile-first, aparece dentro de uma moldura de celular no desktop.
Todos os dados são fictícios. O app **não conhece** `catalog/` nem `graphrag/`: fala com um `SearchService`.

## Rodar

```bash
cd app
npm install
npm run dev        # http://localhost:5173
npm test           # 26 testes: simulador de kits, lojas, comércio e checador de invariantes
npm run build      # tsc --noEmit + vite build
```

Se `src/mocks/` estiver vazio ou desatualizado: `python3 tools/export_app_mock.py` (na raiz do projeto).

## Dois serviços

- `SearchService` (kits): simulado em `src/services/mock/` ou HTTP para o GraphRAG.
- `CommerceService` (catálogo, lojas, estoque por loja, frete, vitrines): só simulado nesta fase.

As telas não importam nada de `src/services/mock/`.

## Motor de kits: simulado ou real

| Variável | Valor | Efeito |
| --- | --- | --- |
| `VITE_SEARCH_BACKEND` | `mock` (padrão) | usa o simulador em `src/services/mock/` (350 ms de atraso artificial) |
| `VITE_SEARCH_BACKEND` | `http` + `VITE_SEARCH_URL` | usa o cliente HTTP do GraphRAG, conforme `contracts/README.md` |

**O cliente HTTP nunca foi exercitado**: o servidor GraphRAG ainda não existe.

## Mapa

```
src/
  contracts/types.ts      tipos do contrato (cópia de contracts/README.md)
  services/
    searchService.ts      escolhe mock ou http
    mock/                 intenção, segurança, compositor de kits (simulador)
    contractChecks.ts     invariantes I1–I14, escritas de forma independente do compositor
    format.ts             moeda pt-BR
  nav.tsx                 abas (Home, Categorias, Ofertas, Favoritos, Mais) com pilha por aba; serviços
  state/app.tsx           cesta (kits com assinatura e produtos), favoritos, buscas recentes, loja, pedidos, cashback
  brand.ts                nome da rede (fora das telas por padrão)
  screens/                Home, SearchFocus, Results, Categories, ProductPage, KitDetail, Cart, Delivery, Payment, Offers, Favorites, More
  components/             Bars, TabBar, ProductCard, ProductImage, KitCard, IntentChips, BudgetPanel, BottomSheet, Toast, Icon, ProductThumb
  mocks/                  *.mock.json gerados por tools/export_app_mock.py (não editar à mão)
public/img/               fotos aprovadas, copiadas pela mesma ponte (não editar à mão)
tests/mockSearch.test.ts
```

## O que o simulador é (e não é)

É determinístico e regrado: entende uma lista fixa de objetivos e sinônimos, monta kits por busca exaustiva sobre os melhores candidatos e passa todas as invariantes. **Não é o GraphRAG** e a relevância é genérica; por exemplo, em rotinas básicas a marca Pura Base tende a dominar o kit Econômico. Serve para o app e o contrato poderem ser construídos e testados antes do motor real.

## Limites conhecidos

- Escopo cosmético: pedidos sobre medicamento, sintoma ou condição de saúde são bloqueados com encaminhamento.
- Checkout simulado: sem pagamento, sem envio, sem armazenamento.
- Sem medição de contraste AA nem teste com leitor de tela; visto apenas em Chromium.
- Sem persistência: recarregar a página esvazia o carrinho.
- Ao ajustar orçamento ou tipo de pele, o campo de busca continua mostrando a frase original.
- Sem fotos reais até o banco de imagens ser baixado e revisado: aparece o desenho provisório com "foto pendente".
- Telas sem print do app real (produto, pagamento, pedidos, Mais) são aproximação (doc 13).

Confidencial: repositório privado; não publicar nem identificar a empresa do desafio.
