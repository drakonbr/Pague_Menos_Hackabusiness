import type { Product } from "../contracts/types";
import { useNav } from "../nav";
import { money } from "../services/format";
import { useApp } from "../state/app";
import { Icon } from "./Icon";
import { ProductImage } from "./ProductImage";

export function discountPct(p: Product): number {
  return p.listPriceCents > p.priceCents ? Math.round((1 - p.priceCents / p.listPriceCents) * 100) : 0;
}

export function ProductCard({ product: p, tag }: { product: Product; tag?: string }) {
  const { push } = useNav();
  const { dispatch, isFav } = useApp();
  const fav = isFav(p.id);
  const off = discountPct(p);
  const label = tag ?? (p.rx ? "Exige receita" : off > 0 ? "Super oferta" : p.cashbackPct > 0 ? `${p.cashbackPct}% de cashback` : undefined);
  const out = p.stockQty <= 0;
  return (
    <article className="pcard">
      {label ? <span className="tag">{label}</span> : null}
      <button className="icon-btn fav" aria-pressed={fav} aria-label={fav ? "Tirar dos favoritos" : "Favoritar"}
        onClick={() => dispatch({ type: "toggleFav", id: p.id })}>
        <Icon name={fav ? "heartFill" : "heart"} size={26} />
      </button>
      <button className="img" onClick={() => push({ name: "product", id: p.id })} aria-label={`Ver ${p.name}`}>
        <ProductImage product={p} />
      </button>
      <div className="body">
        <button className="name" style={{ textAlign: "left" }} onClick={() => push({ name: "product", id: p.id })}>
          {p.name}
        </button>
        <div className="brandrow">
          <span className="brandname">{p.brand}</span>
          <button className="addbtn" disabled={out} aria-label={out ? "Indisponível" : `Adicionar ${p.name} à cesta${p.rx ? " (exige receita)" : ""}`}
            onClick={() => dispatch({ type: "addProduct", product: p })}>
            <Icon name="basketPlus" size={26} />
          </button>
        </div>
        <div className="prices">
          {out ? (
            <span className="unavail">Indisponível</span>
          ) : (
            <>
              {off > 0 ? <span className="old">{money(p.listPriceCents)}</span> : <span className="old" style={{ visibility: "hidden" }}>.</span>}
              <span className="price">{money(p.priceCents)}</span>
              <span className="unit">{`${p.size.value} ${p.size.unit}`}</span>
            </>
          )}
        </div>
      </div>
    </article>
  );
}
