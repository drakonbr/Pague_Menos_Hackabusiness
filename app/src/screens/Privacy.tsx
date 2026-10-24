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
  { key: "useExternalLanguageService", title: "Entender frases difíceis com um serviço externo",
    text: "Ligado neste protótipo. Se o assistente não entende o que você escreveu, ou vê uma palavra que não conhece, a frase vai a um serviço de linguagem no exterior (DeepSeek), só para ser traduzida em termos do catálogo. Tentamos tirar nome, telefone, e-mail, CPF, endereço e idade antes, mas isso não é perfeito: um nome solto e tudo o que você escrever sobre a sua saúde também vão. Desligue para nenhuma frase sair; o assistente passa a entender menos." },
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
              <li><b>O assistente recebe:</b> a frase que você escreve, o contexto da conversa (ids de produto e preferências, como “vegano” ou “sem cheiro”) e a loja escolhida.</li>
              <li><b>O assistente nunca recebe sozinho:</b> a sua lista de medicamentos nem o seu histórico de saúde. Ele recebe só o que você digita na busca; se você escrever um nome ou algo sobre a sua saúde, isso também vai. Evite.</li>
              <li><b>Serviço externo, só quando o assistente não entende ou vê palavra que não conhece:</b> a frase vai a um serviço de linguagem no exterior (DeepSeek), depois de tentarmos tirar dados pessoais (sem garantia). Esse serviço pode manter registros conforme a política dele. Você pode desligar abaixo.</li>
              <li><b>No servidor do assistente:</b> o motor não guarda a sua conversa.</li>
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
