import { afterEach, describe, expect, it } from "vitest";
import paymentSrc from "../src/screens/Payment.tsx?raw";
import { loadSession, saveSession } from "../src/services/cartStorage";
import { PRODUCTS } from "../src/services/mock/catalogData";
import { createMockSearchService } from "../src/services/mock/mockSearchService";
import { RX_MAX_QTY, initialState, maxQty, reducer, type CartLine } from "../src/state/app";

// #43 (RDC 44/2009): receita limita a quantidade; controlado não vai a distância; farmacêutico avalia antes de separar
// #44 (RDC 96/2008): pelo sintoma, remédio de venda livre vem antes do de receita
const rx = PRODUCTS.find((p) => p.rx)!;
const otc = PRODUCTS.find((p) => p.domain === "medicamento" && !p.rx)!;

describe("quantidade de remédio com receita (#43)", () => {
  const add = (s: typeof initialState, p: typeof rx) => reducer(s, { type: "addProduct", product: p, confirmed: true });
  it("o + para no limite da receita e avisa; sem receita segue até 9", () => {
    let s = initialState;
    for (let i = 0; i < 5; i++) s = add(s, rx);
    expect(s.lines[0].qty).toBe(RX_MAX_QTY);
    expect(s.toast?.text).toMatch(/Limite da receita/);
    let t = initialState;
    for (let i = 0; i < 12; i++) t = add(t, otc);
    expect(t.lines[0].qty).toBe(9);
  });
  it("setQty também respeita o limite", () => {
    const s = add(initialState, rx);
    const up = reducer(s, { type: "setQty", key: s.lines[0].key, qty: 9 });
    expect(up.lines[0].qty).toBe(RX_MAX_QTY);
    expect(maxQty(s.lines[0])).toBe(RX_MAX_QTY);
  });
  it("controlado não entra na cesta", () => {
    const controlado = { ...rx, rx: "receita_controlada" } as unknown as typeof rx;
    const s = reducer(initialState, { type: "addProduct", product: controlado, confirmed: true });
    expect(s.lines).toEqual([]);
    expect(s.toast?.text).toMatch(/controlado/);
  });
  it("pedido com receita nasce aguardando o farmacêutico", () => {
    expect(paymentSrc).toContain("Aguardando avaliação da receita pelo farmacêutico");
    expect(paymentSrc).toMatch(/rxProducts\(lines\)\.length \? "Aguardando/);
  });
  describe("cesta guardada de antes do limite", () => {
    afterEach(() => { delete (globalThis as { localStorage?: unknown }).localStorage; });
    it("volta com a quantidade dentro do limite", () => {
      const m = new Map<string, string>();
      (globalThis as { localStorage?: unknown }).localStorage = { getItem: (k: string) => m.get(k) ?? null, setItem: (k: string, v: string) => void m.set(k, v), removeItem: (k: string) => void m.delete(k) };
      const l: CartLine = { key: `p:${rx.id}`, type: "product", product: rx, qty: 9 };
      saveSession({ lines: [l], rxDocs: [], orders: [], walletPendingCents: 0, store: null, mode: null });
      expect(loadSession().lines![0].qty).toBe(RX_MAX_QTY);
    });
  });
});

describe("busca por sintoma no simulador (#44)", () => {
  it("remédio de venda livre vem antes do de receita", async () => {
    const svc = createMockSearchService({ latencyMs: 0 });
    for (const q of ["remédio para enjoo", "estou com azia", "remédio para alergia"]) {
      const r = await svc.search({ query: q });
      const order = r.products.map((p) => (p.rx ? "R" : "o")).join("");
      expect(order, q).toContain("o");
      expect(order, q).toBe([...order].sort((a, b) => Number(a === "R") - Number(b === "R")).join(""));
    }
  });
});
