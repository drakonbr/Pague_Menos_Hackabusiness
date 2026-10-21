import type { Intent } from "../contracts/types";
import { DERMO_GOALS, GOAL_LABEL } from "../contracts/types";
import { money } from "../services/format";
import { Icon } from "./Icon";

interface Props {
  intent: Intent;
  onEditSkin: () => void;
  onEditBudget: () => void;
}

export function IntentChips({ intent, onEditSkin, onEditBudget }: Props) {
  return (
    <div className="chips" aria-label="Como entendi o seu pedido">
      {intent.goals.map((g) => (
        <span key={g} className="chip goal">
          {GOAL_LABEL[g]}
        </span>
      ))}
      {intent.preferences.map((p) => (
        <span key={p} className="chip">
          {p}
        </span>
      ))}
      {intent.goals.some((g) => DERMO_GOALS.includes(g)) ? (
        <button className={`chip ${intent.skinType ? "" : "missing"}`} onClick={onEditSkin}>
          {intent.skinType ? `Pele ${intent.skinType}` : "Tipo de pele"}
          <Icon name="chevron" size={14} />
        </button>
      ) : null}
      <button className={`chip ${intent.budgetCents == null ? "missing" : ""}`} onClick={onEditBudget}>
        {intent.budgetCents == null ? "Sem limite de valor" : `Até ${money(intent.budgetCents)}`}
        <Icon name="chevron" size={14} />
      </button>
    </div>
  );
}
