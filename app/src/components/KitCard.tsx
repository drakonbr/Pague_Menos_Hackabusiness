import type { Kit } from "../contracts/types";
import { STEP_LABEL, TIER_LABEL } from "../contracts/types";
import { money } from "../services/format";
import { Icon } from "./Icon";
import { ProductImage } from "./ProductImage";

export function KitCard({ kit, onOpen, overBudgetBy }: { kit: Kit; onOpen: () => void; overBudgetBy?: number }) {
  const attention = kit.alerts.filter((a) => a.severity === "atencao").length;
  return (
    <button className="kit-card" onClick={onOpen} aria-label={`Abrir kit ${TIER_LABEL[kit.tier]}, ${money(kit.totalCents)}${kit.discountPct ? `, ${kit.discountPct}% de desconto no kit` : ""}`}>
      <div className="row" style={{ justifyContent: "space-between" }}>
        <span className={`tier ${kit.tier}`}>{TIER_LABEL[kit.tier]}</span>
        <span className="mini">{kit.items.length} {kit.items.length === 1 ? "item" : "itens"}</span>
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
            {STEP_LABEL[i.step]}: <b>{i.product.name}</b>   {/* #51: o nome do produto, para o Essencial e o Completo não parecerem iguais */}
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
        {kit.discountCents > 0 ? <span className="old">{money(kit.itemsTotalCents)}</span> : null}
        {kit.discountPct > 0 ? <span className="save">−{kit.discountPct}% no kit</span> : null}
      </div>
      {overBudgetBy ? <span className="over">{money(overBudgetBy)} acima do orçamento</span> : null}
    </button>
  );
}
