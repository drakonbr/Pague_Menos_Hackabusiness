import type {
  Intent,
  Kit,
  KitAdaptation,
  SearchRequest,
  SearchResponse,
  SearchService,
  StepId,
  SwapOption,
} from "../contracts/types";
import { createMockSearchService } from "./mock/mockSearchService";

/**
 * Cliente HTTP do motor real (GraphRAG). Segue o contrato em contracts/README.md.
 * ATENÇÃO: ainda não foi exercitado, porque o servidor GraphRAG não existe nesta fase.
 */
class HttpSearchService implements SearchService {
  constructor(private readonly baseUrl: string) {}

  private async post<T>(path: string, body: unknown): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`Falha ao consultar o serviço (${res.status}).`);
    return (await res.json()) as T;
  }

  search(req: SearchRequest): Promise<SearchResponse> {
    return this.post("/v1/search", req);
  }
  swapOptions(kit: Kit, step: StepId, intent: Intent): Promise<SwapOption[]> {
    return this.post("/v1/kits/swap-options", { kit, step, intent });
  }
  swap(kit: Kit, step: StepId, productId: string, intent: Intent): Promise<Kit> {
    return this.post("/v1/kits/swap", { kit, step, productId, intent });
  }
  adaptToStore(kit: Kit, storeId: string, intent: Intent): Promise<KitAdaptation | null> {
    return this.post("/v1/kits/adapt-to-store", { kit, storeId, intent });
  }
}

/** VITE_SEARCH_BACKEND=mock (padrão) | http, com VITE_SEARCH_URL apontando para o GraphRAG. */
export function createSearchService(): SearchService {
  const backend = import.meta.env.VITE_SEARCH_BACKEND ?? "mock";
  if (backend === "http") {
    const url = import.meta.env.VITE_SEARCH_URL;
    if (!url) throw new Error("Defina VITE_SEARCH_URL para usar o backend http.");
    return new HttpSearchService(url);
  }
  return createMockSearchService({ latencyMs: 350 });
}
