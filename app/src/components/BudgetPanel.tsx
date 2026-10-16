import { useEffect, useRef, useState } from "react";
import { money } from "../services/format";

const MIN = 2000;
const MAX = 30000;
const STEP = 500;
const SHORTCUTS = [8000, 12000, 20000];

interface Props {
  /** null = sem limite */
  value: number | null;
  onChange: (cents: number | null) => void;
}

export function BudgetPanel({ value, onChange }: Props) {
  const [draft, setDraft] = useState<number>(value ?? MAX);
  const timer = useRef<number | undefined>(undefined);

  // acompanha mudanças vindas de fora (atalhos, chip, nova busca)
  useEffect(() => setDraft(value ?? MAX), [value]);
  useEffect(() => () => window.clearTimeout(timer.current), []);

  const slide = (v: number) => {
    setDraft(v);
    window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => onChange(v), 350);
  };
  const jump = (v: number | null) => {
    window.clearTimeout(timer.current);
    setDraft(v ?? MAX);
    onChange(v);
  };

  return (
    <section className="panel" aria-label="Controle de orçamento">
      <div className="budget-top">
        <div>
          <span className="section-title">Quanto quer gastar</span>
          <div>
            <b>{value == null && draft === MAX ? "Sem limite" : `Até ${money(draft)}`}</b>
          </div>
        </div>
        <span>{`${money(MIN)} a ${money(MAX)}`}</span>
      </div>
      <input
        type="range"
        min={MIN}
        max={MAX}
        step={STEP}
        value={draft}
        onChange={(e) => slide(Number(e.target.value))}
        aria-label="Orçamento máximo"
        aria-valuetext={`Até ${money(draft)}`}
      />
      <div className="chips">
        {SHORTCUTS.map((c) => (
          <button key={c} className={`chip ${value === c ? "on" : ""}`} onClick={() => jump(c)}>
            até {money(c).replace(",00", "")}
          </button>
        ))}
        <button className={`chip ${value == null ? "on" : ""}`} onClick={() => jump(null)}>
          sem limite
        </button>
      </div>
    </section>
  );
}
