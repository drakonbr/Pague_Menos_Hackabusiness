import toastSrc from "../src/components/Toast.tsx?raw";
import cartSrc from "../src/screens/Cart.tsx?raw";
import kitSrc from "../src/screens/KitDetail.tsx?raw";
import deliverySrc from "../src/screens/Delivery.tsx?raw";
import productSrc from "../src/screens/ProductPage.tsx?raw";
import moreSrc from "../src/screens/More.tsx?raw";
import homeSrc from "../src/screens/Home.tsx?raw";
import privacySrc from "../src/screens/Privacy.tsx?raw";
import paymentSrc from "../src/screens/Payment.tsx?raw";
import kitCardSrc from "../src/components/KitCard.tsx?raw";
import { describe, expect, it } from "vitest";
import { lowerName } from "../src/services/mock/composer";
import { PRODUCTS } from "../src/services/mock/catalogData";
import { createMockSearchService } from "../src/services/mock/mockSearchService";

const SRC: Record<string, string> = { "components/Toast.tsx": toastSrc, "screens/Cart.tsx": cartSrc, "screens/KitDetail.tsx": kitSrc, "screens/Delivery.tsx": deliverySrc, "screens/ProductPage.tsx": productSrc, "screens/More.tsx": moreSrc, "screens/Home.tsx": homeSrc, "screens/Privacy.tsx": privacySrc, "screens/Payment.tsx": paymentSrc, "components/KitCard.tsx": kitCardSrc };
const src = (f: string) => SRC[f];

describe("achados do teste de usabilidade (#47, #49, #55 a #59)", () => {
  it("#59: nome de ingrediente mantém sigla e letra de vitamina, igual ao motor", () => {
    expect(lowerName("Ômega 3 (EPA e DHA)")).toBe("ômega 3 (EPA e DHA)");
    expect(lowerName("Vitamina E")).toBe("vitamina E");
    expect(lowerName("Vitamina D3")).toBe("vitamina D3");
    expect(lowerName("Niacinamida")).toBe("niacinamida");
  });

  it("#59: justificativa do kit do simulador não perde a sigla", async () => {
    const r = await createMockSearchService({ latencyMs: 0 }).search({ query: "kit de suplementos ômega 3, colágeno e magnésio" });
    const t = r.kits.flatMap((k) => k.items.map((i) => i.reason)).join(" ");
    expect(t).toContain("EPA e DHA");
    expect(t).not.toContain("epa e dha");
  });

  it("#47: suplemento não traz queixa de saúde na descrição", () => {
    for (const p of PRODUCTS.filter((x) => x.domain === "suplemento")) {
      expect(p.description).not.toMatch(/Foco em|gripe|resfriado|pris[aã]o de ventre/i);
    }
  });

  it("#55: aviso com ação fica mais de 5 s e tem botão de fechar", () => {
    const t = src("components/Toast.tsx");
    expect(t).toMatch(/toast\.action \? 10000 : 8000/);
    expect(t).toContain("onMouseEnter");
    expect(t).toContain("setPaused(false), [toast]");   // a pausa não fica presa no aviso seguinte
    expect(t).toContain('aria-label="Fechar aviso"');
  });

  it("#56: botões da cesta e do kit levam o nome do item", () => {
    const cart = src("screens/Cart.tsx");
    for (const v of ["Remover ${lineName}", "Diminuir quantidade de ${lineName}", "Aumentar quantidade de ${lineName}"]) expect(cart).toContain(v);
    const kit = src("screens/KitDetail.tsx");
    expect(kit).toContain("Trocar ${it.product.name}");
    expect(kit).toContain("Levar só este: ${it.product.name}");
  });

  it("#57: a aba Locker tem o texto visível dentro do nome acessível", () => {
    expect(src("screens/Delivery.tsx")).toContain('aria-label="Locker, fora do protótipo"');
  });

  it("#49: página de remédio não promete kit", () => {
    const p = src("screens/ProductPage.tsx");
    expect(p).toContain("remédio não entra em kit");
    expect(p).not.toContain("opções que se completam");
    // suplemento: sem queixa de saúde na página e o atalho leva ao kit de suplementos
    expect(p).toContain('p.concerns[0] === "reposicao"');   // sem atalho que leva a lista vazia
    expect(p).toContain('"Composição"');
    expect(p).toContain('"kit de suplementos"');
  });

  it("#58 e #59: textos atuais, plural e sem crase solta", () => {
    expect(src("screens/More.tsx")).not.toContain("só em reposição");
    expect(src("screens/Home.tsx")).not.toContain("Fotos: Pexels");
    expect(src("screens/Privacy.tsx")).not.toContain("preferências de cosmético");
    const cart = src("screens/Cart.tsx");
    expect(cart).not.toMatch(/\{count\} itens/);
    for (const f of ["screens/Payment.tsx", "screens/More.tsx", "components/KitCard.tsx", "screens/KitDetail.tsx"]) expect(src(f)).not.toMatch(/length\} itens|\{count\} itens/);
    expect(src("screens/Delivery.tsx")).not.toContain("Lojas próximas à<");
  });
});
