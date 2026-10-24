import { describe, expect, it } from "vitest";
import { discountPct } from "../src/components/ProductCard";
import { feeFor } from "../src/screens/Delivery";
import { PRODUCTS } from "../src/services/mock/catalogData";
import { hasMedicine, shippingBaseCents, type CartLine } from "../src/state/app";
import { REFILL_RULES } from "../src/persona";

// #45 (RDC 96/2008): remédio, com ou sem receita, não tem preço riscado, "Super oferta" nem conta para frete grátis
const meds = PRODUCTS.filter((p) => p.domain === "medicamento");
const other = PRODUCTS.find((p) => p.domain !== "medicamento" && p.priceCents > 3000)!;
const line = (p: typeof meds[number], qty = 1): CartLine => ({ key: `p:${p.id}`, type: "product", product: p, qty });

describe("remédio fora de promoção e do frete grátis", () => {
  it("nenhum remédio tem preço riscado nem desconto no cartão", () => {
    expect(meds.length).toBeGreaterThan(50);
    for (const p of meds) {
      expect(p.listPriceCents).toBe(p.priceCents);
      expect(discountPct(p)).toBe(0);
    }
  });
  it("remédio não conta para o frete grátis; o resto da cesta conta", () => {
    const m = meds.find((p) => !p.rx)!;
    const lines = [line(m, 9), line(other, 1)];
    expect(hasMedicine(lines)).toBe(true);
    expect(shippingBaseCents(lines)).toBe(other.priceCents);
    expect(shippingBaseCents([line(m, 9)])).toBe(0);
    const opt = { id: "x", label: "x", feeCents: 1000, freeFromCents: 15000 } as unknown as Parameters<typeof feeFor>[0];
    expect(feeFor(opt, shippingBaseCents([line(m, 9)]))).toBe(1000);   // 9 caixas de remédio não zeram o frete
  });
  it("a reposição automática não promete frete grátis", () => {
    expect(REFILL_RULES.freeShipping).toBe(false);
  });
});
