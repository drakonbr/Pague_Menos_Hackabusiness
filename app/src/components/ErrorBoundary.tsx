import { Component, type ErrorInfo, type ReactNode } from "react";
import { clearSession } from "../services/cartStorage";

/** Rede de segurança (#48): se uma tela quebrar por dado guardado no aparelho, a pessoa consegue limpar e voltar, em vez de tela em branco. */
export class ErrorBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Tela quebrou:", error, info.componentStack);
  }
  render() {
    if (!this.state.failed) return this.props.children;
    return (
      <div className="screen" role="alert">
        <div className="pad" style={{ alignItems: "center", textAlign: "center", paddingTop: 48 }}>
          <h2 style={{ fontSize: 20 }}>Algo deu errado nesta tela</h2>
          <p style={{ color: "var(--text-2)", lineHeight: 1.5 }}>Pode ser um dado antigo guardado neste aparelho. Limpar a cesta e os pedidos da demonstração costuma resolver.</p>
          <button className="btn primary block" onClick={() => { clearSession(); window.location.reload(); }}>Limpar a cesta e recarregar</button>
          <button className="link" onClick={() => window.location.reload()}>Só recarregar</button>
        </div>
      </div>
    );
  }
}
