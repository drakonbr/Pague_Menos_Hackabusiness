import type {
  Intent,
  Kit,
  KitAdaptation,
  Product,
  SearchRequest,
  SearchResponse,
  SearchService,
  SimilarsResponse,
  StepId,
  SwapOption,
} from "../contracts/types";
import { PRODUCT_BY_ID } from "./mock/catalogData";
import { createMockSearchService } from "./mock/mockSearchService";

export const DEFAULT_ENGINE_URL = "http://127.0.0.1:8787";

/** O motor devolve produtos sem foto; as fotos (banco de imagens) moram no app. Preço e estoque vêm sempre do motor. */
export function withImages<T extends Product>(p: T): T {
  const local = PRODUCT_BY_ID.get(p.id);
  return local && local.images.length && !p.images.length ? { ...p, images: local.images } : p;
}
function enrichKit(k: Kit): Kit {
  return { ...k, items: k.items.map((i) => ({ ...i, product: withImages(i.product) })) };
}
function enrichResponse(r: SearchResponse): SearchResponse {
  return { ...r, kits: r.kits.map(enrichKit), closestKit: r.closestKit ? enrichKit(r.closestKit) : null, products: r.products.map(withImages) };
}

/**
 * Cliente HTTP do motor GraphRAG (graphrag/service/server.py). Segue o contrato em contracts/README.md.
 * O app envia a frase, o `context` da resposta anterior e ids de produto. Nunca dados de saúde da pessoa.
 */
export class HttpSearchService implements SearchService {
  readonly engine = "graphrag" as const;
  constructor(
    private readonly baseUrl: string,
    private readonly fetchImpl: typeof fetch = (...a) => fetch(...a),
  ) {}

  async health(timeoutMs = 4000): Promise<boolean> {
    const ctl = new AbortController();
    const t = setTimeout(() => ctl.abort(), timeoutMs);
    try {
      const res = await this.fetchImpl(`${this.baseUrl}/v1/health`, { signal: ctl.signal });
      return res.ok;
    } catch {
      return false;
    } finally {
      clearTimeout(t);
    }
  }

  private async post<T>(path: string, body: unknown): Promise<T> {
    const res = await this.fetchImpl(`${this.baseUrl}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      let detail = "";
      try {
        detail = ((await res.json()) as { error?: string }).error ?? "";
      } catch {
        /* sem corpo */
      }
      throw new Error(detail || `Falha ao consultar o serviço (${res.status}).`);
    }
    return (await res.json()) as T;
  }

  async search(req: SearchRequest): Promise<SearchResponse> {
    return enrichResponse(await this.post<SearchResponse>("/v1/search", req));
  }
  async swapOptions(kit: Kit, step: StepId, intent: Intent): Promise<SwapOption[]> {
    const opts = await this.post<SwapOption[]>("/v1/kits/swap-options", { kit, step, intent });
    return opts.map((o) => ({ ...o, product: withImages(o.product) }));
  }
  async swap(kit: Kit, step: StepId, productId: string, intent: Intent): Promise<Kit> {
    return enrichKit(await this.post<Kit>("/v1/kits/swap", { kit, step, productId, intent }));
  }
  async adaptToStore(kit: Kit, storeId: string, intent: Intent): Promise<KitAdaptation | null> {
    const r = await this.post<KitAdaptation | null>("/v1/kits/adapt-to-store", { kit, storeId, intent });
    return r ? { kit: enrichKit(r.kit), replaced: r.replaced.map((x) => ({ ...x, from: withImages(x.from), to: withImages(x.to) })) } : null;
  }
  async similars(productId: string, storeId: string | null): Promise<SimilarsResponse> {
    const r = await this.post<SimilarsResponse>("/v1/similars", { productId, storeId });
    return { ...r, options: r.options.map((o) => ({ ...o, product: withImages(o.product) })) };
  }
}

/**
 * Padrão do app: tenta o GraphRAG local; se o servidor não responder, cai no motor simulado (sem conversa
 * de vários turnos e sem o ranking híbrido). O selo "Motor" da conversa mostra qual está respondendo.
 */
class AutoSearchService implements SearchService {
  private mode: "graphrag" | "simulado" | null = null;
  private probe: Promise<void> | null = null;
  private readonly http: HttpSearchService;
  private readonly mock = createMockSearchService({ latencyMs: 250 });
  constructor(url: string) {
    this.http = new HttpSearchService(url);
  }
  get engine(): "graphrag" | "simulado" {
    return this.mode ?? "simulado";
  }
  private async pick(): Promise<SearchService> {
    this.probe ??= this.http.health().then((ok) => {
      this.mode = ok ? "graphrag" : "simulado";
    });
    await this.probe;
    return this.mode === "graphrag" ? this.http : this.mock;
  }
  private async run<T>(fn: (s: SearchService) => Promise<T>): Promise<T> {
    const svc = await this.pick();
    try {
      return await fn(svc);
    } catch (e) {
      // servidor caiu no meio da sessão: continua no simulado em vez de travar a tela
      if (svc === this.http && e instanceof TypeError) {
        this.mode = "simulado";
        return fn(this.mock);
      }
      throw e;
    }
  }
  search(req: SearchRequest) { return this.run((s) => s.search(req)); }
  swapOptions(kit: Kit, step: StepId, intent: Intent) { return this.run((s) => s.swapOptions(kit, step, intent)); }
  swap(kit: Kit, step: StepId, productId: string, intent: Intent) { return this.run((s) => s.swap(kit, step, productId, intent)); }
  adaptToStore(kit: Kit, storeId: string, intent: Intent) { return this.run((s) => s.adaptToStore(kit, storeId, intent)); }
  similars(productId: string, storeId: string | null) { return this.run((s) => s.similars(productId, storeId)); }
}

/** VITE_SEARCH_BACKEND = auto (padrão) | mock | http; VITE_SEARCH_URL aponta para o GraphRAG. */
export function createSearchService(): SearchService {
  const backend = import.meta.env.VITE_SEARCH_BACKEND ?? "auto";
  const url = import.meta.env.VITE_SEARCH_URL ?? DEFAULT_ENGINE_URL;
  if (backend === "http") return new HttpSearchService(url);
  if (backend === "mock") return createMockSearchService({ latencyMs: 350 });
  return new AutoSearchService(url);
}
