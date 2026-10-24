// Meus medicamentos: REPOSIÇÃO do que a pessoa já usa (lista que fica no aparelho).
// Os dados (itens, quantidades, receita) ficam no aparelho; o motor só devolve equivalentes a partir de um id de produto.
import { useMemo, useRef, useState } from "react";
import { TitleBar } from "../components/Bars";
import { Icon } from "../components/Icon";
import { ProductImage } from "../components/ProductImage";
import type { Product, SimilarsResponse, StoreAvailability } from "../contracts/types";
import { useNav, useServices } from "../nav";
import { DELIVERY_RANK, PERSONA, REFILL_RULES, daysLeft, needsRefill, runOutDate, type ContinuousMedication } from "../persona";
import { hasStockHere } from "../refillStock";
import { delta, money } from "../services/format";
import { maxQty, useApp } from "../state/app";
import { useAsync } from "../useAsync";

const PRES: Record<string, string> = { referencia: "Referência", generico: "Genérico", similar: "Similar" };

export function Refill() {
  const { commerce } = useServices();
  const { push } = useNav();
  const { store, storeId, dispatch, refillAuto, rxAttached, consent, refillPick, lines } = useApp();
  const meds = PERSONA.continuousMedications;
  const ids = meds.map((m) => m.productId);
  const data = useAsync(async () => {
    const [prods, avail, delivery] = await Promise.all([commerce.products(ids), commerce.storesFor(ids), commerce.delivery()]);
    return { byId: new Map(prods.map((p) => [p.id, p])), avail, delivery };
  }, [commerce]);
  // equivalente escolhido por item (sem escolha, vale o próprio item); guardado na sessão, só para a loja em que foi escolhido
  const choice = refillPick.storeId === storeId ? refillPick.picks : {};
  const pick = (id: string, product: Product | null) => dispatch({ type: "refillPick", id, product, storeId });
  const [picked, setPicked] = useState<Record<string, boolean>>(() => Object.fromEntries(meds.map((m) => [m.productId, needsRefill(m)])));

  const chosen = (m: ContinuousMedication): Product | undefined => choice[m.productId] ?? data.data?.byId.get(m.productId);
  // #50: item que a loja escolhida não tem só entra na conta (e na retirada) depois que a pessoa escolhe um equivalente em estoque
  const hasHere = (m: ContinuousMedication) => hasStockHere({ productId: m.productId, chosenId: choice[m.productId]?.id, avail: data.data?.avail, storeId,
                                                              centralStockQty: data.data?.byId.get(m.productId)?.stockQty });
  const marked = meds.filter((m) => picked[m.productId]);
  const unavailable = marked.filter((m) => !hasHere(m));
  const lineItems = marked.filter(hasHere).map((m) => ({ m, p: chosen(m) })).filter((x): x is { m: ContinuousMedication; p: Product } => !!x.p);
  const itemsCents = lineItems.reduce((t, { p }) => t + p.priceCents, 0);   // #41: o total mostrado é o que a cesta cobra (o desconto da reposição automática não é aplicado no protótipo)
  const anyAuto = lineItems.some(({ m }) => refillAuto[m.productId]);
  const canBuy = lineItems.length > 0 && rxAttached;

  const buy = () => {
    const full = lineItems.filter(({ p }) => lines.some((l) => l.type === "product" && l.product.id === p.id && l.qty >= maxQty(l)));   // #43: já no limite da receita
    for (const { p } of lineItems) if (!full.some((f) => f.p.id === p.id)) dispatch({ type: "addProduct", product: p, confirmed: true });
    dispatch({ type: "attachRx", ids: lineItems.filter(({ p }) => p.rx).map(({ p }) => p.id) });   // receita anexada aqui mesmo
    const added = lineItems.length - full.length;
    const trocados = lineItems.filter(({ m, p }) => p.id !== m.productId).length;   // #46: equivalente escolhido segue sujeito ao farmacêutico
    dispatch({ type: "toast", text: (full.length ? `${added} ${added === 1 ? "item" : "itens"} da reposição na cesta; ${full.length === 1 ? "1 já estava" : `${full.length} já estavam`} no limite da receita` : `${lineItems.length} ${lineItems.length === 1 ? "item" : "itens"} da reposição na cesta`) + (trocados ? " Troca por equivalente: sujeita à confirmação do farmacêutico." : ""), action: "cart" });
    push({ name: "cart" });
  };

  const options = useMemo(() => {
    const d = data.data?.delivery.options ?? [];
    return [...d].sort((a, b) => DELIVERY_RANK(a.id) - DELIVERY_RANK(b.id)).map((o) => {
      // #45 (RDC 96/2008): só remédio na cesta, então nenhum frete grátis (nem por valor, nem pela reposição automática)
      const fee = o.id === "retirada" ? 0 : o.feeCents;
      return { o, fee, total: itemsCents + fee };
    });
  }, [data.data, itemsCents]);
  const best = options.length ? Math.min(...options.map((x) => x.total)) : 0;

  return (
    <div className="screen">
      <TitleBar title="Meus medicamentos" />
      <div className="scroll">
        <div className="pad">
          <div className="note ok" role="note">
            <Icon name="lock" size={18} />
            <p><b>Fica só neste aparelho.</b> A lista dos seus medicamentos nunca vai para o assistente de compras. Aqui você repõe o que já usa em poucos toques.</p>
          </div>

          <button className="row loc-row" onClick={() => push({ name: "stores" })}>
            <Icon name="store" size={20} />
            <span className="grow">{store ? `Retirar na ${store.name} · ${store.neighborhood}` : "Escolher loja de retirada"}</span>
            <Icon name="chevron" size={18} />
          </button>

          {data.loading && !data.data ? <div className="skeleton" style={{ height: 220 }} /> : null}
          {data.error ? <div className="note danger" role="alert"><Icon name="alert" size={18} /><p>{data.error}</p></div> : null}

          {data.data
            ? meds.map((m) => (
                <MedCard key={m.productId} m={m} product={data.data!.byId.get(m.productId)} avail={data.data!.avail} storeId={storeId}
                  picked={!!picked[m.productId]} onPick={(v) => setPicked({ ...picked, [m.productId]: v })}
                  auto={!!refillAuto[m.productId]} onAuto={(on) => dispatch({ type: "setRefillAuto", id: m.productId, on })}
                  reminders={consent.refillReminders}
                  choice={choice[m.productId]} onChoice={(c) => pick(m.productId, c)} onReset={() => pick(m.productId, null)} />
              ))
            : null}

          <section className="panel" aria-label="Receita">
            <div className="row"><Icon name="receipt" size={22} /><b>Receita (simulada)</b></div>
            {rxAttached ? (
              <p className="ok-line"><Icon name="checkCircle" size={18} /> Receita simulada anexada · válida até 30/03/2027 (data fictícia)</p>
            ) : (
              <p style={{ color: "var(--text-2)", fontSize: 14.5, lineHeight: 1.45 }}>Para repor, anexe a receita. Neste protótipo ela é simulada: nenhum documento real é enviado.</p>
            )}
            <button className={`btn ${rxAttached ? "outline" : "primary"} block`} onClick={() => dispatch({ type: "setRx", on: !rxAttached })}>
              {rxAttached ? "Remover receita simulada" : "Anexar receita simulada"}
            </button>
          </section>

          {lineItems.length ? (
            <section className="panel" aria-label="Total com entrega">
              <b>Total com entrega</b>
              <small style={{ color: "var(--text-2)" }}>
                {lineItems.length} {lineItems.length === 1 ? "item" : "itens"} · {money(itemsCents)}
              </small>
              <table className="quote">
                <tbody>
                  {options.map(({ o, fee, total }) => (
                    <tr key={o.id} className={total === best ? "best" : ""}>
                      <th scope="row">{o.label}<small>{o.eta}{o.id === PERSONA.preferences.deliveryPriority[0] ? " · sua preferência" : ""}</small></th>
                      <td>{fee === 0 ? "sem frete" : `frete ${money(fee)}`}</td>
                      <td><b>{money(total)}</b></td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {anyAuto ? <small className="foot">{REFILL_RULES.note}</small> : null}
            </section>
          ) : null}

          <p className="footnote">Protótipo: medicamentos, preços, receita e lojas são fictícios.</p>
        </div>
      </div>
      <div className="summary">
        <small className="foot center" role="status">
          {!marked.length ? "Marque o que quer repor." : !rxAttached ? "Anexe a receita simulada para repor." : !lineItems.length ? "Escolha um equivalente em estoque para seguir."
            : `${lineItems.length} ${lineItems.length === 1 ? "item" : "itens"} · ${money(itemsCents)}${unavailable.length ? ` · fora da conta: ${unavailable.map((m) => m.label).join(", ")} (sem estoque nesta loja)` : ""}`}
        </small>
        <button className="btn primary block" disabled={!canBuy} onClick={buy}>
          <Icon name="basketPlus" size={22} /> {lineItems.length ? `Repor ${lineItems.length} ${lineItems.length === 1 ? "item" : "itens"} na cesta` : "Repor na cesta"}
        </button>
      </div>
    </div>
  );
}

function MedCard({ m, product, avail, storeId, picked, onPick, auto, onAuto, reminders, choice, onChoice, onReset }: {
  m: ContinuousMedication; product: Product | undefined; avail: StoreAvailability[]; storeId: string | null; picked: boolean; onPick: (v: boolean) => void;
  auto: boolean; onAuto: (on: boolean) => void; reminders: boolean; choice?: Product;
  onChoice: (c: Product) => void; onReset: () => void;
}) {
  const { search } = useServices();
  const left = daysLeft(m);
  const urgent = needsRefill(m);
  const pct = Math.max(4, Math.min(100, Math.round((m.unitsLeft / m.packUnits) * 100)));
  const here = storeId ? avail.find((a) => a.store.id === storeId) : null;
  const inStockHere = storeId ? !!here?.availableIds.includes(m.productId) : (product?.stockQty ?? 0) > 0;
  const nearest = avail.find((a) => a.availableIds.includes(m.productId) && a.store.id !== storeId);
  const sims = useAsync<SimilarsResponse | null>(() => (inStockHere ? Promise.resolve(null) : search.similars(m.productId, storeId)), [search, m.productId, storeId, inStockHere]);
  const cur = choice ?? product;     // escolhido um equivalente, ele passa a ser o item deste cartão
  const swapped = !!product && !!choice && choice.id !== product.id;
  // escolher ou desfazer troca o conteúdo do cartão: o foco vai para o cartão (o botão tocado some) e a troca é anunciada
  const cardRef = useRef<HTMLElement>(null);
  const [said, setSaid] = useState("");
  const focusCard = () => setTimeout(() => cardRef.current?.focus(), 0);   // depois do render que tirou o botão
  if (!product || !cur) return null;
  const choose = (p: Product) => { onChoice(p); onPick(true); setSaid(`${p.name} escolhido no lugar de ${product.name}.`); focusCard(); };
  const undo = () => { onReset(); setSaid(`Troca desfeita. Voltou ${product.name}.`); focusCard(); };
  const out = new Date(runOutDate(m)).toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" });

  return (
    <article ref={cardRef} tabIndex={-1} className={`panel med ${urgent && reminders ? "urgent" : ""}`} aria-label={m.label}>
      <label className="row med-head">
        <input type="checkbox" checked={picked} onChange={(e) => onPick(e.target.checked)} aria-label={`Incluir ${cur.name} na reposição`} />
        <span className="grow"><b>{m.label}</b><small>{cur.name}</small>{swapped ? <small className="swap-note">no lugar de {product.name}</small> : null}</span>
        {urgent && reminders ? <span className="mini warn"><Icon name="bell" size={13} /> {left} {left === 1 ? "dia" : "dias"}</span> : null}
      </label>
      <div className="meter" role="img" aria-label={`Restam ${m.unitsLeft} de ${m.packUnits} unidades, cerca de ${left} dias`}>
        <div className="fill" style={{ width: `${pct}%` }} />
      </div>
      <small className="foot">Restam {m.unitsLeft} de {m.packUnits} · acaba por volta de {out}</small>

      <div className="row stockline">
        <Icon name="store" size={18} />
        {inStockHere || swapped ? <span className="ok">Em estoque{here ? ` na ${here.store.name}` : ""}</span>
          : <span className="off">Indisponível{here ? ` na ${here.store.name}` : ""}{nearest ? ` · tem na ${nearest.store.name} (${nearest.distanceKm.toLocaleString("pt-BR")} km)` : ""}</span>}
      </div>

      <p className="sr-only" role="status">{said}</p>
      {swapped || inStockHere ? (
        <div className="med-price">
          <div className="row"><span className="price blue">{money(cur.priceCents)}</span>
            {swapped ? <small className="swap-note">{delta(cur.priceCents - product.priceCents)} em relação ao original · sujeito à confirmação do farmacêutico</small> : null}</div>
          {swapped ? <button className="link plain" onClick={undo}>Desfazer troca e voltar a {product.name}</button> : null}
        </div>
      ) : (
        <div className="equiv" aria-label="Equivalentes disponíveis">
          <b>Equivalentes com estoque</b>
          <small className="foot">Mesmo princípio ativo e mesma dose. Critério deste protótipo, pelo cadastro. A troca é uma sugestão: só vale depois que o farmacêutico confirmar, e na loja ele segue a lista de intercambiáveis da Anvisa (Lei 9.787/1999 e RDC 58/2014). Aqui ninguém confirma de verdade.</small>
          {sims.loading ? <div className="skeleton" style={{ height: 60 }} /> : null}
          {(sims.data?.options ?? []).filter((o) => o.inStock && o.sameDose !== false).map((o) => (   // só os de mesmo princípio ativo e mesma dose
            <div key={o.product.id} className="swap-opt">
              <ProductImage product={o.product} size={44} />
              <span className="grow">
                <b>{o.product.name}</b>
                <small>{PRES[o.presentation ?? "similar"]} · {money(o.product.priceCents)} ({delta(o.deltaCents)}){o.needsPharmacistConfirmation ? " · sujeito à confirmação do farmacêutico" : ""}</small>
              </span>
              <button className="btn outline blue" aria-label={`Escolher ${o.product.name}`} onClick={() => choose(o.product)}>Escolher</button>
            </div>
          ))}
          {sims.data && !sims.data.options.some((o) => o.inStock) ? <p className="off">Nenhum equivalente em estoque nesta loja.</p> : null}
        </div>
      )}

      <label className="switch auto">
        <input type="checkbox" checked={auto} onChange={(e) => onAuto(e.target.checked)} />
        Reposição automática (sem frete grátis nem desconto: remédio não entra em promoção)
      </label>
      {auto ? <small className="foot">Avisamos {REFILL_RULES.alertDaysBefore} dias antes de acabar e você confirma antes de cada compra.</small> : null}
    </article>
  );
}
