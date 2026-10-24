// #50: item de reposição que a loja escolhida não tem só entra na conta depois que a pessoa escolhe um equivalente em estoque.
import type { StoreAvailability } from "./contracts/types";

export function hasStockHere(opts: {
  productId: string;
  chosenId?: string;                 // equivalente escolhido (veio da lista de equivalentes com estoque)
  avail?: StoreAvailability[];
  storeId: string | null;
  centralStockQty?: number;          // estoque central, quando não há loja escolhida
}): boolean {
  if (opts.chosenId && opts.chosenId !== opts.productId) return true;
  if (!opts.storeId || !opts.avail) return (opts.centralStockQty ?? 0) > 0;
  return !!opts.avail.find((a) => a.store.id === opts.storeId)?.availableIds.includes(opts.productId);
}
