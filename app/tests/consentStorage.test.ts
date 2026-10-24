import { afterEach, describe, expect, it } from "vitest";
import { readExternalChoice, saveExternalChoice } from "../src/services/consentStorage";

// #42: a escolha de desligar o serviço externo sobrevive a recarregar a página
describe("escolha do serviço externo guardada no aparelho", () => {
  afterEach(() => { delete (globalThis as { localStorage?: unknown }).localStorage; });
  const fake = () => {
    const m = new Map<string, string>();
    (globalThis as { localStorage?: unknown }).localStorage = { getItem: (k: string) => m.get(k) ?? null, setItem: (k: string, v: string) => void m.set(k, v) };
  };
  it("guarda e lê as duas escolhas", () => {
    fake();
    expect(readExternalChoice()).toBeUndefined();   // nunca escolheu: vale o padrão da persona
    saveExternalChoice(false);
    expect(readExternalChoice()).toBe(false);
    saveExternalChoice(true);
    expect(readExternalChoice()).toBe(true);
  });
  it("sem armazenamento (bloqueado ou indisponível) não quebra", () => {
    expect(readExternalChoice()).toBeUndefined();
    expect(() => saveExternalChoice(false)).not.toThrow();
  });
});
