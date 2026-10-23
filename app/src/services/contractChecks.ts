// Checagem das invariantes do contrato (docs/08, I1 a I14).
// Escrita de forma INDEPENDENTE do compositor, para não validar o código com ele mesmo.
// A mesma lista será portada para a avaliação do GraphRAG.
import type { Intent, Kit, KitTier, SearchResponse } from "../contracts/types";
import { INGREDIENTS, INTERACTIONS, PRODUCT_BY_ID, STORE_STOCK } from "./mock/catalogData";

const PHOTO = new Set(INGREDIENTS.filter((i) => i.photosensitizing).map((i) => i.id));

export function checkKit(kit: Kit, intent: Intent): string[] {
  const v: string[] = [];
  const tag = `${kit.id}`;
  const prods = kit.items.map((i) => i.product);

  // I1
  if (new Set(prods.map((p) => p.id)).size !== prods.length) v.push(`${tag} I1: produto repetido`);
  // M5 (#40): remédio nunca entra em kit
  for (const p of prods) if (PRODUCT_BY_ID.get(p.id)?.domain === "medicamento") v.push(`${tag} M5: ${p.id} é remédio e está no kit`);
  // I2
  const covered = prods.flatMap((p) => p.coversSteps);
  if (new Set(covered).size !== covered.length) v.push(`${tag} I2: etapa coberta duas vezes`);
  if (new Set(prods.map((p) => p.productType)).size !== prods.length) v.push(`${tag} I2: tipo de produto repetido`);
  // I9
  if (kit.items.length > 5 || kit.items.length === 0) v.push(`${tag} I9: ${kit.items.length} itens`);
  // M1 (doc 16): medicamento nunca repete princípio ativo dentro do kit
  const meds = prods.filter((p) => p.domain === "medicamento");
  const actives = meds.flatMap((p) => p.ingredients);
  if (new Set(actives).size !== actives.length) v.push(`${tag} M1: princípio ativo repetido`);

  for (const it of kit.items) {
    const truth = PRODUCT_BY_ID.get(it.product.id);
    if (!truth) {
      v.push(`${tag}: produto ${it.product.id} não existe no catálogo`);
      continue;
    }
    // I3 e I12 (estoque da loja do kit, ou central quando não há loja)
    const qty = kit.storeId ? (STORE_STOCK.get(kit.storeId)?.[truth.id] ?? 0) : truth.stockQty;
    if (qty <= 0) v.push(`${tag} I3: ${truth.id} sem estoque ${kit.storeId ? `na loja ${kit.storeId}` : "central"}`);
    if (it.product.priceCents !== truth.priceCents) v.push(`${tag} I12: preço de ${truth.id} difere do inventário`);
  }

  // I4 e M3 (#30): soma avulsa verdadeira, desconto na regra, kit sempre mais barato que os itens avulsos
  const sum = prods.reduce((t, p) => t + (PRODUCT_BY_ID.get(p.id)?.priceCents ?? 0), 0);
  const pct = prods.length < 2 ? 0 : prods.length === 2 ? 10 : prods.length === 3 ? 12 : 15;
  const off = Math.floor((sum * pct + 50) / 100);
  if (kit.itemsTotalCents !== sum) v.push(`${tag} I4: soma avulsa ${kit.itemsTotalCents} != ${sum}`);
  if (kit.discountPct !== pct || kit.discountCents !== off) v.push(`${tag} M3: desconto ${kit.discountPct}% / ${kit.discountCents} fora da regra`);
  if (kit.totalCents !== sum - off) v.push(`${tag} I4: total ${kit.totalCents} != soma ${sum} menos desconto ${off}`);
  if (prods.length >= 2 && !(kit.totalCents < sum)) v.push(`${tag} M3: kit não sai mais barato que os itens avulsos`);
  // I5
  if (intent.budgetCents != null) {
    if (kit.withinBudget && kit.totalCents > intent.budgetCents) v.push(`${tag} I5: acima do orçamento`);
    if (!kit.withinBudget && kit.totalCents <= intent.budgetCents) v.push(`${tag} I5: marcado fora do orçamento, mas cabe`);
  }

  // I6 e I7
  for (let x = 0; x < prods.length; x++) {
    for (let y = x + 1; y < prods.length; y++) {
      const p = prods[x];
      const q = prods[y];
      if (p.step === "limpeza" || q.step === "limpeza") continue;
      for (const rule of INTERACTIONS) {
        const hit =
          (p.ingredients.includes(rule.a) && q.ingredients.includes(rule.b)) ||
          (p.ingredients.includes(rule.b) && q.ingredients.includes(rule.a));
        if (!hit) continue;
        if (rule.severity === "evitar") v.push(`${tag} I6: ${p.id} x ${q.id} (${rule.a}/${rule.b})`);
        else {
          const split = [p.usagePeriod, q.usagePeriod].sort().join() === "dia,noite";
          if (!split) v.push(`${tag} I7: ${p.id} x ${q.id} sem separar períodos`);
          else if (!kit.alerts.some((a) => a.code === "interacao_separar_periodos"))
            v.push(`${tag} I7: falta alerta de separar períodos`);
        }
      }
    }
  }

  // I8
  const hasPhoto = prods.some((p) => p.ingredients.some((i) => PHOTO.has(i)));
  const hasSun = covered.includes("protecao_solar");
  if (hasPhoto && !hasSun && !kit.alerts.some((a) => a.code === "sem_protetor_no_kit"))
    v.push(`${tag} I8: fotossensibilizante sem protetor e sem alerta`);

  // I15 cashback = soma do cashback dos itens (para baixo por item), reduzida pelo desconto do kit
  const cb = Math.floor(prods.reduce((t, p) => {
    const tr = PRODUCT_BY_ID.get(p.id);
    return t + (tr ? Math.floor((tr.priceCents * tr.cashbackPct) / 100) : 0);
  }, 0) * (100 - pct) / 100);
  if (kit.cashbackCents !== cb) v.push(`${tag} I15: cashback ${kit.cashbackCents} != ${cb}`);
  // I16 loja do kit = loja do pedido
  if ((intent.storeId ?? null) !== kit.storeId) v.push(`${tag} I16: kit na loja ${kit.storeId}, pedido na ${intent.storeId ?? null}`);

  // I11
  if (intent.pregnancy && prods.some((p) => p.warnings.includes("consultar_se_gestante")))
    v.push(`${tag} I11: item com aviso de gestação`);

  // I13
  for (const pref of intent.preferences) {
    const bad = prods.filter((p) => !p.claims.includes(pref));
    if (bad.length) v.push(`${tag} I13: ${bad.map((b) => b.id).join(",")} sem '${pref}'`);
  }

  return v;
}

export function checkResponse(res: SearchResponse): string[] {
  const v: string[] = [];
  for (const k of res.kits) v.push(...checkKit(k, res.intent));
  if (res.closestKit) {
    v.push(...checkKit(res.closestKit, res.intent).filter((m) => !m.includes("I5")));
    if (res.closestKit.withinBudget) v.push(`${res.requestId}: closestKit deveria estar fora do orçamento`);
  }
  // I14
  const sigs = res.kits.map((k) => k.items.map((i) => i.product.id).sort().join("|"));
  if (new Set(sigs).size !== sigs.length) v.push(`${res.requestId} I14: kits idênticos`);
  // M4 (#31): Econômico < Essencial < Completo, nessa ordem e com preço crescente
  const order: KitTier[] = ["economico", "essencial", "completo"];
  const pos = res.kits.map((k) => order.indexOf(k.tier));
  if (pos.some((p, i) => i > 0 && p <= pos[i - 1]) || res.kits.some((k, i) => i > 0 && k.totalCents <= res.kits[i - 1].totalCents))
    v.push(`${res.requestId} M4: faixas fora de ordem ou preço não crescente`);
  // status coerente
  if (res.kitsStatus === "ok" && res.kits.length < 2) v.push(`${res.requestId}: status ok com menos de 2 kits`);
  if (res.kitsStatus === "none_in_budget" && (res.kits.length || !res.closestKit))
    v.push(`${res.requestId}: none_in_budget inconsistente`);
  // produtos individuais: só com estoque e preço do inventário
  for (const p of res.products) {
    const truth = PRODUCT_BY_ID.get(p.id);
    if (!truth || truth.stockQty <= 0 || truth.priceCents !== p.priceCents) v.push(`${res.requestId}: produto ${p.id} inválido na lista`);
  }
  return v;
}
