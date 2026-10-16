const brl = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

/** 6970 -> "R$ 69,70" */
export function money(cents: number): string {
  return brl.format(cents / 100).replace(/ /g, " ");
}

/** +1000 -> "+ R$ 10,00"; -400 -> "− R$ 4,00"; 0 -> "mesmo preço" */
export function delta(cents: number): string {
  if (cents === 0) return "mesmo preço";
  const sign = cents > 0 ? "+" : "−";
  return `${sign} ${money(Math.abs(cents))}`;
}

export function sizeLabel(size: { value: number; unit: string }): string {
  return `${size.value} ${size.unit}`;
}
