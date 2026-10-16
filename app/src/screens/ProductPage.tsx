import { BasketButton } from "../components/Bars";
import { Icon } from "../components/Icon";
import { discountPct } from "../components/ProductCard";
import { ProductImage } from "../components/ProductImage";
import { STEP_LABEL } from "../contracts/types";
import { useNav, useServices } from "../nav";
import { money } from "../services/format";
import { useApp } from "../state/app";
import { useAsync } from "../useAsync";

const joinPt = (xs: string[]) => (xs.length <= 1 ? xs.join("") : `${xs.slice(0, -1).join(", ")} e ${xs[xs.length - 1]}`);

export function ProductPage({ id }: { id: string }) {
  const { commerce } = useServices();
  const { pop, push } = useNav();
  const { dispatch, isFav, storeId, store } = useApp();
  const data = useAsync(async () => {
    const [p, labels] = await Promise.all([commerce.product(id), commerce.labels()]);
    const stores = p ? await commerce.storesFor([p.id]) : [];
    return { p, labels, stores };
  }, [commerce, id]);

  const d = data.data;
  const p = d?.p;
  return (
    <div className="screen">
      <header className="bar">
        <button className="icon-btn" onClick={pop} aria-label="Voltar"><Icon name="back" /></button>
        <h1 style={{ fontSize: 16 }}>Detalhes do produto</h1>
        <button className="icon-btn" onClick={() => push({ name: "searchFocus" })} aria-label="Buscar"><Icon name="search" /></button>
        <BasketButton />
      </header>
      <div className="scroll">
        {data.loading && !d ? <div className="pad"><div className="skeleton" style={{ height: 360 }} /></div> : null}
        {d && !p ? <div className="pad"><p>Produto não encontrado.</p></div> : null}
        {p && d ? (
          <>
            <div className="pdp-img">
              <ProductImage product={p} />
              <button className="icon-btn fav" aria-pressed={isFav(p.id)} aria-label={isFav(p.id) ? "Tirar dos favoritos" : "Favoritar"}
                style={{ color: isFav(p.id) ? "var(--price)" : "var(--text-2)" }} onClick={() => dispatch({ type: "toggleFav", id: p.id })}>
                <Icon name={isFav(p.id) ? "heartFill" : "heart"} size={28} />
              </button>
            </div>
            <div className="pdp-info">
              <span className="brandname">{p.brand}</span>
              <h1>{p.name}</h1>
              <span className="code">cód.: {p.id.toUpperCase()} · {p.size.value} {p.size.unit}{p.fps ? ` · FPS ${p.fps}` : ""}</span>
              <div className="chips" style={{ gap: 6 }}>
                {p.claims.map((c) => <span key={c} className="mini">{c}</span>)}
              </div>
              {p.stockQty > 0 ? (
                <>
                  <div className="row" style={{ gap: 8, alignItems: "baseline" }}>
                    {discountPct(p) > 0 ? <span className="discount">↓{discountPct(p)}%</span> : null}
                    {discountPct(p) > 0 ? <span className="old">{money(p.listPriceCents)}</span> : null}
                  </div>
                  <span className="price" style={{ fontSize: 26 }}>{money(p.priceCents)}</span>
                  {p.cashbackPct > 0 ? (
                    <span className="cashback"><Icon name="wallet" size={16} /> {p.cashbackPct}% de cashback: {money(Math.floor((p.priceCents * p.cashbackPct) / 100))} de volta</span>
                  ) : null}
                  <Availability stores={d.stores} storeId={storeId} storeName={store?.name ?? null} onStores={() => push({ name: "stores" })} />
                  <button className="btn primary block" onClick={() => dispatch({ type: "addProduct", product: p })}>
                    <Icon name="basketPlus" /> Adicionar à cesta
                  </button>
                </>
              ) : (
                <>
                  <span className="unavail" style={{ fontSize: 16 }}>Indisponível</span>
                  <button className="btn outline blue block" onClick={() => dispatch({ type: "toast", text: "Aviso simulado: nenhum dado foi coletado." })}>
                    <Icon name="bell" /> Avise-me quando chegar
                  </button>
                </>
              )}
              <button className="note" style={{ textAlign: "left", width: "100%" }}
                onClick={() => push({ name: "results", req: { query: `cuidados para ${d.labels.concerns[p.concerns[0]] ?? "a pele"}`, storeId } })}>
                <Icon name="sparkle" size={20} />
                <span>Monte um kit para <b>{d.labels.concerns[p.concerns[0]] ?? "a sua pele"}</b>: rotina completa, sem repetir produto.</span>
              </button>
            </div>
            <details className="acc" open>
              <summary>APRESENTAÇÃO <Icon name="chevronDown" size={20} /></summary>
              <p className="txt">{p.description}</p>
            </details>
            <details className="acc">
              <summary>BENEFÍCIOS <Icon name="chevronDown" size={20} /></summary>
              <p className="txt">
                Atua em {joinPt(p.concerns.map((c) => d.labels.concerns[c] ?? c))}. Ativos: {joinPt(p.ingredients.map((i) => d.labels.ingredients[i] ?? i))}.
                {p.claims.length ? ` ${joinPt(p.claims)}.` : ""}
              </p>
            </details>
            <details className="acc">
              <summary>PARA QUE SERVE <Icon name="chevronDown" size={20} /></summary>
              <p className="txt">
                Etapa da rotina: {STEP_LABEL[p.step]}. Indicado para {p.skinTypes.includes("todas") ? "todos os tipos de pele" : `pele ${joinPt(p.skinTypes)}`}.
                Uso: {p.usagePeriod === "dia" ? "de dia" : p.usagePeriod === "noite" ? "à noite" : "de dia e à noite"}.
              </p>
            </details>
            <details className="acc">
              <summary>COMO DEVO USAR <Icon name="chevronDown" size={20} /></summary>
              <p className="txt">{p.howToUse}</p>
            </details>
            <details className="acc">
              <summary>ADVERTÊNCIAS <Icon name="chevronDown" size={20} /></summary>
              <div className="txt">
                {p.warnings.length ? (
                  <ul style={{ margin: 0, paddingLeft: 18 }}>
                    {p.warnings.map((w) => <li key={w}>{d.labels.warnings[w] ?? w}</li>)}
                  </ul>
                ) : (
                  <p>Uso externo. Em caso de irritação, suspenda o uso.</p>
                )}
              </div>
            </details>
            <p className="footnote" style={{ padding: 16 }}>Produto fictício. Informação cosmética, não substitui orientação profissional.</p>
          </>
        ) : null}
      </div>
    </div>
  );
}

function Availability({ stores, storeId, storeName, onStores }: {
  stores: Array<{ store: { id: string; name: string }; distanceKm: number; availableIds: string[] }>;
  storeId: string | null;
  storeName: string | null;
  onStores: () => void;
}) {
  const withStock = stores.filter((s) => s.availableIds.length > 0);
  const mine = storeId ? stores.find((s) => s.store.id === storeId) : null;
  const nearest = withStock[0];
  return (
    <div className="panel" style={{ gap: 6 }}>
      <div className="row" style={{ gap: 8 }}>
        <Icon name="store" size={20} />
        <span className="grow" style={{ fontSize: 14 }}>
          {mine
            ? mine.availableIds.length
              ? <>Disponível na <b>{storeName}</b> · Retirar em até 60 minutos</>
              : <>Sem estoque na <b>{storeName}</b></>
            : nearest
              ? <>Disponível em {withStock.length} de {stores.length} lojas · mais próxima: <b>{nearest.store.name}</b> ({nearest.distanceKm.toLocaleString("pt-BR")} km)</>
              : <>Sem estoque nas lojas; só entrega</>}
        </span>
      </div>
      <button className="link plain" style={{ alignSelf: "flex-start", fontSize: 14, minHeight: 32 }} onClick={onStores}>Ver lojas</button>
      <div className="row" style={{ gap: 8, fontSize: 14 }}>
        <Icon name="truck" size={20} /> <span>Entrega Expressa em até 2 h ou Agendada</span>
      </div>
    </div>
  );
}
