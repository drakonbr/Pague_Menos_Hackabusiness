import { useCallback } from "react";
import { useApp } from "../state/app";
import { BottomSheet } from "./BottomSheet";
import { Icon } from "./Icon";

/** Aviso ao pôr na cesta um item que exige receita (#28). A receita é anexada depois de confirmar a cesta. */
export function RxPrompt() {
  const { rxAsk, dispatch } = useApp();
  const close = useCallback(() => dispatch({ type: "rxCancel" }), [dispatch]);   // estável: o painel não puxa o foco a cada render
  if (!rxAsk) return null;
  const items = rxAsk.kind === "product" ? [rxAsk.product] : rxAsk.kit.items.map((i) => i.product).filter((p) => p.rx);
  return (
    <BottomSheet title={items.length === 1 ? "Este item precisa de receita" : "Estes itens precisam de receita"} onClose={close}>
      <div className="note warn" role="note">
        <Icon name="info" size={18} />
        <p>Depois de confirmar a cesta, você anexa a receita e só então segue para o pagamento. Neste protótipo, a receita é simulada.</p>
      </div>
      <ul className="rx-list">
        {items.map((p) => <li key={p.id}><b>{p.name}</b><small>{p.brand}</small></li>)}
      </ul>
      <div className="row">
        <button className="btn outline grow" onClick={close}>Cancelar</button>
        <button className="btn primary grow" onClick={() => dispatch({ type: "rxConfirm" })}>Adicionar à cesta</button>
      </div>
    </BottomSheet>
  );
}
