import type { IconName } from "./components/Icon";

// Departamentos do menu do app (nomes do menu público). Sem `id` = fora do protótipo.
export const TOP_CATEGORIES: Array<{ label: string; icon: IconName; id?: string }> = [
  { label: "Medicamentos e saúde", icon: "pill", id: "saude" },
  { label: "Dermo e beleza", icon: "lipstick", id: "dermo" },
  { label: "Mamães e bebês", icon: "stroller" },
  { label: "Vida saudável", icon: "dumbbell", id: "vida-saudavel" },
  { label: "Higiene pessoal", icon: "bottle", id: "higiene" },
  { label: "Conveniência", icon: "bag" },
  { label: "Marcas exclusivas", icon: "cross" },
  { label: "Pet shop", icon: "paw" },
];
