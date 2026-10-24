import { describe, expect, it } from "vitest";
import commerce from "../src/mocks/commerce.mock.json";
import { discountPct } from "../src/components/ProductCard";
import { PRODUCTS, noStrike } from "../src/services/mock/catalogData";
import { withImages } from "../src/services/searchService";
import refillSource from "../src/screens/Refill.tsx?raw";

// #41 (RDC 96/2008): remédio de prescrição não aparece em vitrine nem com preço riscado ("de/por")
describe("remédio com receita (#41)", () => {
  const rx = PRODUCTS.filter((p) => p.rx);
  it("nenhum tem preço riscado nos dados, e a tela nunca calcula desconto para ele", () => {
    expect(rx.length).toBeGreaterThan(10);
    for (const p of rx) {
      expect(p.listPriceCents, p.name).toBe(p.priceCents);
      expect(discountPct(p), p.name).toBe(0);
    }
    const promo = { ...rx[0], listPriceCents: rx[0].priceCents * 2 }; // mesmo que um dado novo traga "de/por"
    expect(discountPct(promo)).toBe(0);
    expect(discountPct({ ...promo, rx: null })).toBeGreaterThan(0);   // e o item sem receita continua mostrando
  });
  it("nenhum está em vitrine", () => {
    const ids = new Set(rx.map((p) => p.id));
    for (const s of commerce.showcases as Array<{ id: string; productIds?: string[] }>)
      expect((s.productIds ?? []).filter((i) => ids.has(i)), s.id).toEqual([]);
  });
  it("o dado que chega de fora (servidor ou ingestão) também perde o preço riscado", () => {
    const vindo = { ...rx[0], listPriceCents: rx[0].priceCents * 3 };
    expect(noStrike(vindo).listPriceCents).toBe(vindo.priceCents);
    expect(withImages(vindo).listPriceCents).toBe(vindo.priceCents);
    const sem = { ...vindo, rx: null };
    expect(noStrike(sem).listPriceCents).toBe(sem.listPriceCents);   // sem receita, a promoção segue como está (#45)
  });
  it("a Reposição automática não risca o preço do remédio (tem desconto de 5%, mas sem \"de/por\")", () => {
    expect(refillSource).not.toMatch(/className="old"/);
  });
});
