import { BlueSearchBar } from "../components/Bars";
import { KitCard } from "../components/KitCard";
import { ProductCard } from "../components/ProductCard";
import { useNav, useServices } from "../nav";
import { useApp } from "../state/app";
import { useAsync } from "../useAsync";

export function Favorites() {
  const { favorites, favoriteKits } = useApp();
  const { commerce } = useServices();
  const { goTab, push } = useNav();
  const data = useAsync(() => commerce.products(favorites), [commerce, favorites.join()]);
  const empty = !favorites.length && !favoriteKits.length;
  return (
    <div className="screen">
      <BlueSearchBar />
      <div className="scroll">
        {empty ? (
          <div className="empty" style={{ paddingTop: 56 }}>
            <svg width="150" height="130" viewBox="0 0 150 130" aria-hidden="true">
              <ellipse cx="75" cy="122" rx="48" ry="6" fill="#e6e7ea" />
              <path d="M75 108S20 76 20 42a27 27 0 0 1 55-12 27 27 0 0 1 55 12c0 34-55 66-55 66z" fill="#f05454" />
              <circle cx="58" cy="50" r="5" fill="#222" /><circle cx="92" cy="50" r="5" fill="#222" />
              <path d="M62 66q13 11 26 0" stroke="#222" strokeWidth="4" fill="none" strokeLinecap="round" />
            </svg>
            <h2>Ah não!<br />Lista de favoritos vazia</h2>
            <p style={{ maxWidth: 280, lineHeight: 1.45 }}>Encontre o produto que deseja, clique no coração e guarde para comprar depois</p>
            <button className="btn primary" style={{ marginTop: 16, minWidth: 240 }} onClick={() => goTab("ofertas")}>Ir para ofertas</button>
          </div>
        ) : (
          <div className="pad">
            {favoriteKits.length ? (
              <section aria-label="Kits favoritos">
                <h2 style={{ fontSize: 19, marginBottom: 10 }}>Kits salvos</h2>
                <div className="kit-strip">
                  {favoriteKits.map((k) => (
                    <KitCard key={k.id + k.items.map((i) => i.product.id).join()} kit={k}
                      onOpen={() => push({ name: "kit", kit: k, intent: { goals: [k.goal], primaryGoal: k.goal, budgetCents: null, skinType: null, preferences: [], storeId: k.storeId, missing: [] } })} />
                  ))}
                </div>
              </section>
            ) : null}
            {data.data?.length ? (
              <section aria-label="Produtos favoritos">
                <h2 style={{ fontSize: 19, marginBottom: 10 }}>Produtos</h2>
                <div className="grid2">{data.data.map((p) => <ProductCard key={p.id} product={p} />)}</div>
              </section>
            ) : null}
          </div>
        )}
      </div>
    </div>
  );
}
