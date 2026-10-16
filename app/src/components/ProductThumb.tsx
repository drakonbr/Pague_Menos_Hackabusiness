import type { Product, ProductForm } from "../contracts/types";

// Cores por marca fictícia: [fundo, destaque]
const BRAND: Record<string, [string, string]> = {
  "Aurora Dermo": ["#E6ECF8", "#2F4C8F"],
  "Lume Lab": ["#E4F4EC", "#1E7A5A"],
  Solare: ["#FFF0D6", "#C47000"],
  "Clara Pele": ["#FBE7EC", "#B03556"],
  "Vita Verde": ["#E8F3DF", "#3F7F22"],
  "Pura Base": ["#E4EEFA", "#0B4FA8"],
  "Bem Simples": ["#EEEBF8", "#5546A8"],
};

function shape(form: ProductForm, c: string) {
  const label = <rect x="19" y="24" width="10" height="7" rx="1.5" fill="#fff" fillOpacity=".85" />;
  switch (form) {
    case "tube":
      return (<><path d="M17 9h14l-1.5 4h-11z" fill={c} /><path d="M16 13h16l-3 27H19z" fill={c} fillOpacity=".92" />{label}</>);
    case "bottle":
      return (<><rect x="20" y="7" width="8" height="6" rx="1.5" fill={c} /><rect x="15" y="13" width="18" height="28" rx="5" fill={c} fillOpacity=".92" />{label}</>);
    case "pump":
      return (<><path d="M21 6h9v3h-9zM24 9h3v5h-3z" fill={c} /><rect x="15" y="14" width="18" height="27" rx="5" fill={c} fillOpacity=".92" />{label}</>);
    case "jar":
      return (<><rect x="12" y="15" width="24" height="7" rx="2.5" fill={c} /><rect x="13" y="22" width="22" height="17" rx="4.5" fill={c} fillOpacity=".92" /><rect x="19" y="27" width="10" height="6" rx="1.5" fill="#fff" fillOpacity=".85" /></>);
    case "dropper":
      return (<><circle cx="24" cy="9" r="4" fill={c} /><rect x="21.5" y="12" width="5" height="5" fill={c} /><rect x="16" y="17" width="16" height="24" rx="4.5" fill={c} fillOpacity=".92" /><rect x="19.5" y="25" width="9" height="6" rx="1.5" fill="#fff" fillOpacity=".85" /></>);
    case "stick":
      return (<><rect x="19" y="8" width="10" height="9" rx="3" fill={c} /><rect x="17.5" y="17" width="13" height="24" rx="3.5" fill={c} fillOpacity=".92" /><rect x="20" y="24" width="8" height="6" rx="1.5" fill="#fff" fillOpacity=".85" /></>);
    case "patch":
      return (<><circle cx="18" cy="19" r="7" fill={c} fillOpacity=".92" /><circle cx="30" cy="27" r="7" fill={c} fillOpacity=".7" /><circle cx="18" cy="33" r="5" fill={c} fillOpacity=".5" /></>);
    case "spray":
      return (<><path d="M21 6h8l3 3h-6v4h-5z" fill={c} /><rect x="16" y="13" width="16" height="28" rx="5" fill={c} fillOpacity=".92" />{label}</>);
    case "bar":
      return (<><rect x="11" y="17" width="26" height="17" rx="6" fill={c} fillOpacity=".92" /><rect x="18" y="22" width="12" height="7" rx="2" fill="#fff" fillOpacity=".85" /></>);
  }
}

export function ProductThumb({ product, size = 56 }: { product: Product; size?: number }) {
  const [bg, accent] = BRAND[product.brand] ?? ["#EEF1F6", "#4A5878"];
  return (
    <svg
      className="thumb"
      width={size}
      height={size}
      viewBox="0 0 48 48"
      role="img"
      aria-label={`${product.productType}, ${product.brand}`}
    >
      <rect width="48" height="48" rx="12" fill={bg} />
      {shape(product.form, accent)}
    </svg>
  );
}
