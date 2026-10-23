import { useEffect, useRef, useState } from "react";
import { BasketButton } from "../components/Bars";
import { BottomSheet } from "../components/BottomSheet";
import { Icon } from "../components/Icon";
import { ProductImage } from "../components/ProductImage";
import type { Intent, Kit, StepId, SwapOption } from "../contracts/types";
import { STEP_LABEL, TIER_LABEL, kitPrice } from "../contracts/types";
import { useNav, useServices } from "../nav";
import { delta, money } from "../services/format";
import { useApp, type SubscriptionDays } from "../state/app";
import { useAsync } from "../useAsync";

export function KitDetail({ initialKit, intent }: { initialKit: Kit; intent: Intent }) {
  const { search, commerce } = useServices();
  const { pop, push } = useNav();
  const { dispatch, isFavKit, store } = useApp();
  const [kit, setKit] = useState(initialKit);
  const [every, setEvery] = useState<SubscriptionDays>(0);
  const [swapStep, setSwapStep] = useState<StepId | null>(null);
  const [options, setOptions] = useState<SwapOption[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const token = useRef(0);

  useEffect(() => setKit(initialKit), [initialKit]);
  const ids = kit.items.map((i) => i.product.id);
  const avail = useAsync(() => commerce.storesFor(ids), [commerce, ids.join()]);

  const openSwap = async (step: StepId) => {
    const t = ++token.current;
    setSwapStep(step);
    setOptions(null);
    setError(null);
    try {
      const o = await search.swapOptions(kit, step, intent);
      if (t === token.current) setOptions(o);
    } catch (e) {
      if (t === token.current) setError(e instanceof Error ? e.message : "Não foi possível carregar as opções.");
    }
  };
  const closeSwap = () => {
    token.current++;
    setSwapStep(null);
  };
  const pick = async (productId: string) => {
    if (!swapStep) return;
    try {
      setKit(await search.swap(kit, swapStep, productId, intent));
      closeSwap();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Não foi possível trocar o item.");
    }
  };

  const overBudget = intent.budgetCents != null && !kit.withinBudget ? kit.totalCents - intent.budgetCents : 0;
  const complete = (avail.data ?? []).filter((s) => s.missingIds.length === 0);
  const fav = isFavKit(kit);

  return (
    <div className="screen">
      <header className="bar">
        <button className="icon-btn" onClick={pop} aria-label="Voltar"><Icon name="back" /></button>
        <h1>Seu kit</h1>
        <button className="icon-btn" aria-pressed={fav} aria-label={fav ? "Tirar kit dos favoritos" : "Favoritar kit"}
          style={{ color: fav ? "var(--price)" : "var(--text-2)" }} onClick={() => dispatch({ type: "toggleFavKit", kit })}>
          <Icon name={fav ? "heartFill" : "heart"} />
        </button>
        <BasketButton />
      </header>
      <div className="scroll">
        <div className="pad">
          <div>
            <span className={`tier ${kit.tier}`}>{TIER_LABEL[kit.tier]}</span>
            <h2 style={{ fontSize: 21, marginTop: 6 }}>{kit.title}</h2>
            <p style={{ color: "var(--text-2)", fontSize: 14.5, marginTop: 4, lineHeight: 1.4 }}>{kit.rationale}</p>
          </div>

          <div className="panel" style={{ gap: 6 }}>
            <div className="row" style={{ gap: 8, fontSize: 14 }}>
              <Icon name="store" size={20} />
              <span className="grow">
                {kit.storeId && store
                  ? <>Todos os itens têm estoque na <b>{store.name}</b>. Retirar em até 60 minutos.</>
                  : avail.data
                    ? <>Kit completo em <b>{complete.length} de {avail.data.length}</b> lojas{complete[0] ? <> · mais próxima: {complete[0].store.name}</> : null}</>
                    : "Conferindo estoque nas lojas..."}
              </span>
            </div>
            {kit.cashbackCents > 0 ? (
              <span className="cashback"><Icon name="wallet" size={16} /> {money(kit.cashbackCents)} de cashback neste kit (simulado)</span>
            ) : null}
          </div>

          {overBudget > 0 ? (
            <div className="note warn" role="status"><Icon name="alert" size={18} /><p>Este kit está {money(overBudget)} acima do orçamento escolhido.</p></div>
          ) : null}
          {kit.alerts.map((a) => (
            <div key={a.code + (a.productIds?.join("") ?? "")} className={`note ${a.severity === "atencao" ? "warn" : ""}`} role="note">
              <Icon name={a.severity === "atencao" ? "alert" : "info"} size={18} />
              <p>{a.text}</p>
            </div>
          ))}

          {kit.items.map((it) => (
            <section key={it.product.id} className="step-block" aria-label={STEP_LABEL[it.step]}>
              <div className="step-head">
                <span className="step-label">{STEP_LABEL[it.step]}</span>
                {it.alternativesCount !== 0 ? (
                  <button className="textbtn" onClick={() => openSwap(it.step)}><Icon name="swap" size={16} /> Trocar</button>
                ) : null}
              </div>
              <button className="row" style={{ textAlign: "left" }} onClick={() => push({ name: "product", id: it.product.id })}>
                <span style={{ width: 72, flex: "none" }}><ProductImage product={it.product} size={72} /></span>
                <span className="grow" style={{ display: "flex", flexDirection: "column", gap: 2 }}>
                  <span className="brandname" style={{ fontSize: 12 }}>{it.product.brand}</span>
                  <span style={{ fontSize: 14.5 }}>{it.product.name}</span>
                  <span className="price blue" style={{ fontSize: 16 }}>{money(it.product.priceCents)}</span>
                </span>
              </button>
              <p className="reason">{it.reason}</p>
              <button className="textbtn" style={{ alignSelf: "flex-start" }} onClick={() => dispatch({ type: "addProduct", product: it.product })}>
                <Icon name="plus" size={16} /> Levar só este
              </button>
            </section>
          ))}

          <fieldset className="panel" style={{ margin: 0 }}>
            <legend className="section-title" style={{ padding: "0 4px" }}>Como você quer comprar</legend>
            {([0, 30, 60] as SubscriptionDays[]).map((d) => (
              <label key={d} className="radio" data-sel={every === d} style={{ border: 0, padding: "8px 0", minHeight: 44 }}>
                <input type="radio" name="every" checked={every === d} onChange={() => setEvery(d)} />
                <span className="grow">
                  {d === 0 ? "Comprar uma vez" : `Assinar: receber a cada ${d} dias`}
                  {d !== 0 ? <small>Sem custo de assinatura; cancele quando quiser (simulado)</small> : null}
                </span>
                {d !== 0 ? <Icon name="repeat" size={18} /> : null}
              </label>
            ))}
          </fieldset>
          <p className="footnote">Preços e estoque simulados.</p>
        </div>
      </div>

      <div className="sticky">
        <div className="line1">
          <span>{kit.items.length} itens{kit.discountCents > 0 ? <small className="kit-off"> · avulsos {money(kit.itemsTotalCents)} · desconto do kit {kit.discountPct}% (−{money(kit.discountCents)})</small> : null}</span>
          <b>{money(kit.totalCents)}</b>
        </div>
        <button className="btn primary block" onClick={() => dispatch({ type: "addKit", kit, intent, everyDays: every })}>
          <Icon name="basketPlus" /> {every ? `Assinar kit (a cada ${every} dias)` : "Adicionar kit à cesta"}
        </button>
      </div>

      {swapStep ? (
        <BottomSheet title={`Trocar: ${STEP_LABEL[swapStep]}`} onClose={closeSwap}>
          {error ? <div className="note danger" role="alert"><Icon name="alert" size={18} /><p>{error}</p></div> : null}
          {!options && !error ? <div className="skeleton" style={{ height: 120 }} role="status" aria-label="Carregando opções" /> : null}
          {options?.length === 0 ? <p className="footnote">Nenhuma outra opção disponível para esta etapa.</p> : null}
          {options?.map((o) => {
            const newTotal = kitPrice(kit.itemsTotalCents + o.deltaCents, kit.items.length).totalCents;
            const kitDelta = newTotal - kit.totalCents;          // quanto o kit muda, já com o desconto (#30)
            const over = intent.budgetCents != null && newTotal > intent.budgetCents;
            return (
              <button key={o.product.id} className="opt" disabled={!o.compatible} onClick={() => pick(o.product.id)}>
                <ProductImage product={o.product} size={52} />
                <span className="info">
                  <b>{o.product.name}</b>
                  <small>
                    {o.product.brand} · {money(o.product.priceCents)}
                    {!o.compatible && o.reason ? ` · ${o.reason}` : ""}
                    {o.compatible && over ? " · passa do orçamento" : ""}
                  </small>
                </span>
                {o.compatible ? <span className={`d ${kitDelta > 0 ? "up" : kitDelta < 0 ? "down" : ""}`} aria-label={`kit ${delta(kitDelta)}`}>{delta(kitDelta)}<small> no kit</small></span> : null}
              </button>
            );
          })}
        </BottomSheet>
      ) : null}
    </div>
  );
}
