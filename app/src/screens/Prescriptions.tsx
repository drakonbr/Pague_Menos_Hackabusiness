import { TitleBar } from "../components/Bars";
import { Icon } from "../components/Icon";
import { ProductImage } from "../components/ProductImage";
import { useNav } from "../nav";
import { rxPending, rxProducts, useApp } from "../state/app";

/** Anexar receitas (#28): vem depois de confirmar a cesta e antes da entrega e do pagamento. Receita simulada. */
export function Prescriptions() {
  const { lines, rxDocs, dispatch } = useApp();
  const { push } = useNav();
  const items = rxProducts(lines);
  const missing = rxPending(lines, rxDocs).length;
  return (
    <div className="screen">
      <TitleBar title="Receitas" />
      <div className="scroll">
        <div className="pad">
          <p style={{ color: "var(--text-2)", lineHeight: 1.45 }}>
            {!lines.length
              ? "Sua cesta está vazia."
              : items.length === 0
              ? "Nenhum item da sua cesta precisa de receita. Pode seguir para a entrega."
              : <>{items.length === 1 ? "Este item da sua cesta precisa de receita." : `Estes ${items.length} itens da sua cesta precisam de receita.`}{" "}
                Anexe a receita de cada um para seguir. Neste protótipo ela é simulada: nenhum documento real é enviado.</>}
          </p>
          <ul className="rx-attach">
            {items.map((p) => {
              const ok = rxDocs.includes(p.id);
              return (
                <li key={p.id} className={ok ? "ok" : ""}>
                  <ProductImage product={p} size={48} />
                  <span className="grow"><b>{p.name}</b><small>{ok ? <><Icon name="check" size={14} /> Receita anexada (simulada)</> : "Falta a receita"}</small></span>
                  <button className={`btn ${ok ? "outline" : "primary"}`} aria-label={`${ok ? "Remover" : "Anexar"} receita de ${p.name}`}
                    onClick={() => dispatch(ok ? { type: "detachRx", id: p.id } : { type: "attachRx", ids: [p.id] })}>
                    {ok ? "Remover" : "Anexar"}
                  </button>
                </li>
              );
            })}
          </ul>
        </div>
      </div>
      <div className="summary">
        <small className="foot center" role="status">
          {missing ? `Falta anexar ${missing === 1 ? "1 receita" : `${missing} receitas`}.` : items.length ? "Receitas anexadas. Pode seguir." : ""}
        </small>
        <button className="btn primary block" disabled={missing > 0 || !lines.length} onClick={() => push({ name: "delivery" })}>Continuar para entrega</button>
      </div>
    </div>
  );
}
