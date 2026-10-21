// Conversa na barra de busca: a pessoa escreve do jeito dela e o motor responde com texto, kits, produtos e ações.
// O app só envia a frase, o `context` da resposta anterior e ids. Dados de saúde da pessoa nunca saem daqui.
import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import { PersonaAvatar } from "../components/Avatar";
import { BasketButton } from "../components/Bars";
import { Icon } from "../components/Icon";
import { KitCard } from "../components/KitCard";
import { ProductCard } from "../components/ProductCard";
import { ProductImage } from "../components/ProductImage";
import type { ChatAction, ChatContext, Kit, SearchResponse, SimilarOption, SkinType, StepId } from "../contracts/types";
import { STEP_LABEL, TIER_LABEL } from "../contracts/types";
import { useNav, useServices } from "../nav";
import { PERSONA } from "../persona";
import { delta, money } from "../services/format";
import { useApp, type ChatMsg } from "../state/app";
import { useAsync } from "../useAsync";

const WELCOME_SUGGESTIONS = ["Remédio para dor de cabeça", "Repor meus medicamentos", "Kit de suplementos ômega 3, colágeno e magnésio", "Rotina anti idade premium até R$ 400"];
let seq = 0;
const nextId = () => `m${Date.now().toString(36)}${(seq++).toString(36)}`;

export function Chat({ initial }: { initial?: string }) {
  const { search } = useServices();
  const { chat, dispatch, storeId, store } = useApp();
  const { pop, push } = useNav();
  const [text, setText] = useState("");
  const [, force] = useState(0);
  const bottom = useRef<HTMLDivElement>(null);
  const ctxRef = useRef<ChatContext | null>(chat.context);
  ctxRef.current = chat.context;
  const started = useRef(false);

  const send = useCallback(
    async (q: string) => {
      const t = q.trim();
      if (!t) return;
      dispatch({ type: "recent", q: t });
      dispatch({ type: "chatPush", msg: { id: nextId(), role: "user", text: t } });
      dispatch({ type: "chatPending", pending: true });
      try {
        const res = await search.search({ query: t, storeId, context: ctxRef.current });
        dispatch({ type: "chatPush", msg: { id: nextId(), role: "bot", text: res.reply ?? res.notes[0] ?? "Pronto.", res } });
        if (res.context) dispatch({ type: "chatContext", context: res.context });
        const a = res.action;
        if (a?.type === "add_kit_to_cart") {
          const kit = res.kits.find((k) => k.tier === a.tier) ?? res.kits[0];
          if (kit) dispatch({ type: "addKit", kit, intent: res.intent });
        }
      } catch (e) {
        dispatch({ type: "chatPush", msg: { id: nextId(), role: "bot", local: true, text: e instanceof Error ? e.message : "Não consegui responder agora. Tente de novo." } });
      } finally {
        dispatch({ type: "chatPending", pending: false });
        force((n) => n + 1);
      }
    },
    [dispatch, search, storeId],
  );

  // primeira abertura: boas-vindas e, se veio da busca, já envia a frase
  useEffect(() => {
    if (started.current) return;
    started.current = true;
    if (chat.messages.length === 0) {
      dispatch({ type: "chatPush", msg: { id: nextId(), role: "bot", local: true,
        text: `Oi, ${PERSONA.firstName}! Escreva do seu jeito o que você precisa e, se quiser, quanto pretende gastar. Eu monto 3 opções de kit, comparo o total com entrega e ajudo a repor o que você já usa.` } });
    }
    if (initial) void send(initial);
  }, [initial, chat.messages.length, dispatch, send]);

  useEffect(() => {
    bottom.current?.scrollIntoView?.({ block: "end" });
  }, [chat.messages.length, chat.pending]);

  const submit = (e: FormEvent) => {
    e.preventDefault();
    const t = text;
    setText("");
    void send(t);
  };

  const last = chat.messages[chat.messages.length - 1];
  const chips = last?.role === "bot" && !chat.pending ? last.res?.suggestions ?? (chat.messages.length <= 1 ? WELCOME_SUGGESTIONS : []) : [];
  const engine = search.engine;

  return (
    <div className="screen chat" style={{ background: "var(--bg)" }}>
      <header className="bar blue chat-head">
        <button className="icon-btn" onClick={pop} aria-label="Voltar"><Icon name="back" /></button>
        <div className="chat-title">
          <b>Assistente de compras</b>
          <small title={engine === "graphrag" ? "Motor GraphRAG local (treinado do zero no catálogo)" : "Servidor do GraphRAG não encontrado: usando o motor simulado de reserva"}>
            {engine === "graphrag" ? "Motor: GraphRAG local" : "Motor simulado (reserva)"}
          </small>
        </div>
        <button className="icon-btn" aria-label="Nova conversa" title="Nova conversa" onClick={() => { dispatch({ type: "chatReset" }); started.current = false; force((n) => n + 1); }}>
          <Icon name="repeat" />
        </button>
        <BasketButton />
      </header>

      <div className="scroll chat-scroll" aria-live="polite">
        <div className="chat-list">
          {chat.messages.map((m, i) => (
            <Message key={m.id} m={m} isLast={i === chat.messages.length - 1} onSend={send} storeName={store?.name ?? null} push={push} />
          ))}
          {chat.pending ? (
            <div className="bubble bot typing" role="status" aria-label="Montando a resposta"><span /><span /><span /></div>
          ) : null}
          <div ref={bottom} />
        </div>
      </div>

      {chips.length ? (
        <div className="chat-chips" aria-label="Sugestões">
          {chips.map((c) => (
            <button key={c} className="chip" onClick={() => void send(c)}>{c}</button>
          ))}
        </div>
      ) : null}
      <form className="composer" onSubmit={submit} role="search">
        <label className="sr-only" htmlFor="chat-q">Mensagem</label>
        <input id="chat-q" value={text} onChange={(e) => setText(e.target.value)} placeholder="Escreva aqui, do seu jeito" autoComplete="off" enterKeyHint="send" />
        <button className="send" type="submit" aria-label="Enviar" disabled={!text.trim() || chat.pending}><Icon name="send" size={22} /></button>
      </form>
    </div>
  );
}

function Message({ m, isLast, onSend, storeName, push }: { m: ChatMsg; isLast: boolean; onSend: (q: string) => void; storeName: string | null; push: ReturnType<typeof useNav>["push"] }) {
  if (m.role === "user") {
    return (
      <div className="msg user">
        <div className="bubble user">{m.text}</div>
        <PersonaAvatar size={28} />
      </div>
    );
  }
  return (
    <div className="msg bot">
      <span className="bot-ico"><Icon name="sparkle" size={18} /></span>
      <div className="bot-col">
        <div className={`bubble bot ${m.local ? "local" : ""}`}>{m.text}</div>
        {m.res ? <BotBody res={m.res} isLast={isLast} onSend={onSend} storeName={storeName} push={push} /> : null}
      </div>
    </div>
  );
}

function BotBody({ res, isLast, onSend, storeName, push }: { res: SearchResponse; isLast: boolean; onSend: (q: string) => void; storeName: string | null; push: ReturnType<typeof useNav>["push"] }) {
  const a = res.action as ChatAction | undefined;
  return (
    <>
      {res.safety.decision === "caution" && res.safety.message ? <div className="note warn"><Icon name="alert" size={18} /><p>{res.safety.message}</p></div> : null}

      {res.closestKit && res.kitsStatus === "none_in_budget" ? (
        <div className="kit-strip"><KitCard kit={res.closestKit} onOpen={() => push({ name: "kit", kit: res.closestKit!, intent: res.intent })} overBudgetBy={res.intent.budgetCents != null ? res.closestKit.totalCents - res.intent.budgetCents : undefined} /></div>
      ) : null}
      {res.kits.length && a?.type !== "delivery_quote" && a?.type !== "swap_options" && a?.type !== "show_similars" ? (
        <>
          {res.intent.storeId && storeName ? <p className="chat-meta"><Icon name="store" size={16} /> Só com o estoque da {storeName}</p> : null}
          <div className="kit-strip" tabIndex={0} aria-label="Deslize para ver os kits">
            {res.kits.map((k) => <KitCard key={k.id} kit={k} onOpen={() => push({ name: "kit", kit: k, intent: res.intent })} />)}
          </div>
        </>
      ) : null}
      {res.notes.filter((n) => n !== res.reply).map((n) => <div key={n} className="note"><Icon name="info" size={18} /><p>{n}</p></div>)}

      {a?.type === "show_products" && res.products.length ? (
        <div className="hscroll chat-products">{res.products.slice(0, 8).map((p) => <ProductCard key={p.id} product={p} />)}</div>
      ) : null}
      {res.kitsStatus === "not_applicable" && !a?.type?.match(/show_products|show_similars|open_refill|delivery/) && res.products.length ? (
        <div className="hscroll chat-products">{res.products.slice(0, 8).map((p) => <ProductCard key={p.id} product={p} />)}</div>
      ) : null}

      {a?.type === "open_refill" ? (
        <button className="btn primary block" onClick={() => push({ name: "refill" })}><Icon name="pill" size={20} /> Abrir Meus medicamentos</button>
      ) : null}
      {a?.type === "delivery_quote" ? <DeliveryQuote action={a} push={push} /> : null}
      {a?.type === "delivery_info" ? <button className="btn outline blue block" onClick={() => push({ name: "stores" })}><Icon name="store" size={20} /> Escolher a loja de retirada</button> : null}
      {a?.type === "swap_options" ? <SwapBlock res={res} action={a} onSend={onSend} /> : null}
      {a?.type === "show_similars" ? <SimilarsBlock res={res} action={a} push={push} /> : null}

      {res.clarification && isLast ? (
        <div className="panel" aria-label="Pergunta rápida">
          <b>{res.clarification.question}</b>
          <div className="chips">
            {res.clarification.options.map((o) => <button key={o.value} className="chip" onClick={() => onSend(`minha pele é ${(o.value as SkinType)}`)}>{o.label}</button>)}
          </div>
        </div>
      ) : null}
    </>
  );
}

function DeliveryQuote({ action, push }: { action: Extract<ChatAction, { type: "delivery_quote" }>; push: ReturnType<typeof useNav>["push"] }) {
  const pref = PERSONA.preferences.deliveryPriority[0];
  const cheapest = Math.min(...action.options.map((o) => o.totalCents));
  return (
    <section className="panel" aria-label={`Total do kit ${TIER_LABEL[action.tier]} por forma de entrega`}>
      <b>Total com entrega · Kit {TIER_LABEL[action.tier]}</b>
      <table className="quote">
        <tbody>
          {action.options.map((o) => (
            <tr key={o.id} className={o.totalCents === cheapest ? "best" : ""}>
              <th scope="row">{o.label}<small>{o.eta}{o.id === pref ? " · sua preferência" : ""}</small></th>
              <td>{o.feeCents === 0 ? "sem frete" : `frete ${money(o.feeCents)}`}</td>
              <td><b>{money(o.totalCents)}</b></td>
            </tr>
          ))}
        </tbody>
      </table>
      <button className="btn outline blue block" onClick={() => push({ name: "cart" })}>Ir para a cesta</button>
    </section>
  );
}

function SwapBlock({ res, action, onSend }: { res: SearchResponse; action: Extract<ChatAction, { type: "swap_options" }>; onSend: (q: string) => void }) {
  const { commerce, search } = useServices();
  const { dispatch, chat } = useApp();
  const [busy, setBusy] = useState<string | null>(null);
  const [done, setDone] = useState<string | null>(null);
  const prods = useAsync(() => commerce.products(action.options.map((o) => o.productId)), [commerce, action]);
  const kit = res.kits.find((k) => k.id === action.kitId) ?? res.kits[0];
  if (!kit) return null;
  const cur = kit.items.find((i) => i.step === action.step)?.product;
  const swap = async (productId: string) => {
    setBusy(productId);
    try {
      const nk: Kit = await search.swap(kit, action.step as StepId, productId, res.intent);
      const ctx = chat.context;
      if (ctx) {
        const kits = ctx.kits.map((k) => k.id === nk.id ? { ...k, totalCents: nk.totalCents, items: k.items.map((it) => it.step === action.step ? { ...it, productId } : it) } : k);
        dispatch({ type: "chatContext", context: { ...ctx, kits } });
      }
      dispatch({ type: "chatPush", msg: { id: nextId(), role: "bot", text: `Troquei ${STEP_LABEL[action.step].toLowerCase()} no kit ${TIER_LABEL[nk.tier]}. Ele agora custa ${money(nk.totalCents)}.`, res: { ...res, kits: [nk], action: { type: "show_kits" }, notes: [], suggestions: ["Total com entrega", "Trocar outro item"] } } });
      setDone(productId);
    } catch (e) {
      dispatch({ type: "toast", text: e instanceof Error ? e.message : "Não consegui trocar." });
    } finally {
      setBusy(null);
    }
  };
  return (
    <section className="panel" aria-label="Opções de troca">
      {cur ? <small style={{ color: "var(--text-2)" }}>Agora: {cur.name} · {money(cur.priceCents)}</small> : null}
      {(prods.data ?? []).map((p) => {
        const d = action.options.find((o) => o.productId === p.id)?.deltaCents ?? 0;
        return (
          <div key={p.id} className="swap-opt">
            <ProductImage product={p} size={44} />
            <span className="grow"><b>{p.name}</b><small>{p.brand} · {delta(d)}</small></span>
            <button className="btn outline blue" disabled={busy !== null || done === p.id} onClick={() => void swap(p.id)}>{done === p.id ? "Trocado" : busy === p.id ? "Trocando…" : "Trocar"}</button>
          </div>
        );
      })}
      <button className="link plain" onClick={() => onSend("mais barato")}>Ver o kit inteiro mais barato</button>
    </section>
  );
}

const PRESENTATION: Record<string, string> = { referencia: "Referência", generico: "Genérico", similar: "Similar" };

export function SimilarCard({ o, product, stores, push }: { o: SimilarOption; product: SearchResponse["products"][number]; stores: Map<string, string>; push: ReturnType<typeof useNav>["push"] }) {
  const where = o.storeIdsWithStock.slice(0, 2).map((id) => stores.get(id) ?? id);
  return (
    <div className="swap-opt">
      <ProductImage product={product} size={48} />
      <span className="grow">
        <b>{product.name}</b>
        <small>
          {o.kind === "equivalente"
            ? <>{PRESENTATION[o.presentation ?? "similar"]} · mesmo princípio ativo{o.sameDose ? " e dose" : ""}</>
            : <>{product.brand}</>} · {money(product.priceCents)} ({delta(o.deltaCents)})
        </small>
        <small className={o.inStock ? "ok" : "off"}>{o.inStock ? "Em estoque na sua loja" : where.length ? `Sem estoque aqui · tem na ${where.join(" e na ")}` : "Sem estoque"}</small>
      </span>
      <button className="btn outline blue" onClick={() => push({ name: "product", id: product.id })}>Ver</button>
    </div>
  );
}

function SimilarsBlock({ res, action, push }: { res: SearchResponse; action: Extract<ChatAction, { type: "show_similars" }>; push: ReturnType<typeof useNav>["push"] }) {
  const { commerce } = useServices();
  const byId = new Map(res.products.map((p) => [p.id, p]));
  const stores = useAsync(async () => new Map((await commerce.storesFor([])).map((s) => [s.store.id, s.store.name])), [commerce]);
  const isMed = action.options.some((o) => o.kind === "equivalente");
  return (
    <section className="panel" aria-label="Opções equivalentes">
      {action.options.map((o) => {
        const p = byId.get(o.productId);
        return p ? <SimilarCard key={o.productId} o={o} product={p} stores={stores.data ?? new Map()} push={push} /> : null;
      })}
      {isMed ? (
        <>
          <div className="note"><Icon name="info" size={18} /><p>Mesmo princípio ativo e mesma dose, conforme a sua receita.</p></div>
          <button className="btn primary block" onClick={() => push({ name: "refill" })}><Icon name="pill" size={20} /> Abrir Meus medicamentos</button>
        </>
      ) : null}
    </section>
  );
}
