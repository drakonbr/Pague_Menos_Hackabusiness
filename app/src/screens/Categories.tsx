import { BlueSearchBar, TitleBar } from "../components/Bars";
import { Icon } from "../components/Icon";
import { TOP_CATEGORIES } from "../topCategories";
import { useNav, useServices } from "../nav";
import { useAsync } from "../useAsync";
import { ProductList } from "./Results";

export function CategoriesList() {
  const { push } = useNav();
  return (
    <div className="screen">
      <TitleBar title="Categorias" />
      <div className="scroll">
        <div className="pad">
          <div className="menulist">
            {TOP_CATEGORIES.map((c) => (
              <button key={c.label} className="menurow" disabled={!c.id} onClick={() => c.id && push({ name: "category", id: c.id })}>
                <span className="ico"><Icon name={c.icon} size={30} /></span>
                <span>{c.label}</span>
                {c.id ? <Icon name="chevron" size={20} /> : <small>fora do protótipo</small>}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export function CategoryView({ id }: { id: string }) {
  const { commerce } = useServices();
  const { push } = useNav();
  const data = useAsync(async () => {
    const cats = await commerce.categories();
    const node = cats.find((c) => c.id === id) ?? null;
    const products = node ? await commerce.products(node.productIds, "relevancia") : [];
    return { cats, node, products, children: cats.filter((c) => c.parent === id), parent: cats.find((c) => c.id === node?.parent) ?? null };
  }, [commerce, id]);

  const d = data.data;
  return (
    <div className="screen">
      <BlueSearchBar back />
      <div className="scroll">
        <div className="pad" style={{ paddingBottom: 4 }}>
          {d?.parent ? <span className="footnote" style={{ textAlign: "left" }}>{d.parent.name}</span> : null}
          <h1 style={{ fontSize: 22, fontWeight: 700 }}>{d?.node?.name ?? "Categoria"}</h1>
          {d && d.children.length ? (
            <div className="chips">
              {d.children.map((c) => (
                <button key={c.id} className="chip" onClick={() => push({ name: "category", id: c.id })}>
                  {c.name} <small style={{ color: "var(--muted)" }}>{c.productIds.length}</small>
                </button>
              ))}
            </div>
          ) : null}
          {id === "saude" || d?.parent?.id === "saude" ? (
            <button className="note" style={{ textAlign: "left", width: "100%" }} onClick={() => push({ name: "searchFocus" })}>
              <Icon name="sparkle" size={20} />
              <span><b>Kits inteligentes:</b> diga o que está sentindo, como “dor de cabeça” ou “gripe”, e veja os kits prontos.</span>
            </button>
          ) : id === "dermo" || d?.parent?.id === "tipo" || id === "tipo" ? (
            <button className="note" style={{ textAlign: "left", width: "100%" }} onClick={() => push({ name: "searchFocus" })}>
              <Icon name="sparkle" size={20} />
              <span><b>Kits inteligentes:</b> descreva a sua pele e o que quer resolver. Montamos a rotina completa.</span>
            </button>
          ) : null}
        </div>
        {data.loading && !d ? <div className="pad"><div className="skeleton" style={{ height: 300 }} /></div> : null}
        {d ? <ProductList products={d.products} emptyText="Nenhum produto nesta categoria." /> : null}
      </div>
    </div>
  );
}
