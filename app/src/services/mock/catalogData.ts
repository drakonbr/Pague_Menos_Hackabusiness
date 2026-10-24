// DADOS SIMULADOS. Os JSON em ../../mocks são gerados por tools/export_app_mock.py
// a partir do catálogo fictício. Em produção este arquivo deixa de existir: o app
// passa a chamar o serviço real (ver ../searchService.ts).
import productsJson from "../../mocks/products.mock.json";
import concernsJson from "../../mocks/concerns.mock.json";
import goalsJson from "../../mocks/goals.mock.json";
import interactionsJson from "../../mocks/interactions.mock.json";
import ingredientsJson from "../../mocks/ingredients.mock.json";
import warningsJson from "../../mocks/warnings.mock.json";
import storesJson from "../../mocks/stores.mock.json";
import commerceJson from "../../mocks/commerce.mock.json";
import categoriesJson from "../../mocks/categories.mock.json";
import type {
  Category,
  DeliveryOption,
  GoalId,
  KitPreset,
  Product,
  ProductImage,
  Showcase,
  StepId,
  Store,
  WarningCode,
} from "../../contracts/types";

export interface GoalDef {
  id: GoalId;
  label: string;
  concerns: string[];
  requiredSteps: StepId[];
  optionalSteps: StepId[];
  synonyms: string[];
}

export interface Interaction {
  a: string;
  b: string;
  severity: "evitar" | "separar";
  reason: string;
}

export interface Ingredient {
  id: string;
  name: string;
  family: string;
  function: string;
  photosensitizing: boolean;
}

/** #41 (RDC 96/2008): remédio de prescrição nunca tem preço riscado, venha o dado como vier. */
export const noStrike = <T extends Product>(p: T): T => ((p.rx || p.domain === "medicamento") && p.listPriceCents !== p.priceCents ? { ...p, listPriceCents: p.priceCents } : p);
export const PRODUCTS = (productsJson as unknown as Product[]).map(noStrike);
export const GOALS = goalsJson as unknown as GoalDef[];
export const INTERACTIONS = interactionsJson as unknown as Interaction[];
export const INGREDIENTS = ingredientsJson as unknown as Ingredient[];
export const WARNING_TEXT = warningsJson as unknown as Record<WarningCode, string>;

export const PRODUCT_BY_ID = new Map(PRODUCTS.map((p) => [p.id, p]));

// Ecossistema (lojas fictícias, estoque por loja, frete, vitrines, categorias)
type StoreWithStock = Store & { stock: Record<string, number> };
const STORES_RAW = storesJson as unknown as StoreWithStock[];
export const STORES: Store[] = STORES_RAW.map(({ stock: _stock, ...s }) => s);
export const STORE_BY_ID = new Map(STORES.map((s) => [s.id, s]));
export const STORE_STOCK = new Map(STORES_RAW.map((s) => [s.id, s.stock]));
export const COMMERCE = commerceJson as unknown as {
  freeShippingFromCents: number;
  delivery: DeliveryOption[];
  showcases: Showcase[];
  kitPresets: KitPreset[];
  banners: ProductImage[];
  note: string;
};
export const CATEGORIES = (categoriesJson as unknown as { nodes: Category[] }).nodes;

/** Estoque de um produto: na loja (se houver loja) ou no centro de distribuição. */
export function stockAt(productId: string, storeId: string | null | undefined): number {
  if (!storeId) return PRODUCT_BY_ID.get(productId)?.stockQty ?? 0;
  return STORE_STOCK.get(storeId)?.[productId] ?? 0;
}

export function cashbackOf(p: Product): number {
  return Math.floor((p.priceCents * p.cashbackPct) / 100);
}
export const INGREDIENT_NAME = new Map(INGREDIENTS.map((i) => [i.id, i.name]));

export const CONCERN_LABEL: Record<string, string> = concernsJson;
