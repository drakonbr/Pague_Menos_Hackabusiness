// Estado do app (só na memória da sessão: recarregar a página zera tudo, de propósito).
import { createContext, useCallback, useContext, useMemo, useReducer, type ReactNode } from "react";
import type { ChatContext, FulfillmentMode, Intent, Kit, Product, SearchResponse, Store } from "../contracts/types";
import { PERSONA, type ConsentFlags } from "../persona";
import { readExternalChoice, saveExternalChoice } from "../services/consentStorage";
import { externalLanguage } from "../services/searchService";

export type SubscriptionDays = 0 | 30 | 60;

export type CartLine =
  | { key: string; type: "kit"; kit: Kit; intent: Intent; qty: number; everyDays: SubscriptionDays }
  | { key: string; type: "product"; product: Product; qty: number };

export interface Order {
  id: string;
  createdAt: string;
  lines: CartLine[];
  itemsCents: number;
  feeCents: number;
  totalCents: number;
  cashbackCents: number;
  mode: FulfillmentMode;
  storeName: string | null;
  payment: string;
  status: string;
}

/** Mensagem da conversa na barra de busca. `res` guarda a resposta completa do motor (kits, produtos, ação). */
export interface ChatMsg {
  id: string;
  role: "user" | "bot";
  text: string;
  res?: SearchResponse;
  /** Texto exibido pelo app, não pelo motor (boas-vindas, erro). */
  local?: boolean;
}

export type RxAsk =
  | { kind: "product"; product: Product }
  | { kind: "kit"; kit: Kit; intent: Intent; everyDays: SubscriptionDays };

interface State {
  consent: ConsentFlags;
  chat: { messages: ChatMsg[]; context: ChatContext | null; pending: boolean };
  /** Reposição automática por produto (premissas fictícias). */
  refillAuto: Record<string, boolean>;
  /** Equivalente escolhido na reposição, por item; só vale na loja em que foi escolhido (o estoque era dela). */
  refillPick: { storeId: string | null; picks: Record<string, Product> };
  /** Receita SIMULADA anexada nesta sessão (reposição). */
  rxAttached: boolean;
  /** Item com receita esperando a pessoa confirmar o aviso antes de entrar na cesta (#28). */
  rxAsk: RxAsk | null;
  /** Ids de produto da cesta com receita (simulada) anexada para este pedido. */
  rxDocs: string[];
  lines: CartLine[];
  favorites: string[]; // ids de produto
  favoriteKits: Kit[];
  recents: string[];
  store: Store | null; // loja de retirada/expressa escolhida
  mode: FulfillmentMode | null;
  orders: Order[];
  walletPendingCents: number;
  toast: { text: string; action?: "cart" } | null;
}

type Action =
  | { type: "chatPush"; msg: ChatMsg }
  | { type: "chatContext"; context: ChatContext | null }
  | { type: "chatPending"; pending: boolean }
  | { type: "chatReset" }
  | { type: "setConsent"; key: keyof ConsentFlags; value: boolean }
  | { type: "setRefillAuto"; id: string; on: boolean }
  | { type: "refillPick"; id: string; product: Product | null; storeId: string | null }
  | { type: "setRx"; on: boolean }
  | { type: "addKit"; kit: Kit; intent: Intent; everyDays?: SubscriptionDays; confirmed?: boolean }
  | { type: "replaceKit"; key: string; kit: Kit; intent: Intent }
  | { type: "setEvery"; key: string; everyDays: SubscriptionDays }
  | { type: "addProduct"; product: Product; confirmed?: boolean }
  | { type: "rxConfirm" }
  | { type: "rxCancel" }
  | { type: "attachRx"; ids: string[] }
  | { type: "detachRx"; id: string }
  | { type: "setQty"; key: string; qty: number }
  | { type: "remove"; key: string }
  | { type: "toggleFav"; id: string }
  | { type: "toggleFavKit"; kit: Kit }
  | { type: "recent"; q: string }
  | { type: "removeRecent"; q: string }
  | { type: "clearRecents" }
  | { type: "setStore"; store: Store | null }
  | { type: "setMode"; mode: FulfillmentMode | null }
  | { type: "placeOrder"; order: Order }
  | { type: "toast"; text: string; action?: "cart" }
  | { type: "hideToast" };

const MAX_QTY = 9;
export const kitSignature = (kit: Kit) => kit.items.map((i) => i.product.id).sort().join("-");
const kitKey = (kit: Kit) => `kit:${kit.tier}:${kitSignature(kit)}`;

/** Produtos de uma linha da cesta (o próprio produto, ou os itens do kit). */
export const lineProducts = (l: CartLine): Product[] => (l.type === "kit" ? l.kit.items.map((i) => i.product) : [l.product]);
/** Produtos únicos da cesta que exigem receita (avulsos e dentro de kits). */
export const rxProducts = (lines: CartLine[]): Product[] => {
  const seen = new Map<string, Product>();
  for (const l of lines) for (const p of lineProducts(l)) if (p.rx) seen.set(p.id, p);
  return [...seen.values()];
};
/** Itens com receita ainda sem receita anexada: enquanto houver algum, não se paga. */
export const rxPending = (lines: CartLine[], rxDocs: string[]): Product[] => rxProducts(lines).filter((p) => !rxDocs.includes(p.id));

/** Troca as linhas da cesta e esquece a receita de quem saiu dela (voltar a pôr pede a receita de novo). */
const withLines = (s: State, lines: CartLine[]): State => {
  const ids = new Set(rxProducts(lines).map((p) => p.id));
  return { ...s, lines, rxDocs: s.rxDocs.filter((id) => ids.has(id)) };
};

export function reducer(s: State, a: Action): State {
  switch (a.type) {
    case "chatPush":
      return { ...s, chat: { ...s.chat, messages: [...s.chat.messages, a.msg] } };
    case "chatContext":
      return { ...s, chat: { ...s.chat, context: a.context } };
    case "chatPending":
      return { ...s, chat: { ...s.chat, pending: a.pending } };
    case "chatReset":
      return { ...s, chat: { messages: [], context: null, pending: false } };
    case "setConsent":
      return { ...s, consent: { ...s.consent, [a.key]: a.value } };
    case "setRefillAuto":
      return { ...s, refillAuto: { ...s.refillAuto, [a.id]: a.on }, toast: { text: a.on ? "Reposição automática ativada (simulada)" : "Reposição automática desativada" } };
    case "refillPick": {
      const base = s.refillPick.storeId === a.storeId ? { ...s.refillPick.picks } : {};
      if (a.product) base[a.id] = a.product;
      else delete base[a.id];
      return { ...s, refillPick: { storeId: a.storeId, picks: base } };
    }
    case "setRx":
      return { ...s, rxAttached: a.on };
    case "addKit": {
      if (!a.confirmed && a.kit.items.some((i) => i.product.rx))
        return { ...s, rxAsk: { kind: "kit", kit: a.kit, intent: a.intent, everyDays: a.everyDays ?? 0 } };
      const key = kitKey(a.kit);
      const found = s.lines.find((l) => l.key === key);
      const lines = found
        ? s.lines.map((l) => (l.key === key ? { ...l, qty: Math.min(MAX_QTY, l.qty + 1) } : l))
        : [...s.lines, { key, type: "kit" as const, kit: a.kit, intent: a.intent, qty: 1, everyDays: a.everyDays ?? 0 }];
      return { ...s, lines, toast: { text: "Kit adicionado à cesta", action: "cart" } };
    }
    case "replaceKit":   // troca de loja na entrega: a receita de quem saiu é esquecida; a do novo item fica pendente
      return withLines(s, s.lines.map((l) => (l.key === a.key && l.type === "kit" ? { ...l, kit: a.kit, intent: a.intent, key: kitKey(a.kit) } : l)));
    case "setEvery":
      return { ...s, lines: s.lines.map((l) => (l.key === a.key && l.type === "kit" ? { ...l, everyDays: a.everyDays } : l)) };
    case "addProduct": {
      if (!a.confirmed && a.product.rx) return { ...s, rxAsk: { kind: "product", product: a.product } };
      const key = `p:${a.product.id}`;
      const found = s.lines.find((l) => l.key === key);
      const lines = found
        ? s.lines.map((l) => (l.key === key ? { ...l, qty: Math.min(MAX_QTY, l.qty + 1) } : l))
        : [...s.lines, { key, type: "product" as const, product: a.product, qty: 1 }];
      return { ...s, lines, toast: { text: "Produto adicionado à cesta", action: "cart" } };
    }
    case "rxConfirm": {
      const ask = s.rxAsk;
      if (!ask) return s;
      const next = { ...s, rxAsk: null };
      return ask.kind === "product"
        ? reducer(next, { type: "addProduct", product: ask.product, confirmed: true })
        : reducer(next, { type: "addKit", kit: ask.kit, intent: ask.intent, everyDays: ask.everyDays, confirmed: true });
    }
    case "rxCancel":
      return { ...s, rxAsk: null };
    case "attachRx":
      return { ...s, rxDocs: [...new Set([...s.rxDocs, ...a.ids])] };
    case "detachRx":
      return { ...s, rxDocs: s.rxDocs.filter((x) => x !== a.id) };
    case "setQty":
      return withLines(s, s.lines
        .map((l) => (l.key === a.key ? { ...l, qty: Math.max(0, Math.min(MAX_QTY, a.qty)) } : l))
        .filter((l) => l.qty > 0));
    case "remove":
      return withLines(s, s.lines.filter((l) => l.key !== a.key));
    case "toggleFav":
      return { ...s, favorites: s.favorites.includes(a.id) ? s.favorites.filter((x) => x !== a.id) : [...s.favorites, a.id] };
    case "toggleFavKit": {
      const sig = kitSignature(a.kit);
      const has = s.favoriteKits.some((k) => kitSignature(k) === sig);
      return { ...s, favoriteKits: has ? s.favoriteKits.filter((k) => kitSignature(k) !== sig) : [...s.favoriteKits, a.kit] };
    }
    case "recent": {
      const q = a.q.trim();
      if (!q) return s;
      return { ...s, recents: [q, ...s.recents.filter((x) => x.toLowerCase() !== q.toLowerCase())].slice(0, 6) };
    }
    case "removeRecent":
      return { ...s, recents: s.recents.filter((x) => x !== a.q) };
    case "clearRecents":
      return { ...s, recents: [] };
    case "setStore":
      return { ...s, store: a.store };
    case "setMode":
      return { ...s, mode: a.mode };
    case "placeOrder":
      if (rxPending(s.lines, s.rxDocs).length) return s;   // #28: pedido com receita faltando é recusado aqui também
      return {
        ...s,
        lines: [],
        rxDocs: [],
        orders: [a.order, ...s.orders],
        walletPendingCents: s.walletPendingCents + a.order.cashbackCents,
      };
    case "toast":
      return { ...s, toast: { text: a.text, action: a.action } };
    case "hideToast":
      return { ...s, toast: null };
  }
}

export const lineUnitCents = (l: CartLine) => (l.type === "kit" ? l.kit.totalCents : l.product.priceCents);
export const lineListCents = (l: CartLine) => (l.type === "kit" ? l.kit.itemsTotalCents : l.product.listPriceCents);
export const lineTotalCents = (l: CartLine) => lineUnitCents(l) * l.qty;
export const lineUnits = (l: CartLine) => (l.type === "kit" ? l.kit.items.length : 1) * l.qty;
export const lineCashbackCents = (l: CartLine) =>
  (l.type === "kit" ? l.kit.cashbackCents : Math.floor((l.product.priceCents * l.product.cashbackPct) / 100)) * l.qty;
/** Ids de produto únicos na cesta (para checar estoque por loja). */
export const cartProductIds = (lines: CartLine[]) => [
  ...new Set(lines.flatMap((l) => (l.type === "kit" ? l.kit.items.map((i) => i.product.id) : [l.product.id]))),
];

export const initialState: State = {
  consent: PERSONA.privacy.consent,
  chat: { messages: [], context: null, pending: false },
  refillAuto: {},
  refillPick: { storeId: null, picks: {} },
  rxAttached: false,
  rxAsk: null,
  rxDocs: [],
  lines: [],
  favorites: [],
  favoriteKits: [],
  recents: [],
  store: null,
  mode: null,
  orders: [],
  walletPendingCents: 0,
  toast: null,
};

type Api = State & {
  dispatch: (a: Action) => void;
  storeId: string | null;
  count: number;
  itemsCents: number;
  listCents: number;
  cashbackCents: number;
  isFav: (id: string) => boolean;
  isFavKit: (kit: Kit) => boolean;
};

const Ctx = createContext<Api | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [state, dispatchRaw] = useReducer(reducer, initialState, (s: State): State => {
    const saved = readExternalChoice();   // #42: a escolha da pessoa sobrevive a recarregar
    return saved === undefined ? s : { ...s, consent: { ...s.consent, useExternalLanguageService: saved } };
  });
  const dispatch = useCallback((a: Action) => {
    if (a.type === "setConsent" && a.key === "useExternalLanguageService") saveExternalChoice(a.value);
    dispatchRaw(a);
  }, []);
  externalLanguage.allowed = state.consent.useExternalLanguageService !== false;   // #42: vale já na próxima busca
  const api = useMemo<Api>(() => {
    const favSet = new Set(state.favorites);
    const favKits = new Set(state.favoriteKits.map(kitSignature));
    return {
      ...state,
      dispatch,
      storeId: state.store?.id ?? null,
      count: state.lines.reduce((n, l) => n + lineUnits(l), 0),
      itemsCents: state.lines.reduce((t, l) => t + lineTotalCents(l), 0),
      listCents: state.lines.reduce((t, l) => t + lineListCents(l) * l.qty, 0),
      cashbackCents: state.lines.reduce((t, l) => t + lineCashbackCents(l), 0),
      isFav: (id) => favSet.has(id),
      isFavKit: (kit) => favKits.has(kitSignature(kit)),
    };
  }, [state, dispatch]);
  return <Ctx.Provider value={api}>{children}</Ctx.Provider>;
}

export function useApp(): Api {
  const c = useContext(Ctx);
  if (!c) throw new Error("useApp fora do AppProvider");
  return c;
}
