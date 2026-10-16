import { TitleBar } from "../components/Bars";
import { Icon } from "../components/Icon";
import { ProductCard, discountPct } from "../components/ProductCard";
import { ProductImage } from "../components/ProductImage";
import { STEP_LABEL, TIER_LABEL } from "../contracts/types";
import { BRAND } from "../brand";
import { useNav, useServices } from "../nav";
import { SIMULATED_LOCATION } from "../location";
import { money } from "../services/format";
import { lineListCents, lineTotalCents, useApp, type CartLine, type SubscriptionDays } from "../state/app";
import { useAsync } from "../useAsync";

export function FreeShippingRuler({ itemsCents, freeFrom }: { itemsCents: number; freeFrom: number }) {
  const missing = Math.max(0, freeFrom - itemsCents);
  const pct = Math.min(100, Math.round((itemsCents / freeFrom) * 100));
  return (
    <div className="ruler">
      <div className="row" style={{ justifyContent: "space-between", fontSize: 15, color: "var(--text-2)" }}>
        <span>{missing > 0 ? <>Faltam <b>{money(missing)}</b> para frete grátis.</> : <b style={{ color: "var(--ok)" }}>Você ganhou frete grátis na entrega!</b>}</span>
        <span title={`Frete grátis a partir de ${money(freeFrom)} (premissa do protótipo)`}><Icon name="info" size={20} /></span>
      </div>
      <div className="track" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100} aria-label="Progresso para frete grátis">
        <div className="fill" style={{ width: `${Math.max(pct, 4)}%` }} />
      </div>
    </div>
  );
}

export function Cart() {
  const { lines, count, itemsCents, listCents, cashbackCents, dispatch } = useApp();
  const { push, resetTo } = useNav();
  const { commerce } = useServices();
  const info = useAsync(async () => {
    const [d, h] = await Promise.all([commerce.delivery(), commerce.home()]);
    const top = h.showcases.find((s) => s.id === "mais-vendidos");
    return { freeFrom: d.freeShippingFromCents, top: await commerce.products(top?.productIds ?? [], "relevancia") };
  }, [commerce]);

  const share = (
    <button className="icon-btn" aria-label="Compartilhar cesta" onClick={() => dispatch({ type: "toast", text: "Compartilhar é simulado no protótipo." })}>
      <Icon name="share" />
    </button>
  );

  if (lines.length === 0) {
    return (
      <div className="screen">
        <TitleBar title="Minha cesta" />
        <div className="scroll">
          <div className="empty">
            <span className="art"><Icon name="basket" size={120} strokeWidth={1} /></span>
            <h2>Ops! Sua cesta está vazia</h2>
            <p>Aproveite nossas ofertas!</p>
          </div>
          <div className="pad">
            <button className="btn primary block" onClick={() => resetTo("home")}>Continuar comprando</button>
            {info.data?.top.length ? (
              <section aria-label="Top de vendas">
                <div className="sec-head"><h2>Top de vendas!</h2></div>
                <div className="hscroll" style={{ marginTop: 12 }}>
                  {info.data.top.map((p) => <ProductCard key={p.id} product={p} />)}
                </div>
              </section>
            ) : null}
          </div>
        </div>
      </div>
    );
  }

  const discounts = listCents - itemsCents;
  return (
    <div className="screen">
      <TitleBar title="Minha cesta" right={share} />
      <div className="scroll">
        <div className="pack">
          <div className="pack-head">
            <div>
              <b>Pacote 1</b>
              <div><small>Vendido e entregue por <span style={{ color: "var(--brand)" }}>{BRAND.seller}</span></small></div>
            </div>
            <small style={{ alignSelf: "flex-end" }}>{count} {count === 1 ? "item" : "itens"}</small>
          </div>
          {lines.map((l) => <Line key={l.key} line={l} />)}
          <div style={{ padding: "14px 16px", display: "flex", flexDirection: "column", gap: 6 }}>
            <b style={{ fontWeight: 500, color: "var(--text-2)" }}>Resumo pacote 1</b>
            <div className="sumrow"><span>Subtotal</span><span>{money(listCents)}</span></div>
            {discounts > 0 ? <div className="sumrow"><span>Descontos</span><span>- {money(discounts)}</span></div> : null}
            <div className="sumrow total"><span>Total ({count} itens):</span><span>{money(itemsCents)}</span></div>
            {cashbackCents > 0 ? <div className="sumrow" style={{ color: "var(--ok)" }}><span>Cashback a receber (simulado)</span><span>{money(cashbackCents)}</span></div> : null}
            <div style={{ marginTop: 10 }}>
              {info.data ? <FreeShippingRuler itemsCents={itemsCents} freeFrom={info.data.freeFrom} /> : null}
            </div>
            <span style={{ fontSize: 14, color: "var(--text-2)", marginTop: 6 }}>Aplicado para: {SIMULATED_LOCATION.label}</span>
          </div>
        </div>
      </div>
      <div className="summary">
        <div className="row" style={{ justifyContent: "space-between", color: "var(--text-2)", fontSize: 17 }}>
          <span>Resumo da compra</span>
        </div>
        <div className="tot"><span>Total ({count} itens)</span><b>{money(itemsCents)}</b></div>
        <button className="btn primary block" onClick={() => push({ name: "delivery" })}>Seguir para entrega</button>
        <button className="link" style={{ alignSelf: "center", minHeight: 40 }} onClick={() => resetTo("home")}>Continuar comprando</button>
      </div>
    </div>
  );
}

function Line({ line: l }: { line: CartLine }) {
  const { dispatch } = useApp();
  const { push } = useNav();
  const unitList = lineListCents(l);
  const off = l.type === "kit" ? (unitList > l.kit.totalCents ? Math.round((1 - l.kit.totalCents / unitList) * 100) : 0) : discountPct(l.product);

  return (
    <div className="cline">
      <div className="row" style={{ alignItems: "flex-start" }}>
        <span style={{ width: 64, flex: "none" }}>
          {l.type === "kit" ? (
            <span style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 2 }}>
              {l.kit.items.slice(0, 4).map((i) => <ProductImage key={i.product.id} product={i.product} size={31} />)}
            </span>
          ) : (
            <ProductImage product={l.product} size={64} />
          )}
        </span>
        <div className="grow" style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          {l.type === "kit" ? (
            <span className="mini blue" style={{ alignSelf: "flex-start" }}><Icon name="sparkle" size={13} /> Kit inteligente · {TIER_LABEL[l.kit.tier]}</span>
          ) : off > 0 ? (
            <span className="mini red" style={{ alignSelf: "flex-start" }}>Super oferta</span>
          ) : null}
          <button style={{ textAlign: "left", fontSize: 16.5, lineHeight: 1.3 }}
            onClick={() => (l.type === "kit" ? push({ name: "kit", kit: l.kit, intent: l.intent }) : push({ name: "product", id: l.product.id }))}>
            {l.type === "kit" ? `${l.kit.title} (${l.kit.items.length} itens)` : l.product.name}
          </button>
          {l.type === "kit" ? (
            <small style={{ color: "var(--text-2)", lineHeight: 1.4 }}>
              {l.kit.items.map((i) => `${STEP_LABEL[i.step]}: ${i.product.name}`).join(" · ")}
            </small>
          ) : null}
        </div>
        <button className="icon-btn" style={{ color: "var(--brand)" }} onClick={() => dispatch({ type: "remove", key: l.key })} aria-label="Remover da cesta">
          <Icon name="trash" />
        </button>
      </div>
      <div className="row" style={{ justifyContent: "space-between" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
          <div className="row" style={{ gap: 8 }}>
            {off > 0 ? <span className="discount">↓{off}%</span> : null}
            {off > 0 ? <span className="old">{money(unitList * l.qty)}</span> : null}
          </div>
          <span style={{ fontSize: 22, fontWeight: 500 }}>{money(lineTotalCents(l))}</span>
          {l.qty > 1 ? <span className="unit">{money(lineTotalCents(l) / l.qty)}/1und</span> : null}
        </div>
        <div className="qty" role="group" aria-label="Quantidade">
          <button onClick={() => dispatch({ type: "setQty", key: l.key, qty: l.qty - 1 })} aria-label="Diminuir"><Icon name="minus" /></button>
          <span aria-live="polite">{l.qty}</span>
          <button onClick={() => dispatch({ type: "setQty", key: l.key, qty: l.qty + 1 })} aria-label="Aumentar" disabled={l.qty >= 9}><Icon name="plus" /></button>
        </div>
      </div>
      {l.type === "kit" ? (
        <label className="row" style={{ gap: 8, fontSize: 14, color: "var(--text-2)" }}>
          <Icon name="repeat" size={18} />
          <span className="grow">Assinatura</span>
          <select value={l.everyDays} onChange={(e) => dispatch({ type: "setEvery", key: l.key, everyDays: Number(e.target.value) as SubscriptionDays })}
            style={{ minHeight: 40, borderRadius: 8, border: "1px solid var(--line)", padding: "0 8px", background: "#fff" }}>
            <option value={0}>Comprar uma vez</option>
            <option value={30}>A cada 30 dias</option>
            <option value={60}>A cada 60 dias</option>
          </select>
        </label>
      ) : null}
      {off > 0 ? (
        <div className="promo-on"><Icon name="checkCircle" size={20} /> Promoção ativada!</div>
      ) : null}
    </div>
  );
}
