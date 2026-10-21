# app/ — Kits inteligentes (protótipo de interface)

React 19 + TypeScript + Vite. Mobile-first, aparece dentro de uma moldura de celular no desktop.
Todos os dados são fictícios. O app **não conhece** `catalog/` nem `graphrag/`: fala com um `SearchService`.

## Rodar

```bash
cd app
npm install
npm run dev        # http://localhost:5173
npm test           # 46 testes: simulador de kits, lojas, comércio, persona e checador de invariantes
npm run build      # tsc --noEmit + vite build
```

Se `src/mocks/` estiver vazio ou desatualizado: `python3 tools/export_app_mock.py` (na raiz do projeto).

## Dois serviços

- `SearchService` (kits): GraphRAG local por HTTP, com o simulado de `src/services/mock/` como reserva.
- `CommerceService` (catálogo, lojas, estoque por loja, frete, vitrines): só simulado nesta fase.

As telas não importam nada de `src/services/mock/`.

## Motor de kits: simulado ou real

| Variável | Valor | Efeito |
| --- | --- | --- |
| `VITE_SEARCH_BACKEND` | `auto` (padrão) | tenta o GraphRAG (`/v1/health`); se não responder, ou cair no meio da sessão, usa o simulado |
| `VITE_SEARCH_BACKEND` | `mock` | só o simulador em `src/services/mock/` (atraso artificial) |
| `VITE_SEARCH_BACKEND` | `http` | só o cliente HTTP do GraphRAG, conforme `contracts/README.md` |
| `VITE_SEARCH_URL` | endereço do motor | padrão: servidor local na porta 8787 |

Para usar o motor real, suba `python3 -m graphrag.service.server --port 8787` na raiz antes do `npm run dev`. O selo "Motor" na conversa mostra qual dos dois está respondendo.

## Mapa

```
src/
  contracts/types.ts      tipos do contrato (cópia de contracts/README.md)
  services/
    searchService.ts      auto (GraphRAG com reserva no simulado), mock ou http
    mock/                 intenção, segurança, compositor de kits (simulador)
    contractChecks.ts     invariantes I1–I16, escritas de forma independente do compositor
    format.ts             moeda pt-BR
  nav.tsx                 abas (Home, Categorias, Ofertas, Favoritos, Mais) com pilha por aba; serviços
  state/app.tsx           cesta (kits com assinatura e produtos), favoritos, buscas recentes, loja, pedidos, cashback
  brand.ts                nome da rede (fora das telas por padrão)
  persona.ts, location.ts persona Renata (dados no aparelho) e localização simulada no Recife
  screens/                Home, SearchFocus, Results, Chat, Categories, ProductPage, KitDetail, Cart, Delivery, Payment, Offers, Favorites, More, Refill, Privacy
  components/             Avatar, Bars, TabBar, ProductCard, ProductImage, KitCard, IntentChips, BudgetPanel, BottomSheet, Toast, Icon, ProductThumb
  mocks/                  *.mock.json gerados por tools/export_app_mock.py (não editar à mão)
public/img/               fotos aprovadas, copiadas pela mesma ponte (não editar à mão)
tests/mockSearch.test.ts, tests/persona.test.ts
```

## O que o simulador é (e não é)

É determinístico e regrado: entende uma lista fixa de objetivos e sinônimos, monta kits por busca exaustiva sobre os melhores candidatos e passa todas as invariantes. **Não é o GraphRAG** e a relevância é genérica; por exemplo, em rotinas básicas a marca Pura Base tende a dominar o kit Econômico. Hoje é a reserva quando o GraphRAG não responde: não tem conversa de vários turnos nem o ranking híbrido.

## Limites conhecidos

- Escopo cosmético: pedidos sobre medicamento, sintoma ou condição de saúde são bloqueados com encaminhamento.
- Checkout simulado: sem pagamento, sem envio, sem armazenamento.
- Sem medição de contraste AA nem teste com leitor de tela; visto apenas em Chromium.
- Sem persistência: recarregar a página esvazia o carrinho.
- Persona fixa: o app abre logado como Renata, com dados fictícios em `src/mocks/persona.mock.json` que nunca vão para o motor.
- Ao ajustar orçamento ou tipo de pele, o campo de busca continua mostrando a frase original.
- Sem fotos reais até o banco de imagens ser baixado e revisado: aparece o desenho provisório com "foto pendente".
- Telas sem print do app real (produto, pagamento, pedidos, Mais) são aproximação (doc 13).

Confidencial: repositório privado; não publicar nem identificar a empresa do desafio.
