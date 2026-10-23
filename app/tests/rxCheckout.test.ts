import { describe, expect, it } from "vitest";
import type { Kit, Product } from "../src/contracts/types";
import { PRODUCTS } from "../src/services/mock/catalogData";
import { initialState, reducer, rxPending } from "../src/state/app";

const rx = PRODUCTS.find((p) => p.rx && p.domain === "medicamento")!;
const free = PRODUCTS.find((p) => !p.rx && p.domain === "medicamento")!;
const kitWith = (items: Product[]): Kit => ({
  id: "k", tier: "economico", title: "t", goal: "dor_de_cabeca", rationale: "", storeId: null, alerts: [],
  items: items.map((product) => ({ step: product.step, product, reason: "", alternativesCount: 0 })),
  totalCents: items.reduce((t, p) => t + p.priceCents, 0), listTotalCents: items.reduce((t, p) => t + p.listPriceCents, 0),
  withinBudget: true, cashbackCents: 0,
} as unknown as Kit);

describe("receita na compra (#28)", () => {
  it("item sem receita entra direto na cesta", () => {
    const s = reducer(initialState, { type: "addProduct", product: free });
    expect(s.lines).toHaveLength(1);
    expect(s.rxAsk).toBeNull();
  });

  it("item com receita pede confirmação antes de entrar; cancelar não adiciona", () => {
    const asked = reducer(initialState, { type: "addProduct", product: rx });
    expect(asked.lines).toHaveLength(0);
    expect(asked.rxAsk).toEqual({ kind: "product", product: rx });
    expect(reducer(asked, { type: "rxCancel" }).lines).toHaveLength(0);
    const ok = reducer(asked, { type: "rxConfirm" });
    expect(ok.lines).toHaveLength(1);
    expect(ok.rxAsk).toBeNull();
  });

  it("kit com remédio de receita também pede confirmação", () => {
    const asked = reducer(initialState, { type: "addKit", kit: kitWith([rx, free]), intent: {} as never });
    expect(asked.rxAsk?.kind).toBe("kit");
    expect(reducer(asked, { type: "rxConfirm" }).lines).toHaveLength(1);
  });

  it("sem a receita anexada não dá para pagar; anexada, libera; pedido feito limpa as receitas", () => {
    const s = reducer(reducer(initialState, { type: "addProduct", product: rx }), { type: "rxConfirm" });
    expect(rxPending(s.lines, s.rxDocs).map((p) => p.id)).toEqual([rx.id]);
    const attached = reducer(s, { type: "attachRx", ids: [rx.id] });
    expect(rxPending(attached.lines, attached.rxDocs)).toEqual([]);
    const detached = reducer(attached, { type: "detachRx", id: rx.id });
    expect(detached.rxDocs).toEqual([]);
    expect(rxPending(detached.lines, detached.rxDocs).map((p) => p.id)).toEqual([rx.id]);
    const done = reducer(attached, { type: "placeOrder", order: { id: "x" } as never });
    expect(done.rxDocs).toEqual([]);
  });
});

describe("receita na compra (#28): cesta muda", () => {
  it("remover o item esquece a receita: pôr de novo pede a receita outra vez", () => {
    let s = reducer(reducer(initialState, { type: "addProduct", product: rx }), { type: "rxConfirm" });
    s = reducer(s, { type: "attachRx", ids: [rx.id] });
    s = reducer(s, { type: "remove", key: s.lines[0].key });
    expect(s.rxDocs).toEqual([]);
    s = reducer(reducer(s, { type: "addProduct", product: rx }), { type: "rxConfirm" });
    expect(rxPending(s.lines, s.rxDocs).map((p) => p.id)).toEqual([rx.id]);
  });
});

describe("receita na compra (#28): quantidade e troca de loja", () => {
  it("zerar a quantidade também esquece a receita", () => {
    let s = reducer(reducer(initialState, { type: "addProduct", product: rx }), { type: "rxConfirm" });
    s = reducer(s, { type: "attachRx", ids: [rx.id] });
    s = reducer(s, { type: "setQty", key: s.lines[0].key, qty: 0 });
    expect(s.lines).toEqual([]);
    expect(s.rxDocs).toEqual([]);
  });

  it("trocar um item do kit (troca de loja) esquece a receita do que saiu e deixa pendente a do que entrou", () => {
    const rx2 = PRODUCTS.find((p) => p.rx && p.domain === "medicamento" && p.id !== rx.id)!;
    let s = reducer(initialState, { type: "addKit", kit: kitWith([rx, free]), intent: {} as never, confirmed: true });
    s = reducer(s, { type: "attachRx", ids: [rx.id] });
    s = reducer(s, { type: "replaceKit", key: s.lines[0].key, kit: kitWith([rx2, free]), intent: {} as never });
    expect(s.rxDocs).toEqual([]);
    expect(rxPending(s.lines, s.rxDocs).map((p) => p.id)).toEqual([rx2.id]);
  });
});

describe("receita na compra (#28): o pedido em si", () => {
  it("pedido com receita faltando é recusado pelo estado, não só pela tela", () => {
    const s = reducer(reducer(initialState, { type: "addProduct", product: rx }), { type: "rxConfirm" });
    const tried = reducer(s, { type: "placeOrder", order: { id: "x", cashbackCents: 0 } as never });
    expect(tried).toBe(s);
    expect(tried.orders).toEqual([]);
  });
});
