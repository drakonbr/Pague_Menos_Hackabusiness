import { describe, expect, it } from "vitest";
import type { Kit, SearchRequest, SkinType } from "../src/contracts/types";
import { PRODUCT_BY_ID, PRODUCTS, STORES, stockAt } from "../src/services/mock/catalogData";
import { createMockCommerceService } from "../src/services/mock/mockCommerceService";
import { checkResponse } from "../src/services/contractChecks";
import { checkKit } from "../src/services/contractChecks";
import { createMockSearchService } from "../src/services/mock/mockSearchService";

const svc = createMockSearchService({ latencyMs: 0 });
const run = (query: string, extra: Partial<SearchRequest> = {}) => svc.search({ query, ...extra });
// etapas cobertas por um kit (um hidratante com FPS cobre também a proteção solar)
const covers = (k: Kit) => k.items.flatMap((i) => i.product.coversSteps);

describe("casos de teste do doc 08", () => {
  it("T1: cuidar da pele até R$ 120", async () => {
    const r = await run("Quero cuidar da pele até R$ 120");
    expect(r.intent.primaryGoal).toBe("skincare_basico");
    expect(r.intent.budgetCents).toBe(12000);
    expect(r.kitsStatus).toBe("ok");
    expect(r.kits.length).toBeGreaterThanOrEqual(2);
    for (const k of r.kits) expect(k.totalCents).toBeLessThanOrEqual(12000);
    expect(r.clarification?.id).toBe("skinType");
    expect(r.safety.decision).toBe("allow");
  });

  it("T2: quero fazer skin care (sem orçamento)", async () => {
    const r = await run("Quero fazer skin care");
    expect(r.intent.primaryGoal).toBe("skincare_basico");
    expect(r.intent.budgetCents).toBeNull();
    expect(r.kits.length).toBeGreaterThanOrEqual(2);
    expect(r.products.length).toBeGreaterThan(0);
  });

  it("T3: tratamento de acne", async () => {
    const r = await run("Preciso de produtos para tratamento de acne");
    expect(r.intent.primaryGoal).toBe("acne");
    expect(r.kits.length).toBeGreaterThanOrEqual(2);
    for (const k of r.kits) {
      const t = k.items.find((i) => i.step === "tratamento");
      expect(t, k.id).toBeTruthy();
      expect(t!.product.concerns).toContain("acne");
    }
  });

  it("T4: protetor solar para pele oleosa", async () => {
    const r = await run("Protetor solar para pele oleosa");
    expect(r.intent.primaryGoal).toBe("protecao_solar");
    expect(r.intent.skinType).toBe("oleosa");
    expect(r.kits.length).toBeGreaterThanOrEqual(2);
    for (const k of r.kits) {
      expect(covers(k)).toContain("protecao_solar");
      expect(covers(k)).toContain("protecao_corporal");
      for (const i of k.items) expect(["oleosa", "todas"].some((s) => (i.product.skinTypes as string[]).includes(s))).toBe(true);
    }
  });

  it("T5: uniformizar manchas até R$ 80", async () => {
    const r = await run("Quero uniformizar manchas até R$ 80");
    expect(r.intent.primaryGoal).toBe("manchas");
    expect(r.kits.length).toBeGreaterThanOrEqual(1);
    for (const k of r.kits) {
      expect(k.totalCents).toBeLessThanOrEqual(8000);
      expect(covers(k)).toContain("protecao_solar");
    }
  });

  it("T6: nada dentro do orçamento mostra o kit mais próximo", async () => {
    const r = await run("Acne, pele oleosa, até R$ 40");
    expect(r.kitsStatus).toBe("none_in_budget");
    expect(r.kits).toHaveLength(0);
    expect(r.closestKit).toBeTruthy();
    expect(r.closestKit!.totalCents).toBeGreaterThan(4000);
    expect(r.closestKit!.withinBudget).toBe(false);
    expect(r.products.length).toBeGreaterThan(0);
  });

  it("T7: dor de cabeça traz kit com dipirona e paracetamol (doc 16)", async () => {
    const r = await run("Estou com dor de cabeça, o que posso tomar?");
    expect(r.safety.decision).toBe("allow");
    expect(r.intent.primaryGoal).toBe("dor_de_cabeca");
    expect(r.kits.length).toBeGreaterThanOrEqual(1);
    for (const k of r.kits) {
      const ings = k.items.flatMap((i) => i.product.ingredients);
      expect(ings).toContain("dipirona");
      expect(ings).toContain("paracetamol");
      expect(new Set(ings).size).toBe(ings.length); // M1: nada de princípio ativo repetido
    }
  });

  it("T7b: sintoma não bloqueia e não pergunta tipo de pele", async () => {
    const r = await run("Estou com febre e muita dor");
    expect(r.safety.decision).toBe("allow");
    expect(r.intent.missing).not.toContain("skinType");
    expect(r.clarification ?? null).toBeNull();
  });

  it("T8: nenhuma resposta manda procurar médico ou farmacêutico", async () => {
    for (const q of ["Qual remédio para acne forte?", "dor muscular", "tosse com catarro", "Estou grávida, quero remédio para enjoo"]) {
      const r = await run(q);
      const shown = [r.reply ?? "", ...(r.suggestions ?? []), ...r.notes, r.safety.message ?? ""].join(" ").toLowerCase();
      expect(shown).not.toMatch(/médic|farmacêutic|profissional de saúde|procure|consulte/);
    }
  });

  it("T9: gestação retira retinol e mostra cautela", async () => {
    const r = await run("Estou grávida, quero um kit anti-idade");
    expect(r.safety.decision).toBe("caution");
    expect(r.safety.category).toBe("gestacao_e_ativos");
    expect(r.kits.length).toBeGreaterThanOrEqual(1);
    for (const k of r.kits)
      for (const i of k.items) expect(i.product.warnings).not.toContain("consultar_se_gestante");
  });

  it("T10: retinol com ácido glicólico nunca no mesmo kit", async () => {
    const r = await run("Quero um kit com retinol e ácido glicólico");
    for (const k of [...r.kits, ...(r.closestKit ? [r.closestKit] : [])]) {
      const ing = k.items.flatMap((i) => i.product.ingredients);
      expect(ing.includes("retinol") && ing.includes("acido_glicolico")).toBe(false);
    }
    expect(r.notes.join(" ")).toMatch(/não entram no mesmo kit/);
  });

  it("T11: vegano, pele seca, até R$ 150", async () => {
    const r = await run("Kit vegano para pele seca até R$ 150");
    expect(r.intent.preferences).toContain("vegano");
    expect(r.intent.skinType).toBe("seca");
    expect(r.kits.length).toBeGreaterThanOrEqual(1);
    for (const k of r.kits) {
      expect(k.totalCents).toBeLessThanOrEqual(15000);
      for (const i of k.items) expect(i.product.claims).toContain("vegano");
    }
  });

  it("T12: texto sem sentido não gera kit e pede reformulação", async () => {
    const r = await run("asdfgh");
    expect(r.kitsStatus).toBe("not_applicable");
    expect(r.kits).toHaveLength(0);
    expect(r.products.length).toBeGreaterThan(0);
    expect(r.notes.join(" ")).toMatch(/Não entendi/);
  });
});

describe("sobrescritas explícitas (chips e controle de orçamento)", () => {
  it("orçamento explícito vence o da frase; null significa sem limite", async () => {
    const a = await run("Quero cuidar da pele até R$ 120", { budgetCents: 8000 });
    expect(a.intent.budgetCents).toBe(8000);
    for (const k of a.kits) expect(k.totalCents).toBeLessThanOrEqual(8000);
    const b = await run("Quero cuidar da pele até R$ 120", { budgetCents: null });
    expect(b.intent.budgetCents).toBeNull();
  });

  it("responder o tipo de pele remove a pergunta e filtra produtos", async () => {
    const r = await run("Quero cuidar da pele", { skinType: "seca" });
    expect(r.clarification).toBeUndefined();
    for (const k of r.kits)
      for (const i of k.items) expect((i.product.skinTypes as string[]).some((s) => s === "seca" || s === "todas")).toBe(true);
  });
});

describe("invariantes do contrato em varredura", () => {
  const queries = [
    "Quero cuidar da pele",
    "Preciso de produtos para tratamento de acne",
    "Protetor solar para pele oleosa",
    "Quero uniformizar manchas",
    "Quero um kit anti-idade",
    "Quero um kit anti-idade com retinol",
    "Kit para pele sensível",
    "Controle de oleosidade",
    "Estou grávida, quero um kit anti-idade",
    "Quero um kit com retinol e ácido glicólico",
    "Kit vegano para pele seca",
    "Quero cuidar da pele sem fragrância",
  ];
  const budgets: Array<number | null> = [null];
  for (let b = 3000; b <= 30000; b += 1500) budgets.push(b);
  const skins: Array<SkinType | undefined> = [undefined, "oleosa", "mista", "seca", "normal", "sensível"];

  it("nenhuma resposta viola I1 a I16 (consultas x orçamentos x peles)", async () => {
    const violations: string[] = [];
    let responses = 0;
    let kits = 0;
    for (const q of queries) {
      for (const budgetCents of budgets) {
        for (const skinType of skins) {
          const r = await run(q, { budgetCents, ...(skinType ? { skinType } : {}) });
          responses++;
          kits += r.kits.length;
          for (const v of checkResponse(r)) violations.push(`[${q} | ${budgetCents} | ${skinType}] ${v}`);
        }
      }
    }
    // garante que a varredura realmente exercitou kits (não passou "no vazio")
    expect(responses).toBeGreaterThan(1000);
    expect(kits).toBeGreaterThan(1500);
    expect(violations.slice(0, 10)).toEqual([]);
  }, 120_000);

  it("é determinístico", async () => {
    const a = await run("Preciso de produtos para tratamento de acne até R$ 150");
    const b = await run("Preciso de produtos para tratamento de acne até R$ 150");
    expect(b).toEqual(a);
  });
});

describe("troca de item", () => {
  it("toda troca compatível mantém as invariantes; incompatível é recusada", async () => {
    const r = await run("Preciso de produtos para tratamento de acne até R$ 200");
    let applied = 0;
    let refused = 0;
    for (const kit of r.kits) {
      for (const it of kit.items) {
        const opts = await svc.swapOptions(kit, it.step, r.intent);
        for (const o of opts.filter((x) => x.compatible).slice(0, 4)) {
          const nk = await svc.swap(kit, it.step, o.product.id, r.intent);
          expect(checkKit(nk, r.intent), `${kit.id} ${it.step} -> ${o.product.id}`).toEqual([]);
          expect(nk.totalCents - kit.totalCents).toBe(o.deltaCents);
          applied++;
        }
        for (const o of opts.filter((x) => !x.compatible)) {
          await expect(svc.swap(kit, it.step, o.product.id, r.intent)).rejects.toThrow();
          refused++;
        }
      }
    }
    expect(applied).toBeGreaterThan(10);
    expect(refused).toBeGreaterThanOrEqual(0);
  });

  it("trocar o hidratante com FPS por um sem FPS é recusado (deixaria o kit sem proteção)", async () => {
    const r = await run("Quero cuidar da pele", { budgetCents: null });
    for (const kit of r.kits) {
      const withFps = kit.items.find((i) => i.product.coversSteps.length > 1);
      if (!withFps) continue;
      const opts = await svc.swapOptions(kit, withFps.step, r.intent);
      const plain = opts.find((o) => o.product.coversSteps.length === 1);
      if (plain) expect(plain.compatible).toBe(false);
    }
  });
});

describe("o verificador de invariantes realmente reprova kits ruins", () => {
  it("detecta item repetido, total errado, sem estoque, retinol + glicólico e preferência violada", async () => {
    const r = await run("Preciso de produtos para tratamento de acne até R$ 200");
    const good = r.kits[0];
    expect(checkKit(good, r.intent)).toEqual([]);

    const dup: Kit = { ...good, items: [...good.items, good.items[0]] };
    expect(checkKit(dup, r.intent).join()).toMatch(/I1/);

    const wrongTotal: Kit = { ...good, totalCents: good.totalCents + 1 };
    expect(checkKit(wrongTotal, r.intent).join()).toMatch(/I4/);

    const out = [...PRODUCT_BY_ID.values()].find((p) => p.stockQty === 0)!;
    const noStock: Kit = { ...good, items: [{ ...good.items[0], product: out }, ...good.items.slice(1)] };
    expect(checkKit(noStock, r.intent).join()).toMatch(/I3/);

    const retinol = [...PRODUCT_BY_ID.values()].find((p) => p.ingredients.includes("retinol") && p.stockQty > 0)!;
    const glic = [...PRODUCT_BY_ID.values()].find((p) => p.ingredients.includes("acido_glicolico") && p.stockQty > 0)!;
    const bad: Kit = {
      ...good,
      items: [
        { step: "tratamento", product: retinol, reason: "" },
        { step: "preparo", product: glic, reason: "" },
      ],
      totalCents: retinol.priceCents + glic.priceCents,
    };
    expect(checkKit(bad, r.intent).join()).toMatch(/I6/);

    const nonVegan = checkKit(good, { ...r.intent, preferences: ["vegano"] });
    expect(nonVegan.join()).toMatch(/I13/);

    const over = checkKit({ ...good, withinBudget: true }, { ...r.intent, budgetCents: good.totalCents - 1 });
    expect(over.join()).toMatch(/I5/);
  });
});

describe("lojas: estoque por loja, ajuste do kit e cashback", () => {
  const storeIds = STORES.map((s) => s.id);
  const queries = [
    "Quero cuidar da pele",
    "Preciso de produtos para tratamento de acne",
    "Protetor solar para pele oleosa",
    "Quero uniformizar manchas",
    "Quero um kit anti-idade",
    "Kit para pele sensível",
  ];

  it("T13: com loja escolhida, todo item de todo kit tem estoque nessa loja (varredura)", async () => {
    const violations: string[] = [];
    let kits = 0;
    for (const storeId of storeIds) {
      for (const q of queries) {
        for (const budgetCents of [null, 8000, 12000, 20000]) {
          const r = await run(q, { storeId, budgetCents });
          expect(r.intent.storeId).toBe(storeId);
          for (const k of r.kits) {
            kits++;
            expect(k.storeId).toBe(storeId);
            for (const it of k.items) if (stockAt(it.product.id, storeId) <= 0) violations.push(`${storeId} ${k.id} ${it.product.id}`);
          }
          for (const v of checkResponse(r)) violations.push(`[${storeId} | ${q} | ${budgetCents}] ${v}`);
        }
      }
    }
    expect(kits).toBeGreaterThan(300);
    expect(violations.slice(0, 10)).toEqual([]);
  }, 120_000);

  it("T14: kit montado no estoque central é ajustado a uma loja trocando só o que falta", async () => {
    let adapted = 0;
    let impossible = 0;
    for (const q of queries) {
      const r = await run(q);
      for (const k of r.kits) {
        for (const storeId of storeIds) {
          const missing = k.items.filter((i) => stockAt(i.product.id, storeId) <= 0);
          const a = await svc.adaptToStore(k, storeId, r.intent);
          if (!a) {
            impossible++;
            continue;
          }
          adapted++;
          expect(a.kit.storeId).toBe(storeId);
          expect(a.replaced.map((x) => x.from.id).sort()).toEqual(missing.map((i) => i.product.id).sort());
          // itens que tinham estoque continuam iguais
          for (const it of k.items) {
            if (stockAt(it.product.id, storeId) > 0) {
              expect(a.kit.items.find((x) => x.step === it.step)?.product.id).toBe(it.product.id);
            }
          }
          expect(checkKit(a.kit, { ...r.intent, storeId }), `${k.id} -> ${storeId}`).toEqual([]);
        }
      }
    }
    expect(adapted).toBeGreaterThan(50);
    // registro: quantos não fecharam em alguma loja (não é erro; a interface sugere outra loja)
    expect(impossible).toBeGreaterThanOrEqual(0);
  }, 60_000);

  it("T15: cashback do kit é a soma do cashback dos itens", async () => {
    const r = await run("Preciso de produtos para tratamento de acne");
    for (const k of r.kits) {
      const sum = k.items.reduce((t, i) => t + Math.floor((i.product.priceCents * i.product.cashbackPct) / 100), 0);
      expect(k.cashbackCents).toBe(sum);
    }
    const bad = { ...r.kits[0], cashbackCents: r.kits[0].cashbackCents + 1 };
    expect(checkKit(bad, r.intent).join()).toMatch(/I15/);
    const wrongStore = { ...r.kits[0], storeId: "s01" };
    expect(checkKit(wrongStore, r.intent).join()).toMatch(/I16/);
  });
});

describe("serviço de comércio (simulado)", () => {
  const com = createMockCommerceService({ latencyMs: 0 });

  it("lojas vêm ordenadas por distância e com disponibilidade correta", async () => {
    const ids = ["p001", "p012", "p030"];
    const list = await com.storesFor(ids);
    expect(list.length).toBe(STORES.length);
    for (let i = 1; i < list.length; i++) expect(list[i].distanceKm).toBeGreaterThanOrEqual(list[i - 1].distanceKm);
    for (const s of list) {
      expect([...s.availableIds, ...s.missingIds].sort()).toEqual([...ids].sort());
      for (const id of s.availableIds) expect(stockAt(id, s.store.id)).toBeGreaterThan(0);
      expect(s.missingIds).toContain("p012"); // p012 está sem estoque de propósito
    }
  });

  it("ordenação de produtos: preço e relevância, sem estoque no fim", async () => {
    const all = PRODUCTS.map((p) => p.id);
    const asc = await com.products(all, "menor_preco");
    const inStock = asc.filter((p) => p.stockQty > 0);
    expect(asc.slice(0, inStock.length)).toEqual(inStock);
    for (let i = 1; i < inStock.length; i++) expect(inStock[i].priceCents).toBeGreaterThanOrEqual(inStock[i - 1].priceCents);
    const rel = await com.products(all);
    expect(rel[0].salesRank).toBeLessThanOrEqual(rel[1].salesRank);
  });

  it("vitrines e categorias apontam para produtos que existem", async () => {
    const h = await com.home();
    for (const sc of h.showcases) for (const id of sc.productIds ?? []) expect(PRODUCT_BY_ID.has(id)).toBe(true);
    for (const c of h.categories) for (const id of c.productIds) expect(PRODUCT_BY_ID.has(id)).toBe(true);
    expect(h.kitPresets.length).toBeGreaterThan(3);
  });
});
