// MOCK da interpretação de intenção e da camada de segurança.
// No sistema real isto vira: regras de segurança + extração por modelo (docs 06 e 07).
import type { GoalId, Intent, Safety, SafetyCategory, SearchRequest, SkinType } from "../../contracts/types";
import { GOALS } from "./catalogData";

export function norm(s: string): string {
  return s
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "");
}

const GOAL_PRIORITY: GoalId[] = [
  "acne",
  "manchas",
  "anti_idade",
  "protecao_solar",
  "skincare_basico",
  "pele_sensivel",
  "oleosidade",
];

// Sinônimos extras só da versão simulada (o catálogo traz os principais).
const EXTRA_SYNONYMS: Partial<Record<GoalId, string[]>> = {
  anti_idade: ["retinol", "firmeza"],
  manchas: ["vitamina c"],
  protecao_solar: ["bloqueador"],
};

const SKIN_PATTERNS: Array<[RegExp, SkinType]> = [
  [/\b(sensivel|sensiveis)\b/, "sensível"],
  [/\b(oleosa|oleosas|oleosidade|brilho)\b/, "oleosa"],
  [/\b(seca|secas|ressecada)\b/, "seca"],
  [/\b(mista)\b/, "mista"],
  [/\bpele normal\b/, "normal"],
];

// preferência -> claim do catálogo
const PREFERENCE_PATTERNS: Array<[RegExp, string]> = [
  [/\b(vegano|vegana|veganos|veganas)\b/, "vegano"],
  [/\b(sem fragrancia|sem perfume)\b/, "sem fragrância"],
  [/\b(sem alcool)\b/, "sem álcool"],
  [/\b(oil[- ]?free|sem oleo)\b/, "oil free"],
  [/\b(mineral)\b/, "filtro mineral"],
  [/\b(com cor|colorido)\b/, "com cor"],
  [/\b(toque seco)\b/, "toque seco"],
];

const INGREDIENT_MENTIONS: Array<[RegExp, string]> = [
  [/\bretinol\b/, "retinol"],
  [/\b(acido )?glicolico\b/, "acido_glicolico"],
  [/\bvitamina c\b/, "vitamina_c"],
  [/\bniacinamida\b/, "niacinamida"],
  [/\bsalicilico\b/, "acido_salicilico"],
];

export function parseBudgetCents(q: string): number | null {
  const m1 = q.match(/r\$\s*(\d{1,4}(?:[.,]\d{1,2})?)/);
  const m2 = q.match(/\b(?:ate|no maximo|maximo de|por ate|menos de|abaixo de)\s*(?:r\$\s*)?(\d{1,4}(?:[.,]\d{1,2})?)/);
  const raw = (m1 ?? m2)?.[1];
  if (!raw) return null;
  const value = parseFloat(raw.replace(",", "."));
  return Number.isFinite(value) && value > 0 ? Math.round(value * 100) : null;
}

export interface ParsedIntent {
  intent: Intent;
  requestedIngredients: string[];
  understood: boolean;
  normalized: string;
}

export function parseIntent(req: SearchRequest): ParsedIntent {
  const q = norm(req.query);

  const matched = new Set<GoalId>();
  for (const g of GOALS) {
    const syns = [...g.synonyms, ...(EXTRA_SYNONYMS[g.id] ?? [])].map(norm);
    if (syns.some((s) => new RegExp(`\\b${s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\b`).test(q))) {
      matched.add(g.id);
    }
  }

  let skinType: SkinType | null = null;
  for (const [re, skin] of SKIN_PATTERNS) {
    if (re.test(q)) {
      skinType = skin;
      break;
    }
  }

  let understood = matched.size > 0;
  if (!understood && (/\bpele\b/.test(q) || /\bkit\b/.test(q) || skinType)) {
    matched.add("skincare_basico");
    understood = true;
  }

  const goals = GOAL_PRIORITY.filter((g) => matched.has(g));
  const primaryGoal = goals[0] ?? null;

  if (!skinType && primaryGoal === "pele_sensivel") skinType = "sensível";
  if (!skinType && primaryGoal === "oleosidade") skinType = "oleosa";

  const preferences = new Set<string>(req.preferences ?? []);
  for (const [re, claim] of PREFERENCE_PATTERNS) if (re.test(q)) preferences.add(claim);

  const requestedIngredients = INGREDIENT_MENTIONS.filter(([re]) => re.test(q)).map(([, id]) => id);
  const pregnancy = /\b(gravida|gestante|gravidez|gestacao|amamentando|amamentacao|lactante)\b/.test(q);

  // Sobrescritas explícitas (chips editados, controle de orçamento, resposta à pergunta)
  const budgetCents = req.budgetCents !== undefined ? req.budgetCents : parseBudgetCents(q);
  if (req.skinType !== undefined) skinType = req.skinType;

  const missing: Intent["missing"] = [];
  if (!skinType) missing.push("skinType");
  if (budgetCents == null) missing.push("budget");

  return {
    intent: {
      goals,
      primaryGoal,
      budgetCents,
      skinType,
      preferences: [...preferences],
      pregnancy,
      storeId: req.storeId ?? null,
      missing,
    },
    requestedIngredients,
    understood,
    normalized: q,
  };
}

// ---------------------------------------------------------------------------
// Segurança (doc 07). Regras determinísticas, rodam antes de qualquer outra coisa.
// ---------------------------------------------------------------------------
const BLOCK_RULES: Array<[SafetyCategory, RegExp, string]> = [
  [
    "medicamento",
    /\b(remedio|remedios|medicamento|medicamentos|antibiotico\w*|anti-?inflamatorio\w*|corticoide\w*|isotretinoina|roacutan|analgesico\w*|dipirona|paracetamol|ibuprofeno|receita|posologia|comprimido\w*|dose|o que (eu )?(posso )?tomar)\b/,
    "medicamentos",
  ],
  ["sintoma", /\b(dor|dores|febre|coceira|sangramento|sangrando|inchaco|tontura|nausea|enjoo|tosse|vomito)\b/, "sintomas de saúde"],
  [
    "condicao_de_saude",
    /\b(dermatite|psoriase|rosacea|micose|infeccao|infeccionad\w*|ferida|herpes|eczema|candidiase|alergia)\b/,
    "uma condição de saúde",
  ],
];

export const SAFETY_REFERRAL = "Falar com um farmacêutico";

export function assessSafety(normalized: string, pregnancy: boolean, primaryGoal: GoalId | null): Safety {
  for (const [category, re, subject] of BLOCK_RULES) {
    if (re.test(normalized)) {
      const alt =
        primaryGoal === "acne"
          ? "Quero cuidados cosméticos para acne"
          : primaryGoal === "manchas"
            ? "Quero cuidados cosméticos para manchas"
            : undefined;
      return {
        decision: "blocked",
        category,
        message: `Esse tipo de pedido envolve ${subject}. Aqui eu só monto kits de cuidados com a pele. Para medicamentos, sintomas e condições de saúde, converse com um farmacêutico ou médico.`,
        referral: SAFETY_REFERRAL,
        alternativeQuery: alt,
      };
    }
  }
  if (pregnancy) {
    return {
      decision: "caution",
      category: "gestacao_e_ativos",
      message:
        "Você mencionou gestação ou amamentação. Retiramos dos kits os produtos que pedem orientação profissional nesse período. Converse com seu médico ou dermatologista antes de usar qualquer ativo.",
      referral: SAFETY_REFERRAL,
    };
  }
  return { decision: "allow" };
}
