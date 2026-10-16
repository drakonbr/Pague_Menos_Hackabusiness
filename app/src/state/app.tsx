// Estado do app (só na memória da sessão: recarregar a página zera tudo, de propósito).
import { createContext, useCallback, useContext, useMemo, useReducer, type ReactNode } from "react";
import type { FulfillmentMode, Intent, Kit, Product, Store } from "../contracts/types";

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

interface State {
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
  | { type: "addKit"; kit: Kit; intent: Intent; everyDays?: SubscriptionDays }
  | { type: "replaceKit"; key: string; kit: Kit; intent: Intent }
  | { type: "setEvery"; key: string; everyDays: SubscriptionDays }
  | { type: "addProduct"; product: Product }
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

function reducer(s: State, a: Action): State {
  switch (a.type) {
    case "addKit": {
      const key = kitKey(a.kit);
      const found = s.lines.find((l) => l.key === key);
      const lines = found
        ? s.lines.map((l) => (l.key === key ? { ...l, qty: Math.min(MAX_QTY, l.qty + 1) } : l))
        : [...s.lines, { key, type: "kit" as const, kit: a.kit, intent: a.intent, qty: 1, everyDays: a.everyDays ?? 0 }];
      return { ...s, lines, toast: { text: "Kit adicionado à cesta", action: "cart" } };
    }
    case "replaceKit":
      return {
        ...s,
        lines: s.lines.map((l) => (l.key === a.key && l.type === "kit" ? { ...l, kit: a.kit, intent: a.intent, key: kitKey(a.kit) } : l)),
      };
    case "setEvery":
      return { ...s, lines: s.lines.map((l) => (l.key === a.key && l.type === "kit" ? { ...l, everyDays: a.everyDays } : l)) };
    case "addProduct": {
      const key = `p:${a.product.id}`;
      const found = s.lines.find((l) => l.key === key);
      const lines = found
        ? s.lines.map((l) => (l.key === key ? { ...l, qty: Math.min(MAX_QTY, l.qty + 1) } : l))
        : [...s.lines, { key, type: "product" as const, product: a.product, qty: 1 }];
      return { ...s, lines, toast: { text: "Produto adicionado à cesta", action: "cart" } };
    }
    case "setQty":
      return {
        ...s,
        lines: s.lines
          .map((l) => (l.key === a.key ? { ...l, qty: Math.max(0, Math.min(MAX_QTY, a.qty)) } : l))
          .filter((l) => l.qty > 0),
      };
    case "remove":
      return { ...s, lines: s.lines.filter((l) => l.key !== a.key) };
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
      return {
        ...s,
        lines: [],
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
export const lineListCents = (l: CartLine) => (l.type === "kit" ? l.kit.listTotalCents : l.product.listPriceCents);
export const lineTotalCents = (l: CartLine) => lineUnitCents(l) * l.qty;
export const lineUnits = (l: CartLine) => (l.type === "kit" ? l.kit.items.length : 1) * l.qty;
export const lineCashbackCents = (l: CartLine) =>
  (l.type === "kit" ? l.kit.cashbackCents : Math.floor((l.product.priceCents * l.product.cashbackPct) / 100)) * l.qty;
/** Ids de produto únicos na cesta (para checar estoque por loja). */
export const cartProductIds = (lines: CartLine[]) => [
  ...new Set(lines.flatMap((l) => (l.type === "kit" ? l.kit.items.map((i) => i.product.id) : [l.product.id]))),
];

const initial: State = {
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
  const [state, dispatchRaw] = useReducer(reducer, initial);
  const dispatch = useCallback((a: Action) => dispatchRaw(a), []);
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
