import { describe, expect, it } from "vitest";
import chatSrc from "../src/screens/Chat.tsx?raw";
import kitCardSrc from "../src/components/KitCard.tsx?raw";
import refillSrc from "../src/screens/Refill.tsx?raw";
import { hasStockHere } from "../src/refillStock";
import { PERSONA } from "../src/persona";
import { createMockSearchService } from "../src/services/mock/mockSearchService";
import { stockAt } from "../src/services/mock/catalogData";
import type { StoreAvailability } from "../src/contracts/types";

const [a, b] = PERSONA.continuousMedications;
const avail = [{ store: { id: "s01" }, availableIds: [b.productId] }, { store: { id: "s02" }, availableIds: [a.productId, b.productId] }] as unknown as StoreAvailability[];

describe("reposição: estoque da loja (#50)", () => {
  it("item que a loja não tem fica fora até escolher um equivalente", () => {
    expect(hasStockHere({ productId: a.productId, avail, storeId: "s01" })).toBe(false);
    expect(hasStockHere({ productId: b.productId, avail, storeId: "s01" })).toBe(true);
    expect(hasStockHere({ productId: a.productId, chosenId: "p999", avail, storeId: "s01" })).toBe(true);     // escolheu um equivalente
    expect(hasStockHere({ productId: a.productId, chosenId: a.productId, avail, storeId: "s01" })).toBe(false); // "escolheu" o próprio
    expect(hasStockHere({ productId: a.productId, avail, storeId: "s02" })).toBe(true);
  });
  it("sem loja escolhida vale o estoque central", () => {
    expect(hasStockHere({ productId: a.productId, storeId: null, centralStockQty: 5 })).toBe(true);
    expect(hasStockHere({ productId: a.productId, storeId: null, centralStockQty: 0 })).toBe(false);
  });
  it("a tela deixa o item fora da conta e avisa", () => {
    expect(refillSrc).toContain("hasStockHere");
    expect(refillSrc).toContain("fora da conta");
    expect(refillSrc).toContain("Escolha um equivalente em estoque");
  });
});

describe("reposição: troca por equivalente é com o farmacêutico (#46)", () => {
  it("o equivalente de remédio de receita vem marcado e a tela diz isso", async () => {
    const svc = createMockSearchService({ latencyMs: 0 });
    const storeWithout = ["s01", "s02", "s03", "s04", "s05", "s06", "s07", "s08"].find((s) => stockAt(a.productId, s) === 0) ?? "s01";
    const r = await svc.similars(a.productId, storeWithout);
    expect(r.options.length).toBeGreaterThan(0);
    expect(r.options.every((o) => o.needsPharmacistConfirmation)).toBe(true);
    expect(r.options.every((o) => o.sameActive && o.sameDose !== false)).toBe(true);
    expect(refillSrc).toContain("só vale depois que o farmacêutico confirmar");
    expect(refillSrc).toContain("o.sameDose !== false");
    // o mesmo aviso e o mesmo filtro no chat (#46): quem lê só o chat não vê a troca como pronta
    expect(chatSrc).toContain('o.kind !== "equivalente" || o.sameDose !== false');
    expect(chatSrc).toContain("só vale depois que o farmacêutico confirmar");
    expect(chatSrc).not.toContain("conforme a sua receita");
    expect(refillSrc).toContain("Troca por equivalente: sujeita à confirmação do farmacêutico");
  });
});

describe("cartão de kit mostra o produto (#51)", () => {
  it("lista o nome do produto, não só o tipo", () => {
    expect(kitCardSrc).toContain("<b>{i.product.name}</b>");
    expect(kitCardSrc).not.toContain("i.product.productType");
  });
});
