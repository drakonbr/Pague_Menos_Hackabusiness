import type { Kit } from "../contracts/types";
import { STEP_LABEL, TIER_LABEL } from "../contracts/types";
import { money } from "../services/format";
import { Icon } from "./Icon";
import { ProductImage } from "./ProductImage";

export function KitCard({ kit, onOpen, overBudgetBy }: { kit: Kit; onOpen: () => void; overBudgetBy?: number }) {
  const saving = kit.listTotalCents - kit.totalCents;
  const attention = kit.alerts.filter((a) => a.severity === "atencao").length;
  return (
    <button className="kit-card" onClick={onOpen} aria-label={`Abrir kit ${TIER_LABEL[kit.tier]}, ${money(kit.totalCents)}`}>
      <div className="row" style={{ justifyContent: "space-between" }}>
        <span className={`tier ${kit.tier}`}>{TIER_LABEL[kit.tier]}</span>
        <span className="mini">{kit.items.length} itens</span>
      </div>
      <h3>{kit.title}</h3>
      <div className="kit-thumbs">
        {kit.items.map((i) => (
          <ProductImage key={i.product.id} product={i.product} size={52} />
        ))}
      </div>
      <ul className="kit-items">
        {kit.items.map((i) => (
          <li key={i.product.id}>
            {STEP_LABEL[i.step]}: <b>{i.product.domain === "medicamento" ? i.product.name : i.product.productType}</b>
          </li>
        ))}
      </ul>
      <div className="chips" style={{ gap: 6 }}>
        {kit.cashbackCents > 0 ? <span className="mini green">{money(kit.cashbackCents)} de cashback</span> : null}
        {attention > 0 ? (
          <span className="mini warn">
            <Icon name="alert" size={13} /> {attention} {attention === 1 ? "ponto de atenção" : "pontos de atenção"}
          </span>
        ) : null}
      </div>
      <div className="price-row">
        <span className="price blue">{money(kit.totalCents)}</span>
        {saving > 0 ? <span className="old">{money(kit.listTotalCents)}</span> : null}
        {saving > 0 ? <span className="save">economiza {money(saving)}</span> : null}
      </div>
      {overBudgetBy ? <span className="over">{money(overBudgetBy)} acima do orçamento</span> : null}
    </button>
  );
}
