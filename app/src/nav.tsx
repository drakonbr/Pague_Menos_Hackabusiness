// Navegação por abas, cada aba com sua pilha de telas (como no app real).
import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";
import type { CommerceService, Intent, Kit, SearchRequest, SearchService } from "./contracts/types";

export type Tab = "home" | "categorias" | "ofertas" | "favoritos" | "mais";

export type View =
  | { name: "home" }
  | { name: "searchFocus"; initial?: string }
  | { name: "chat"; initial?: string }
  | { name: "refill" }
  | { name: "privacy" }
  | { name: "results"; req: SearchRequest }
  | { name: "categorias" }
  | { name: "category"; id: string }
  | { name: "product"; id: string }
  | { name: "kit"; kit: Kit; intent: Intent }
  | { name: "cart" }
  | { name: "delivery" }
  | { name: "payment" }
  | { name: "done"; orderId: string }
  | { name: "ofertas" }
  | { name: "favoritos" }
  | { name: "mais" }
  | { name: "orders" }
  | { name: "subscriptions" }
  | { name: "wallet" }
  | { name: "credits" }
  | { name: "stores" };

/** Telas que escondem a barra de abas (como a cesta e a entrega no app real). */
export const FULLSCREEN = new Set<View["name"]>(["searchFocus", "chat", "cart", "delivery", "payment", "done"]);

const ROOT: Record<Tab, View> = {
  home: { name: "home" },
  categorias: { name: "categorias" },
  ofertas: { name: "ofertas" },
  favoritos: { name: "favoritos" },
  mais: { name: "mais" },
};

interface NavApi {
  tab: Tab;
  view: View;
  depth: number;
  push: (v: View) => void;
  pop: () => void;
  replace: (v: View) => void;
  goTab: (t: Tab) => void;
  resetTo: (t: Tab, extra?: View) => void;
  /** Volta todas as abas à raiz e abre `t` (depois de finalizar um pedido). */
  resetAll: (t: Tab, extra?: View) => void;
}

const NavCtx = createContext<NavApi | null>(null);

export function NavProvider({ children }: { children: ReactNode }) {
  const [tab, setTab] = useState<Tab>("home");
  const [stacks, setStacks] = useState<Record<Tab, View[]>>({
    home: [ROOT.home],
    categorias: [ROOT.categorias],
    ofertas: [ROOT.ofertas],
    favoritos: [ROOT.favoritos],
    mais: [ROOT.mais],
  });

  const push = useCallback((v: View) => setStacks((s) => ({ ...s, [tab]: [...s[tab], v] })), [tab]);
  const pop = useCallback(() => setStacks((s) => ({ ...s, [tab]: s[tab].length > 1 ? s[tab].slice(0, -1) : s[tab] })), [tab]);
  const replace = useCallback((v: View) => setStacks((s) => ({ ...s, [tab]: [...s[tab].slice(0, -1), v] })), [tab]);
  const goTab = useCallback(
    (t: Tab) => {
      // tocar na aba ativa volta para a raiz dela
      if (t === tab) setStacks((s) => ({ ...s, [t]: [ROOT[t]] }));
      setTab(t);
    },
    [tab],
  );
  const resetTo = useCallback((t: Tab, extra?: View) => {
    setStacks((s) => ({ ...s, [t]: extra ? [ROOT[t], extra] : [ROOT[t]] }));
    setTab(t);
  }, []);

  const resetAll = useCallback((t: Tab, extra?: View) => {
    setStacks({
      home: [ROOT.home],
      categorias: [ROOT.categorias],
      ofertas: [ROOT.ofertas],
      favoritos: [ROOT.favoritos],
      mais: [ROOT.mais],
      [t]: extra ? [ROOT[t], extra] : [ROOT[t]],
    } as Record<Tab, View[]>);
    setTab(t);
  }, []);

  const api = useMemo<NavApi>(() => {
    const stack = stacks[tab];
    return { tab, view: stack[stack.length - 1], depth: stack.length, push, pop, replace, goTab, resetTo, resetAll };
  }, [tab, stacks, push, pop, replace, goTab, resetTo, resetAll]);
  return <NavCtx.Provider value={api}>{children}</NavCtx.Provider>;
}

export function useNav(): NavApi {
  const c = useContext(NavCtx);
  if (!c) throw new Error("useNav fora do NavProvider");
  return c;
}

// Serviços (busca de kits e comércio) disponíveis para todas as telas
interface Services {
  search: SearchService;
  commerce: CommerceService;
}
const SvcCtx = createContext<Services | null>(null);
export function ServicesProvider({ value, children }: { value: Services; children: ReactNode }) {
  return <SvcCtx.Provider value={value}>{children}</SvcCtx.Provider>;
}
export function useServices(): Services {
  const c = useContext(SvcCtx);
  if (!c) throw new Error("useServices fora do ServicesProvider");
  return c;
}
