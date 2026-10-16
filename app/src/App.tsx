import { useMemo } from "react";
import { TabBar } from "./components/TabBar";
import { Toast } from "./components/Toast";
import { FULLSCREEN, NavProvider, ServicesProvider, useNav } from "./nav";
import { createCommerceService } from "./services/commerceService";
import { createSearchService } from "./services/searchService";
import { AppProvider } from "./state/app";
import { Cart } from "./screens/Cart";
import { CategoriesRoot, CategoryView } from "./screens/Categories";
import { Delivery } from "./screens/Delivery";
import { Favorites } from "./screens/Favorites";
import { Home } from "./screens/Home";
import { KitDetail } from "./screens/KitDetail";
import { Credits, More, Orders, Pharmacist, Stores, Subscriptions, Wallet } from "./screens/More";
import { Offers } from "./screens/Offers";
import { Confirmation, Payment } from "./screens/Payment";
import { ProductPage } from "./screens/ProductPage";
import { Results } from "./screens/Results";
import { SearchFocus } from "./screens/SearchFocus";

export function App() {
  const services = useMemo(() => ({ search: createSearchService(), commerce: createCommerceService() }), []);
  return (
    <ServicesProvider value={services}>
      <AppProvider>
        <NavProvider>
          <div className="stage">
            <main className="phone" aria-label="Aplicativo da farmácia (protótipo)">
              <Shell />
            </main>
          </div>
        </NavProvider>
      </AppProvider>
    </ServicesProvider>
  );
}

function Shell() {
  const { view, tab } = useNav();
  const key = `${tab}:${view.name}:${"id" in view ? view.id : ""}`;
  return (
    <>
      <div className="screen" key={key}>
        <Screen />
      </div>
      {FULLSCREEN.has(view.name) ? null : <TabBar />}
      <Toast />
    </>
  );
}

function Screen() {
  const { view } = useNav();
  switch (view.name) {
    case "home": return <Home />;
    case "searchFocus": return <SearchFocus initial={view.initial} />;
    case "results": return <Results req={view.req} />;
    case "categorias": return <CategoriesRoot />;
    case "category": return <CategoryView id={view.id} />;
    case "product": return <ProductPage id={view.id} />;
    case "kit": return <KitDetail initialKit={view.kit} intent={view.intent} />;
    case "cart": return <Cart />;
    case "delivery": return <Delivery />;
    case "payment": return <Payment />;
    case "done": return <Confirmation orderId={view.orderId} />;
    case "ofertas": return <Offers />;
    case "favoritos": return <Favorites />;
    case "mais": return <More />;
    case "orders": return <Orders />;
    case "subscriptions": return <Subscriptions />;
    case "wallet": return <Wallet />;
    case "credits": return <Credits />;
    case "pharmacist": return <Pharmacist />;
    case "stores": return <Stores />;
  }
}
