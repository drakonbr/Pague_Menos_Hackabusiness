// MOCK dos serviços de comércio que já existem no sistema real (catálogo, lojas, estoque, frete).
// No sistema real, cada método vira um adaptador fino para o serviço correspondente (doc 10).
import type { CommerceService, Product, SortKey, StoreAvailability } from "../../contracts/types";
import { CATEGORIES, COMMERCE, CONCERN_LABEL, INGREDIENT_NAME, PRODUCTS, PRODUCT_BY_ID, STORES, WARNING_TEXT, stockAt } from "./catalogData";

import { SIMULATED_LOCATION } from "../../location";

export function distanceKm(a: { lat: number; lng: number }, b: { lat: number; lng: number }): number {
  const R = 6371;
  const rad = (d: number) => (d * Math.PI) / 180;
  const dLat = rad(b.lat - a.lat);
  const dLng = rad(b.lng - a.lng);
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(rad(a.lat)) * Math.cos(rad(b.lat)) * Math.sin(dLng / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(h));
}

export function sortProducts(list: Product[], sort: SortKey = "relevancia"): Product[] {
  const inStockFirst = (a: Product, b: Product) => Number(b.stockQty > 0) - Number(a.stockQty > 0);
  const copy = [...list];
  switch (sort) {
    case "menor_preco":
      return copy.sort((a, b) => inStockFirst(a, b) || a.priceCents - b.priceCents || a.id.localeCompare(b.id));
    case "maior_preco":
      return copy.sort((a, b) => inStockFirst(a, b) || b.priceCents - a.priceCents || a.id.localeCompare(b.id));
    default:
      return copy.sort((a, b) => inStockFirst(a, b) || a.salesRank - b.salesRank);
  }
}

export function createMockCommerceService(opts: { latencyMs?: number } = {}): CommerceService {
  const wait = () => (opts.latencyMs ? new Promise<void>((r) => setTimeout(r, opts.latencyMs)) : Promise.resolve());

  return {
    async home() {
      await wait();
      return {
        showcases: COMMERCE.showcases,
        kitPresets: COMMERCE.kitPresets,
        categories: CATEGORIES,
        banners: COMMERCE.banners,
      };
    },
    async categories() {
      await wait();
      return CATEGORIES;
    },
    async product(id) {
      await wait();
      return PRODUCT_BY_ID.get(id) ?? null;
    },
    async products(ids, sort) {
      await wait();
      return sortProducts(
        ids.map((id) => PRODUCT_BY_ID.get(id)).filter((p): p is Product => !!p),
        sort,
      );
    },
    async storesFor(productIds) {
      await wait();
      const out: StoreAvailability[] = STORES.map((store) => {
        const availableIds = productIds.filter((id) => stockAt(id, store.id) > 0);
        return {
          store,
          distanceKm: Math.round(distanceKm(SIMULATED_LOCATION, store) * 10) / 10,
          availableIds,
          missingIds: productIds.filter((id) => !availableIds.includes(id)),
        };
      });
      return out.sort((a, b) => a.distanceKm - b.distanceKm || a.store.id.localeCompare(b.store.id));
    },
    async labels() {
      await wait();
      return { warnings: { ...WARNING_TEXT }, concerns: { ...CONCERN_LABEL }, ingredients: Object.fromEntries(INGREDIENT_NAME) };
    },
    async delivery() {
      await wait();
      return { options: COMMERCE.delivery, freeShippingFromCents: COMMERCE.freeShippingFromCents };
    },
  };
}

export const ALL_PRODUCTS = PRODUCTS;
