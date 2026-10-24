// MOCK do serviço de busca. Obedece ao contrato (contracts/README.md) para que o app
// não saiba se fala com isto ou com o GraphRAG real.
import type {
  ChatAction,
  ChatContext,
  Clarification,
  Intent,
  Kit,
  Product,
  SearchRequest,
  SearchResponse,
  SearchService,
  SimilarsResponse,
  SkinType,
  StepId,
  SwapOption,
} from "../../contracts/types";
import { GOAL_LABEL, STEP_ORDER, TIER_LABEL } from "../../contracts/types";
import { PRODUCTS, PRODUCT_BY_ID, STORES, stockAt } from "./catalogData";
import { urgency } from "../urgency";
import { adaptToStore, applySwap, buildCtx, compose, isHealthGoal, rankProducts, swapOptions } from "./composer";
import { assessSafety, isRefillRequest, norm, parseIntent } from "./intent";

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

const money = (c: number) => `R$ ${(c / 100).toFixed(2).replace(".", ",")}`;

function emptyIntent(storeId: string | null): Intent {
  return { goals: [], primaryGoal: null, budgetCents: null, skinType: null, preferences: [], pregnancy: false, storeId, missing: [] };
}

/** Texto, sugestões e ação do modo simulado (o motor real escreve os seus). */
function chatFields(res: Omit<SearchResponse, "reply" | "suggestions" | "action" | "context" | "act">, act: string, turn: number) {
  let reply: string;
  let action: ChatAction = { type: "none" };
  const goal = res.intent.primaryGoal ? GOAL_LABEL[res.intent.primaryGoal].toLowerCase() : "";
  if (res.kits.length) {
    reply = `Montei ${res.kits.length} opções de ${goal}: ${res.kits.map((k) => `${TIER_LABEL[k.tier]} ${money(k.totalCents)}`).join(", ")}. (modo simulado)`;
    action = { type: "show_kits" };
  } else if (res.kitsStatus === "none_in_budget" && res.closestKit) {
    reply = `Com esse orçamento não fechei um kit completo de ${goal}. O mais próximo custa ${money(res.closestKit.totalCents)}.`;
  } else reply = res.notes[0] ?? "Não consegui entender bem o pedido. Tente “pele oleosa até R$ 100”.";
  const context: ChatContext = { intent: res.intent, requested: [], excluded: [], kits: [], lastAct: act, turn: turn + 1 };
  const health = res.intent.primaryGoal != null && isHealthGoal(res.intent.primaryGoal);
  const suggestions = res.kits.length ? ["Mais barato", "Sem fragrância", "Total com entrega"]
    : health ? ["Mais barato", "Remédio para gripe", "Remédio para dor de cabeça"] : ["Kit de suplementos", "Higiene premium"];
  return { act, reply, suggestions, action, context };
}

export interface MockOptions {
  /** Atraso artificial, para mostrar o estado de carregamento. Use 0 nos testes. */
  latencyMs?: number;
}

export function createMockSearchService(opts: MockOptions = {}): SearchService {
  const wait = () => (opts.latencyMs ? new Promise<void>((r) => setTimeout(r, opts.latencyMs)) : Promise.resolve());

  return {
    engine: "simulado" as const,
    async search(req: SearchRequest): Promise<SearchResponse> {
      await wait();
      const requestId = `r_${hash(JSON.stringify({ ...req, context: undefined }))}`;
      const parsed = parseIntent(req);
      const turn = req.context?.turn ?? 0;
      // conversa simplificada: sem objetivo novo, ajusta a busca anterior (preço, pele, preferência)
      const prev = req.context?.intent;
      if (prev?.primaryGoal && !parsed.intent.primaryGoal && (parsed.intent.budgetCents != null || parsed.intent.skinType || parsed.intent.preferences.length)) {
        parsed.intent = {
          ...prev,
          budgetCents: parsed.intent.budgetCents ?? prev.budgetCents,
          skinType: parsed.intent.skinType ?? prev.skinType,
          preferences: [...new Set([...prev.preferences, ...parsed.intent.preferences])],
          storeId: req.storeId ?? prev.storeId ?? null,
          missing: [],
        };
        parsed.understood = true;
      }
      const { intent } = parsed;
      const urgent = urgency(req.query);   // #63: antes de qualquer outra coisa
      if (urgent) {
        const intent0 = emptyIntent(req.storeId ?? null);
        return {
          requestId, query: req.query, safety: urgent, intent: intent0, closestKit: null, kitsStatus: "not_applicable", kits: [], products: [], notes: [],
          act: "urgencia", reply: urgent.message ?? "", suggestions: [], action: { type: "none" },
          context: { intent: intent0, requested: [], excluded: [], kits: [], lastAct: "urgencia", turn: turn + 1 },
        };
      }
      if (isRefillRequest(parsed.normalized)) {
        const safety = { decision: "allow" } as const;
        const base = { requestId, query: req.query, safety, intent: emptyIntent(req.storeId ?? null), closestKit: null, kitsStatus: "not_applicable" as const, kits: [], products: [], notes: [] };
        return {
          ...base,
          act: "repor_medicamento",
          reply: "Abri a sua reposição de uso contínuo. Confira as quantidades e a loja mais próxima com estoque. (modo simulado)",
          suggestions: ["Tem equivalente disponível?", "Qual a entrega mais rápida?"],
          action: { type: "open_refill" },
          context: { intent: base.intent, requested: [], excluded: [], kits: [], lastAct: "repor_medicamento", turn: turn + 1 },
        };
      }
      const safety = assessSafety(parsed.normalized, !!intent.pregnancy, intent.primaryGoal);

      const base = {
        requestId,
        query: req.query,
        safety,
        intent,
        closestKit: null,
      } as const;

      if (!parsed.understood) {
        const found = tokenSearch(req.query);
        const r = {
          ...base,
          kitsStatus: "not_applicable" as const,
          kits: [],
          products: found.length ? found : popularProducts(),
          notes: [
            found.length
              ? "Mostrando produtos que combinam com a sua busca. Descreva um objetivo, como pele oleosa até R$ 100, para ver kits."
              : "Não entendi o pedido. Mostrando alguns produtos; tente descrever um objetivo, como pele oleosa até R$ 100.",
          ],
        };
        return { ...r, ...chatFields(r, "busca", turn) };
      }

      const ctx = buildCtx(intent, parsed.requestedIngredients)!;
      // K13: objetivo de remédio não tem kit; mostra só a lista avulsa
      const products = rankProducts(ctx);
      const comp = isHealthGoal(ctx.primary)
        ? { status: "not_applicable" as const, kits: [], closestKit: null,
            notes: [`Encontrei ${products.length} ${products.length === 1 ? "item" : "itens"} de ${GOAL_LABEL[ctx.primary].toLowerCase()}. Toque numa sugestão para ajustar a lista.`] }
        : compose(ctx, requestId);
      const clarification: Clarification | undefined = intent.missing.includes("skinType")
        ? { id: "skinType", question: "Como é a sua pele?", options: SKIN_OPTIONS }
        : undefined;

      const r = {
        ...base,
        clarification,
        kitsStatus: comp.status,
        kits: comp.kits,
        closestKit: comp.closestKit,
        products,
        notes: comp.notes,
      };
      return { ...r, ...chatFields(r, "busca", turn) };
    },

    async similars(productId: string, storeId: string | null): Promise<SimilarsResponse> {
      await wait();
      const p = PRODUCT_BY_ID.get(productId);
      if (!p) throw new Error("Produto inexistente.");
      const withStock = (q: Product) => STORES.filter((s) => stockAt(q.id, s.id) > 0).map((s) => s.id);
      const pool =
        p.equivalence
          ? PRODUCTS.filter((q) => q.id !== p.id && q.equivalence?.group === p.equivalence!.group)
          : PRODUCTS.filter((q) => q.id !== p.id && q.step === p.step && q.concerns.some((c) => p.concerns.includes(c)));
      const options = pool
        .map((q) => ({
          product: q,
          kind: p.equivalence ? ("equivalente" as const) : ("parecido" as const),
          presentation: q.equivalence?.presentation,
          sameActive: p.equivalence ? true : undefined,
          sameDose: p.equivalence ? q.equivalence?.dose === p.equivalence?.dose : undefined,
          deltaCents: q.priceCents - p.priceCents,
          inStock: stockAt(q.id, storeId) > 0,
          storeIdsWithStock: withStock(q),
          needsPharmacistConfirmation: !!(p.rx || q.rx),   // #46: trocar remédio de receita é com o farmacêutico
        }))
        .sort((a, b) => Number(b.inStock) - Number(a.inStock) || a.deltaCents - b.deltaCents || a.product.id.localeCompare(b.product.id))
        .slice(0, 6);
      return { productId, domain: p.domain, storeId, inStockHere: stockAt(p.id, storeId) > 0, options };
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
