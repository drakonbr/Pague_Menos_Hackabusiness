// Cópia em TypeScript de contracts/README.md. A fonte da verdade é o documento.
// Se mudar aqui, mude lá (e vice-versa).

export type StepId =
  | "limpeza"
  | "preparo"
  | "tratamento"
  | "hidratacao"
  | "protecao_solar"
  | "protecao_corporal"
  | "complemento"
  | "omega3"
  | "colageno"
  | "magnesio"
  | "vitaminas"
  | "higiene_corpo"
  | "higiene_cabelo"
  | "higiene_oral"
  | "desodorante"
  | "reposicao"
  // medicamentos (doc 16): papéis dentro do kit de cada área de saúde
  | "analgesico_dipirona"
  | "analgesico_paracetamol"
  | "antiinflamatorio"
  | "relaxante_muscular"
  | "dor_topico"
  | "antiespasmodico"
  | "antigases"
  | "antiacido"
  | "protetor_gastrico"
  | "antigripal"
  | "descongestionante_nasal"
  | "imunidade"
  | "expectorante"
  | "antitussigeno"
  | "pastilha_garganta"
  | "spray_garganta"
  | "antialergico"
  | "antidiarreico"
  | "probiotico"
  | "reidratacao"
  | "laxante"
  | "fibra"
  | "antiemetico";

export type GoalId =
  | "acne"
  | "manchas"
  | "skincare_basico"
  | "protecao_solar"
  | "anti_idade"
  | "pele_sensivel"
  | "oleosidade"
  | "suplementos"
  | "higiene_premium"
  // áreas de saúde (doc 16)
  | "dor_de_cabeca"
  | "dor_no_corpo"
  | "dor_muscular"
  | "dor_de_barriga"
  | "azia"
  | "gripe"
  | "tosse"
  | "tosse_seca"
  | "dor_de_garganta"
  | "alergia"
  | "diarreia"
  | "prisao_de_ventre"
  | "enjoo";

/** Objetivos de pele: só neles o tipo de pele importa (chip, pergunta e filtro). */
export const DERMO_GOALS: GoalId[] = ["acne", "manchas", "skincare_basico", "protecao_solar", "anti_idade", "pele_sensivel", "oleosidade"];

export type SkinType = "oleosa" | "mista" | "seca" | "normal" | "sensível";
export type KitTier = "economico" | "essencial" | "completo";
export type PriceTier = "economico" | "intermediario" | "premium";
export type UsagePeriod = "dia" | "noite" | "dia_noite";

export type WarningCode =
  | "fotossensibilizante"
  | "consultar_se_gestante"
  | "evitar_contato_olhos"
  | "nao_usar_pele_irritada"
  | "teste_de_sensibilidade"
  | "consultar_se_medicacao"
  | "receita_obrigatoria"
  | "confirmar_troca_com_farmaceutico";

export type AlertCode = WarningCode | "interacao_separar_periodos" | "sem_protetor_no_kit";

export type ProductForm =
  | "tube"
  | "bottle"
  | "pump"
  | "jar"
  | "dropper"
  | "stick"
  | "patch"
  | "spray"
  | "bar"
  | "caps"
  | "powder"
  | "box";

export type ProductDomain = "dermo" | "suplemento" | "higiene" | "medicamento";
export type PresentationKind = "referencia" | "generico" | "similar";

/** Só medicamentos de reposição: mesmo princípio ativo e dose, apresentações diferentes. */
export interface Equivalence {
  group: string;
  presentation: PresentationKind;
  active: string;
  dose: string;
}

export interface Product {
  id: string;
  name: string;
  brand: string;
  line: string;
  step: StepId;
  coversSteps: StepId[];
  productType: string;
  form: ProductForm;
  size: { value: number; unit: string };
  skinTypes: Array<SkinType | "todas">;
  concerns: string[];
  ingredients: string[];
  fps: number | null;
  usagePeriod: UsagePeriod;
  claims: string[];
  warnings: WarningCode[];
  description: string;
  howToUse: string;
  priceTier: PriceTier;
  priceCents: number;
  listPriceCents: number;
  /** Estoque central (centro de distribuição). O estoque de cada loja vem do CommerceService. */
  stockQty: number;
  /** Premissa fictícia do protótipo (Carteira+ real pode ter outras regras). */
  cashbackPct: number;
  /** Ranking de vendas simulado (1 = mais vendido). */
  salesRank: number;
  categoryIds: string[];
  /** Fotos reais sem marca; vazio enquanto o banco de imagens não foi revisado. */
  images: ProductImage[];
  domain: ProductDomain;
  /** null = venda livre; "receita_simples" = medicamento (receita SIMULADA no protótipo). */
  rx: null | "receita_simples";
  equivalence: Equivalence | null;
}

export interface ProductImage {
  src: string;
  alt: string;
  credit: { source: "Pexels"; photographer: string; photographerUrl: string; pageUrl: string };
}

export interface Intent {
  goals: GoalId[];
  primaryGoal: GoalId | null;
  /** null = sem limite. */
  budgetCents: number | null;
  skinType: SkinType | null;
  preferences: string[];
  pregnancy?: boolean;
  /** Loja de onde sai o pedido (retirada ou expressa). null = estoque central (entrega agendada). */
  storeId?: string | null;
  missing: Array<"skinType" | "budget">;
}

export interface SearchRequest {
  query: string;
  /** undefined = extrair da frase; null = sem limite (escolha explícita). */
  budgetCents?: number | null;
  /** undefined = extrair da frase. */
  skinType?: SkinType | null;
  preferences?: string[];
  /** Loja escolhida: os kits só usam itens com estoque nela. Ausente/null = estoque central. */
  storeId?: string | null;
  /** Conversa: o `context` da resposta anterior (o motor não guarda estado). */
  context?: ChatContext | null;
  /** Produto em foco (só o id; nunca dados da pessoa). */
  focusProductId?: string | null;
  /** #42: false = o motor nunca envia a frase a um serviço externo (a pessoa desligou na Privacidade). Ausente = true. */
  allowExternal?: boolean;
}

/** Estado da conversa devolvido pelo motor e reenviado pelo app. Só ids e preferências de cosmético. */
export interface ChatContext {
  intent: Intent;
  requested: string[];
  excluded: string[];
  /** Kits em forma compacta (ids). O motor reconstrói preço e estoque a partir do catálogo. */
  kits: Array<{ id: string; tier: KitTier; totalCents: number; items: Array<{ step: StepId; productId: string }> } & Record<string, unknown>>;
  lastAct: string;
  turn: number;
  /** Prateleira da última lista (ids), para "mais barato"/"sem álcool" ajustarem a mesma lista. */
  scope?: { kind: string; steps: string[]; concerns: string[]; ingredients: string[]; concepts: string[] };
  focusTier?: KitTier;
  focusProductId?: string;
}

// Desde o doc 16 não existe bloqueio nem encaminhamento: medicamento é busca como outra qualquer.
// Exceção estreita (#63): "urgent" = risco de vida ou sinal de alerta; resposta fixa, sem produtos.
export type SafetyDecision = "allow" | "caution" | "urgent";
export type SafetyCategory = "gestacao_e_ativos" | "risco_de_vida" | "sinal_de_alerta";

export interface Safety {
  decision: SafetyDecision;
  category?: SafetyCategory;
  message?: string;
}

export interface Clarification {
  id: "skinType";
  question: string;
  options: Array<{ value: SkinType; label: string }>;
}

export interface Alert {
  code: AlertCode;
  severity: "info" | "atencao";
  text: string;
  productIds?: string[];
}

export interface KitItem {
  step: StepId;
  product: Product;
  reason: string;
  alternativesCount?: number;
}

export interface Kit {
  id: string;
  tier: KitTier;
  title: string;
  goal: GoalId;
  items: KitItem[];
  /** Soma dos itens avulsos (preço de cada um hoje). */
  itemsTotalCents: number;
  /** Desconto do kit (#30): 10% com 2 itens, 12% com 3, 15% com 4 ou mais. */
  discountPct: number;
  discountCents: number;
  /** Preço do kit = soma avulsa menos o desconto. */
  totalCents: number;
  listTotalCents: number;
  withinBudget: boolean;
  /** Soma do cashback dos itens (premissa fictícia). */
  cashbackCents: number;
  /** Loja usada para checar estoque; null = estoque central. */
  storeId: string | null;
  alerts: Alert[];
  rationale: string;
}

export type KitsStatus = "ok" | "partial" | "none_in_budget" | "not_applicable";

export type ChatAction =
  | { type: "none" }
  | { type: "show_kits"; tier?: KitTier }
  | { type: "show_products" }
  | { type: "open_refill" }
  | { type: "add_kit_to_cart"; tier: KitTier; kitId: string }
  | { type: "delivery_info" }
  | { type: "delivery_quote"; tier: KitTier; kitTotalCents: number; options: DeliveryQuoteOption[] }
  | { type: "swap_options"; tier: KitTier; kitId: string; step: StepId; options: Array<{ productId: string; deltaCents: number }> }
  | { type: "show_similars"; productId: string; options: SimilarOption[] };

export interface DeliveryQuoteOption {
  id: FulfillmentMode;
  label: string;
  eta: string;
  feeCents: number;
  totalCents: number;
  stockSource: "loja" | "centro_distribuicao";
}

export interface SimilarOption {
  productId: string;
  kind: "equivalente" | "parecido";
  presentation?: PresentationKind;
  sameActive?: boolean;
  sameDose?: boolean;
  score?: number;
  deltaCents: number;
  inStock: boolean;
  storeIdsWithStock: string[];
  needsPharmacistConfirmation: boolean;
}

export interface SimilarsResponse {
  productId: string;
  domain: ProductDomain;
  storeId: string | null;
  inStockHere: boolean;
  options: Array<Omit<SimilarOption, "productId"> & { product: Product }>;
}

/** Aviso de que o pedido cita algo que o catálogo não tem ("Não temos maquiagem no catálogo."). */
export interface CatalogNotice {
  missing: string[];
  /** Prateleira vizinha que existe, quando há. */
  shelf: string | null;
  message: string;
}

/** De que prateleira a busca está falando e quantos itens vieram. */
export interface ScopeInfo {
  kind: "shelf" | "concern" | "ingredient" | "goal" | "vote" | "absent" | "unknown";
  label: string;
  items: number;
}

export interface SearchResponse {
  requestId: string;
  query: string;
  /** Ato de fala entendido (busca, refinar, trocar_item, entrega_frete, repor_medicamento...). */
  act?: string;
  /** Texto da resposta na conversa. */
  reply?: string;
  suggestions?: string[];
  catalogNotice?: CatalogNotice;
  scope?: ScopeInfo;
  /** Frase depois de corrigir erros de digitação (só vem quando algo mudou). */
  correctedQuery?: string;
  /** Pedido de agora + o que a conversa já sabia, numa frase autônoma (chip "Buscando: …"). Nunca contém dado de saúde. */
  rewrittenQuery?: string | null;
  action?: ChatAction;
  context?: ChatContext;
  safety: Safety;
  intent: Intent;
  clarification?: Clarification;
  kitsStatus: KitsStatus;
  kits: Kit[];
  closestKit: Kit | null;
  products: Product[];
  notes: string[];
}

export interface SwapOption {
  product: Product;
  deltaCents: number;
  compatible: boolean;
  reason?: string;
}

export interface KitAdaptation {
  kit: Kit;
  replaced: Array<{ step: StepId; from: Product; to: Product }>;
}

export interface SearchService {
  search(req: SearchRequest): Promise<SearchResponse>;
  swapOptions(kit: Kit, step: StepId, intent: Intent): Promise<SwapOption[]>;
  swap(kit: Kit, step: StepId, productId: string, intent: Intent): Promise<Kit>;
  /** Troca só os itens sem estoque na loja. null = o kit não fecha nessa loja. */
  adaptToStore(kit: Kit, storeId: string, intent: Intent): Promise<KitAdaptation | null>;
  /** Equivalentes (medicamento: mesmo ativo e dose) ou parecidos (demais). */
  similars(productId: string, storeId: string | null): Promise<SimilarsResponse>;
  /** Qual motor responde: "graphrag" (servidor Python) ou "simulado" (fallback local). */
  readonly engine: "graphrag" | "simulado";
  /** #60: o motor tem o serviço de linguagem externo (DeepSeek) ligado? undefined = não sabemos (motor simulado ou ainda sem resposta). */
  readonly external?: boolean;
}

export const STEP_ORDER: StepId[] = [
  "limpeza",
  "preparo",
  "tratamento",
  "hidratacao",
  "protecao_solar",
  "protecao_corporal",
  "complemento",
  "omega3",
  "colageno",
  "magnesio",
  "vitaminas",
  "higiene_corpo",
  "higiene_cabelo",
  "higiene_oral",
  "desodorante",
  "analgesico_dipirona",
  "analgesico_paracetamol",
  "antiinflamatorio",
  "relaxante_muscular",
  "dor_topico",
  "antiespasmodico",
  "antigases",
  "antiacido",
  "protetor_gastrico",
  "antigripal",
  "descongestionante_nasal",
  "imunidade",
  "expectorante",
  "antitussigeno",
  "pastilha_garganta",
  "spray_garganta",
  "antialergico",
  "antidiarreico",
  "probiotico",
  "reidratacao",
  "laxante",
  "fibra",
  "antiemetico",
  "reposicao",
];

export const STEP_LABEL: Record<StepId, string> = {
  limpeza: "Limpeza",
  preparo: "Preparo",
  tratamento: "Tratamento",
  hidratacao: "Hidratação",
  protecao_solar: "Proteção solar",
  protecao_corporal: "Proteção corporal",
  complemento: "Complemento",
  omega3: "Ômega 3",
  colageno: "Colágeno",
  magnesio: "Magnésio",
  vitaminas: "Vitaminas",
  higiene_corpo: "Banho e corpo",
  higiene_cabelo: "Cabelo",
  higiene_oral: "Higiene bucal",
  desodorante: "Desodorante",
  reposicao: "Reposição",
  analgesico_dipirona: "Dipirona",
  analgesico_paracetamol: "Paracetamol",
  antiinflamatorio: "Anti-inflamatório",
  relaxante_muscular: "Relaxante muscular",
  dor_topico: "Gel ou pomada para dor",
  antiespasmodico: "Para cólica",
  antigases: "Antigases",
  antiacido: "Antiácido",
  protetor_gastrico: "Protetor gástrico",
  antigripal: "Antigripal",
  descongestionante_nasal: "Nariz (soro e descongestionante)",
  imunidade: "Vitamina C",
  expectorante: "Expectorante",
  antitussigeno: "Para tosse seca",
  pastilha_garganta: "Pastilha para garganta",
  spray_garganta: "Spray ou gargarejo para garganta",
  antialergico: "Antialérgico",
  antidiarreico: "Antidiarreico",
  probiotico: "Probiótico",
  reidratacao: "Reidratação oral",
  laxante: "Laxante",
  fibra: "Fibra",
  antiemetico: "Contra enjoo",
};

/** Desconto do kit pelo número de itens (#30). A mesma regra está no motor (graphrag/composer.py). */
export function kitDiscountPct(nItems: number): number {
  return nItems < 2 ? 0 : nItems === 2 ? 10 : nItems === 3 ? 12 : 15;
}
export const MAX_KIT_DISCOUNT_PCT = 15;
export function kitPrice(itemsCents: number, nItems: number) {
  const discountPct = kitDiscountPct(nItems);
  const discountCents = Math.floor((itemsCents * discountPct + 50) / 100);   // meio centavo para cima, igual ao motor
  return { itemsTotalCents: itemsCents, discountPct, discountCents, totalCents: itemsCents - discountCents };
}

/** Cashback do kit: o dos itens, reduzido na proporção do desconto (sobre o que a pessoa paga). Igual ao motor. */
export const kitCashback = (itemsCashback: number, discountPct: number) => Math.floor((itemsCashback * (100 - discountPct)) / 100);

export const TIER_LABEL: Record<KitTier, string> = {
  economico: "Econômico",
  essencial: "Essencial",
  completo: "Completo",
};

export const GOAL_LABEL: Record<GoalId, string> = {
  acne: "Controle de acne",
  manchas: "Uniformizar manchas",
  skincare_basico: "Rotina básica de skin care",
  protecao_solar: "Proteção solar",
  anti_idade: "Cuidado antissinais",
  pele_sensivel: "Pele sensível",
  oleosidade: "Controle de oleosidade",
  suplementos: "Suplementos e vitaminas",
  higiene_premium: "Higiene premium",
  dor_de_cabeca: "Dor de cabeça e febre",
  dor_no_corpo: "Dor no corpo",
  dor_muscular: "Dor muscular",
  dor_de_barriga: "Dor de barriga e cólica",
  azia: "Azia e má digestão",
  gripe: "Gripe e resfriado",
  tosse: "Tosse com catarro",
  tosse_seca: "Tosse seca",
  dor_de_garganta: "Dor de garganta",
  alergia: "Alergia e rinite",
  diarreia: "Diarreia",
  prisao_de_ventre: "Prisão de ventre",
  enjoo: "Enjoo e náusea",
};

// ---------------------------------------------------------------------------
// Comércio: o que no sistema real são os serviços que JÁ existem (catálogo, lojas,
// estoque, frete). Fica separado do SearchService (motor de kits / GraphRAG).
// ---------------------------------------------------------------------------
export type FulfillmentMode = "retirada" | "expressa" | "agendada";

export interface Store {
  id: string;
  name: string;
  neighborhood: string;
  city: string;
  uf: string;
  address: string;
  size: "grande" | "media" | "pequena";
  open24h: boolean;
  hours: string;
  lat: number;
  lng: number;
}

export interface DeliveryOption {
  id: FulfillmentMode;
  label: string;
  eta: string;
  feeCents: number;
  freeFromCents: number | null;
  stockSource: "loja" | "centro_distribuicao";
}

export interface Category {
  id: string;
  name: string;
  parent: string | null;
  productIds: string[];
}

export interface Showcase {
  id: string;
  title: string;
  type: "kit_presets" | "products";
  productIds?: string[];
}

export interface KitPreset {
  id: string;
  label: string;
  query: string;
}

export interface StoreAvailability {
  store: Store;
  distanceKm: number;
  availableIds: string[];
  missingIds: string[];
}

export interface HomeData {
  showcases: Showcase[];
  kitPresets: KitPreset[];
  categories: Category[];
  banners: ProductImage[];
}

export type SortKey = "relevancia" | "menor_preco" | "maior_preco" | "mais_vendidos";

export interface CommerceService {
  home(): Promise<HomeData>;
  categories(): Promise<Category[]>;
  product(id: string): Promise<Product | null>;
  products(ids: string[], sort?: SortKey): Promise<Product[]>;
  /** Lojas ordenadas por distância, com o que cada uma tem dos produtos pedidos. */
  storesFor(productIds: string[]): Promise<StoreAvailability[]>;
  delivery(): Promise<{ options: DeliveryOption[]; freeShippingFromCents: number }>;
  /** Textos dos vocabulários (avisos, preocupações, ingredientes) para as telas. */
  labels(): Promise<Labels>;
}

export interface Labels {
  warnings: Record<string, string>;
  concerns: Record<string, string>;
  ingredients: Record<string, string>;
}
