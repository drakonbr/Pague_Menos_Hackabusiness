import { useEffect, useMemo } from "react";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { RxPrompt } from "./components/RxPrompt";
import { TabBar } from "./components/TabBar";
import { Toast } from "./components/Toast";
import { showsTabBar, NavProvider, ServicesProvider, useNav, useServices } from "./nav";
import { createCommerceService } from "./services/commerceService";
import { createSearchService } from "./services/searchService";
import { AppProvider, useApp } from "./state/app";
import { DEFAULT_STORE_ID } from "./location";
import { Chat } from "./screens/Chat";
import { Privacy } from "./screens/Privacy";
import { Refill } from "./screens/Refill";
import { Cart } from "./screens/Cart";
import { CategoriesList, CategoryView } from "./screens/Categories";
import { Prescriptions } from "./screens/Prescriptions";
import { Delivery } from "./screens/Delivery";
import { Favorites } from "./screens/Favorites";
import { Home } from "./screens/Home";
import { KitDetail } from "./screens/KitDetail";
import { Credits, More, Orders, Stores, Subscriptions, Wallet } from "./screens/More";
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
              <ErrorBoundary><Shell /></ErrorBoundary>
            </main>
          </div>
        </NavProvider>
      </AppProvider>
    </ServicesProvider>
  );
}

/** Cliente logada: começa com a loja onde costuma retirar (a mais próxima do endereço fictício). */
function useDefaultStore() {
  const { commerce } = useServices();
  const { store, dispatch } = useApp();
  useEffect(() => {
    if (store) return;
    let alive = true;
    commerce.storesFor([]).then((list) => {
      const s = list.find((x) => x.store.id === DEFAULT_STORE_ID)?.store;
      if (alive && s) {
        dispatch({ type: "setStore", store: s });
        dispatch({ type: "setMode", mode: "retirada" });
      }
    });
    return () => { alive = false; };
    // só na primeira montagem
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
}

function Shell() {
  useDefaultStore();
  const { view, tab, depth } = useNav();
  const key = `${tab}:${view.name}:${"id" in view ? view.id : ""}`;
  return (
    <>
      <div className="screen" key={key}>
        <Screen />
      </div>
      {showsTabBar(view, tab, depth) ? <TabBar /> : null}
      <Toast />
      <RxPrompt />
    </>
  );
}

function Screen() {
  const { view } = useNav();
  switch (view.name) {
    case "home": return <Home />;
    case "searchFocus": return <SearchFocus initial={view.initial} />;
    case "results": return <Results req={view.req} />;
    case "chat": return <Chat initial={view.initial} />;
    case "refill": return <Refill />;
    case "privacy": return <Privacy />;
    case "categorias": return <CategoriesList />;
    case "prescriptions": return <Prescriptions />;
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
    case "stores": return <Stores />;
  }
}
