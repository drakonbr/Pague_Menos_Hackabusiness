import { afterEach, describe, expect, it } from "vitest";
import { clearSession, loadSession, saveSession, type SavedSession } from "../src/services/cartStorage";
import { PRODUCTS } from "../src/services/mock/catalogData";
import { createMockSearchService } from "../src/services/mock/mockSearchService";
import { initialState, reducer, type CartLine } from "../src/state/app";

// #48: cesta e pedidos sobrevivem a recarregar a página
const fake = () => {
  const m = new Map<string, string>();
  (globalThis as { localStorage?: unknown }).localStorage = {
    getItem: (k: string) => m.get(k) ?? null, setItem: (k: string, v: string) => void m.set(k, v), removeItem: (k: string) => void m.delete(k),
  };
  return m;
};
const line = (i: number): CartLine => ({ key: `p:${PRODUCTS[i].id}`, type: "product", product: PRODUCTS[i], qty: 2 });
const empty: SavedSession = { lines: [], rxDocs: [], orders: [], walletPendingCents: 0, store: null, mode: null };

describe("sessão guardada no aparelho", () => {
  afterEach(() => { delete (globalThis as { localStorage?: unknown }).localStorage; });

  it("guarda e devolve a cesta, a receita anexada, o pedido e o modo de entrega", () => {
    fake();
    const rx = PRODUCTS.find((p) => p.rx)!;
    const order = { id: "o1", createdAt: "2026-10-24", lines: [line(0)], itemsCents: 100, feeCents: 0, totalCents: 100, cashbackCents: 5, mode: "retirada" as const, storeName: "Madalena", payment: "pix", status: "ok" };
    saveSession({ ...empty, lines: [line(0), { key: `p:${rx.id}`, type: "product", product: rx, qty: 1 }], rxDocs: [rx.id], orders: [order], walletPendingCents: 5, mode: "retirada" });
    const s = loadSession();
    expect(s.lines).toHaveLength(2);
    expect(s.lines![0].qty).toBe(2);
    expect(s.rxDocs).toEqual([rx.id]);
    expect(s.orders).toHaveLength(1);
    expect(s.walletPendingCents).toBe(5);
    expect(s.mode).toBe("retirada");
  });

  it("descarta linha de produto que não existe mais e receita de quem saiu da cesta", () => {
    const m = fake();
    const ghost = { ...line(0), key: "p:fantasma", product: { ...PRODUCTS[0], id: "fantasma" } };
    m.set("pm.session.v1", JSON.stringify({ ...empty, lines: [ghost, line(1)], rxDocs: ["fantasma", PRODUCTS[1].id, "outro"] }));
    const s = loadSession();
    expect(s.lines!.map((l) => l.key)).toEqual([line(1).key]);
    expect(s.rxDocs).toEqual([PRODUCTS[1].id]);
  });

  it("conteúdo estragado, sem armazenamento ou modo inválido não quebram", () => {
    expect(loadSession()).toEqual({});                       // sem localStorage
    const m = fake();
    m.set("pm.session.v1", "{não é json");
    expect(loadSession()).toEqual({});
    m.set("pm.session.v1", JSON.stringify({ lines: "x", orders: 7, mode: "teletransporte", store: { semId: 1 } }));
    const s = loadSession();
    expect(s.lines).toEqual([]);
    expect(s.orders).toEqual([]);
    expect(s.mode).toBeNull();
    expect(s.store).toBeNull();
    expect(() => saveSession(empty)).not.toThrow();
  });

  it("clearSession apaga e o reducer limpa cesta, pedidos e carteira", () => {
    const m = fake();
    saveSession({ ...empty, lines: [line(0)] });
    clearSession();
    expect(m.has("pm.session.v1")).toBe(false);
    const s = reducer({ ...initialState, lines: [line(0)], walletPendingCents: 9, mode: "retirada" }, { type: "clearSession" });
    expect(s.lines).toEqual([]);
    expect(s.walletPendingCents).toBe(0);
    expect(s.mode).toBeNull();
  });

  it("kit guardado com dado incompleto é descartado, não derruba a tela (#48)", () => {
    const m = fake();
    const bad = { key: "kit:x", type: "kit", qty: 1, everyDays: 0, intent: {}, kit: { id: "k", tier: "economico", title: "t", goal: "g", items: [{ product: { id: PRODUCTS[0].id } }] } };
    const semProduto = { key: "p:z", type: "product", qty: 1, product: { id: PRODUCTS[0].id } };   // produto "fino": volta com os dados do catálogo
    m.set("pm.session.v1", JSON.stringify({ ...empty, lines: [bad, semProduto] }));
    const s = loadSession();
    expect(s.lines!.map((l) => l.key)).toEqual(["p:z"]);
    expect(s.lines![0].type === "product" && s.lines![0].product.images).toBeDefined();
  });

  it("kit inteiro volta com produtos de hoje; pedido com linha estragada é descartado", async () => {
    const m = fake();
    const r = await createMockSearchService({ latencyMs: 0 }).search({ query: "pele oleosa" });
    const kit = r.kits[0];
    const kline: CartLine = { key: "kit:a", type: "kit", kit, intent: r.intent, qty: 3, everyDays: 30 };
    const order = (lines: unknown[]) => ({ id: "o1", createdAt: "2026-10-24", lines, itemsCents: 1, feeCents: 0, totalCents: 1, cashbackCents: 0, mode: "retirada", storeName: null, payment: "pix", status: "ok" });
    m.set("pm.session.v1", JSON.stringify({ ...empty, lines: [kline], orders: [order([kline]), order([null]), order([{ type: "product" }]), { ...order([kline]), totalCents: "x" }] }));
    const s = loadSession();
    expect(s.lines).toHaveLength(1);
    expect(s.lines![0].qty).toBe(3);
    expect(s.orders).toHaveLength(1);
    expect(() => JSON.stringify(s)).not.toThrow();
    // preço de item mudou depois de guardado: a soma do kit guardado não bate, então o kit não volta
    m.set("pm.session.v1", JSON.stringify({ ...empty, lines: [{ ...kline, kit: { ...kit, itemsTotalCents: kit.itemsTotalCents + 100 } }] }));
    expect(loadSession().lines).toEqual([]);
  });
});
