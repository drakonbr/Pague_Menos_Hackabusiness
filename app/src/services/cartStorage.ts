// #48: cesta, receitas anexadas (simuladas) e pedidos ficam neste aparelho e sobrevivem a recarregar a página.
import type { FulfillmentMode, Intent, Kit, Product, Store } from "../contracts/types";
import type { CartLine, Order } from "../state/app";
import { PRODUCT_BY_ID } from "./mock/catalogData";

/** #43 (RDC 44/2009): a receita limita a quantidade; neste protótipo, a receita simulada vale por 2 caixas por item. */
export const RX_MAX_QTY = 2;
const KEY = "pm.session.v1";
const MAX_ORDERS = 20;

export interface SavedSession {
  lines: CartLine[];
  rxDocs: string[];
  orders: Order[];
  walletPendingCents: number;
  store: Store | null;
  mode: FulfillmentMode | null;
}

const isNum = (x: unknown): x is number => typeof x === "number" && Number.isFinite(x);
const isStr = (x: unknown): x is string => typeof x === "string" && x.length > 0;
const isObj = (x: unknown): x is Record<string, unknown> => !!x && typeof x === "object" && !Array.isArray(x);

/** Produto com os dados de hoje do catálogo (preço e estoque); só as imagens guardadas, se houver, são mantidas. */
function freshProduct(saved: unknown): Product | null {
  const base = PRODUCT_BY_ID.get(isObj(saved) && isStr(saved.id) ? saved.id : "");
  if (!base) return null;
  const imgs = isObj(saved) ? saved.images : undefined;
  return Array.isArray(imgs) ? { ...base, images: imgs as Product["images"] } : base;
}

/** Kit só entra inteiro: todos os campos que as telas leem, e os produtos de hoje; se faltar algo, descarta o kit. */
function cleanKit(k: unknown): Kit | null {
  if (!isObj(k) || !isStr(k.id) || !isStr(k.tier) || !isStr(k.title) || !isStr(k.goal) || !Array.isArray(k.items) || !k.items.length) return null;
  if (![k.itemsTotalCents, k.discountPct, k.discountCents, k.totalCents, k.listTotalCents, k.cashbackCents].every(isNum)) return null;
  if (!Array.isArray(k.alerts) || typeof k.rationale !== "string" || typeof k.withinBudget !== "boolean") return null;
  const items: Kit["items"] = [];
  for (const it of k.items) {
    if (!isObj(it) || !isStr(it.step) || typeof it.reason !== "string") return null;
    const product = freshProduct(it.product);
    if (!product) return null;
    items.push({ ...(it as unknown as Kit["items"][number]), product });
  }
  // preço de algum item mudou depois de guardado: a soma do kit guardado não bate mais, então o kit não volta
  if (items.reduce((t, i) => t + i.product.priceCents, 0) !== k.itemsTotalCents) return null;
  return { ...(k as unknown as Kit), items };
}

/** Só entra linha inteira e com produtos que ainda existem no catálogo; os dados guardados nunca vão direto para a tela. */
function cleanLine(l: unknown): CartLine | null {
  if (!isObj(l) || !isStr(l.key) || !isNum(l.qty) || l.qty < 1) return null;
  const qty = Math.min(Math.floor(l.qty), 9);
  if (l.type === "product") {
    const p = freshProduct(l.product);
    return p ? { key: l.key, type: "product", product: p, qty: Math.min(qty, p.rx ? RX_MAX_QTY : 9) } : null;
  }
  if (l.type === "kit") {
    const kit = cleanKit(l.kit);
    if (!kit || !isObj(l.intent) || !(l.everyDays === 0 || l.everyDays === 30 || l.everyDays === 60)) return null;
    return { key: l.key, type: "kit", kit, intent: l.intent as unknown as Intent, qty, everyDays: l.everyDays };
  }
  return null;
}

/** Pedido só entra com todas as linhas válidas e os totais numéricos. */
function cleanOrder(o: unknown): Order | null {
  if (!isObj(o) || !isStr(o.id) || !isStr(o.createdAt) || !Array.isArray(o.lines) || !o.lines.length) return null;
  if (![o.itemsCents, o.feeCents, o.totalCents, o.cashbackCents].every(isNum) || typeof o.payment !== "string" || typeof o.status !== "string") return null;
  if (!(o.mode === "retirada" || o.mode === "expressa" || o.mode === "agendada")) return null;
  const lines = o.lines.map(cleanLine);
  if (lines.some((x) => x === null)) return null;
  return { ...(o as unknown as Order), lines: lines as CartLine[] };
}

export function loadSession(): Partial<SavedSession> {
  try {
    const raw = JSON.parse(localStorage.getItem(KEY) ?? "null") as Partial<SavedSession> | null;
    if (!raw || typeof raw !== "object") return {};
    const lines = (Array.isArray(raw.lines) ? raw.lines : []).map(cleanLine).filter((l): l is CartLine => l !== null);
    const inCart = new Set(lines.flatMap((l) => (l.type === "kit" ? l.kit.items.map((i) => i.product.id) : [l.product.id])));
    return {
      lines,
      rxDocs: (Array.isArray(raw.rxDocs) ? raw.rxDocs : []).filter((id): id is string => typeof id === "string" && inCart.has(id)),
      orders: (Array.isArray(raw.orders) ? raw.orders : []).map(cleanOrder).filter((o): o is Order => o !== null).slice(0, MAX_ORDERS),
      walletPendingCents: isNum(raw.walletPendingCents) ? raw.walletPendingCents : 0,
      store: raw.store && typeof raw.store.id === "string" ? raw.store : null,
      mode: raw.mode === "retirada" || raw.mode === "expressa" || raw.mode === "agendada" ? raw.mode : null,
    };
  } catch {
    return {}; // armazenamento bloqueado ou conteúdo estragado: começa vazio
  }
}

export function saveSession(s: SavedSession): void {
  try {
    localStorage.setItem(KEY, JSON.stringify({ ...s, orders: s.orders.slice(0, MAX_ORDERS) }));
  } catch {
    /* sem armazenamento ou cheio: vale só até recarregar */
  }
}

export function clearSession(): void {
  try {
    localStorage.removeItem(KEY);
  } catch {
    /* nada a apagar */
  }
}
