// Meus medicamentos: REPOSIÇÃO do que a pessoa já usa. Nada aqui recomenda medicamento, dose ou troca de tratamento.
// Os dados (itens, quantidades, receita) ficam no aparelho; o motor só devolve equivalentes a partir de um id de produto.
import { useMemo, useState } from "react";
import { TitleBar } from "../components/Bars";
import { Icon } from "../components/Icon";
import { ProductImage } from "../components/ProductImage";
import type { Product, SimilarsResponse, StoreAvailability } from "../contracts/types";
import { useNav, useServices } from "../nav";
import { DELIVERY_RANK, PERSONA, REFILL_RULES, daysLeft, needsRefill, refillPrice, runOutDate, type ContinuousMedication } from "../persona";
import { delta, money } from "../services/format";
import { useApp } from "../state/app";
import { useAsync } from "../useAsync";

const PRES: Record<string, string> = { referencia: "Referência", generico: "Genérico", similar: "Similar" };

export function Refill() {
  const { commerce } = useServices();
  const { push } = useNav();
  const { store, storeId, dispatch, refillAuto, rxAttached, consent } = useApp();
  const meds = PERSONA.continuousMedications;
  const ids = meds.map((m) => m.productId);
  const data = useAsync(async () => {
    const [prods, avail, delivery] = await Promise.all([commerce.products(ids), commerce.storesFor(ids), commerce.delivery()]);
    return { byId: new Map(prods.map((p) => [p.id, p])), avail, delivery };
  }, [commerce]);
  // escolha de apresentação por item (começa no próprio item); troca por equivalente exige confirmação
  const [choice, setChoice] = useState<Record<string, { product: Product; confirmed: boolean }>>({});
  const [picked, setPicked] = useState<Record<string, boolean>>(() => Object.fromEntries(meds.map((m) => [m.productId, needsRefill(m)])));

  const chosen = (m: ContinuousMedication): Product | undefined => choice[m.productId]?.product ?? data.data?.byId.get(m.productId);
  const lineItems = meds.filter((m) => picked[m.productId]).map((m) => ({ m, p: chosen(m) })).filter((x): x is { m: ContinuousMedication; p: Product } => !!x.p);
  const swapsUnconfirmed = lineItems.some(({ m, p }) => p.id !== m.productId && !choice[m.productId]?.confirmed);
  const itemsCents = lineItems.reduce((t, { m, p }) => t + refillPrice(p.priceCents, !!refillAuto[m.productId]), 0);
  const anyAuto = lineItems.some(({ m }) => refillAuto[m.productId]);
  const canBuy = lineItems.length > 0 && rxAttached && !swapsUnconfirmed;

  const buy = () => {
    for (const { p } of lineItems) dispatch({ type: "addProduct", product: p });
    dispatch({ type: "toast", text: `${lineItems.length} ${lineItems.length === 1 ? "item" : "itens"} da reposição na cesta`, action: "cart" });
    push({ name: "cart" });
  };

  const options = useMemo(() => {
    const d = data.data?.delivery.options ?? [];
    return [...d].sort((a, b) => DELIVERY_RANK(a.id) - DELIVERY_RANK(b.id)).map((o) => {
      const free = (o.freeFromCents != null && itemsCents >= o.freeFromCents) || (anyAuto && REFILL_RULES.freeShipping && o.id !== "retirada");
      const fee = o.id === "retirada" ? 0 : free ? 0 : o.feeCents;
      return { o, fee, total: itemsCents + fee };
    });
  }, [data.data, itemsCents, anyAuto]);
  const best = options.length ? Math.min(...options.map((x) => x.total)) : 0;

  return (
    <div className="screen">
      <TitleBar title="Meus medicamentos" />
      <div className="scroll">
        <div className="pad">
          <div className="note ok" role="note">
            <Icon name="lock" size={18} />
            <p><b>Fica só neste aparelho.</b> A lista dos seus medicamentos nunca vai para o assistente de compras. Aqui você só repõe o que já usa, sem recomendação.</p>
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
                  choice={choice[m.productId]} onChoice={(c) => setChoice({ ...choice, [m.productId]: c })} onReset={() => { const n = { ...choice }; delete n[m.productId]; setChoice(n); }} />
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
                {lineItems.length} {lineItems.length === 1 ? "item" : "itens"} · {money(itemsCents)}{anyAuto ? ` (estimativa com ${REFILL_RULES.discountPct}% da reposição automática)` : ""}
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

          <button className="btn primary block" disabled={!canBuy} onClick={buy}>
            <Icon name="basketPlus" size={22} /> Repor {lineItems.length || ""} {lineItems.length === 1 ? "item" : "itens"} na cesta
          </button>
          {!rxAttached && lineItems.length ? <small className="foot center">Anexe a receita simulada para repor.</small> : null}
          {swapsUnconfirmed ? <small className="foot center">Confirme a troca com o farmacêutico para continuar.</small> : null}
          <p className="footnote">Protótipo: medicamentos, preços, receita e lojas são fictícios. Não é orientação médica.</p>
        </div>
      </div>
    </div>
  );
}

function MedCard({ m, product, avail, storeId, picked, onPick, auto, onAuto, reminders, choice, onChoice, onReset }: {
  m: ContinuousMedication; product: Product | undefined; avail: StoreAvailability[]; storeId: string | null; picked: boolean; onPick: (v: boolean) => void;
  auto: boolean; onAuto: (on: boolean) => void; reminders: boolean; choice?: { product: Product; confirmed: boolean };
  onChoice: (c: { product: Product; confirmed: boolean }) => void; onReset: () => void;
}) {
  const { search } = useServices();
  const { push } = useNav();
  const left = daysLeft(m);
  const urgent = needsRefill(m);
  const pct = Math.max(4, Math.min(100, Math.round((m.unitsLeft / m.packUnits) * 100)));
  const here = storeId ? avail.find((a) => a.store.id === storeId) : null;
  const inStockHere = storeId ? !!here?.availableIds.includes(m.productId) : (product?.stockQty ?? 0) > 0;
  const nearest = avail.find((a) => a.availableIds.includes(m.productId) && a.store.id !== storeId);
  const sims = useAsync<SimilarsResponse | null>(() => (inStockHere ? Promise.resolve(null) : search.similars(m.productId, storeId)), [search, m.productId, storeId, inStockHere]);
  if (!product) return null;
  const cur = choice?.product ?? product;
  const out = new Date(runOutDate(m)).toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" });

  return (
    <article className={`panel med ${urgent && reminders ? "urgent" : ""}`} aria-label={m.label}>
      <label className="row med-head">
        <input type="checkbox" checked={picked} onChange={(e) => onPick(e.target.checked)} aria-label={`Incluir ${product.name} na reposição`} />
        <span className="grow"><b>{m.label}</b><small>{product.name}</small></span>
        {urgent && reminders ? <span className="mini warn"><Icon name="bell" size={13} /> {left} {left === 1 ? "dia" : "dias"}</span> : null}
      </label>
      <div className="meter" role="img" aria-label={`Restam ${m.unitsLeft} de ${m.packUnits} unidades, cerca de ${left} dias`}>
        <div className="fill" style={{ width: `${pct}%` }} />
      </div>
      <small className="foot">Restam {m.unitsLeft} de {m.packUnits} · acaba por volta de {out}</small>

      <div className="row stockline">
        <Icon name="store" size={18} />
        {inStockHere ? <span className="ok">Em estoque{here ? ` na ${here.store.name}` : ""}</span>
          : <span className="off">Indisponível{here ? ` na ${here.store.name}` : ""}{nearest ? ` · tem na ${nearest.store.name} (${nearest.distanceKm.toLocaleString("pt-BR")} km)` : ""}</span>}
      </div>

      {!inStockHere ? (
        <div className="equiv" aria-label="Equivalentes disponíveis">
          <b>Equivalentes com estoque</b>
          <small className="foot">Mesmo princípio ativo e mesma dose. A troca só vale com a confirmação do farmacêutico e conforme a sua receita.</small>
          {sims.loading ? <div className="skeleton" style={{ height: 60 }} /> : null}
          {(sims.data?.options ?? []).filter((o) => o.inStock).map((o) => {
            const on = choice?.product.id === o.product.id;
            return (
              <div key={o.product.id} className={`swap-opt ${on ? "on" : ""}`}>
                <ProductImage product={o.product} size={44} />
                <span className="grow">
                  <b>{o.product.name}</b>
                  <small>{PRES[o.presentation ?? "similar"]} · {money(o.product.priceCents)} ({delta(o.deltaCents)})</small>
                </span>
                <button className="btn outline blue" aria-pressed={on} onClick={() => (on ? onReset() : onChoice({ product: o.product, confirmed: false }))}>{on ? "Escolhido" : "Escolher"}</button>
              </div>
            );
          })}
          {sims.data && !sims.data.options.some((o) => o.inStock) ? <p className="off">Nenhum equivalente em estoque nesta loja. Fale com o farmacêutico.</p> : null}
          {choice ? (
            <label className="confirm">
              <input type="checkbox" checked={choice.confirmed} onChange={(e) => onChoice({ ...choice, confirmed: e.target.checked })} />
              Entendi que a troca depende da confirmação do farmacêutico e da minha receita.
            </label>
          ) : null}
          <button className="link plain" onClick={() => push({ name: "pharmacist" })}>Falar com um farmacêutico</button>
        </div>
      ) : (
        <div className="row"><span className="price blue">{money(refillPrice(cur.priceCents, auto))}</span>{auto ? <span className="old">{money(cur.priceCents)}</span> : null}</div>
      )}

      <label className="switch auto">
        <input type="checkbox" checked={auto} onChange={(e) => onAuto(e.target.checked)} />
        Reposição automática ({REFILL_RULES.discountPct}% e frete grátis, premissas fictícias)
      </label>
      {auto ? <small className="foot">Avisamos {REFILL_RULES.alertDaysBefore} dias antes de acabar e você confirma antes de cada compra.</small> : null}
    </article>
  );
}
