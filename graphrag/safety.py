"""Camada de segurança (doc 07, revisada no doc 16). Roda ANTES de qualquer outra coisa.

Desde 21/10 (doc 16) a busca de medicamento funciona como numa farmácia: "dor de cabeça" traz remédio para dor de
cabeça, com ou sem receita. Não há bloqueio por medicamento, sintoma ou condição, e nenhuma resposta manda procurar
médico ou farmacêutico. O que sobra aqui é a gestação: os kits tiram o que tem restrição nesse período e avisam.

Exceção estreita (#63, 24/10): risco de vida e sinais de alerta (dor no peito, falta de ar, sangue nas fezes, língua inchada...)
recebem uma resposta fixa, sem lista de produtos e sem nunca ir à DeepSeek. A lista de frases está em `urgency` e é espelhada
no app (app/src/services/urgency.ts); os dois lados têm teste com as mesmas frases.
"""
from __future__ import annotations

import re

from .text import norm

CRISIS_MESSAGE = ("Sinto muito que você esteja passando por isso. Você não precisa enfrentar isso sozinho(a): ligue agora para o CVV, "
                  "188 (gratuito, 24 horas), ou fale pelo chat em cvv.org.br. Se estiver em perigo agora, ligue 192 (SAMU) ou vá ao "
                  "pronto-atendimento mais próximo. Não vou sugerir produtos para isso.")
ALERT_MESSAGE = ("Isso pode ser urgente. Ligue 192 (SAMU) ou vá agora ao pronto-atendimento mais próximo. "
                 "Não vou sugerir produtos para isso.")

_CRISIS = re.compile(
    r"\b(me matar|me mata(?! de)|qro morrer|quero morre|tirar (a )?minha (propria )?vida(?! (social|sexual|amorosa|financeira|profissional))|acabar com a minha vida|acabar com a minha propria vida|nao quero mais viver|nao aguento mais viver|nao vejo (mais )?sentido (na|em) (minha )?vida|quero morrer(?! de (rir|vergonha|fome|calor|sono|saudade|medo|raiva))|vontade de morrer|melhor (eu )?morrer|queria (sumir|morrer|estar morto|estar morta)|sumir de vez|pensando em acabar com tudo|nao quero acordar amanha|queria desaparecer|(sinto que )?(vou|to|estou) morrer(?! de)|cansei de (tudo|viver)|pensando em me (machucar|ferir|cortar)|quero (acabar com tudo|dormir pra sempre|dormir para sempre|desaparecer)|pensando em (morrer|suicidio|me matar)|suicid\w*|(quero|vontade de|vou|tentei|tentando) me (cortar|machucar|ferir|jogar|enforcar|atirar|matar)|automutilac\w*|(tomar|tomei) (todos|todas) (os|as) (remedios|comprimidos|pilulas|cartelas)(?! (que|do|da|de acordo))|tomei (um monte|varios|muitos|[0-9]+|dez) (de )?(remedios?|comprimidos?|pilulas?)|ingeri (varios|muitos) (remedios|comprimidos)|tomei (uma|a) cartela (inteira|toda)|tomei tudo de uma vez)\b")
_ALERT = re.compile(
    r"\b(dor (forte )?no peito(?! do pe)|aperto no peito|pressao no peito|falta d[ea]? ar(?! condicionado)|faltando ar|nao consigo respirar|nao (to|estou) conseguindo respirar|sem conseguir respirar|(estou|to|ficando|fiquei) sem ar\b(?! (condicionado|fresco|puro|limpo|de ))|dificuldade (pra|para|de) respirar|sufocando|nao respira|labios roxos|ta roxo|ficou roxo|engasgou|engasgando|cobra (picou|mordeu)|picada de (cobra|escorpiao|aranha)|mordida de cobra|tomei o frasco inteiro|(bebi|engoli|engoliu|bebeu) (um pouco de |muita |a )?(agua sanitaria|detergente|soda caustica|cloro|veneno)|desmaiei|desmaiou|desmaiando|vou desmaiar|quase desmaiei|perdi a consciencia|inconsciente|(ele|ela|pai|mae|filho|filha|bebe|crianca|avo|marido|esposa|amigo|amiga) nao (acorda|responde|desperta)|convuls\w+|(fezes|coco|diarreia|vomito|vomitando|vomitei|tosse|tossindo|urina|xixi|mijo|mijando|cagando|evacuando|cuspindo) (com )?sangue|sangue (nas|na|no|nos) (fezes|coco|urina|xixi|vomito|tosse|escarro)|sangramento (intenso|forte|que nao para)|hemorragia|(lingua|garganta) (esta |ta |ficou )*(inchada|inchando|inchou|fechando)|(rosto|labios) (esta |ta |ficou |todo |todos )*(inchando|inchou|fechando)|inchaco (na|no) (garganta|lingua)|rigidez no pescoco|pescoco (duro|rigido|travado) (e|com) febre|boca (esta |ficou )?torta|boca entortou|entortou a boca|fala (esta |ficou )?enrolada|perdi a visao|paralisia|dormente de um lado|fraqueza de um lado|nao consigo (mexer|levantar) (o|a) (braco|perna)|(estou|to|ta|esta|tendo|suspeita de|sintomas de|sinais de|acho que (estou|to) (tendo|com)) (um |uma |tendo )?(avc|infarto|derrame|ataque cardiaco|ataque do coracao)|dor (forte |intensa )(no|do|na) (braco|ombro|mandibula) esquerd[oa]|(dor|formigamento|dormencia) (no|do|na) (braco|ombro|mandibula) esquerd[oa] (irradiando|e (suor|falta|aperto|enjoo|nausea))|irradiando (pro|para o) (braco|ombro|mandibula)|suor frio|visao turva|fala (arrastada|embolada)|sangue vivo|sangue na calcinha|(gravida|gravidez) (e |com )?(sangrando|sangramento)|(pior|mais forte) dor de cabeca da (minha )?vida|(crianca|bebe|filho|filha|neto|neta) (engoliu|bebeu|tomou|comeu) (uma |um |o |a |muito )?(veneno|remedio|produto|pilha|agua sanitaria|soda|cloro)|tomei (veneno|agua sanitaria)|tomei (remedio|comprimido)s? demais|overdose|(febre (de|acima de) 4[0-9]|4[0-9] (graus )?de febre))\b")


def urgency(text: str) -> dict | None:
    """Risco de vida ou sinal de alerta na frase: resposta fixa. None quando não há."""
    t = norm(text)
    if _CRISIS.search(t):
        return {"decision": "urgent", "category": "risco_de_vida", "message": CRISIS_MESSAGE}
    if _ALERT.search(t):
        return {"decision": "urgent", "category": "sinal_de_alerta", "message": ALERT_MESSAGE}
    return None


def assess(text: str, pregnancy: bool, primary_goal: str | None, refill_flow: bool = False) -> dict:
    if pregnancy:
        return {"decision": "caution", "category": "gestacao_e_ativos",
                "message": "Você mencionou gestação ou amamentação. Retiramos dos kits os produtos com restrição nesse período."}
    return {"decision": "allow"}
