import { useNav, type Tab } from "../nav";
import { Icon, type IconName } from "./Icon";

const TABS: Array<{ id: Tab; label: string; icon: IconName }> = [
  { id: "home", label: "Home", icon: "home" },
  { id: "chat", label: "Chat", icon: "chat" },
  { id: "ofertas", label: "Ofertas", icon: "tag" },
  { id: "favoritos", label: "Favoritos", icon: "heart" },
  { id: "mais", label: "Mais", icon: "more" },
];

export function TabBar() {
  const { tab, goTab } = useNav();
  return (
    <nav className="tabbar" aria-label="Navegação principal">
      {TABS.map((t) => (
        <button key={t.id} onClick={() => goTab(t.id)} aria-current={tab === t.id ? "page" : undefined}>
          <Icon name={t.icon} size={26} strokeWidth={tab === t.id ? 2 : 1.6} />
          {t.label}
        </button>
      ))}
    </nav>
  );
}
