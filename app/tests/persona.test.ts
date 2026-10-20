import { describe, expect, it, vi } from "vitest";
import type { SearchResponse } from "../src/contracts/types";
import { PERSONA, REFILL_RULES, daysLeft, needsRefill, refillPrice } from "../src/persona";
import { HttpSearchService } from "../src/services/searchService";
import { checkResponse } from "../src/services/contractChecks";
import { PRODUCT_BY_ID, PRODUCTS, stockAt } from "../src/services/mock/catalogData";
import { createMockSearchService } from "../src/services/mock/mockSearchService";

const svc = createMockSearchService({ latencyMs: 0 });

describe("persona (Renata) e reposição", () => {
  it("tem dois medicamentos de uso contínuo e consentimento de saúde desligado por padrão", () => {
    expect(PERSONA.continuousMedications).toHaveLength(2);
    expect(PERSONA.privacy.consent.useHealthDataForRecommendations).toBe(false);
    expect(PERSONA.privacy.consent.shareHealthDataWithPartners).toBe(false);
    expect(PERSONA.privacy.healthDataStays).toBe("no_aparelho");
  });

  it("avisa a reposição com a antecedência da premissa (7 dias)", () => {
    const [a, b] = PERSONA.continuousMedications;
    expect(daysLeft(a)).toBe(5);
    expect(needsRefill(a)).toBe(true);
    expect(needsRefill(b)).toBe(true);
    expect(needsRefill({ ...a, unitsLeft: 20 })).toBe(false);
    expect(REFILL_RULES.alertDaysBefore).toBe(7);
  });

  it("desconto da reposição automática só quando ligada", () => {
    expect(refillPrice(10000, false)).toBe(10000);
    expect(refillPrice(10000, true)).toBe(9500);
  });

  it("os itens da persona existem no catálogo, são medicamentos com equivalentes e exigem receita simulada", () => {
    for (const m of PERSONA.continuousMedications) {
      const p = PRODUCT_BY_ID.get(m.productId)!;
      expect(p.domain).toBe("medicamento");
      expect(p.rx).toBe("receita_simples");
      expect(PRODUCTS.some((q) => q.id !== p.id && q.equivalence?.group === p.equivalence?.group)).toBe(true);
    }
  });
});

describe("medicamento fica fora de kits e da busca livre", () => {
  const queries = ["kit de suplementos", "rotina anti idade", "higiene premium", "Quero cuidar da pele", "tratamento de acne", "quero meu remédio"];
  it.each(queries)("%s", async (q) => {
    const r = await svc.search({ query: q });
    expect(checkResponse(r)).toEqual([]);
    for (const p of r.products) expect(p.domain).not.toBe("medicamento");
    for (const k of r.kits) for (const i of k.items) expect(i.product.domain).not.toBe("medicamento");
  });
});

describe("reposição sem recomendar (modo simulado)", () => {
  it("abre a reposição sem citar remédio nem condição", async () => {
    const r = await svc.search({ query: "preciso repor meu remédio de pressão" });
    expect(r.action?.type).toBe("open_refill");
    expect(r.safety.decision).toBe("allow");
    expect(r.reply?.toLowerCase()).not.toMatch(/press[aã]o|colesterol|tensivalol|lipostan/);
    expect(JSON.stringify(r.context)).not.toMatch(/press[aã]o|rem[eé]dio/i);
  });
  it.each(["qual remédio devo tomar para pressão alta", "qual a dose do meu remédio", "preciso repor remédio, estou com tontura"])("bloqueia: %s", async (q) => {
    const r = await svc.search({ query: q });
    expect(r.safety.decision).toBe("blocked");
    expect(r.kits).toEqual([]);
  });
  it("equivalentes do item da persona que está sem estoque na Loja Madalena", async () => {
    expect(stockAt("p136", "s01")).toBe(0);
    const r = await svc.similars("p136", "s01");
    expect(r.inStockHere).toBe(false);
    expect(r.options.every((o) => o.sameActive && o.needsPharmacistConfirmation)).toBe(true);
    expect(r.options[0].inStock).toBe(true);
  });
});

describe("suplementos e higiene no modo simulado", () => {
  it("kit de suplementos tem as 3 etapas e o aviso de medicação", async () => {
    const r = await svc.search({ query: "quero um kit de suplementos ômega 3, colágeno e magnésio" });
    expect(checkResponse(r)).toEqual([]);
    expect(r.intent.primaryGoal).toBe("suplementos");
    expect(r.clarification).toBeUndefined();
    for (const k of r.kits) {
      expect(["omega3", "colageno", "magnesio"].every((s) => k.items.some((i) => i.step === s))).toBe(true);
      expect(k.alerts.some((a) => a.code === "consultar_se_medicacao")).toBe(true);
    }
  });
  it("conversa de dois turnos: o ajuste de preço mantém o objetivo", async () => {
    const r1 = await svc.search({ query: "kit de higiene premium" });
    const r2 = await svc.search({ query: "até 150 reais", context: r1.context });
    expect(r2.intent.primaryGoal).toBe("higiene_premium");
    expect(r2.intent.budgetCents).toBe(15000);
  });
});

describe("cliente HTTP do GraphRAG", () => {
  const fakeRes: SearchResponse = {
    requestId: "r_x", query: "oi", safety: { decision: "allow" }, intent: { goals: [], primaryGoal: null, budgetCents: null, skinType: null, preferences: [], missing: [] },
    kitsStatus: "not_applicable", kits: [], closestKit: null, products: [], notes: [], reply: "Oi!", suggestions: [], action: { type: "none" },
  };
  it("envia frase, contexto e loja; nada além disso", async () => {
    const f = vi.fn(async () => new Response(JSON.stringify(fakeRes), { status: 200 }));
    const http = new HttpSearchService("http://x", f as unknown as typeof fetch);
    const ctx = { intent: fakeRes.intent, requested: [], excluded: [], kits: [], lastAct: "busca", turn: 1 };
    const r = await http.search({ query: "oi", storeId: "s01", context: ctx });
    expect(r.reply).toBe("Oi!");
    const [url, init] = f.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe("http://x/v1/search");
    expect(Object.keys(JSON.parse(init.body as string)).sort()).toEqual(["context", "query", "storeId"]);
  });
  it("mostra o erro do servidor", async () => {
    const f = vi.fn(async () => new Response(JSON.stringify({ error: "kit inválido" }), { status: 400 }));
    const http = new HttpSearchService("http://x", f as unknown as typeof fetch);
    await expect(http.search({ query: "x" })).rejects.toThrow("kit inválido");
  });
  it("health falso quando o servidor não responde", async () => {
    const f = vi.fn(async () => { throw new TypeError("fetch failed"); });
    expect(await new HttpSearchService("http://x", f as unknown as typeof fetch).health(50)).toBe(false);
  });
});
