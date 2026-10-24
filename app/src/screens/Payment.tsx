import { useState } from "react";
import { TitleBar } from "../components/Bars";
import { Icon } from "../components/Icon";
import { useNav, useServices } from "../nav";
import { money } from "../services/format";
import { rxPending, useApp, type Order } from "../state/app";
import { useAsync } from "../useAsync";
import { feeFor } from "./Delivery";

const PAYMENTS = [
  { id: "pix", label: "Pix", hint: "Código gerado na confirmação (simulado)" },
  { id: "cartao", label: "Cartão de crédito", hint: "Sem campos de cartão: pagamento simulado" },
  { id: "retirada", label: "Pagar na retirada", hint: "Na loja, no balcão" },
] as const;

export function Payment() {
  const { lines, count, itemsCents, listCents, cashbackCents, mode, store, dispatch, rxDocs } = useApp();
  const rxMissing = rxPending(lines, rxDocs).length;   // #28: sem todas as receitas, não paga
  const { resetAll, push } = useNav();
  const { commerce } = useServices();
  const [pay, setPay] = useState<(typeof PAYMENTS)[number]["id"]>("pix");
  const del = useAsync(() => commerce.delivery(), [commerce]);
  const opt = del.data?.options.find((o) => o.id === mode);
  const fee = feeFor(opt, itemsCents);
  const total = itemsCents + fee;

  const confirm = () => {
    if (rxMissing) return;
    if (!mode || !lines.length) return;
    const order: Order = {
      id: `SIM-${Date.now().toString(36).toUpperCase().slice(-6)}`,
      createdAt: new Date().toISOString(),
      lines,
      itemsCents,
      feeCents: fee,
      totalCents: total,
      cashbackCents,
      mode,
      storeName: mode === "agendada" ? null : (store?.name ?? null),
      payment: PAYMENTS.find((p) => p.id === pay)!.label,
      status: mode === "retirada" ? "Separando para retirada (simulado)" : pay === "pix" ? "Aguardando pagamento Pix (simulado)" : "Pedido recebido (simulado)",
    };
    dispatch({ type: "placeOrder", order });
    resetAll("mais", { name: "done", orderId: order.id });
  };

  return (
    <div className="screen">
      <TitleBar title="Pagamento" />
      <div className="scroll">
        <div className="pad">
          <div className="note warn" role="note"><Icon name="info" size={18} /><p>Simulação: nenhum pagamento é processado e nenhum dado de pagamento é enviado.</p></div>
          <div className="panel" style={{ gap: 4 }}>
            <span className="section-title">Receber</span>
            <span style={{ fontSize: 15 }}>
              {opt ? opt.label : "Carregando..."}{opt && store && mode !== "agendada" ? ` · ${store.name}` : ""}
            </span>
            <small style={{ color: "var(--text-2)" }}>{opt?.eta}</small>
          </div>
          <fieldset style={{ border: 0, padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: 8 }}>
            <legend className="section-title" style={{ marginBottom: 8 }}>Forma de pagamento</legend>
            {PAYMENTS.filter((p) => p.id !== "retirada" || mode === "retirada").map((p) => (
              <label key={p.id} className="radio" data-sel={pay === p.id}>
                <input type="radio" name="pay" checked={pay === p.id} onChange={() => setPay(p.id)} />
                <span className="grow"><b style={{ fontWeight: 500 }}>{p.label}</b><small>{p.hint}</small></span>
              </label>
            ))}
          </fieldset>
          <div className="panel" style={{ gap: 4 }}>
            <div className="sumrow"><span>Subtotal ({count} {count === 1 ? "item" : "itens"})</span><span>{money(listCents)}</span></div>
            {listCents > itemsCents ? <div className="sumrow"><span>Descontos</span><span>- {money(listCents - itemsCents)}</span></div> : null}
            <div className="sumrow"><span>Entrega</span><span>{fee ? money(fee) : "Grátis"}</span></div>
            <div className="sumrow total" style={{ fontSize: 18, borderTop: "1px dashed var(--line)", paddingTop: 8, marginTop: 4 }}>
              <span>Total</span><span>{money(total)}</span>
            </div>
            {cashbackCents > 0 ? <div className="sumrow" style={{ color: "var(--ok)" }}><span>Cashback a receber</span><span>{money(cashbackCents)}</span></div> : null}
          </div>
        </div>
      </div>
      <div className="sticky">
        {rxMissing ? (
          <button className="note warn" style={{ textAlign: "left", width: "100%" }} onClick={() => push({ name: "prescriptions" })}>
            <Icon name="alert" size={18} /><span>Falta anexar {rxMissing === 1 ? "1 receita" : `${rxMissing} receitas`}. Anexar receitas</span>
          </button>
        ) : null}
        <button className="btn primary block" disabled={!mode || !lines.length || !opt || rxMissing > 0} onClick={confirm}>Finalizar pedido simulado</button>
      </div>
    </div>
  );
}

export function Confirmation({ orderId }: { orderId: string }) {
  const { orders } = useApp();
  const { replace, resetTo } = useNav();
  const o = orders.find((x) => x.id === orderId);
  return (
    <div className="screen">
      <TitleBar title="Pedido realizado" back={false} />
      <div className="scroll">
        <div className="pad" style={{ alignItems: "center", textAlign: "center", paddingTop: 32 }}>
          <span style={{ width: 76, height: 76, borderRadius: "50%", background: "var(--ok-bg)", color: "var(--ok)", display: "grid", placeItems: "center" }}>
            <Icon name="check" size={40} />
          </span>
          <h2 style={{ fontSize: 22 }}>Pedido simulado registrado</h2>
          {o ? (
            <p style={{ color: "var(--text-2)", lineHeight: 1.5 }}>
              Número {o.id} · {money(o.totalCents)}<br />
              {o.status}
              {o.cashbackCents ? <><br />{money(o.cashbackCents)} de cashback a receber (simulado)</> : null}
            </p>
          ) : null}
          <div className="note" style={{ textAlign: "left" }}><Icon name="info" size={18} /><p>Demonstração: nada foi cobrado e o pedido não foi enviado a nenhuma loja; ele fica só neste navegador. As frases da busca seguem as regras de Privacidade e dados.</p></div>
          <button className="btn primary block" onClick={() => replace({ name: "orders" })}>Ver meus pedidos</button>
          <button className="link" onClick={() => resetTo("home")}>Continuar comprando</button>
        </div>
      </div>
    </div>
  );
}
