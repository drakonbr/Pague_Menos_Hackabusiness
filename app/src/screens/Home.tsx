import { PersonaAvatar } from "../components/Avatar";
import { BasketButton } from "../components/Bars";
import { Icon, LogoMark } from "../components/Icon";
import { ProductCard } from "../components/ProductCard";
import { SEARCH_HINT } from "../components/SearchHint";
import type { Product } from "../contracts/types";
import { BRAND } from "../brand";
import { useNav, useServices } from "../nav";
import { SIMULATED_LOCATION } from "../location";
import { PERSONA, daysLeft, needsRefill, REFILL_RULES } from "../persona";
import { useApp } from "../state/app";
import { useAsync } from "../useAsync";
import { TOP_CATEGORIES } from "../topCategories";

function greeting(): string {
  const h = new Date().getHours();
  return h < 12 ? "Bom dia" : h < 18 ? "Boa tarde" : "Boa noite";
}

export function Home() {
  const { push, goTab } = useNav();
  const { commerce } = useServices();
  const { store, storeId, consent } = useApp();
  const due = PERSONA.continuousMedications.filter((m) => needsRefill(m)).length;
  const soonest = Math.min(...PERSONA.continuousMedications.map(daysLeft));
  const home = useAsync(async () => {
    const h = await commerce.home();
    const rows = await Promise.all(
      h.showcases.filter((s) => s.type === "products").map(async (s) => ({ s, products: await commerce.products(s.productIds ?? [], "relevancia") })),
    );
    return { ...h, rows };
  }, [commerce]);
  const banner = home.data?.banners ?? [];

  return (
    <div className="screen">
      <div className="scroll">
        <div className="home-head">
          <div className="row">
            <LogoMark size={40} />
            <p className="hello">
              {greeting()}, <b>{PERSONA.firstName}!</b>
            </p>
            <button className="icon-btn avatar-btn" onClick={() => goTab("mais")} aria-label="Meu perfil"><PersonaAvatar size={38} ring /></button>
            <BasketButton />
          </div>
        </div>
        <div className="home-search">
          <button className="searchpill" onClick={() => push({ name: "searchFocus" })}>
            <Icon name="search" />
            <span className="ph">{SEARCH_HINT}</span>
            <span className="soft"><Icon name="camera" /></span>
            <span className="soft"><Icon name="mic" /></span>
          </button>
        </div>
        <button className="loc" onClick={() => push({ name: "stores" })}>
          <Icon name="pin" size={20} />
          <span>{store ? `Retirar na ${store.name} · ${store.neighborhood}` : SIMULATED_LOCATION.label}</span>
          <Icon name="chevronDown" size={20} />
        </button>

        <div className="pad">
          {/* #29: Meus medicamentos sempre no topo; vira "Hora de repor" quando algo está acabando */}
          {consent.refillReminders && due > 0 ? (
            <button className="refill-card" onClick={() => push({ name: "refill" })}>
              <Icon name="bell" size={26} />
              <span className="grow"><b>Hora de repor</b><small>{due} {due === 1 ? "item de uso contínuo acaba" : "itens de uso contínuo acabam"} em até {REFILL_RULES.alertDaysBefore} dias</small></span>
              <span className="cta">Repor agora</span>
            </button>
          ) : (
            <button className="refill-card calm" onClick={() => push({ name: "refill" })}>
              <Icon name="pill" size={26} />
              <span className="grow"><b>Meus medicamentos</b><small>{PERSONA.continuousMedications.length} de uso contínuo · {soonest === 0 ? "um deles acaba hoje" : `próximo acaba em ${soonest} ${soonest === 1 ? "dia" : "dias"}`}</small></span>
              <span className="cta">Ver e repor</span>
            </button>
          )}
          <section aria-labelledby="h-cat">
            <div className="sec-head">
              <h2 id="h-cat">Categorias</h2>
              <button className="link plain" onClick={() => push({ name: "categorias" })}>Exibir tudo</button>
            </div>
            <div className="cat-tiles" style={{ marginTop: 12 }}>
              {/* na Home as ativas vêm primeiro (o topo da tela é o lugar mais nobre); a tela Categorias segue a ordem do menu */}
              {[...TOP_CATEGORIES].sort((a, b) => Number(!a.id) - Number(!b.id)).map((c) => (
                <button key={c.label} className="cat-tile" disabled={!c.id} onClick={() => c.id && push({ name: "category", id: c.id })}
                  aria-describedby={c.id ? undefined : "cat-off"}>
                  <span className="ico"><Icon name={c.icon} size={30} /></span>
                  {c.label}
                </button>
              ))}
            </div>
            <p id="cat-off" className="cat-off">Categorias em cinza ficam fora deste protótipo.</p>
          </section>
          <div className="shortcuts">
            <button className="shortcut" onClick={() => push({ name: "searchFocus" })}>
              <Icon name="sparkle" size={30} />
              <span className="pill-new">Novo</span>
              <b>Monte um kit pelo que você precisa</b>
            </button>
          </div>

          <div className="banners" aria-label="Destaques">
            <button className="banner" onClick={() => push({ name: "searchFocus" })}>
              {banner[0] ? <img src={banner[0].src} alt="" /> : null}
              <span className="shade" />
              <span className="txt">
                <b>Kits inteligentes</b>
                <span>Diga o que precisa: a rotina vem completa, sem item repetido e no seu orçamento.</span>
                <span className="cta">Montar meu kit</span>
              </span>
            </button>
            <button className="banner" onClick={() => push({ name: "stores" })}>
              {banner[1] ? <img src={banner[1].src} alt="" /> : null}
              <span className="shade" />
              <span className="txt">
                <b>Kit completo na sua loja</b>
                <span>Escolha a loja e os kits usam só o que ela tem em estoque. Retire em até 60 minutos.</span>
                <span className="cta">Escolher loja</span>
              </span>
            </button>
            <button className="banner" onClick={() => push({ name: "category", id: "solar-facial" })}>
              {banner[2] ? <img src={banner[2].src} alt="" /> : null}
              <span className="shade" />
              <span className="txt">
                <b>Protetor solar facial</b>
                <span>Toque seco, com cor ou mineral.</span>
                <span className="cta">Ver produtos</span>
              </span>
            </button>
          </div>

          <section aria-labelledby="h-kits">
            <div className="sec-head">
              <h2 id="h-kits">Kits inteligentes para você</h2>
            </div>
            <div className="presets" style={{ marginTop: 12 }}>
              {(home.data?.kitPresets ?? []).map((k) => (
                <button key={k.id} className="preset" onClick={() => push({ name: "results", req: { query: k.query, storeId } })}>
                  <Icon name="sparkle" size={22} />
                  <b>{k.label}</b>
                  <small>3 faixas de preço</small>
                </button>
              ))}
            </div>
          </section>

          {home.loading && !home.data ? <div className="skeleton" style={{ height: 260 }} /> : null}
          {(home.data?.rows ?? []).map(({ s, products }) => (
            <Shelf key={s.id} title={s.id === "ofertas" ? "Aproveite as Melhores Ofertas para Você!" : s.title} products={products}
              tag={s.id === "ofertas" ? "Super oferta" : undefined} />
          ))}
          <p className="footnote">{BRAND.protoNote}</p>
        </div>
      </div>
    </div>
  );
}

function Shelf({ title, products, tag }: { title: string; products: Product[]; tag?: string }) {
  if (!products.length) return null;
  return (
    <section aria-label={title}>
      <div className="sec-head">
        <h2>{title}</h2>
      </div>
      <div className="hscroll" style={{ marginTop: 12 }}>
        {products.map((p) => (
          <ProductCard key={p.id} product={p} tag={tag} />
        ))}
      </div>
    </section>
  );
}
