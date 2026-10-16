import type { ReactNode } from "react";
import { useNav } from "../nav";
import { useApp } from "../state/app";
import { Icon } from "./Icon";

export function BasketButton() {
  const { count } = useApp();
  const { push } = useNav();
  return (
    <button className="icon-btn basket-btn" onClick={() => push({ name: "cart" })} aria-label={`Cesta, ${count} ${count === 1 ? "item" : "itens"}`}>
      <Icon name="basket" size={30} strokeWidth={1.6} />
      {count > 0 ? <span className="badge">{count}</span> : null}
    </button>
  );
}

/** Cabeçalho branco com título (Ofertas, Categorias, Minha cesta...). */
export function TitleBar({ title, back = true, right }: { title: string; back?: boolean; right?: ReactNode }) {
  const { pop, depth } = useNav();
  return (
    <header className="bar">
      {back && depth > 1 ? (
        <button className="icon-btn" onClick={pop} aria-label="Voltar">
          <Icon name="back" />
        </button>
      ) : null}
      <h1>{title}</h1>
      {right}
    </header>
  );
}

/** Barra azul com campo de busca e cesta (Favoritos, Categorias internas). */
export function BlueSearchBar({ back }: { back?: boolean }) {
  const { push, pop } = useNav();
  return (
    <header className="bar blue">
      {back ? (
        <button className="icon-btn" onClick={pop} aria-label="Voltar">
          <Icon name="back" />
        </button>
      ) : null}
      <button className="searchpill" style={{ minHeight: 48, boxShadow: "none" }} onClick={() => push({ name: "searchFocus" })}>
        <Icon name="search" />
        <span className="ph">O que você procura?</span>
      </button>
      <BasketButton />
    </header>
  );
}

/** Barra de resultados: voltar, campo com a busca atual, cesta. */
export function ResultsBar({ query }: { query: string }) {
  const { push, pop } = useNav();
  return (
    <header className="bar">
      <button className="icon-btn" onClick={pop} aria-label="Voltar">
        <Icon name="back" />
      </button>
      <div className="searchfield" style={{ cursor: "text" }}>
        <Icon name="search" />
        <button style={{ flex: 1, textAlign: "left", minHeight: 44, fontSize: 16, overflow: "hidden", whiteSpace: "nowrap", textOverflow: "ellipsis" }}
          onClick={() => push({ name: "searchFocus", initial: query })} aria-label={`Editar busca: ${query}`}>
          {query}
        </button>
        <button className="icon-btn" style={{ width: 36, height: 36 }} onClick={() => push({ name: "searchFocus" })} aria-label="Limpar busca">
          <Icon name="close" size={20} />
        </button>
      </div>
      <BasketButton />
    </header>
  );
}
