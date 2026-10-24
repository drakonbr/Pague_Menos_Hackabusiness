import { describe, expect, it } from "vitest";
import resultsSrc from "../src/screens/Results.tsx?raw";
import chatSrc from "../src/screens/Chat.tsx?raw";
import { checkResponse } from "../src/services/contractChecks";
import { createMockSearchService } from "../src/services/mock/mockSearchService";
import { ALERT_MESSAGE, CRISIS_MESSAGE, urgency } from "../src/services/urgency";

// #63: as mesmas frases de graphrag/tests/test_urgencia_cota.py (o motor e o simulador têm de concordar)
const CRISE = ["quero me matar, que remédio tomo", "to pensando em suicídio", "não quero mais viver", "vontade de me cortar", "quero morrer", "tomei todos os comprimidos", "melhor eu morrer", "quero me mata", "queria sumir de vez", "não vejo mais sentido na vida", "tentei me cortar", "vou morrer", "cansei de tudo", "pensando em me machucar", "tomei um monte de remédio", "tomei 10 comprimidos de dipirona de uma vez"];
const ALERTA = ["dor no peito e falta de ar", "cagando sangue", "urticária e língua inchada", "cabeça explodindo e rigidez no pescoço",
  "pior dor de cabeça da minha vida", "tosse com sangue", "desmaiei agora", "meu filho engoliu veneno", "minha boca está torta", "não tô conseguindo respirar", "falta d ar", "evacuando sangue", "minha língua tá inchando", "pescoço duro com febre", "minha boca entortou", "tomei veneno", "suspeita de AVC", "febre de 41", "dor no ombro esquerdo irradiando", "meu bebê engoliu uma pilha", "meu bebê não respira", "lábios roxos", "cobra picou meu cachorro", "engasgou", "formigamento no braço esquerdo e suor frio", "visão turva e fala arrastada", "sangue na calcinha", "acho que estou tendo um infarto", "meu pai não acorda", "ele desmaiou"];
const NORMAL = ["estou morrendo de rir", "quero morrer de vergonha", "matar as espinhas", "dor no peito do pé", "dor de cabeça",
  "pele oleosa até R$ 100", "tosse seca", "dor no joelho", "vomitei duas vezes", "sem ar condicionado", "quero um quarto sem ar", "pneu sem ar", "apaguei a luz", "tirar a minha vida social", "falta de ar condicionado", "inchaço no rosto de um dente", "meu pai teve AVC, que suplemento ajuda?", "colesterol alto e risco de infarto", "tenho infarto na família, quero omega 3", "derrame de óleo", "estou sem ar fresco", "lábios inchados de piercing", "desmaiar de cansaço? quero vitamina", "dor no ombro esquerdo depois do treino", "o cabelo não acorda hidratado", "tomei todos os comprimidos que o médico mandou, posso repor?"];

describe("urgência (#63)", () => {
  it("detecta como o motor", () => {
    for (const q of CRISE) expect(urgency(q)?.category, q).toBe("risco_de_vida");
    for (const q of ALERTA) expect(urgency(q)?.category, q).toBe("sinal_de_alerta");
    for (const q of NORMAL) expect(urgency(q), q).toBeNull();
  });
  it("o simulador responde fixo, sem produtos nem kits", async () => {
    const svc = createMockSearchService({ latencyMs: 0 });
    for (const [q, msg] of [["quero me matar, que remédio tomo", CRISIS_MESSAGE], ["dor no peito e falta de ar", ALERT_MESSAGE]] as const) {
      const r = await svc.search({ query: q });
      expect(r.safety.decision).toBe("urgent");
      expect(r.reply).toBe(msg);
      expect([r.products.length, r.kits.length, (r.suggestions ?? []).length]).toEqual([0, 0, 0]);
      expect(checkResponse(r)).toEqual([]);
    }
  });
  it("as telas mostram o aviso em destaque", () => {
    expect(resultsSrc).toContain('className="note urgent"');
    expect(chatSrc).toContain('role={m.res?.safety.decision === "urgent" ? "alert" : undefined}');
  });
});
