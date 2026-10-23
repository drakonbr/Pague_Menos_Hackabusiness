import { describe, expect, it } from "vitest";
import { PRODUCTS } from "../src/services/mock/catalogData";
import { initialState, reducer } from "../src/state/app";

const colemax = PRODUCTS.find((p) => p.name.startsWith("Colemax"))!;

describe("equivalente escolhido na reposição (#29)", () => {
  it("fica guardado na sessão para a mesma loja e some ao desfazer", () => {
    let s = reducer(initialState, { type: "refillPick", id: "p136", product: colemax, storeId: "s01" });
    expect(s.refillPick).toEqual({ storeId: "s01", picks: { p136: colemax } });
    s = reducer(s, { type: "refillPick", id: "p136", product: null, storeId: "s01" });
    expect(s.refillPick.picks).toEqual({});
  });

  it("escolher em outra loja descarta as escolhas da loja anterior (o estoque era dela)", () => {
    let s = reducer(initialState, { type: "refillPick", id: "p136", product: colemax, storeId: "s01" });
    s = reducer(s, { type: "refillPick", id: "p132", product: colemax, storeId: "s04" });
    expect(s.refillPick).toEqual({ storeId: "s04", picks: { p132: colemax } });
  });
});
