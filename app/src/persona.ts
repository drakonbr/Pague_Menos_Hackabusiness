// Persona fictícia do grupo (Renata Almeida). Dados SINTÉTICOS, usados só para demonstrar a experiência logada.
// PRIVACIDADE: medicamentos, receitas e histórico ficam neste arquivo/estado do aparelho. Nunca vão ao motor:
// o motor recebe só a frase, o `context` da conversa e ids de produto (ver docs/14-persona-e-privacidade.md).
import personaJson from "./mocks/persona.mock.json";
import commerceJson from "./mocks/commerce.mock.json";

export interface ContinuousMedication {
  productId: string;
  unitsPerDay: number;
  unitsLeft: number;
  packUnits: number;
  /** Rótulo privado, mostrado só na tela "Meus medicamentos". */
  label: string;
}

export interface ConsentFlags {
  refillReminders: boolean;
  personalizeWithPurchaseHistory: boolean;
  useHealthDataForRecommendations: boolean;
  shareHealthDataWithPartners: boolean;
  /** #42: frases que o motor não entende podem ser traduzidas por um serviço de linguagem externo (DeepSeek). */
  useExternalLanguageService: boolean;
}

export interface PersonaOrder {
  id: string;
  date: string;
  deliveryId: "retirada" | "expressa" | "agendada";
  health: boolean;
  items: Array<{ productId: string; qty: number }>;
}

export interface Persona {
  id: string;
  name: string;
  firstName: string;
  age: number;
  occupation: string;
  quote: string;
  address: { label: string; street: string; neighborhood: string; city: string; uf: string; cep: string; lat: number; lng: number };
  interests: string[];
  preferences: { deliveryPriority: Array<"retirada" | "expressa" | "agendada">; priceView: string; wantsSimilarOptions: boolean; fewTaps: boolean };
  privacy: { consent: ConsentFlags; healthDataStays: string };
  continuousMedications: ContinuousMedication[];
  orderHistory: PersonaOrder[];
}

export const PERSONA = personaJson as unknown as Persona;

/** Premissas FICTÍCIAS da reposição automática (o programa real pode ter outras regras). */
export const REFILL_RULES = (commerceJson as unknown as { refill: { freeShipping: boolean; discountPct: number; alertDaysBefore: number; note: string } }).refill;

export const daysLeft = (m: ContinuousMedication) => Math.floor(m.unitsLeft / m.unitsPerDay);
export const needsRefill = (m: ContinuousMedication, alertDays = REFILL_RULES.alertDaysBefore) => daysLeft(m) <= alertDays;
export function runOutDate(m: ContinuousMedication, from = new Date()): Date {
  return new Date(from.getTime() + daysLeft(m) * 86400000);
}
/** Preço com o desconto de reposição automática (premissa fictícia). */
export const refillPrice = (priceCents: number, auto: boolean) =>
  auto ? Math.round(priceCents * (1 - REFILL_RULES.discountPct / 100)) : priceCents;

export const DELIVERY_RANK = (id: string) => PERSONA.preferences.deliveryPriority.indexOf(id as "retirada");
