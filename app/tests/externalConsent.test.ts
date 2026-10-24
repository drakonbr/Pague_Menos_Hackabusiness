import { describe, expect, it } from "vitest";
import { PERSONA } from "../src/persona";
import { HttpSearchService, externalLanguage } from "../src/services/searchService";

// #42 (LGPD): o consentimento "serviço de linguagem externo" existe, é informado na Privacidade e viaja em toda busca
describe("serviço externo de linguagem (#42)", () => {
  const bodies: Array<Record<string, unknown>> = [];
  const fakeFetch = (async (_url: string, init: RequestInit) => {
    bodies.push(JSON.parse(String(init.body)));
    return new Response(JSON.stringify({ kits: [], products: [], notes: [], suggestions: [], context: {}, intent: {} }), { status: 200 });
  }) as unknown as typeof fetch;

  it("a persona traz o consentimento como booleano", () => {
    expect(typeof PERSONA.privacy.consent.useExternalLanguageService).toBe("boolean");
  });
  it("a busca envia allowExternal conforme a escolha da pessoa", async () => {
    const svc = new HttpSearchService("http://motor", fakeFetch);
    externalLanguage.allowed = true;
    await svc.search({ query: "pele oleosa" });
    externalLanguage.allowed = false;
    await svc.search({ query: "pele oleosa" });
    externalLanguage.allowed = true;
    expect(bodies.map((b) => b.allowExternal)).toEqual([true, false]);
  });
  it("lê da saúde do servidor se a DeepSeek está ligada (#60)", async () => {
    for (const [body, esperado] of [[{ ok: true, rag: true }, true], [{ ok: true, rag: false }, false], [{ ok: true }, undefined]] as const) {
      const f = (async () => new Response(JSON.stringify(body), { status: 200 })) as unknown as typeof fetch;
      const svc = new HttpSearchService("http://motor", f);
      expect(await svc.health()).toBe(true);
      expect(svc.rag).toBe(esperado);
    }
  });
});
