import { describe, expect, it } from "vitest";
import { showsTabBar } from "../src/nav";

describe("barra de abas (#27)", () => {
  it("aparece no chat aberto pela aba Chat", () => {
    expect(showsTabBar({ name: "chat" }, "chat", 1)).toBe(true);
  });
  it("some no chat aberto por uma busca de conversa (tela cheia, com voltar)", () => {
    expect(showsTabBar({ name: "chat", initial: "repor meus remédios" }, "home", 3)).toBe(false);
    expect(showsTabBar({ name: "chat", initial: "x" }, "chat", 2)).toBe(false);
  });
  it("continua sumindo na cesta e no pagamento e aparecendo nas telas comuns", () => {
    expect(showsTabBar({ name: "cart" }, "home", 2)).toBe(false);
    expect(showsTabBar({ name: "payment" }, "home", 4)).toBe(false);
    expect(showsTabBar({ name: "home" }, "home", 1)).toBe(true);
    expect(showsTabBar({ name: "categorias" }, "home", 2)).toBe(true);
  });
});
