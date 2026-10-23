// MOCK do compositor de kits. Implementa as regras K1 a K12 do doc 06 de forma simples,
// só para demonstrar as telas. No sistema real isto é o módulo graphrag/composer.
import type {
  Alert,
  GoalId,
  Intent,
  Kit,
  KitItem,
  KitTier,
  KitsStatus,
  Product,
  SkinType,
  StepId,
  SwapOption,
} from "../../contracts/types";
import { GOAL_LABEL, STEP_LABEL, STEP_ORDER, kitCashback, kitPrice } from "../../contracts/types";
import {
  CONCERN_LABEL,
  GOALS,
  INGREDIENT_NAME,
  INTERACTIONS,
  PRODUCTS,
  WARNING_TEXT,
  cashbackOf,
  stockAt,
} from "./catalogData";

// ---------------------------------------------------------------------------
// Contexto de composição
// ---------------------------------------------------------------------------
export interface Ctx {
  goals: GoalId[];
  primary: GoalId;
  concerns: Set<string>;
  primaryConcerns: Set<string>;
  skinType: SkinType | null;
  assumedSkin: SkinType | null;
  prefs: string[];
  pregnancy: boolean;
  budgetCents: number | null;
  requestedIngredients: string[];
  storeId: string | null;
}

/** K13 (#40, regra da Anvisa): remédio nunca entra em kit nem na troca de item; continua nas listas. Igual ao motor. */
const KIT_POOL = PRODUCTS.filter((p) => p.domain !== "medicamento");
/** Objetivo de saúde: alguma etapa obrigatória só tem remédio, então não há kit (dor de cabeça, gripe...). */
export function isHealthGoal(goal: GoalId): boolean {
  return !GOALS.find((g) => g.id === goal)!.requiredSteps.every((s) => KIT_POOL.some((p) => p.coversSteps.includes(s)));
}

export function buildCtx(intent: Intent, requestedIngredients: string[]): Ctx | null {
  if (!intent.primaryGoal) return null;
  const defs = GOALS.filter((g) => intent.goals.includes(g.id));
  const primaryDef = GOALS.find((g) => g.id === intent.primaryGoal)!;
  const assumedSkin: SkinType | null = intent.skinType
    ? null
    : intent.primaryGoal === "acne" || intent.primaryGoal === "oleosidade"
      ? "oleosa"
      : intent.primaryGoal === "pele_sensivel"
        ? "sensível"
        : null;
  return {
    goals: intent.goals,
    primary: intent.primaryGoal,
    concerns: new Set(defs.flatMap((g) => g.concerns)),
    primaryConcerns: new Set(primaryDef.concerns),
    skinType: intent.skinType,
    assumedSkin,
    prefs: intent.preferences,
    pregnancy: !!intent.pregnancy,
    budgetCents: intent.budgetCents,
    requestedIngredients,
    storeId: intent.storeId ?? null,
  };
}

// ---------------------------------------------------------------------------
// Elegibilidade e relevância
// ---------------------------------------------------------------------------
export function baseEligible(p: Product, ctx: Ctx, relaxSkin = false): boolean {
  if (stockAt(p.id, ctx.storeId) <= 0) return false;
  if (ctx.pregnancy && p.warnings.includes("consultar_se_gestante")) return false;
  if (!ctx.prefs.every((pref) => p.claims.includes(pref))) return false;
  if (!relaxSkin) {
    const skin = ctx.skinType ?? ctx.assumedSkin;
    if (skin && !(p.skinTypes.includes("todas") || p.skinTypes.includes(skin))) return false;
  }
  return true;
}

const NEEDS_CONCERN_MATCH: StepId[] = ["tratamento", "preparo", "complemento"];

function concernMatch(p: Product, ctx: Ctx): boolean {
  return p.concerns.some((c) => ctx.concerns.has(c));
}

export function score(p: Product, ctx: Ctx): number {
  let s = 0;
  for (const c of p.concerns) {
    if (ctx.primaryConcerns.has(c)) s += 10;
    else if (ctx.concerns.has(c)) s += 6;
  }
  const skin = ctx.skinType ?? ctx.assumedSkin;
  if (skin) {
    if (p.skinTypes.includes(skin)) s += 6;
    else if (p.skinTypes.includes("todas")) s += 3;
  } else if (p.skinTypes.includes("todas")) {
    s += 2;
  }
  if (skin === "oleosa" && p.claims.includes("oil free")) s += 3;
  if (p.claims.includes("não comedogênico")) s += 1;
  for (const ing of ctx.requestedIngredients) if (p.ingredients.includes(ing)) s += 12;
  // equilíbrio de faixa: com relevância igual, o Essencial prefere a faixa intermediária
  s += TIER_BONUS[p.priceTier] ?? 0;
  return s;
}

function cmpProducts(ctx: Ctx) {
  return (a: Product, b: Product) =>
    score(b, ctx) - score(a, ctx) || a.priceCents - b.priceCents || a.id.localeCompare(b.id);
}

// Preocupações "de especialidade": um produto que as declara só deve entrar em etapas genéricas
// (limpeza, hidratação, proteção) quando o objetivo também as inclui. Evita, por exemplo, um
// sabonete antiacne no kit de rotina básica só por ser o mais barato.
const SPECIALTY = new Set(["acne", "manchas", "sinais_idade", "olheiras", "textura"]);
const GENERIC_STEPS: StepId[] = ["limpeza", "hidratacao", "protecao_solar", "protecao_corporal"];

function specialtyMismatch(p: Product, ctx: Ctx): boolean {
  return p.concerns.some((c) => SPECIALTY.has(c) && !ctx.concerns.has(c));
}

export function candidatesFor(step: StepId, ctx: Ctx): { list: Product[]; relaxed: boolean } {
  const pool = KIT_POOL.filter((p) => p.coversSteps.includes(step));
  const filt = (relax: boolean) => {
    const base = pool.filter(
      (p) => baseEligible(p, ctx, relax) && (!NEEDS_CONCERN_MATCH.includes(step) || concernMatch(p, ctx)),
    );
    if (!GENERIC_STEPS.includes(step)) return base;
    const clean = base.filter((p) => !specialtyMismatch(p, ctx));
    return clean.length >= 3 ? clean : base;
  };
  const strict = filt(false);
  if (strict.length > 0) return { list: strict, relaxed: false };
  return { list: filt(true), relaxed: true };
}

function shortlist(list: Product[], ctx: Ctx): Product[] {
  const top = [...list].sort(cmpProducts(ctx)).slice(0, 4);
  const cheapest = [...list]
    .sort((a, b) => a.priceCents - b.priceCents || a.id.localeCompare(b.id))
    .slice(0, 3);
  return [...new Set([...top, ...cheapest])];
}

// ---------------------------------------------------------------------------
// Interações (K4)
// ---------------------------------------------------------------------------
const INTERACTION_MAP = new Map<string, (typeof INTERACTIONS)[number]>();
for (const i of INTERACTIONS) {
  INTERACTION_MAP.set(`${i.a}|${i.b}`, i);
  INTERACTION_MAP.set(`${i.b}|${i.a}`, i);
}

export interface Conflict {
  severity: "evitar" | "separar";
  reason: string;
}

/** Retorna conflito entre dois produtos que ficam na pele; null se compatíveis. */
export function conflictBetween(p: Product, q: Product): Conflict | null {
  // medicamento (doc 16): o kit nunca repete princípio ativo; dois anti-inflamatórios caem nas interações
  if (p.domain === "medicamento" && q.domain === "medicamento" && p.ingredients.some((i) => q.ingredients.includes(i)))
    return { severity: "evitar", reason: "O kit não repete princípio ativo." };
  if (p.step === "limpeza" || q.step === "limpeza") return null; // enxaguados
  for (const a of p.ingredients) {
    for (const b of q.ingredients) {
      const hit = INTERACTION_MAP.get(`${a}|${b}`);
      if (!hit) continue;
      if (hit.severity === "evitar") return { severity: "evitar", reason: hit.reason };
      const ok =
        (p.usagePeriod === "dia" && q.usagePeriod === "noite") ||
        (p.usagePeriod === "noite" && q.usagePeriod === "dia");
      if (!ok) return { severity: "separar", reason: hit.reason };
    }
  }
  return null;
}

const isPhoto = (p: Product) => p.warnings.includes("fotossensibilizante");

// ---------------------------------------------------------------------------
// Enumeração de combinações (K1 a K9)
// ---------------------------------------------------------------------------
interface Slot {
  step: StepId;
  product: Product;
}
interface Combo {
  slots: Slot[];
  total: number;
  list: number;
  rel: number;
  relq: number; // rel sem o bônus de faixa de preço: é o que conta como "item melhor" no Completo
}
const TIER_BONUS: Record<string, number> = { intermediario: 2, premium: 1 };

const ids = (c: Combo) => c.slots.map((s) => s.product.id);

function enumerate(steps: StepId[], cand: Map<StepId, Product[]>, ctx: Ctx, maxBudget: number | null): Combo[] {
  const ordered = [...steps].sort((a, b) => STEP_ORDER.indexOf(a) - STEP_ORDER.indexOf(b));
  const out: Combo[] = [];
  const chosen: Slot[] = [];
  const covered = new Set<StepId>();

  const rec = (i: number, total: number) => {
    if (i === ordered.length) {
      if (chosen.some((c) => isPhoto(c.product)) && !covered.has("protecao_solar")) return; // K5
      if (chosen.length > 5) return; // K9
      let rel = 0;
      let list = 0;
      for (const c of chosen) {
        rel += score(c.product, ctx);
        list += c.product.listPriceCents;
      }
      for (let x = 0; x < chosen.length; x++)
        for (let y = x + 1; y < chosen.length; y++)
          if (chosen[x].product.brand === chosen[y].product.brand) rel += 2;
      const kitTotal = kitPrice(total, chosen.length).totalCents;
      if (maxBudget != null && kitTotal > maxBudget) return; // K3 (com o desconto do kit)
      const tier = chosen.reduce((t, c) => t + (TIER_BONUS[c.product.priceTier] ?? 0), 0);
      out.push({ slots: chosen.map((c) => ({ ...c })), total: kitTotal, list, rel, relq: rel - tier });
      return;
    }
    const step = ordered[i];
    if (covered.has(step)) {
      rec(i + 1, total);
      return;
    }
    for (const p of cand.get(step) ?? []) {
      if (maxBudget != null && kitPrice(total + p.priceCents, 5).totalCents > maxBudget) continue; // K3: nem com o maior desconto
      if (p.coversSteps.some((s) => covered.has(s))) continue; // K1
      if (chosen.some((c) => c.product.id === p.id || c.product.productType === p.productType)) continue; // K1
      if (chosen.some((c) => conflictBetween(c.product, p))) continue; // K4
      chosen.push({ step, product: p });
      p.coversSteps.forEach((s) => covered.add(s));
      rec(i + 1, total + p.priceCents);
      p.coversSteps.forEach((s) => covered.delete(s));
      chosen.pop();
    }
  };
  rec(0, 0);
  return out;
}

const cmpCheap = (a: Combo, b: Combo) => a.total - b.total || b.rel - a.rel || ids(a).join().localeCompare(ids(b).join());
const cmpBest = (a: Combo, b: Combo) => b.rel - a.rel || a.total - b.total || ids(a).join().localeCompare(ids(b).join());

// ---------------------------------------------------------------------------
// Textos
// ---------------------------------------------------------------------------
const GENERIC_ING = new Set(["glicerina", "tensoativo_suave", "filtro_uv", "aloe_vera"]);
const DEFAULT_REASON: Record<StepId, string> = {
  limpeza: "Limpa a pele sem agredir, primeira etapa da rotina.",
  preparo: "Prepara a pele para o tratamento.",
  tratamento: "Tratamento focado no objetivo escolhido.",
  hidratacao: "Mantém a pele hidratada e protege a barreira.",
  protecao_solar: "Proteção diária contra o sol, etapa essencial.",
  protecao_corporal: "Proteção solar para o corpo.",
  complemento: "Cuidado complementar para áreas específicas.",
  omega3: "Suplemento de ômega 3 para a rotina diária.",
  colageno: "Suplemento de colágeno para a rotina diária.",
  magnesio: "Suplemento de magnésio para a rotina diária.",
  vitaminas: "Complemento de vitaminas para a rotina diária.",
  higiene_corpo: "Higiene do banho com toque premium.",
  higiene_cabelo: "Cuidado diário com os cabelos.",
  higiene_oral: "Higiene bucal completa.",
  desodorante: "Desodorante de uso diário.",
  reposicao: "Reposição do que você já usa.",
  analgesico_dipirona: "Dipirona.",
  analgesico_paracetamol: "Paracetamol.",
  antiinflamatorio: "Anti-inflamatório.",
  relaxante_muscular: "Relaxante muscular.",
  dor_topico: "Gel ou pomada para dor.",
  antiespasmodico: "Para cólica.",
  antigases: "Antigases.",
  antiacido: "Antiácido.",
  protetor_gastrico: "Protetor gástrico.",
  antigripal: "Antigripal.",
  descongestionante_nasal: "Nariz (soro e descongestionante).",
  imunidade: "Vitamina C.",
  expectorante: "Expectorante.",
  antitussigeno: "Para tosse seca.",
  pastilha_garganta: "Pastilha para garganta.",
  spray_garganta: "Spray ou gargarejo para garganta.",
  antialergico: "Antialérgico.",
  antidiarreico: "Antidiarreico.",
  probiotico: "Probiótico.",
  reidratacao: "Reidratação oral.",
  laxante: "Laxante.",
  fibra: "Fibra.",
  antiemetico: "Contra enjoo.",
};

function listPt(items: string[]): string {
  if (items.length <= 1) return items.join("");
  return `${items.slice(0, -1).join(", ")} e ${items[items.length - 1]}`;
}

export function explainItem(p: Product, ctx: Ctx, step: StepId): string {
  const matched = p.concerns.filter((c) => ctx.concerns.has(c)).map((c) => CONCERN_LABEL[c] ?? c);
  const actives = p.ingredients
    .filter((i) => !GENERIC_ING.has(i))
    .slice(0, 2)
    .map((i) => (INGREDIENT_NAME.get(i) ?? i).toLowerCase());
  const parts: string[] = [];
  if (matched.length) {
    parts.push(`Atende ${listPt(matched.slice(0, 3))}${actives.length ? `, com ${listPt(actives)}` : ""}.`);
  } else if (actives.length) {
    parts.push(`Com ${listPt(actives)}.`);
  }
  if (p.fps) parts.push(`FPS ${p.fps}.`);
  const skin = ctx.skinType ?? ctx.assumedSkin;
  if (skin && p.skinTypes.includes(skin)) parts.push(`Indicado para pele ${skin}.`);
  if (p.coversSteps.length > 1) parts.push("Cobre também a proteção solar, sem item extra.");
  return parts.length ? parts.join(" ") : DEFAULT_REASON[step];
}

export function buildAlerts(products: Product[]): Alert[] {
  const alerts: Alert[] = [];
  const byCode = new Map<string, string[]>();
  for (const p of products) {
    for (const w of p.warnings) byCode.set(w, [...(byCode.get(w) ?? []), p.id]);
  }
  for (const [code, productIds] of byCode) {
    const c = code as keyof typeof WARNING_TEXT;
    alerts.push({
      code: c,
      severity: c === "fotossensibilizante" || c === "consultar_se_gestante" || c === "consultar_se_medicacao" ? "atencao" : "info",
      text: WARNING_TEXT[c],
      productIds,
    });
  }
  // pares "separar" permitidos (dia x noite)
  for (let x = 0; x < products.length; x++) {
    for (let y = x + 1; y < products.length; y++) {
      const p = products[x];
      const q = products[y];
      if (p.step === "limpeza" || q.step === "limpeza") continue;
      for (const a of p.ingredients) {
        for (const b of q.ingredients) {
          const hit = INTERACTION_MAP.get(`${a}|${b}`);
          if (hit?.severity === "separar") {
            const day = p.usagePeriod === "dia" ? p : q;
            const night = day === p ? q : p;
            alerts.push({
              code: "interacao_separar_periodos",
              severity: "info",
              text: `Use ${day.name} de dia e ${night.name} à noite. ${hit.reason}`,
              productIds: [p.id, q.id],
            });
          }
        }
      }
    }
  }
  const covered = new Set(products.flatMap((p) => p.coversSteps));
  if (products.some(isPhoto) && !covered.has("protecao_solar")) {
    alerts.push({
      code: "sem_protetor_no_kit",
      severity: "atencao",
      text: "Este kit inclui produto que aumenta a sensibilidade ao sol e não tem protetor solar. Use protetor durante o dia.",
    });
  }
  return alerts.sort((a, b) => (a.severity === b.severity ? 0 : a.severity === "atencao" ? -1 : 1));
}

const TO_MG: Record<string, number> = { mcg: 0.001, mg: 1, g: 1000 };
/** Primeira dose do nome: [valor, unidade], com mcg/mg/g em mg. Igual ao motor. */
export function dose(name: string): [number, string] | null {
  const m = /(\d+(?:[.,]\d+)?)\s*(mcg|mg|g|ui|%)(?![a-z])/i.exec(name);
  if (!m) return null;
  const v = Number(m[1].replace(",", "."));
  const u = m[2].toLowerCase();
  return u in TO_MG ? [v * TO_MG[u], "mg"] : [v, u];
}

/** b é versão superior de a: mesmo tipo, preço maior e FPS estritamente maior (protetor) ou, com os mesmos ativos, dose
 * maior lida do nome (ex.: dipirona 500 mg -> 1 g). Sabor, embalagem maior ou marca de referência não contam. Igual ao motor. */
function betterItem(a: Product, b: Product): boolean {
  if (a.productType !== b.productType || b.priceCents <= a.priceCents) return false;
  if (a.fps || b.fps) return (b.fps ?? 0) > (a.fps ?? 0);
  const sameIngs = a.ingredients.length === b.ingredients.length && a.ingredients.every((i) => b.ingredients.includes(i));
  const da = dose(a.name);
  const db = dose(b.name);
  return sameIngs && !!da && !!db && da[1] === db[1] && db[0] > da[0];
}

/** Mesma quantidade e mesmas etapas, cada item igual ou em versão superior, e pelo menos um superior. */
function isUpgrade(base: Combo, c: Combo): boolean {
  const a = new Map(base.slots.map((s) => [s.step, s.product]));
  const b = new Map(c.slots.map((s) => [s.step, s.product]));
  if (a.size !== b.size || [...a.keys()].some((k) => !b.has(k))) return false;
  const ups = [...a.keys()].filter((k) => a.get(k)!.id !== b.get(k)!.id);
  return ups.length > 0 && ups.every((k) => betterItem(a.get(k)!, b.get(k)!));
}

/** c só troca itens de base por variações do mesmo item (mesmo tipo e ativos: embalagem, sabor), sem versão superior.
 * Ex.: psyllium 10 -> 30 sachês. Não serve de Completo para esse Essencial. Igual ao motor. */
function isVariant(base: Combo, c: Combo): boolean {
  const a = new Map(base.slots.map((s) => [s.step, s.product]));
  const b = new Map(c.slots.map((s) => [s.step, s.product]));
  if (a.size !== b.size || [...a.keys()].some((k) => !b.has(k))) return false;
  const ups = [...a.keys()].filter((k) => a.get(k)!.id !== b.get(k)!.id);
  const same = (x: Product, y: Product) =>
    x.productType === y.productType && x.ingredients.length === y.ingredients.length && x.ingredients.every((i) => y.ingredients.includes(i));
  return ups.length > 0 && ups.every((k) => same(a.get(k)!, b.get(k)!) && !betterItem(a.get(k)!, b.get(k)!));
}

/** Diz o que o Completo tem a mais que a faixa anterior, sem prometer o que a regra não garante (#31). Igual ao motor. */
function completeRationale(base: Combo, comp: Combo, baseName: string): string {
  const extra = comp.slots.length - base.slots.length;
  if (extra > 0) return `A opção mais completa: ${extra} ${extra === 1 ? "item" : "itens"} a mais que o ${baseName}.`;
  if (isUpgrade(base, comp)) return `Os mesmos tipos de item do ${baseName}, em versões superiores (ex.: dose ou proteção maior).`;
  return `Itens com maior relevância para o seu pedido que os do ${baseName}.`;
}

function rationaleFor(tier: KitTier, steps: StepId[], ctx: Ctx): string {
  const labels = listPt(steps.map((s) => STEP_LABEL[s].toLowerCase()));
  if (tier === "economico") return `Menor preço que cobre ${labels}.`;
  if (tier === "essencial")
    return `Seleção mais indicada para ${GOAL_LABEL[ctx.primary].toLowerCase()}${ctx.budgetCents != null ? ", dentro do orçamento" : ""}.`;
  return `A opção mais completa: cobre ${labels}.`;
}

export function assembleKit(
  tier: KitTier,
  slots: Slot[],
  ctx: Ctx,
  requestId: string,
  full: Map<StepId, Product[]>,
): Kit {
  const sorted = [...slots].sort((a, b) => STEP_ORDER.indexOf(a.step) - STEP_ORDER.indexOf(b.step));
  const items: KitItem[] = sorted.map((s) => ({
    step: s.step,
    product: s.product,
    reason: explainItem(s.product, ctx, s.step),
    alternativesCount: Math.max(0, (full.get(s.step)?.length ?? 1) - 1),
  }));
  const price = kitPrice(items.reduce((t, i) => t + i.product.priceCents, 0), items.length);
  const { totalCents } = price;
  const listTotalCents = items.reduce((t, i) => t + i.product.listPriceCents, 0);
  return {
    id: `k_${requestId}_${tier}`,
    tier,
    title: GOAL_LABEL[ctx.primary],
    goal: ctx.primary,
    items,
    ...price,
    listTotalCents,
    withinBudget: ctx.budgetCents == null ? true : totalCents <= ctx.budgetCents,
    cashbackCents: kitCashback(items.reduce((t, i) => t + cashbackOf(i.product), 0), price.discountPct),
    storeId: ctx.storeId,
    alerts: buildAlerts(items.map((i) => i.product)),
    rationale: rationaleFor(tier, items.map((i) => i.step), ctx),
  };
}

// ---------------------------------------------------------------------------
// Composição (K8 e K10)
// ---------------------------------------------------------------------------
export interface Composition {
  status: KitsStatus;
  kits: Kit[];
  closestKit: Kit | null;
  notes: string[];
}

export function compose(ctx: Ctx, requestId: string): Composition {
  const goal = GOALS.find((g) => g.id === ctx.primary)!;
  const notes: string[] = [];

  const full = new Map<StepId, Product[]>();
  const short = new Map<StepId, Product[]>();
  const relaxed: StepId[] = [];
  const stepsWanted = [...goal.requiredSteps, ...goal.optionalSteps];
  for (const step of stepsWanted) {
    const { list, relaxed: r } = candidatesFor(step, ctx);
    if (list.length === 0) continue;
    if (r) relaxed.push(step);
    full.set(step, list);
    short.set(step, shortlist(list, ctx));
  }

  const required = goal.requiredSteps;
  if (required.some((s) => !short.has(s))) {
    return {
      status: "not_applicable",
      kits: [],
      closestKit: null,
      notes: ["Não encontramos produtos suficientes para montar um kit completo com essas preferências."],
    };
  }
  for (const s of relaxed.filter((x) => required.includes(x))) {
    notes.push(
      `Há poucos produtos de ${STEP_LABEL[s].toLowerCase()} para pele ${ctx.skinType ?? ctx.assumedSkin}; incluímos o mais próximo.`,
    );
  }

  const allRequired = enumerate(required, short, ctx, null);
  if (allRequired.length === 0) {
    return { status: "not_applicable", kits: [], closestKit: null, notes: ["Não foi possível montar um kit compatível."] };
  }
  const econ = [...allRequired].sort(cmpCheap)[0];

  if (ctx.budgetCents != null && econ.total > ctx.budgetCents) {
    return {
      status: "none_in_budget",
      kits: [],
      closestKit: assembleKit("economico", econ.slots, ctx, requestId, full),
      notes: [],
    };
  }

  const effBudget = ctx.budgetCents ?? Math.round(econ.total * 2.0);
  const altBudget = ctx.budgetCents ?? Math.round(econ.total * 2.4);
  const maxB = Math.max(effBudget, altBudget);

  const optional = goal.optionalSteps.filter((s) => short.has(s));
  // toda combinação de opcionais que cabe no limite de 5 itens (K9), das maiores para as menores. Igual ao motor.
  const combos = (xs: StepId[], k: number): StepId[][] =>
    k === 0 ? [[]] : xs.flatMap((x, i) => combos(xs.slice(i + 1), k - 1).map((c) => [x, ...c]));
  const room = Math.max(0, 5 - required.length);
  const optSets: StepId[][] = [];
  for (let k = Math.min(room, optional.length); k >= 0; k--) optSets.push(...combos(optional, k));

  // #31: Econômico < Essencial < Completo no preço. Completo = mais itens (etapas opcionais) e, no empate, itens mais
  // relevantes; pode repetir itens do Essencial. Essencial = o mais relevante entre os dois em preço. Igual ao motor.
  const pool: Combo[] = [];
  const seen = new Set<string>();
  for (const set of optSets) {
    const part = set.length === 0 ? allRequired.filter((c) => c.total <= maxB) : enumerate([...required, ...set], short, ctx, maxB);
    for (const c of part) {
      const key = [...ids(c)].sort().join();
      if (!seen.has(key)) { seen.add(key); pool.push(c); }
    }
  }
  const n = (c: Combo) => c.slots.length;
  const byComplete = (a: Combo, b: Combo) => n(b) - n(a) || b.rel - a.rel || a.total - b.total || ids(a).join().localeCompare(ids(b).join());
  let comp: Combo | undefined = pool.filter((c) => c.total > econ.total && c.total <= altBudget).sort(byComplete)[0];
  let ess: Combo | undefined = pool
    .filter((c) => c.total > econ.total && c.total <= effBudget
      && (!comp || (c.total < comp.total && (n(c) < n(comp) || (c.relq < comp.relq && !isVariant(c, comp))))))
    .sort(cmpBest)[0];
  if (comp && !ess) {
    // sem meio-termo (ex.: só kits de 2 itens): Essencial = o mais relevante; Completo = mais itens ou a mesma cesta em
    // versão superior (upgrade). Se não houver, fica o Completo do passo anterior, sem Essencial. Igual ao motor.
    const e2 = pool.filter((c) => c.total > econ.total && c.total <= effBudget).sort(cmpBest)[0];
    const up = e2 ? pool.filter((c) => c.total > e2.total && c.total <= altBudget && (n(c) > n(e2) || isUpgrade(e2, c))) : [];
    if (up.length) {
      ess = e2;
      comp = up.sort(byComplete)[0];
    }
  }
  if (comp && !ess && !(n(comp) > n(econ) || isUpgrade(econ, comp))) {
    ess = comp; // 2º kit sem nada "a mais" que o Econômico: é um Essencial, não um Completo
    comp = undefined;
  }

  const kits: Kit[] = [assembleKit("economico", econ.slots, ctx, requestId, full)];
  if (ess) kits.push(assembleKit("essencial", ess.slots, ctx, requestId, full));
  if (comp) kits.push({ ...assembleKit("completo", comp.slots, ctx, requestId, full), rationale: completeRationale(ess ?? econ, comp, ess ? "Essencial" : "Econômico") });

  // K12: pedido explícito de combinação que o catálogo proíbe
  for (const i of INTERACTIONS) {
    if (i.severity === "evitar" && ctx.requestedIngredients.includes(i.a) && ctx.requestedIngredients.includes(i.b)) {
      const an = INGREDIENT_NAME.get(i.a) ?? i.a;
      const bn = INGREDIENT_NAME.get(i.b) ?? i.b;
      notes.push(`${an} e ${bn.toLowerCase()} não entram no mesmo kit. ${i.reason}`);
    }
  }
  if (kits.length === 1) notes.push("Só encontramos uma combinação relevante para esse pedido.");

  return { status: kits.length >= 2 ? "ok" : "partial", kits, closestKit: null, notes };
}

// ---------------------------------------------------------------------------
// Lista de produtos individuais
// ---------------------------------------------------------------------------
export function rankProducts(ctx: Ctx, limit = 30): Product[] {
  // pedido de remédio lista remédios; os demais pedidos não listam remédio (o motor real faz isso pela prateleira)
  const med = isHealthGoal(ctx.primary);
  const goal = GOALS.find((g) => g.id === ctx.primary)!;
  const goalSteps = new Set([...goal.requiredSteps, ...goal.optionalSteps]);
  // objetivo de saúde lista o que trata aquele objetivo (remédio ou não, ex.: psyllium); os demais não listam remédio
  const same = med ? PRODUCTS.filter((p) => p.coversSteps.some((s) => goalSteps.has(s))) : PRODUCTS.filter((p) => p.domain !== "medicamento");
  const strict = same.filter((p) => baseEligible(p, ctx, false));
  const pool = strict.length >= 8 ? strict : same.filter((p) => baseEligible(p, ctx, true));
  return [...pool].sort(cmpProducts(ctx)).slice(0, limit);
}

// ---------------------------------------------------------------------------
// Troca de item
// ---------------------------------------------------------------------------
function coveredBy(products: Product[]): Set<StepId> {
  return new Set(products.flatMap((p) => p.coversSteps));
}

function swapCompat(
  kit: Kit,
  idx: number,
  cand: Product,
): { compatible: boolean; reason?: string } | null {
  const others = kit.items.filter((_, i) => i !== idx).map((i) => i.product);
  const covOthers = coveredBy(others);
  if (cand.coversSteps.some((s) => covOthers.has(s))) return null; // sobreposição: nem mostra
  if (others.some((o) => o.productType === cand.productType)) return null;
  const before = coveredBy(kit.items.map((i) => i.product));
  const after = new Set([...covOthers, ...cand.coversSteps]);
  const lost = [...before].filter((s) => !after.has(s));
  if (lost.length) return { compatible: false, reason: `Deixaria o kit sem ${STEP_LABEL[lost[0]].toLowerCase()}.` };
  for (const o of others) {
    const c = conflictBetween(o, cand);
    if (c) return { compatible: false, reason: `Não combina com ${o.name}. ${c.reason}` };
  }
  if (isPhoto(cand) && !after.has("protecao_solar")) {
    return { compatible: false, reason: "Pede protetor solar no kit." };
  }
  return { compatible: true };
}

export function swapOptions(kit: Kit, step: StepId, ctx: Ctx): SwapOption[] {
  const idx = kit.items.findIndex((i) => i.step === step);
  if (idx < 0) return [];
  const cur = kit.items[idx].product;
  const out: Array<SwapOption & { s: number }> = [];
  for (const p of KIT_POOL) {
    if (p.id === cur.id || !p.coversSteps.includes(step)) continue;
    if (!baseEligible(p, ctx, false)) continue;
    const compat = swapCompat(kit, idx, p);
    if (!compat) continue;
    out.push({
      product: p,
      deltaCents: p.priceCents - cur.priceCents,
      compatible: compat.compatible,
      reason: compat.reason,
      s: score(p, ctx),
    });
  }
  out.sort(
    (a, b) =>
      Number(b.compatible) - Number(a.compatible) || b.s - a.s || a.product.priceCents - b.product.priceCents || a.product.id.localeCompare(b.product.id),
  );
  const good = out.filter((o) => o.compatible).slice(0, 10);
  const bad = out.filter((o) => !o.compatible).slice(0, 3);
  return [...good, ...bad].map(({ s: _s, ...rest }) => rest);
}

export function applySwap(kit: Kit, step: StepId, productId: string, ctx: Ctx): Kit {
  const idx = kit.items.findIndex((i) => i.step === step);
  const cand = PRODUCTS.find((p) => p.id === productId);
  if (idx < 0 || !cand) throw new Error("Troca inválida.");
  if (cand.domain === "medicamento") throw new Error("Remédio não entra em kit."); // K13
  const compat = swapCompat(kit, idx, cand);
  if (!compat || !compat.compatible) throw new Error(compat?.reason ?? "Produto incompatível com o kit.");
  if (!baseEligible(cand, ctx, false)) throw new Error("Produto indisponível para essas preferências.");
  const items = kit.items.map((it, i) =>
    i === idx ? { ...it, product: cand, reason: `Escolhido por você. ${explainItem(cand, ctx, step)}` } : it,
  );
  const price = kitPrice(items.reduce((t, i) => t + i.product.priceCents, 0), items.length);
  const { totalCents } = price;
  const listTotalCents = items.reduce((t, i) => t + i.product.listPriceCents, 0);
  return {
    ...kit,
    items,
    ...price,
    listTotalCents,
    withinBudget: ctx.budgetCents == null ? true : totalCents <= ctx.budgetCents,
    cashbackCents: kitCashback(items.reduce((t, i) => t + cashbackOf(i.product), 0), price.discountPct),
    storeId: ctx.storeId,
    alerts: buildAlerts(items.map((i) => i.product)),
    rationale: kit.rationale.endsWith("(editado)") ? kit.rationale : `${kit.rationale} (editado)`,
  };
}


// ---------------------------------------------------------------------------
// Adaptar um kit a uma loja: troca só os itens sem estoque nela, pela mesma etapa,
// mantendo as regras (sem repetição, sem conflito). null = não dá para completar.
// ---------------------------------------------------------------------------
export interface Adaptation {
  kit: Kit;
  replaced: Array<{ step: StepId; from: Product; to: Product }>;
}

export function adaptToStore(kit: Kit, storeId: string, ctx: Ctx): Adaptation | null {
  const storeCtx: Ctx = { ...ctx, storeId };
  let current: Kit = { ...kit, storeId };
  const replaced: Adaptation["replaced"] = [];
  for (const item of kit.items) {
    if (stockAt(item.product.id, storeId) > 0) continue;
    const opts = swapOptions(current, item.step, storeCtx).filter((o) => o.compatible);
    if (opts.length === 0) return null;
    // a mais parecida no preço entre as 3 mais relevantes
    const pick = opts.slice(0, 3).sort((a, b) => Math.abs(a.deltaCents) - Math.abs(b.deltaCents))[0];
    current = applySwap(current, item.step, pick.product.id, storeCtx);
    const idx = current.items.findIndex((i) => i.step === item.step);
    current.items[idx] = {
      ...current.items[idx],
      reason: `Trocado por falta de estoque na loja. ${explainItem(pick.product, storeCtx, item.step)}`,
    };
    replaced.push({ step: item.step, from: item.product, to: pick.product });
  }
  return { kit: { ...current, storeId }, replaced };
}
