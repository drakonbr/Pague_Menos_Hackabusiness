import { useEffect, useState } from "react";
import { useNav } from "../nav";
import { useApp } from "../state/app";
import { Icon } from "./Icon";

export function Toast() {
  const { toast, dispatch } = useApp();
  const { push, view } = useNav();
  const [paused, setPaused] = useState(false);   // pausa com o mouse ou o foco em cima do aviso (WCAG 2.2.1)
  // mouse e foco não disparam leave/blur quando o aviso some: sem isto a pausa ficaria presa no aviso seguinte
  useEffect(() => setPaused(false), [toast]);
  useEffect(() => {
    if (!toast || paused) return;
    // WCAG 2.2.1: aviso com ação fica tempo de sobra e tem botão de fechar (#55)
    const t = window.setTimeout(() => dispatch({ type: "hideToast" }), toast.action ? 10000 : 8000);
    return () => window.clearTimeout(t);
  }, [toast, paused, dispatch]);
  if (!toast) return null;
  return (
    <div className="toast" role="status" aria-live="polite" onMouseEnter={() => setPaused(true)} onMouseLeave={() => setPaused(false)} onFocus={() => setPaused(true)} onBlur={() => setPaused(false)}>
      <Icon name="checkCircle" size={20} />
      <span>{toast.text}</span>
      {toast.action === "cart" && view.name !== "cart" ? (
        <button onClick={() => { dispatch({ type: "hideToast" }); push({ name: "cart" }); }}>Ver cesta</button>
      ) : null}
      <button className="toast-x" aria-label="Fechar aviso" onClick={() => dispatch({ type: "hideToast" })}><Icon name="close" size={18} /></button>
    </div>
  );
}
