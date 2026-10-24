// #63: risco de vida e sinais de alerta recebem resposta fixa, sem lista de produtos. Espelho de graphrag/safety.py
// (urgency): as duas listas de frases têm teste com os mesmos exemplos.
import type { Safety } from "../contracts/types";

export const CRISIS_MESSAGE =
  "Sinto muito que você esteja passando por isso. Você não precisa enfrentar isso sozinho(a): ligue agora para o CVV, 188 (gratuito, 24 horas), ou fale pelo chat em cvv.org.br. Se estiver em perigo agora, ligue 192 (SAMU) ou vá ao pronto-atendimento mais próximo. Não vou sugerir produtos para isso.";
export const ALERT_MESSAGE =
  "Isso pode ser urgente. Ligue 192 (SAMU) ou vá agora ao pronto-atendimento mais próximo. Não vou sugerir produtos para isso.";

const CRISIS = new RegExp(
  "\\b(me matar|me mata(?! de)|qro morrer|quero morre|tirar (a )?minha (propria )?vida(?! (social|sexual|amorosa|financeira|profissional))|acabar com a minha vida|acabar com a minha propria vida|nao quero mais viver|nao aguento mais viver|nao vejo (mais )?sentido (na|em) (minha )?vida|quero morrer(?! de (rir|vergonha|fome|calor|sono|saudade|medo|raiva))|vontade de morrer|melhor (eu )?morrer|queria (sumir|morrer|estar morto|estar morta)|sumir de vez|pensando em acabar com tudo|nao quero acordar amanha|queria desaparecer|(sinto que )?(vou|to|estou) morrer(?! de)|cansei de (tudo|viver)|pensando em me (machucar|ferir|cortar)|quero (acabar com tudo|dormir pra sempre|dormir para sempre|desaparecer)|pensando em (morrer|suicidio|me matar)|suicid\\w*|(quero|vontade de|vou|tentei|tentando) me (cortar|machucar|ferir|jogar|enforcar|atirar|matar)|automutilac\\w*|(tomar|tomei) (todos|todas) (os|as) (remedios|comprimidos|pilulas|cartelas)(?! (que|do|da|de acordo))|tomei (um monte|varios|muitos|[0-9]+|dez) (de )?(remedios?|comprimidos?|pilulas?)|ingeri (varios|muitos) (remedios|comprimidos)|tomei (uma|a) cartela (inteira|toda)|tomei tudo de uma vez)\\b",
);
const ALERT = new RegExp(
  "\\b(dor (forte )?no peito(?! do pe)|aperto no peito|pressao no peito|falta d[ea]? ar(?! condicionado)|faltando ar|nao consigo respirar|nao (to|estou) conseguindo respirar|sem conseguir respirar|(estou|to|ficando|fiquei) sem ar\\b(?! (condicionado|fresco|puro|limpo|de ))|dificuldade (pra|para|de) respirar|sufocando|nao respira|labios roxos|ta roxo|ficou roxo|engasgou|engasgando|cobra (picou|mordeu)|picada de (cobra|escorpiao|aranha)|mordida de cobra|tomei o frasco inteiro|(bebi|engoli|engoliu|bebeu) (um pouco de |muita |a )?(agua sanitaria|detergente|soda caustica|cloro|veneno)|desmaiei|desmaiou|desmaiando|vou desmaiar|quase desmaiei|perdi a consciencia|inconsciente|(ele|ela|pai|mae|filho|filha|bebe|crianca|avo|marido|esposa|amigo|amiga) nao (acorda|responde|desperta)|convuls\\w+|(fezes|coco|diarreia|vomito|vomitando|vomitei|tosse|tossindo|urina|xixi|mijo|mijando|cagando|evacuando|cuspindo) (com )?sangue|sangue (nas|na|no|nos) (fezes|coco|urina|xixi|vomito|tosse|escarro)|sangramento (intenso|forte|que nao para)|hemorragia|(lingua|garganta) (esta |ta |ficou )*(inchada|inchando|inchou|fechando)|(rosto|labios) (esta |ta |ficou |todo |todos )*(inchando|inchou|fechando)|inchaco (na|no) (garganta|lingua)|rigidez no pescoco|pescoco (duro|rigido|travado) (e|com) febre|boca (esta |ficou )?torta|boca entortou|entortou a boca|fala (esta |ficou )?enrolada|perdi a visao|paralisia|dormente de um lado|fraqueza de um lado|nao consigo (mexer|levantar) (o|a) (braco|perna)|(estou|to|ta|esta|tendo|suspeita de|sintomas de|sinais de|acho que (estou|to) (tendo|com)) (um |uma |tendo )?(avc|infarto|derrame|ataque cardiaco|ataque do coracao)|dor (forte |intensa )(no|do|na) (braco|ombro|mandibula) esquerd[oa]|(dor|formigamento|dormencia) (no|do|na) (braco|ombro|mandibula) esquerd[oa] (irradiando|e (suor|falta|aperto|enjoo|nausea))|irradiando (pro|para o) (braco|ombro|mandibula)|suor frio|visao turva|fala (arrastada|embolada)|sangue vivo|sangue na calcinha|(gravida|gravidez) (e |com )?(sangrando|sangramento)|(pior|mais forte) dor de cabeca da (minha )?vida|(crianca|bebe|filho|filha|neto|neta) (engoliu|bebeu|tomou|comeu) (uma |um |o |a |muito )?(veneno|remedio|produto|pilha|agua sanitaria|soda|cloro)|tomei (veneno|agua sanitaria)|tomei (remedio|comprimido)s? demais|overdose|(febre (de|acima de) 4[0-9]|4[0-9] (graus )?de febre))\\b",
);

const norm = (s: string) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();

export function urgency(text: string): Safety | null {
  const t = norm(text);
  if (CRISIS.test(t)) return { decision: "urgent", category: "risco_de_vida", message: CRISIS_MESSAGE };
  if (ALERT.test(t)) return { decision: "urgent", category: "sinal_de_alerta", message: ALERT_MESSAGE };
  return null;
}
