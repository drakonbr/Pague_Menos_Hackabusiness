// Privacidade e dados: o que fica no aparelho, o que o assistente recebe e os consentimentos da persona.
import { TitleBar } from "../components/Bars";
import { Icon } from "../components/Icon";
import { PERSONA, type ConsentFlags } from "../persona";
import { useApp } from "../state/app";

const FLAGS: Array<{ key: keyof ConsentFlags; title: string; text: string }> = [
  { key: "refillReminders", title: "Lembretes de reposição", text: "Avisar quando um item de uso contínuo estiver para acabar. Usa só as quantidades guardadas neste aparelho." },
  { key: "personalizeWithPurchaseHistory", title: "Personalizar com meu histórico de compras", text: "Sugerir cosméticos, suplementos e higiene parecidos com o que você já compra. Itens de saúde ficam de fora." },
  { key: "useHealthDataForRecommendations", title: "Usar dados de saúde nas recomendações", text: "Desligado por padrão. O assistente nunca recebe a sua lista de medicamentos nem usa seus dados de saúde para sugerir produtos." },
  { key: "shareHealthDataWithPartners", title: "Compartilhar dados de saúde com parceiros", text: "Desligado por padrão. Neste protótipo nada é compartilhado." },
];

export function Privacy() {
  const { consent, dispatch, chat } = useApp();
  return (
    <div className="screen">
      <TitleBar title="Privacidade e dados" />
      <div className="scroll">
        <div className="pad">
          <div className="panel" style={{ gap: 8 }}>
            <div className="row"><Icon name="lock" size={22} /><b>O que acontece com os seus dados</b></div>
            <ul className="plain-list">
              <li><b>Fica só neste aparelho:</b> seus medicamentos de uso contínuo, quantidades, receita e histórico de compras de saúde.</li>
              <li><b>O assistente recebe:</b> a frase que você escreve, o contexto da conversa (ids de produto e preferências de cosmético, como “vegano”) e a loja escolhida.</li>
              <li><b>O assistente nunca recebe:</b> nome, endereço, lista de medicamentos nem histórico de saúde. Ele recebe só o que você digita na busca.</li>
              <li><b>Nada é gravado no servidor:</b> o motor não guarda a sua conversa e não registra a frase.</li>
            </ul>
          </div>

          <section aria-label="Consentimentos" className="menulist">
            {FLAGS.map((f) => (
              <label key={f.key} className="consent-row">
                <span className="grow"><b>{f.title}</b><small>{f.text}</small></span>
                <input type="checkbox" role="switch" checked={consent[f.key]} onChange={(e) => dispatch({ type: "setConsent", key: f.key, value: e.target.checked })} aria-label={f.title} />
              </label>
            ))}
          </section>

          <button className="btn outline blue block" disabled={chat.messages.length === 0} onClick={() => { dispatch({ type: "chatReset" }); dispatch({ type: "toast", text: "Conversa apagada deste aparelho" }); }}>
            Apagar a conversa deste aparelho
          </button>
          <p className="footnote">Persona fictícia ({PERSONA.name}). Dados sintéticos para demonstração; as regras reais de privacidade da rede seguem a LGPD e podem ser diferentes.</p>
        </div>
      </div>
    </div>
  );
}
