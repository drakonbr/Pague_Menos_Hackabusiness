import { TitleBar } from "../components/Bars";
import { Icon } from "../components/Icon";
import { useServices } from "../nav";
import { useAsync } from "../useAsync";
import { ProductList } from "./Results";

export function Offers() {
  const { commerce } = useServices();
  const data = useAsync(async () => {
    const h = await commerce.home();
    const s = h.showcases.find((x) => x.id === "ofertas");
    return commerce.products(s?.productIds ?? [], "relevancia");
  }, [commerce]);
  return (
    <div className="screen">
      <TitleBar title="Ofertas" back={false} />
      <div className="scroll">
        <div className="pad" style={{ paddingBottom: 0 }}>
          <div className="offer-banner">
            <span className="ico"><Icon name="tag" size={42} /></span>
            <span className="txt">
              <b>Descontos ativados</b>
              <span>As ofertas abaixo já valem no preço. Kits mostram quanto você economiza.</span>
            </span>
          </div>
        </div>
        {data.data ? <ProductList products={data.data} emptyText="Nenhuma oferta agora." /> : <div className="pad"><div className="skeleton" style={{ height: 300 }} /></div>}
      </div>
    </div>
  );
}
