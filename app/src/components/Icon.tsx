import type { ReactNode } from "react";

export type IconName =
  | "search" | "back" | "basket" | "basketPlus" | "mic" | "camera" | "barcode" | "receipt" | "bell"
  | "home" | "grid" | "tag" | "heart" | "heartFill" | "more" | "pin" | "chevron" | "chevronDown" | "chevronUp"
  | "close" | "filter" | "clock" | "share" | "trash" | "plus" | "minus" | "check" | "checkCircle" | "info"
  | "alert" | "shield" | "swap" | "store" | "truck" | "locker" | "map" | "cross" | "wallet" | "repeat"
  | "box" | "sparkle" | "pill" | "lipstick" | "stroller" | "dumbbell" | "bottle" | "bag" | "paw" | "image" | "user";

const P: Record<IconName, ReactNode> = {
  search: (<><circle cx="11" cy="11" r="6.5" /><path d="M16 16l4.5 4.5" /></>),
  back: <path d="M19 12H5M11 6l-6 6 6 6" />,
  basket: (<><path d="M3 9h18l-1.6 9.2a2 2 0 0 1-2 1.8H6.6a2 2 0 0 1-2-1.8z" /><path d="M8 9l3-5M16 9l-3-5M9 13v4M12 13v4M15 13v4" /></>),
  basketPlus: (<><path d="M3 9h18l-.7 4M8 9l3-5M16 9l-3-5" /><path d="M13 20H6.6a2 2 0 0 1-2-1.8L3.4 11" /><circle cx="17.5" cy="17.5" r="4" /><path d="M17.5 15.5v4M15.5 17.5h4" /></>),
  mic: (<><rect x="9" y="3" width="6" height="11" rx="3" /><path d="M6 11a6 6 0 0 0 12 0M12 17v4" /></>),
  camera: (<><rect x="3" y="6.5" width="18" height="13" rx="2.5" /><path d="M8.5 6.5L10 4h4l1.5 2.5" /><circle cx="12" cy="13" r="3.2" /></>),
  barcode: <path d="M4 6v12M7 6v12M10.5 6v12M13 6v12M16.5 6v12M20 6v12" />,
  receipt: (<><path d="M7 3h7l4 4v14H7z" /><path d="M14 3v4h4M10 12h5M10 16h5" /></>),
  bell: (<><path d="M6 16V11a6 6 0 0 1 12 0v5l1.5 2h-15z" /><path d="M10 20a2 2 0 0 0 4 0" /></>),
  home: (<><path d="M4 10.5L12 4l8 6.5V20h-5.5v-6h-5v6H4z" /></>),
  grid: (<><rect x="4" y="4" width="7" height="7" rx="1.5" /><rect x="13" y="4" width="7" height="4.5" rx="1.5" /><rect x="4" y="13" width="7" height="7" rx="1.5" /><rect x="13" y="10.5" width="7" height="9.5" rx="1.5" /></>),
  tag: (<><path d="M3.5 12.2V4.5a1 1 0 0 1 1-1h7.7l8.3 8.3a1 1 0 0 1 0 1.4l-7.3 7.3a1 1 0 0 1-1.4 0z" /><circle cx="8" cy="8" r="1.4" /></>),
  heart: <path d="M12 20s-7.5-4.6-7.5-10A4.3 4.3 0 0 1 12 7.4 4.3 4.3 0 0 1 19.5 10c0 5.4-7.5 10-7.5 10z" />,
  heartFill: <path d="M12 20s-7.5-4.6-7.5-10A4.3 4.3 0 0 1 12 7.4 4.3 4.3 0 0 1 19.5 10c0 5.4-7.5 10-7.5 10z" fill="currentColor" />,
  more: (<><circle cx="5" cy="12" r="1.8" /><circle cx="12" cy="12" r="1.8" /><circle cx="19" cy="12" r="1.8" /></>),
  pin: (<><path d="M12 21s6.5-5.7 6.5-11A6.5 6.5 0 0 0 5.5 10c0 5.3 6.5 11 6.5 11z" /><circle cx="12" cy="10" r="2.3" /></>),
  chevron: <path d="M9 6l6 6-6 6" />,
  chevronDown: <path d="M6 9l6 6 6-6" />,
  chevronUp: <path d="M6 15l6-6 6 6" />,
  close: <path d="M6 6l12 12M18 6L6 18" />,
  filter: (<><path d="M4 7h10M18 7h2M4 17h4M12 17h8" /><circle cx="16" cy="7" r="2" /><circle cx="10" cy="17" r="2" /></>),
  clock: (<><circle cx="12" cy="12" r="8.5" /><path d="M12 7.5V12l3 2" /></>),
  share: (<><circle cx="6" cy="12" r="2.3" /><circle cx="18" cy="6" r="2.3" /><circle cx="18" cy="18" r="2.3" /><path d="M8 11l8-4M8 13l8 4" /></>),
  trash: <path d="M4 7h16M10 11v6M14 11v6M6 7l1 12a1.5 1.5 0 0 0 1.5 1.4h7a1.5 1.5 0 0 0 1.5-1.4L18 7M9 7V4.5h6V7" />,
  plus: <path d="M12 5v14M5 12h14" />,
  minus: <path d="M5 12h14" />,
  check: <path d="M5 12.5l4.5 4.5L19 7.5" />,
  checkCircle: (<><circle cx="12" cy="12" r="8.5" /><path d="M8.3 12.3l2.6 2.6 5-5.2" /></>),
  info: (<><circle cx="12" cy="12" r="8.5" /><path d="M12 11v5M12 8v.1" /></>),
  alert: (<><path d="M12 4l9 16H3z" /><path d="M12 10v4.5M12 17.5v.1" /></>),
  shield: (<><path d="M12 3l7 3v5.5c0 4.3-2.8 7.6-7 9.5-4.2-1.9-7-5.2-7-9.5V6z" /><path d="M9 12l2.2 2.2L15.5 10" /></>),
  swap: (<><path d="M5 8h13M14.5 4.5L18 8l-3.5 3.5" /><path d="M19 16H6M9.5 12.5L6 16l3.5 3.5" /></>),
  store: (<><path d="M4 9l1.5-5h13L20 9" /><path d="M4 9a2.7 2.7 0 0 0 5.3 0 2.7 2.7 0 0 0 5.4 0A2.7 2.7 0 0 0 20 9" /><path d="M5.5 11.5V20h13v-8.5M10 20v-4.5h4V20" /></>),
  truck: (<><path d="M3 6h11v10H3zM14 9.5h3.5L21 13v3h-7" /><circle cx="7" cy="17.5" r="1.7" /><circle cx="17" cy="17.5" r="1.7" /></>),
  locker: (<><rect x="4" y="4" width="16" height="16" rx="1.5" /><path d="M12 4v16M4 10h8M12 14h8M8.5 7v.1M15.5 17v.1" /></>),
  map: (<><path d="M9 4L3.5 6v14L9 18l6 2 5.5-2V4L15 6z" /><path d="M9 4v14M15 6v14" /></>),
  cross: <path d="M9 3.5h6v5.5h5.5v6H15v5.5H9V15H3.5V9H9z" />,
  wallet: (<><rect x="3.5" y="6" width="17" height="13" rx="2" /><path d="M3.5 9h17M16 13.5h2" /><path d="M6 6l9-2.5L16 6" /></>),
  repeat: (<><path d="M4 11V9a3 3 0 0 1 3-3h12M16 3l3 3-3 3" /><path d="M20 13v2a3 3 0 0 1-3 3H5M8 21l-3-3 3-3" /></>),
  box: (<><path d="M4 7.5L12 4l8 3.5v9L12 20l-8-3.5z" /><path d="M4 7.5L12 11l8-3.5M12 11v9" /></>),
  sparkle: (<><path d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5L18 18M18 6l-2.5 2.5M8.5 15.5L6 18" /></>),
  pill: (<><rect x="3" y="8.5" width="18" height="7" rx="3.5" transform="rotate(-40 12 12)" /><path d="M9.5 9.2l5.4 5.6" /></>),
  lipstick: (<><path d="M5.5 21V12h4.5v9zM6.5 12V7l2.5-2.5V12" /><rect x="13" y="9" width="6" height="12" rx="1" /><path d="M13 13h6M13 17h6" /></>),
  stroller: (<><path d="M4 5h2l2 9h9.5l2-6H7" /><circle cx="9" cy="18.5" r="1.7" /><circle cx="17" cy="18.5" r="1.7" /></>),
  dumbbell: (<><path d="M4 9v6M7 7v10M17 7v10M20 9v6M7 12h10" /></>),
  bottle: (<><rect x="8" y="7" width="8" height="14" rx="2" /><path d="M10 7V3.5h4V7M10 11h4" /></>),
  bag: (<><path d="M5 8h14l-1 12H6z" /><path d="M9 8V6a3 3 0 0 1 6 0v2" /></>),
  paw: (<><circle cx="8" cy="8" r="1.8" /><circle cx="16" cy="8" r="1.8" /><circle cx="5" cy="12.5" r="1.6" /><circle cx="19" cy="12.5" r="1.6" /><path d="M12 12c-3 0-5 3.5-4 5.5s6 2 8 0-1-5.5-4-5.5z" /></>),
  image: (<><rect x="3.5" y="5" width="17" height="14" rx="2" /><circle cx="9" cy="10" r="1.8" /><path d="M20.5 16l-5-5-8.5 8" /></>),
  user: (<><circle cx="12" cy="8.5" r="3.8" /><path d="M4.5 20a7.5 7.5 0 0 1 15 0" /></>),
};

export function Icon({ name, size = 22, className, strokeWidth = 1.7 }: { name: IconName; size?: number; className?: string; strokeWidth?: number }) {
  return (
    <svg className={className} width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
      {P[name]}
    </svg>
  );
}

/** Marca do app: quadrado vermelho com cruz branca (símbolo genérico de farmácia). */
export function LogoMark({ size = 36 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 40 40" aria-hidden="true" focusable="false">
      <rect width="40" height="40" rx="9" fill="var(--logo)" />
      <path d="M16 8h8v8h8v8h-8v8h-8v-8H8v-8h8z" fill="#fff" />
    </svg>
  );
}
