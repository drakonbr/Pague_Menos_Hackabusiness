import { describe, expect, it } from "vitest";
import { SEARCH_HINT } from "../src/components/SearchHint";

describe("texto da barra de busca (#26)", () => {
  it("é a pergunta escolhida pela Julia", () => {
    expect(SEARCH_HINT).toBe("O que você está precisando hoje?");
  });
});
