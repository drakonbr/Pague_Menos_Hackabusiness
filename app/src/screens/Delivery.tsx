import { useMemo, useState } from "react";
import { TitleBar } from "../components/Bars";
import { BottomSheet } from "../components/BottomSheet";
import { Icon } from "../components/Icon";
import type { DeliveryOption, KitAdaptation, Store, StoreAvailability } from "../contracts/types";
import { STEP_LABEL } from "../contracts/types";
import { SIMULATED_LOCATION } from "../location";
import { useNav, useServices } from "../nav";
import { delta, money } from "../services/format";
import { cartProductIds, useApp, type CartLine } from "../state/app";
import { useAsync } from "../useAsync";

type TabId = "entrega" | "retirada";

export function feeFor(opt: DeliveryOption | undefined, itemsCents: number): number {
  if (!opt) return 0;
  return opt.freeFromCents != null && itemsCents >= opt.freeFromCents ? 0 : opt.feeCents;
}

interface Plan {
  store: Store;
  kits: Array<{ line: Extract<CartLine, { type: "kit" }>; result: KitAdaptation | null }>;
  missingProducts: Array<Extract<CartLine, { type: "product" }>>;
}

export function Delivery() {
  const { lines, itemsCents, store, mode, dispatch } = useApp();
  const { push } = useNav();
  const { commerce, search } = useServices();
  const [tab, setTab] = useState<TabId>(mode === "retirada" ? "retirada" : "entrega");
  const [onlyStock, setOnlyStock] = useState(false);
  const [showMap, setShowMap] = useState(false);
  const [plan, setPlan] = useState<Plan | null>(null);
  const ids = useMemo(() => cartProductIds(lines), [lines]);

  const data = useAsync(async () => {
    const [stores, d] = await Promise.all([commerce.storesFor(ids), commerce.delivery()]);
    return { stores, ...d };
  }, [commerce, ids.join()]);

  const stores = data.data?.stores ?? [];
  const complete = stores.filter((s) => s.missingIds.length === 0);
  const expressStore = complete[0] ?? null;
  const opt = (id: string) => data.data?.options.find((o) => o.id === id);
  const centralOk = lines.every((l) => (l.type === "kit" ? l.kit.items.every((i) => i.product.stockQty > 0) : l.product.stockQty > 0));

  const choose = async (s: StoreAvailability) => {
    if (s.missingIds.length === 0) {
      dispatch({ type: "setStore", store: s.store });
      dispatch({ type: "setMode", mode: "retirada" });
      return;
    }
    const missing = new Set(s.missingIds);
    const kits = await Promise.all(
      lines
        .filter((l): l is Extract<CartLine, { type: "kit" }> => l.type === "kit" && l.kit.items.some((i) => missing.has(i.product.id)))
        .map(async (line) => ({ line, result: await search.adaptToStore(line.kit, s.store.id, line.intent) })),
    );
    const missingProducts = lines.filter((l): l is Extract<CartLine, { type: "product" }> => l.type === "product" && missing.has(l.product.id));
    setPlan({ store: s.store, kits, missingProducts });
  };

  const applyPlan = () => {
    if (!plan) return;
    for (const k of plan.kits) {
      if (k.result) dispatch({ type: "replaceKit", key: k.line.key, kit: k.result.kit, intent: { ...k.line.intent, storeId: plan.store.id } });
    }
    for (const p of plan.missingProducts) dispatch({ type: "remove", key: p.key });
    dispatch({ type: "setStore", store: plan.store });
    dispatch({ type: "setMode", mode: "retirada" });
    setPlan(null);
  };

  const shown = onlyStock ? complete : stores;
  const canContinue =
    (mode === "retirada" && store && complete.some((s) => s.store.id === store.id)) ||
    (mode === "expressa" && !!expressStore) ||
    (mode === "agendada" && centralOk);

  return (
    <div className="screen">
      <TitleBar title="Forma de Entrega" />
      <div className="tabs3" role="tablist">
        <button role="tab" aria-selected={tab === "entrega"} onClick={() => setTab("entrega")}><Icon name="truck" /> Entrega</button>
        <button role="tab" aria-selected={tab === "retirada"} onClick={() => setTab("retirada")}><Icon name="store" /> Retirar na loja</button>
        <button role="tab" aria-selected={false} disabled title="Fora do protótipo"><Icon name="locker" /> Locker</button>
      </div>
      <div className="scroll">
        <div className="pad">
          {data.loading && !data.data ? <div className="skeleton" style={{ height: 200 }} /> : null}

          {tab === "entrega" && data.data ? (
            <>
              <h2 style={{ fontSize: 20, fontWeight: 500, color: "var(--text-2)" }}>Endereços</h2>
              <div className="panel">
                <div className="row">
                  <Icon name="home" />
                  <b className="grow" style={{ fontWeight: 500 }}>Casa</b>
                  <span className="mini blue">Principal</span>
                </div>
                <span style={{ color: "var(--text-2)", fontSize: 14.5 }}>Endereço simulado · {SIMULATED_LOCATION.label}</span>
              </div>
              {(["expressa", "agendada"] as const).map((id) => {
                const o = opt(id)!;
                const disabled = id === "expressa" ? !expressStore : !centralOk;
                const fee = feeFor(o, itemsCents);
                return (
                  <label key={id} className="radio" data-sel={mode === id} style={{ opacity: disabled ? 0.5 : 1 }}>
                    <input type="radio" name="mode" disabled={disabled} checked={mode === id}
                      onChange={() => {
                        dispatch({ type: "setMode", mode: id });
                        if (id === "expressa" && expressStore) dispatch({ type: "setStore", store: expressStore.store });
                      }} />
                    <span className="grow">
                      <b style={{ fontWeight: 500 }}>{o.label}</b>
                      <small>
                        {o.eta}
                        {id === "expressa" ? (expressStore ? ` · sai da ${expressStore.store.name}` : " · nenhuma loja tem a cesta completa") : " · centro de distribuição"}
                      </small>
                    </span>
                    <b style={{ color: fee ? "var(--text)" : "var(--ok)" }}>{fee ? money(fee) : "Grátis"}</b>
                  </label>
                );
              })}
            </>
          ) : null}

          {tab === "retirada" && data.data ? (
            <>
              <div>
                <h2 style={{ fontSize: 22 }}>Lojas próximas à</h2>
                <p style={{ color: "var(--text-2)", marginTop: 4 }}>{SIMULATED_LOCATION.label}</p>
              </div>
              <div className="seg" role="group" aria-label="Filtrar lojas">
                <button aria-pressed={!onlyStock} onClick={() => setOnlyStock(false)}>Todas as lojas</button>
                <button aria-pressed={onlyStock} onClick={() => setOnlyStock(true)}>Com estoque</button>
              </div>
              <div className="row" style={{ justifyContent: "space-between" }}>
                <span style={{ color: "var(--text-2)" }}>{shown.length} resultados</span>
                <button className="link" onClick={() => setShowMap((m) => !m)}>{showMap ? "Fechar mapa" : "Abrir mapa"}</button>
              </div>
              {showMap ? <MiniMap stores={shown} selected={store?.id ?? null} /> : null}
              {shown.map((s, i) => (
                <button key={s.store.id} className="store" aria-pressed={mode === "retirada" && store?.id === s.store.id} onClick={() => choose(s)}>
                  <span className="t">
                    <span style={{ color: "var(--logo)", flex: "none" }}><Icon name="cross" size={22} /></span>
                    <span className="grow">{s.store.name} ({s.store.id.toUpperCase()}){s.store.open24h ? " 24 Horas." : ""}</span>
                    <Icon name="chevron" size={20} />
                  </span>
                  <span><span className="open">Aberta</span> · <span style={{ color: "var(--text-2)" }}>{s.store.hours}</span></span>
                  <span className="addr">{s.store.address}, Fortaleza - CE (endereço fictício)</span>
                  <span className="chips">
                    {i === 0 && !onlyStock ? <span className="mini blue">+ Próxima</span> : null}
                    <span className="mini">{s.distanceKm.toLocaleString("pt-BR")} km</span>
                    <span className="mini">Retirar em até 60 minutos</span>
                    {s.missingIds.length === 0 ? (
                      <span className="mini green"><Icon name="check" size={13} /> Cesta completa</span>
                    ) : (
                      <span className="mini warn">{s.missingIds.length === 1 ? "Falta 1 item" : `Faltam ${s.missingIds.length} itens`}</span>
                    )}
                  </span>
                </button>
              ))}
            </>
          ) : null}
        </div>
      </div>
      <div className="sticky">
        <button className="btn primary block" disabled={!canContinue} onClick={() => push({ name: "payment" })}>Continuar para pagamento</button>
      </div>

      {plan ? (
        <BottomSheet title={`Ajustar para a ${plan.store.name}`} onClose={() => setPlan(null)}>
          <p style={{ fontSize: 14.5, color: "var(--text-2)", lineHeight: 1.4 }}>
            Esta loja não tem todos os itens. Para kits, trocamos só o que falta por um item equivalente que ela tem, sem quebrar as regras do kit.
          </p>
          {plan.kits.map(({ line, result }) => (
            <div key={line.key} className="panel" style={{ gap: 6 }}>
              <b>{line.kit.title}</b>
              {result ? (
                result.replaced.map((r) => (
                  <div key={r.step} style={{ fontSize: 13.5, display: "flex", flexDirection: "column", gap: 2 }}>
                    <span className="step-label">{STEP_LABEL[r.step]}</span>
                    <span style={{ textDecoration: "line-through", color: "var(--muted)" }}>{r.from.name}</span>
                    <span>{r.to.name} <b style={{ color: r.to.priceCents > r.from.priceCents ? "var(--danger)" : "var(--ok)" }}>{delta(r.to.priceCents - r.from.priceCents)}</b></span>
                  </div>
                ))
              ) : (
                <span className="mini warn" style={{ alignSelf: "flex-start" }}>Este kit não fecha nesta loja e sairá da cesta</span>
              )}
            </div>
          ))}
          {plan.missingProducts.map((l) => (
            <div key={l.key} className="panel" style={{ gap: 4 }}>
              <b style={{ fontWeight: 500 }}>{l.product.name}</b>
              <span className="mini warn" style={{ alignSelf: "flex-start" }}>Sem estoque nesta loja; sai da cesta</span>
            </div>
          ))}
          <div className="row" style={{ marginTop: 6 }}>
            <button className="btn outline grow" onClick={() => setPlan(null)}>Escolher outra loja</button>
            <button className="btn primary grow"
              onClick={() => {
                for (const k of plan.kits) if (!k.result) dispatch({ type: "remove", key: k.line.key });
                applyPlan();
              }}>
              Ajustar e retirar aqui
            </button>
          </div>
        </BottomSheet>
      ) : null}
    </div>
  );
}

/** Mapa esquemático (sem serviço de mapas): posições relativas das lojas fictícias. */
function MiniMap({ stores, selected }: { stores: StoreAvailability[]; selected: string | null }) {
  const pts = [...stores.map((s) => s.store), { id: "me", name: "Você", lat: SIMULATED_LOCATION.lat, lng: SIMULATED_LOCATION.lng } as Store];
  const lats = pts.map((p) => p.lat);
  const lngs = pts.map((p) => p.lng);
  const [minLa, maxLa, minLn, maxLn] = [Math.min(...lats), Math.max(...lats), Math.min(...lngs), Math.max(...lngs)];
  const x = (lng: number) => 20 + ((lng - minLn) / (maxLn - minLn || 1)) * 320;
  const y = (lat: number) => 20 + ((maxLa - lat) / (maxLa - minLa || 1)) * 160;
  return (
    <svg viewBox="0 0 360 200" role="img" aria-label="Mapa esquemático das lojas" style={{ background: "#e8eef7", borderRadius: 10, width: "100%" }}>
      {stores.map((s) => (
        <g key={s.store.id}>
          <circle cx={x(s.store.lng)} cy={y(s.store.lat)} r={selected === s.store.id ? 9 : 7} fill={s.missingIds.length ? "#b9bccf" : "var(--logo)"} stroke="#fff" strokeWidth={2} />
          <text x={x(s.store.lng) + 10} y={y(s.store.lat) + 4} fontSize="10" fill="#333">{s.store.neighborhood}</text>
        </g>
      ))}
      <circle cx={x(SIMULATED_LOCATION.lng)} cy={y(SIMULATED_LOCATION.lat)} r={7} fill="var(--brand)" stroke="#fff" strokeWidth={2} />
      <text x={x(SIMULATED_LOCATION.lng) + 10} y={y(SIMULATED_LOCATION.lat) + 4} fontSize="10" fontWeight="700" fill="var(--brand)">Você</text>
    </svg>
  );
}
