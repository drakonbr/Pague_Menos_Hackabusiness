import { useEffect, useMemo, useRef, useState } from "react";
import { ResultsBar } from "../components/Bars";
import { BottomSheet } from "../components/BottomSheet";
import { BudgetPanel } from "../components/BudgetPanel";
import { Icon } from "../components/Icon";
import { IntentChips } from "../components/IntentChips";
import { KitCard } from "../components/KitCard";
import { ProductCard } from "../components/ProductCard";
import type { Kit, Product, SearchRequest, SearchResponse, SkinType, SortKey } from "../contracts/types";
import { useNav, useServices } from "../nav";
import { money } from "../services/format";
import { useApp } from "../state/app";

const SKINS: Array<{ value: SkinType; label: string }> = [
  { value: "oleosa", label: "Oleosa" },
  { value: "mista", label: "Mista" },
  { value: "seca", label: "Seca" },
  { value: "normal", label: "Normal" },
  { value: "sensível", label: "Sensível" },
];

const SEARCH_ACTS = new Set(["busca", "refinar", "negacao"]);

export function sortList(list: Product[], sort: SortKey): Product[] {
  const stock = (a: Product, b: Product) => Number(b.stockQty > 0) - Number(a.stockQty > 0);
  const c = [...list];
  if (sort === "menor_preco") return c.sort((a, b) => stock(a, b) || a.priceCents - b.priceCents);
  if (sort === "maior_preco") return c.sort((a, b) => stock(a, b) || b.priceCents - a.priceCents);
  if (sort === "mais_vendidos") return c.sort((a, b) => stock(a, b) || a.salesRank - b.salesRank);
  return c; // relevância = ordem do serviço
}

type State = { status: "loading" } | { status: "error"; message: string } | { status: "done"; res: SearchResponse; refreshing: boolean };

export function Results({ req }: { req: SearchRequest }) {
  const { search } = useServices();
  const { replace, push } = useNav();
  const { storeId, store } = useApp();
  const [state, setState] = useState<State>({ status: "loading" });
  const counter = useRef(0);

  // a loja escolhida no app vale para a busca (kits só com o que a loja tem)
  useEffect(() => {
    if ((req.storeId ?? null) !== storeId) replace({ name: "results", req: { ...req, storeId } });
  }, [storeId, req, replace]);

  useEffect(() => {
    const id = ++counter.current;
    setState((s) => (s.status === "done" ? { ...s, refreshing: true } : { status: "loading" }));
    search.search(req).then(
      (res) => id === counter.current && setState({ status: "done", res, refreshing: false }),
      (e: unknown) => id === counter.current && setState({ status: "error", message: e instanceof Error ? e.message : "Falha na busca." }),
    );
  }, [req, search]);

  const patch = (p: Partial<SearchRequest>) => replace({ name: "results", req: { ...req, ...p } });
  // chip de ajuste ("Mais barato", "Sem fragrância"): refaz a MESMA lista, levando o contexto da resposta atual
  const refine = (q: string) => {
    if (state.status !== "done") return;
    replace({ name: "results", req: { query: q, storeId, context: state.res.context ?? null } });
  };

  // pedidos de conversa (repor remédio, entrega, trocar item...) continuam no assistente; busca e ajustes ficam aqui
  const act = state.status === "done" ? state.res.act : undefined;
  useEffect(() => {
    if (act && !SEARCH_ACTS.has(act)) replace({ name: "chat", initial: req.query });
  }, [act, req.query, replace]);

  return (
    <div className="screen">
      <ResultsBar query={req.query} />
      <div className="scroll">
        {state.status === "loading" ? (
          <div className="pad" role="status" aria-label="Montando seus kits">
            <div className="skeleton" style={{ height: 36, width: "70%" }} />
            <div className="skeleton" style={{ height: 240 }} />
            <div className="skeleton" style={{ height: 200 }} />
          </div>
        ) : null}
        {state.status === "error" ? (
          <div className="pad">
            <div className="note danger" role="alert">
              <Icon name="alert" size={18} />
              <p>{state.message}</p>
            </div>
            <button className="btn outline blue" onClick={() => patch({})}>Tentar de novo</button>
          </div>
        ) : null}
        {state.status === "done" ? (
          <div aria-busy={state.refreshing || undefined} style={{ opacity: state.refreshing ? 0.55 : 1, transition: "opacity .15s" }}>
            <ResultBody res={state.res} storeName={store?.name ?? null} onPatch={patch} onRefine={refine}
              onOpen={(kit) => push({ name: "kit", kit, intent: state.res.intent })} onStores={() => push({ name: "stores" })} />
          </div>
        ) : null}
      </div>
    </div>
  );
}

/** Kits em cima (quando há), a lista COMPLETA de itens individuais logo abaixo, e ajustes em chips. */
function ResultBody({ res, storeName, onPatch, onRefine, onOpen, onStores }: {
  res: SearchResponse;
  storeName: string | null;
  onPatch: (p: Partial<SearchRequest>) => void;
  onRefine: (q: string) => void;
  onOpen: (k: Kit) => void;
  onStores: () => void;
}) {
  const hasKits = res.kitsStatus !== "not_applicable";
  const label = res.scope?.label;
  const listTitle = label ? `Todos os itens de ${label}` : "Itens relacionados";
  const empty = !res.products.length && !res.kits.length && !res.closestKit;
  const lead = res.reply && !hasKits ? res.reply : null;
  return (
    <>
      {res.correctedQuery ? (
        <div className="pad" style={{ paddingBottom: 0 }}>
          <div className="note" role="status"><Icon name="info" size={18} /><p>Mostrando resultados para <b>{res.correctedQuery}</b>.</p></div>
        </div>
      ) : null}
      {res.catalogNotice ? (
        <div className="pad" style={{ paddingBottom: 0 }}>
          <div className="note warn" role="status" data-testid="catalog-notice">
            <Icon name="alert" size={18} />
            <p>{res.catalogNotice.message}{res.catalogNotice.shelf ? ` Veja o que temos em ${res.catalogNotice.shelf}.` : ""}</p>
          </div>
        </div>
      ) : null}
      {hasKits ? (
        <KitZone res={res} storeName={storeName} onPatch={onPatch} onOpen={onOpen} onStores={onStores} />
      ) : (
        <div className="pad" style={{ paddingBottom: 0 }}>
          {res.safety.decision === "caution" && res.safety.message ? (
            <div className="note warn" role="note"><Icon name="alert" size={18} /><p>{res.safety.message}</p></div>
          ) : null}
          {lead && !res.catalogNotice ? <div className="note" role="status"><Icon name="info" size={18} /><p>{lead}</p></div> : null}
          {res.notes.filter((n) => !res.reply?.includes(n)).map((n) => <div key={n} className="note"><Icon name="info" size={18} /><p>{n}</p></div>)}
        </div>
      )}
      {res.products.length ? (
        <ProductList products={res.products} title={hasKits ? `${listTitle} (${res.products.length})` : undefined} />
      ) : empty && !res.catalogNotice && !lead ? (
        <p className="count">Não encontrei itens para esse pedido. Tente outras palavras ou escolha uma das sugestões abaixo.</p>
      ) : null}
      {res.suggestions?.length ? (
        <div className="chips" style={{ padding: "4px 16px 20px" }} aria-label="Ajustar a busca">
          {res.suggestions.map((c) => <button key={c} className="chip" onClick={() => onRefine(c)}>{c}</button>)}
        </div>
      ) : null}
    </>
  );
}

function KitZone({ res, storeName, onPatch, onOpen, onStores }: {
  res: SearchResponse;
  storeName: string | null;
  onPatch: (p: Partial<SearchRequest>) => void;
  onOpen: (k: Kit) => void;
  onStores: () => void;
}) {
  const [sheet, setSheet] = useState(false);
  const [budgetOpen, setBudgetOpen] = useState(false);
  const { intent } = res;
  const budget = intent.budgetCents;

  return (
    <section className="kitzone" aria-label="Kits inteligentes">
      <div className="title">
        <Icon name="sparkle" size={20} /> Kits inteligentes para o seu pedido
      </div>
      <IntentChips intent={intent} onEditSkin={() => setSheet(true)} onEditBudget={() => setBudgetOpen(true)} />
      <button className="row" style={{ fontSize: 13.5, color: "var(--text-2)", textAlign: "left", minHeight: 36 }} onClick={onStores}>
        <Icon name="store" size={18} />
        <span className="grow">{storeName ? `Só com o estoque da ${storeName}` : "Estoque para entrega em casa"}</span>
        <span className="link plain" style={{ fontSize: 13.5 }}>{storeName ? "Trocar loja" : "Retirar na loja"}</span>
      </button>

      {res.safety.decision === "caution" && res.safety.message ? (
        <div className="note warn" role="note"><Icon name="alert" size={18} /><p>{res.safety.message}</p></div>
      ) : null}


      {res.notes.map((n) => (
        <div key={n} className="note" role="note"><Icon name="info" size={18} /><p>{n}</p></div>
      ))}

      {res.kitsStatus === "none_in_budget" && res.closestKit ? (
        <>
          <div className="note warn" role="status">
            <Icon name="alert" size={18} />
            <p>Não encontramos um kit completo {budget != null ? `até ${money(budget)}` : ""}. Este é o mais próximo.</p>
          </div>
          <div className="kit-strip">
            <KitCard kit={res.closestKit} onOpen={() => onOpen(res.closestKit!)} overBudgetBy={budget != null ? res.closestKit.totalCents - budget : undefined} />
          </div>
          <button className="btn outline blue block" onClick={() => onPatch({ budgetCents: Math.ceil(res.closestKit!.totalCents / 500) * 500 })}>
            Subir orçamento para {money(Math.ceil(res.closestKit.totalCents / 500) * 500)}
          </button>
        </>
      ) : null}

      {res.kits.length ? (
        <div className="kit-strip" tabIndex={0} aria-label="Deslize para ver os kits">
          {res.kits.map((k) => (
            <KitCard key={k.id} kit={k} onOpen={() => onOpen(k)} />
          ))}
        </div>
      ) : null}

      {res.clarification ? (
        <div className="panel" aria-label="Pergunta rápida">
          <b>{res.clarification.question}</b>
          <div className="chips">
            {res.clarification.options.map((o) => (
              <button key={o.value} className="chip" onClick={() => onPatch({ skinType: o.value })}>{o.label}</button>
            ))}
          </div>
          <span className="footnote" style={{ textAlign: "left" }}>Opcional. Os kits acima já valem para qualquer tipo de pele.</span>
        </div>
      ) : null}

      {budgetOpen ? (
        <BottomSheet title="Quanto quer gastar?" onClose={() => setBudgetOpen(false)}>
          <BudgetPanel value={budget} onChange={(c) => { setBudgetOpen(false); onPatch({ budgetCents: c }); }} />
        </BottomSheet>
      ) : null}

      {sheet ? (
        <BottomSheet title="Como é a sua pele?" onClose={() => setSheet(false)}>
          {SKINS.map((s) => (
            <button key={s.value} className="opt" onClick={() => { setSheet(false); onPatch({ skinType: s.value }); }}>
              <div className="info"><b>{s.label}</b></div>
              {intent.skinType === s.value ? <Icon name="check" size={18} /> : null}
            </button>
          ))}
        </BottomSheet>
      ) : null}
    </section>
  );
}

type Filters = { inStock: boolean; noRx: boolean; skin: SkinType | null; claims: string[] };
const NO_FILTERS: Filters = { inStock: false, noRx: false, skin: null, claims: [] };

export function ProductList({ products, emptyText, title }: { products: Product[]; emptyText?: string; title?: string }) {
  const [sort, setSort] = useState<SortKey>("relevancia");
  const [filters, setFilters] = useState<Filters>(NO_FILTERS);
  const [open, setOpen] = useState(false);
  const claimsAvailable = useMemo(() => [...new Set(products.flatMap((p) => p.claims))].sort(), [products]);
  const hasDermo = products.some((p) => p.domain === "dermo");
  const hasRx = products.some((p) => p.rx) && products.some((p) => p.domain === "medicamento" && !p.rx);
  const shown = useMemo(() => {
    const f = products.filter(
      (p) =>
        (!filters.inStock || p.stockQty > 0) &&
        (!filters.noRx || !p.rx) &&
        (!filters.skin || p.skinTypes.includes("todas") || p.skinTypes.includes(filters.skin)) &&
        filters.claims.every((c) => p.claims.includes(c)),
    );
    return sortList(f, sort);
  }, [products, filters, sort]);
  const active = Number(filters.inStock) + Number(filters.noRx) + Number(!!filters.skin) + filters.claims.length;

  if (!products.length) return emptyText ? <p className="count">{emptyText}</p> : null;
  return (
    <section aria-label="Produtos">
      <div className="sortband">
        <label className="sr-only" htmlFor="sort">Ordenar</label>
        <select id="sort" value={sort} onChange={(e) => setSort(e.target.value as SortKey)}>
          <option value="relevancia">Relevância</option>
          <option value="mais_vendidos">Mais vendidos</option>
          <option value="menor_preco">Menor preço</option>
          <option value="maior_preco">Maior preço</option>
        </select>
        <button className="filterbtn" onClick={() => setOpen(true)}>
          <Icon name="filter" /> Filtros{active ? ` (${active})` : ""}
        </button>
      </div>
      {title ? <h2 className="sec-title" style={{ fontSize: 18, margin: "12px 16px 0" }}>{title}</h2> : null}
      <p className="count">{shown.length} {shown.length === 1 ? "produto encontrado" : "produtos encontrados"}</p>
      <div className="grid2 listpad">
        {shown.map((p) => (
          <ProductCard key={p.id} product={p} />
        ))}
      </div>
      {open ? (
        <BottomSheet title="Filtros" onClose={() => setOpen(false)}>
          <label className="switch">
            <input type="checkbox" checked={filters.inStock} onChange={(e) => setFilters({ ...filters, inStock: e.target.checked })} />
            Só produtos disponíveis
          </label>
          {hasRx ? (
            <label className="switch">
              <input type="checkbox" checked={filters.noRx} onChange={(e) => setFilters({ ...filters, noRx: e.target.checked })} />
              Só sem receita
            </label>
          ) : null}
          {hasDermo ? (
            <>
              <span className="section-title">Tipo de pele</span>
              <div className="chips">
                {SKINS.map((s) => (
                  <button key={s.value} className={`chip ${filters.skin === s.value ? "on" : ""}`}
                    onClick={() => setFilters({ ...filters, skin: filters.skin === s.value ? null : s.value })}>{s.label}</button>
                ))}
              </div>
            </>
          ) : null}
          {claimsAvailable.length ? (
            <>
              <span className="section-title">Características</span>
              <div className="chips">
                {claimsAvailable.map((c) => (
                  <button key={c} className={`chip ${filters.claims.includes(c) ? "on" : ""}`}
                    onClick={() => setFilters({ ...filters, claims: filters.claims.includes(c) ? filters.claims.filter((x) => x !== c) : [...filters.claims, c] })}>{c}</button>
                ))}
              </div>
            </>
          ) : null}
          <div className="row" style={{ marginTop: 8 }}>
            <button className="btn outline grow" onClick={() => setFilters(NO_FILTERS)}>Limpar</button>
            <button className="btn primary grow" onClick={() => setOpen(false)}>Ver {shown.length} produtos</button>
          </div>
        </BottomSheet>
      ) : null}
    </section>
  );
}
