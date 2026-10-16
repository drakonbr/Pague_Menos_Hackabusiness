// MOCK do serviço de busca. Obedece ao contrato (contracts/README.md) para que o app
// não saiba se fala com isto ou com o GraphRAG real.
import type {
  Clarification,
  Intent,
  Kit,
  Product,
  SearchRequest,
  SearchResponse,
  SearchService,
  SkinType,
  StepId,
  SwapOption,
} from "../../contracts/types";
import { STEP_ORDER } from "../../contracts/types";
import { PRODUCTS } from "./catalogData";
import { adaptToStore, applySwap, buildCtx, compose, rankProducts, swapOptions } from "./composer";
import { assessSafety, norm, parseIntent } from "./intent";

const SKIN_OPTIONS: Clarification["options"] = [
  { value: "oleosa", label: "Oleosa" },
  { value: "mista", label: "Mista" },
  { value: "seca", label: "Seca" },
  { value: "normal", label: "Normal" },
  { value: "sensível", label: "Sensível" },
];

function hash(s: string): string {
  let h = 5381;
  for (let i = 0; i < s.length; i++) h = ((h << 5) + h + s.charCodeAt(i)) >>> 0;
  return h.toString(36).padStart(6, "0").slice(0, 6);
}

const STOP = new Set(["para", "com", "uma", "que", "quero", "preciso", "produto", "produtos", "kit", "de", "da", "do"]);

function popularProducts(limit = 12): Product[] {
  return PRODUCTS.filter((p) => p.stockQty > 0 && p.priceTier === "economico")
    .sort((a, b) => STEP_ORDER.indexOf(a.step) - STEP_ORDER.indexOf(b.step) || a.priceCents - b.priceCents)
    .slice(0, limit);
}

function tokenSearch(query: string, limit = 24): Product[] {
  const tokens = norm(query)
    .split(/[^a-z0-9]+/)
    .filter((t) => t.length >= 3 && !STOP.has(t));
  if (tokens.length === 0) return [];
  return PRODUCTS.filter((p) => p.stockQty > 0)
    .map((p) => {
      const text = norm([p.name, p.brand, p.productType, ...p.concerns, ...p.claims].join(" "));
      return { p, hits: tokens.filter((t) => text.includes(t)).length };
    })
    .filter((x) => x.hits > 0)
    .sort((a, b) => b.hits - a.hits || a.p.priceCents - b.p.priceCents || a.p.id.localeCompare(b.p.id))
    .slice(0, limit)
    .map((x) => x.p);
}

export interface MockOptions {
  /** Atraso artificial, para mostrar o estado de carregamento. Use 0 nos testes. */
  latencyMs?: number;
}

export function createMockSearchService(opts: MockOptions = {}): SearchService {
  const wait = () => (opts.latencyMs ? new Promise<void>((r) => setTimeout(r, opts.latencyMs)) : Promise.resolve());

  return {
    async search(req: SearchRequest): Promise<SearchResponse> {
      await wait();
      const requestId = `r_${hash(JSON.stringify(req))}`;
      const parsed = parseIntent(req);
      const { intent } = parsed;
      const safety = assessSafety(parsed.normalized, !!intent.pregnancy, intent.primaryGoal);

      const base = {
        requestId,
        query: req.query,
        safety,
        intent,
        closestKit: null,
      } as const;

      if (safety.decision === "blocked") {
        return { ...base, kitsStatus: "not_applicable", kits: [], products: [], notes: [] };
      }

      if (!parsed.understood) {
        const found = tokenSearch(req.query);
        return {
          ...base,
          kitsStatus: "not_applicable",
          kits: [],
          products: found.length ? found : popularProducts(),
          notes: [
            found.length
              ? "Mostrando produtos que combinam com a sua busca. Descreva um objetivo, como pele oleosa até R$ 100, para ver kits."
              : "Não entendi o pedido. Mostrando alguns produtos; tente descrever um objetivo, como pele oleosa até R$ 100.",
          ],
        };
      }

      const ctx = buildCtx(intent, parsed.requestedIngredients)!;
      const comp = compose(ctx, requestId);
      const clarification: Clarification | undefined = intent.skinType
        ? undefined
        : { id: "skinType", question: "Como é a sua pele?", options: SKIN_OPTIONS };

      return {
        ...base,
        clarification,
        kitsStatus: comp.status,
        kits: comp.kits,
        closestKit: comp.closestKit,
        products: rankProducts(ctx),
        notes: comp.notes,
      };
    },

    async swapOptions(kit: Kit, step: StepId, intent: Intent): Promise<SwapOption[]> {
      await wait();
      const ctx = buildCtx(intent, []);
      return ctx ? swapOptions(kit, step, ctx) : [];
    },

    async swap(kit: Kit, step: StepId, productId: string, intent: Intent): Promise<Kit> {
      await wait();
      const ctx = buildCtx(intent, []);
      if (!ctx) throw new Error("Sem contexto para trocar o item.");
      return applySwap(kit, step, productId, ctx);
    },

    async adaptToStore(kit: Kit, storeId: string, intent: Intent) {
      await wait();
      const ctx = buildCtx(intent, []);
      if (!ctx) return null;
      return adaptToStore(kit, storeId, ctx);
    },
  };
}

export type { SkinType };
