import { useState, type FormEvent } from "react";
import { Icon } from "../components/Icon";
import { useNav } from "../nav";
import { useApp } from "../state/app";

const EXAMPLES = [
  "preciso de produtos para tratamento de acne, pele oleosa, até R$ 100",
  "quero começar a cuidar da pele até R$ 120",
  "protetor solar e manchas, sem perfume",
  "pele sensível, algo simples",
];

export function SearchFocus({ initial = "" }: { initial?: string }) {
  const { pop, replace, view } = useNav();
  const { recents, dispatch, storeId } = useApp();
  const [q, setQ] = useState(initial);

  const go = (query: string) => {
    const t = query.trim();
    if (!t) return;
    dispatch({ type: "recent", q: t });
    replace({ name: "results", req: { query: t, storeId } });
  };
  const submit = (e: FormEvent) => {
    e.preventDefault();
    go(q);
  };

  return (
    <div className="screen" style={{ background: "#fff" }} key={view.name}>
      <form className="bar" onSubmit={submit} role="search" style={{ boxShadow: "none" }}>
        <div className="searchfield" style={{ borderColor: "var(--brand)" }}>
          <Icon name="search" />
          <label className="sr-only" htmlFor="q">O que você procura?</label>
          <input id="q" autoFocus value={q} onChange={(e) => setQ(e.target.value)} placeholder="O que você procura?" autoComplete="off" enterKeyHint="search" />
          {q ? (
            <button type="button" className="icon-btn" style={{ width: 36, height: 36 }} onClick={() => setQ("")} aria-label="Apagar">
              <Icon name="close" size={18} />
            </button>
          ) : null}
        </div>
        <button type="button" className="link plain" style={{ padding: "0 8px", minHeight: 44 }} onClick={pop}>Cancelar</button>
      </form>
      <div className="scroll">
        <div className="pad">
          <div className="shortcuts" style={{ gridTemplateColumns: "1fr 1fr 1fr", gap: 8 }}>
            <button className="shortcut" style={{ minHeight: 84, alignItems: "center", textAlign: "center", border: 0 }} disabled title="Fora do protótipo">
              <Icon name="mic" /> <b style={{ fontSize: 13 }}>Buscar por áudio</b>
            </button>
            <button className="shortcut" style={{ minHeight: 84, alignItems: "center", textAlign: "center", border: 0 }} disabled title="Fora do protótipo (medicamentos)">
              <Icon name="receipt" /> <b style={{ fontSize: 13 }}>Buscar com receita</b>
            </button>
            <button className="shortcut" style={{ minHeight: 84, alignItems: "center", textAlign: "center", border: 0 }} disabled title="Fora do protótipo">
              <Icon name="barcode" /> <b style={{ fontSize: 13 }}>Ler código de barras</b>
            </button>
          </div>
          <div className="note">
            <Icon name="sparkle" size={20} />
            <p>
              <b>Novo:</b> descreva o que você precisa e quanto quer gastar. A gente monta kits completos, sem produto repetido.
            </p>
          </div>

          {recents.length ? (
            <section aria-label="Buscas recentes">
              <div className="sec-head">
                <h2 style={{ fontSize: 19 }}>Buscas recentes</h2>
                <button className="link plain" onClick={() => dispatch({ type: "clearRecents" })}>Limpar busca</button>
              </div>
              <ul style={{ listStyle: "none", padding: 0, margin: "8px 0 0" }}>
                {recents.map((r) => (
                  <li key={r} className="row" style={{ borderBottom: "1px solid var(--line)", minHeight: 52 }}>
                    <button className="row grow" style={{ textAlign: "left", minHeight: 52, color: "var(--text-2)" }} onClick={() => go(r)}>
                      <Icon name="clock" size={20} /> <span className="grow">{r}</span>
                    </button>
                    <button className="icon-btn" onClick={() => dispatch({ type: "removeRecent", q: r })} aria-label={`Remover ${r}`}>
                      <Icon name="close" size={20} />
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          <section aria-label="Exemplos">
            <h2 style={{ fontSize: 19 }}>Experimente</h2>
            <ul style={{ listStyle: "none", padding: 0, margin: "8px 0 0" }}>
              {EXAMPLES.map((r) => (
                <li key={r}>
                  <button className="row" style={{ textAlign: "left", minHeight: 52, width: "100%", borderBottom: "1px solid var(--line)", color: "var(--text-2)" }} onClick={() => go(r)}>
                    <Icon name="search" size={20} /> <span className="grow">{r}</span>
                  </button>
                </li>
              ))}
            </ul>
          </section>
        </div>
      </div>
    </div>
  );
}
