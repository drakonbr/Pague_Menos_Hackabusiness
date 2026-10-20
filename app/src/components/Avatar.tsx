/** Retrato ilustrado da persona (desenho original, vetorial). Renata, 49 anos: cabelo castanho curto com fios grisalhos,
 *  blusa azul da marca. Usado na tela inicial, em Mais e na conversa. */
export function PersonaAvatar({ size = 48, ring = false }: { size?: number; ring?: boolean }) {
  return (
    <svg width={size} height={size} viewBox="0 0 96 96" role="img" aria-label="Foto de perfil de Renata (ilustração)"
      style={{ borderRadius: "50%", flex: "none", boxShadow: ring ? "0 0 0 3px #fff" : undefined }}>
      <defs>
        <clipPath id="av-c"><circle cx="48" cy="48" r="48" /></clipPath>
        <linearGradient id="av-bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stopColor="#dfe6ff" /><stop offset="1" stopColor="#f6d9e3" /></linearGradient>
        <linearGradient id="av-hair" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#4a3228" /><stop offset="1" stopColor="#33211a" /></linearGradient>
      </defs>
      <g clipPath="url(#av-c)">
        <rect width="96" height="96" fill="url(#av-bg)" />
        {/* blusa */}
        <path d="M10 100c2-20 16-30 38-30s36 10 38 30z" fill="#2a2ad6" />
        <path d="M36 72c3 8 9 12 12 12s9-4 12-12c-4-2-8-3-12-3s-8 1-12 3z" fill="#e7b896" />
        {/* pescoço */}
        <path d="M41 60h14v14c0 4-3 7-7 7s-7-3-7-7z" fill="#e7b896" />
        {/* cabelo atrás */}
        <path d="M20 50c-2-22 10-34 28-34s30 12 28 34c-1 12-4 18-8 22l-40 0c-4-4-7-10-8-22z" fill="url(#av-hair)" />
        {/* rosto */}
        <ellipse cx="48" cy="46" rx="18" ry="22" fill="#f0c4a2" />
        {/* franja lateral */}
        <path d="M29 42c2-15 12-22 24-21 9 1 15 7 15 17-8-3-17-9-21-16-3 8-9 15-18 20z" fill="url(#av-hair)" />
        {/* fios grisalhos */}
        <path d="M33 30c4-6 10-9 16-9" stroke="#c9c6cf" strokeWidth="1.6" fill="none" strokeLinecap="round" />
        <path d="M30 36c2-3 4-5 7-7" stroke="#d9d6de" strokeWidth="1.3" fill="none" strokeLinecap="round" />
        {/* olhos e sobrancelhas */}
        <path d="M38 41q3-2 6 0M52 41q3-2 6 0" stroke="#3a2a22" strokeWidth="1.8" fill="none" strokeLinecap="round" />
        <circle cx="41" cy="46" r="1.7" fill="#2b1d17" /><circle cx="55" cy="46" r="1.7" fill="#2b1d17" />
        {/* nariz e sorriso */}
        <path d="M48 47c-1 4-2 6 0 7" stroke="#c99478" strokeWidth="1.4" fill="none" strokeLinecap="round" />
        <path d="M41 57q7 6 14 0" stroke="#b5483f" strokeWidth="2.2" fill="none" strokeLinecap="round" />
        {/* brinco */}
        <circle cx="30" cy="54" r="1.8" fill="#f4d27a" /><circle cx="66" cy="54" r="1.8" fill="#f4d27a" />
      </g>
    </svg>
  );
}
