import type { Product } from "../contracts/types";
import { ProductThumb } from "./ProductThumb";

/** Foto real (banco de imagens). Enquanto a foto não foi revisada, mostra o desenho provisório. */
export function ProductImage({ product, size }: { product: Product; size?: number }) {
  const img = product.images[0];
  if (img) {
    return (
      <img className="photo" src={img.src} alt={img.alt || `${product.productType} ${product.brand}`} loading="lazy"
        style={size ? { width: size, height: size } : undefined} />
    );
  }
  return (
    <div className="photo-fallback" style={size ? { width: size, height: size } : undefined} title="Foto ainda não revisada">
      <ProductThumb product={product} size={size ? size * 0.9 : 96} />
      {!size || size >= 80 ? <span className="pend">foto pendente</span> : null}
    </div>
  );
}
