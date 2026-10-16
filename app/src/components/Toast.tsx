import { useEffect } from "react";
import { useNav } from "../nav";
import { useApp } from "../state/app";
import { Icon } from "./Icon";

export function Toast() {
  const { toast, dispatch } = useApp();
  const { push, view } = useNav();
  useEffect(() => {
    if (!toast) return;
    const t = window.setTimeout(() => dispatch({ type: "hideToast" }), 2600);
    return () => window.clearTimeout(t);
  }, [toast, dispatch]);
  if (!toast) return null;
  return (
    <div className="toast" role="status" aria-live="polite">
      <Icon name="checkCircle" size={20} />
      <span>{toast.text}</span>
      {toast.action === "cart" && view.name !== "cart" ? (
        <button onClick={() => { dispatch({ type: "hideToast" }); push({ name: "cart" }); }}>Ver cesta</button>
      ) : null}
    </div>
  );
}
