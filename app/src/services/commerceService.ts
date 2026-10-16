import type { CommerceService } from "../contracts/types";
import { createMockCommerceService } from "./mock/mockCommerceService";

/**
 * Serviços de comércio (catálogo, lojas, estoque, frete). No sistema real, são adaptadores para
 * os serviços que já existem no e-commerce (doc 10). Nesta fase só existe o simulado.
 */
export function createCommerceService(): CommerceService {
  return createMockCommerceService({ latencyMs: 200 });
}
