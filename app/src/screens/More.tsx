import { PersonaAvatar } from "../components/Avatar";
import { TitleBar } from "../components/Bars";
import { Icon, type IconName } from "../components/Icon";
import { ProductImage } from "../components/ProductImage";
import type { ProductImage as Img } from "../contracts/types";
import { BRAND } from "../brand";
import { SIMULATED_LOCATION } from "../location";
import { PERSONA } from "../persona";
import { useNav, useServices, type View } from "../nav";
import { money } from "../services/format";
import { useApp } from "../state/app";
import { useAsync } from "../useAsync";

const ROWS: Array<{ label: string; icon: IconName; to?: View; off?: string }> = [
  { label: "Meus pedidos", icon: "box", to: { name: "orders" } },
  { label: "Assinaturas", icon: "repeat", to: { name: "subscriptions" } },
  { label: "Carteira e cashback", icon: "wallet", to: { name: "wallet" } },
  { label: "Lojas e retirada", icon: "store", to: { name: "stores" } },
  { label: "Meus medicamentos", icon: "pill", to: { name: "refill" } },
  { label: "Privacidade e dados", icon: "lock", to: { name: "privacy" } },
  { label: "Convênios e PBM", icon: "shield", off: "fora do protótipo" },
  { label: "Créditos das fotos", icon: "image", to: { name: "credits" } },
];

export function More() {
  const { push } = useNav();
  return (
    <div className="screen">
      <TitleBar title="Mais" back={false} />
      <div className="scroll">
        <div className="pad">
          <div className="panel row">
            <PersonaAvatar size={56} />
            <span className="grow">
              <b style={{ fontWeight: 500 }}>{PERSONA.name}</b>
              <br />
              <small style={{ color: "var(--text-2)" }}>{PERSONA.address.neighborhood}, {PERSONA.address.city} - {PERSONA.address.uf} · persona fictícia</small>
            </span>
          </div>
          <div className="menulist">
            {ROWS.map((r) => (
              <button key={r.label} className="menurow" disabled={!r.to} onClick={() => r.to && push(r.to)}>
                <span className="ico"><Icon name={r.icon} size={26} /></span>
                <span>{r.label}</span>
                {r.to ? <Icon name="chevron" size={20} /> : <small>{r.off}</small>}
              </button>
            ))}
          </div>
          <p className="footnote">{BRAND.protoNote} Medicamentos aparecem só avulsos, nunca em kit; convênios ficam fora do escopo.</p>
        </div>
      </div>
    </div>
  );
}

export function Orders() {
  const { orders } = useApp();
  const { resetTo } = useNav();
  return (
    <div className="screen">
      <TitleBar title="Meus pedidos" />
      <div className="scroll">
        <div className="pad">
          {!orders.length ? (
            <div className="empty">
              <span className="art"><Icon name="box" size={90} strokeWidth={1} /></span>
              <h2>Nenhum pedido ainda</h2>
              <button className="btn primary" onClick={() => resetTo("home")}>Começar a comprar</button>
            </div>
          ) : (
            orders.map((o) => (
              <article key={o.id} className="panel" style={{ gap: 6 }}>
                <div className="row" style={{ justifyContent: "space-between" }}>
                  <b style={{ fontWeight: 500 }}>Pedido {o.id}</b>
                  <span className="mini green">{o.status}</span>
                </div>
                <small style={{ color: "var(--text-2)" }}>
                  {new Date(o.createdAt).toLocaleString("pt-BR")} · {o.mode === "retirada" ? `Retirar na ${o.storeName}` : o.mode === "expressa" ? `Entrega Expressa (${o.storeName})` : "Entrega Agendada"} · {o.payment}
                </small>
                <ul style={{ margin: 0, paddingLeft: 18, fontSize: 14, color: "var(--text-2)" }}>
                  {o.lines.map((l) => (
                    <li key={l.key}>
                      {l.qty}× {l.type === "kit" ? `Kit ${l.kit.title} (${l.kit.items.length} ${l.kit.items.length === 1 ? "item" : "itens"})${l.everyDays ? `, assinatura a cada ${l.everyDays} dias` : ""}` : l.product.name}
                    </li>
                  ))}
                </ul>
                <div className="sumrow total"><span>Total</span><span>{money(o.totalCents)}</span></div>
              </article>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

export function Subscriptions() {
  const { orders } = useApp();
  const subs = orders.flatMap((o) => o.lines.filter((l) => l.type === "kit" && l.everyDays).map((l) => ({ o, l })));
  return (
    <div className="screen">
      <TitleBar title="Assinaturas" />
      <div className="scroll">
        <div className="pad">
          <div className="note"><Icon name="repeat" size={18} /><p>Assine um kit de rotina e receba de novo a cada 30 ou 60 dias. Sem custo de assinatura (simulado).</p></div>
          {!subs.length ? <p style={{ color: "var(--text-2)" }}>Nenhuma assinatura. Escolha "Assinar" na tela de um kit.</p> : null}
          {subs.map(({ o, l }) =>
            l.type === "kit" ? (
              <article key={o.id + l.key} className="panel" style={{ gap: 6 }}>
                <b style={{ fontWeight: 500 }}>Kit {l.kit.title}</b>
                <small style={{ color: "var(--text-2)" }}>A cada {l.everyDays} dias · próximo envio em {new Date(Date.parse(o.createdAt) + l.everyDays * 86400000).toLocaleDateString("pt-BR")}</small>
                <div className="kit-thumbs">{l.kit.items.map((i) => <ProductImage key={i.product.id} product={i.product} size={44} />)}</div>
                <div className="sumrow total"><span>{money(l.kit.totalCents)} por envio</span></div>
              </article>
            ) : null,
          )}
        </div>
      </div>
    </div>
  );
}

export function Wallet() {
  const { walletPendingCents, cashbackCents } = useApp();
  return (
    <div className="screen">
      <TitleBar title="Carteira e cashback" />
      <div className="scroll">
        <div className="pad">
          <div className="panel" style={{ gap: 4 }}>
            <span className="section-title">Cashback a receber</span>
            <span className="price blue" style={{ fontSize: 28 }}>{money(walletPendingCents)}</span>
            <small style={{ color: "var(--text-2)" }}>Dos pedidos simulados desta sessão</small>
          </div>
          {cashbackCents > 0 ? <div className="note ok"><Icon name="wallet" size={18} /><p>A cesta atual rende {money(cashbackCents)} de cashback.</p></div> : null}
          <div className="note"><Icon name="info" size={18} /><p>Percentuais de cashback são premissas do protótipo. As regras reais do programa podem ser diferentes.</p></div>
        </div>
      </div>
    </div>
  );
}

export function Stores() {
  const { commerce } = useServices();
  const { store, dispatch } = useApp();
  const { pop } = useNav();
  const data = useAsync(() => commerce.storesFor([]), [commerce]);
  return (
    <div className="screen">
      <TitleBar title="Lojas e retirada" />
      <div className="scroll">
        <div className="pad">
          <p style={{ color: "var(--text-2)", lineHeight: 1.45 }}>
            Escolha a loja onde quer retirar. Os kits passam a usar só o que ela tem em estoque. Lojas fictícias perto de {SIMULATED_LOCATION.label}.
          </p>
          <button className="store" aria-pressed={!store} onClick={() => { dispatch({ type: "setStore", store: null }); pop(); }}>
            <span className="t"><Icon name="truck" /> <span className="grow">Receber em casa</span></span>
            <span className="addr">Kits com o estoque do centro de distribuição</span>
          </button>
          {(data.data ?? []).map((s) => (
            <button key={s.store.id} className="store" aria-pressed={store?.id === s.store.id}
              onClick={() => { dispatch({ type: "setStore", store: s.store }); dispatch({ type: "setMode", mode: "retirada" }); pop(); }}>
              <span className="t">
                <span style={{ color: "var(--logo)" }}><Icon name="cross" /></span>
                <span className="grow">{s.store.name}{s.store.open24h ? " 24 Horas." : ""}</span>
              </span>
              <span><span className="open">Aberta</span> · <span style={{ color: "var(--text-2)" }}>{s.store.hours}</span></span>
              <span className="addr">{s.store.address} (endereço fictício)</span>
              <span className="chips"><span className="mini">{s.distanceKm.toLocaleString("pt-BR")} km</span><span className="mini">Retirar em até 60 minutos</span></span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

export function Credits() {
  const { commerce } = useServices();
  const data = useAsync(async () => {
    const [cats, home] = await Promise.all([commerce.categories(), commerce.home()]);
    const all = await commerce.products(cats.find((c) => c.id === "dermo")?.productIds ?? []);
    const imgs: Img[] = [...all.flatMap((p) => p.images), ...home.banners];
    const seen = new Map<string, Img>();
    for (const i of imgs) seen.set(i.credit.pageUrl, i);
    return [...seen.values()];
  }, [commerce]);
  return (
    <div className="screen">
      <TitleBar title="Créditos das fotos" />
      <div className="scroll">
        <div className="pad">
          <p style={{ lineHeight: 1.5 }}>
            Fotos fornecidas pelo <a className="link" href="https://www.pexels.com" target="_blank" rel="noreferrer">Pexels</a>, sob a{" "}
            <a className="link" href="https://www.pexels.com/license/" target="_blank" rel="noreferrer">licença Pexels</a>. Embalagens sem marca; os produtos do app são fictícios.
          </p>
          {data.data && !data.data.length ? <div className="note warn"><Icon name="info" size={18} /><p>O banco de imagens ainda não foi revisado. Por enquanto, os produtos aparecem com desenho provisório.</p></div> : null}
          <ul style={{ margin: 0, paddingLeft: 18, lineHeight: 1.8, fontSize: 14 }}>
            {(data.data ?? []).map((i) => (
              <li key={i.credit.pageUrl}>
                Foto de <a className="link" href={i.credit.photographerUrl} target="_blank" rel="noreferrer">{i.credit.photographer}</a> no{" "}
                <a className="link" href={i.credit.pageUrl} target="_blank" rel="noreferrer">Pexels</a>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
