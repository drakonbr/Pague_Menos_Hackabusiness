"""Camada de segurança (doc 07). Regras determinísticas que rodam ANTES de qualquer outra coisa.

Regra de ouro: o motor nunca recomenda medicamento, dose, diagnóstico nem trata sintoma. A única exceção é a
REPOSIÇÃO do que a pessoa já usa (abrir a tela dela, que fica no aparelho): nenhum nome de remédio ou condição
volta na resposta, e qualquer pedido de recomendação, dose ou sintoma continua bloqueado mesmo nesse fluxo.
"""
from __future__ import annotations

import re

from .text import norm

REFERRAL = "Falar com um farmacêutico"

# pedidos de RECOMENDAÇÃO: bloqueados sempre, inclusive dentro do fluxo de reposição
RECOMMEND = re.compile(
    r"\b(o que (eu )?(posso |devo )?tomar|qual (remedio|medicamento)\b|indica\w* (um |algum )?(remedio|medicamento)|"
    r"recomend\w* (um |algum )?(remedio|medicamento)|dose|doses|posologia|quantos comprimidos|parar de tomar|"
    r"sem receita|trocar (a )?dose|aumentar (a )?dose|misturar (com )?(remedio|medicamento)|tomar junto)\b|"
    r"\b(posso|pode|devo|podem) (tomar|usar|misturar|combinar)\b.*\b(remedio|remedios|medicamento|medicamentos)\b|"
    r"\binterage\w* com (o |meu |meus )?(remedio|medicamento)")

BLOCK_RULES: list[tuple[str, re.Pattern, str]] = [
    ("medicamento", re.compile(
        r"\b(remedio|remedios|medicamento|medicamentos|medicacao|medicacoes|antibiotico\w*|anti-?inflamatorio\w*|"
        r"corticoide\w*|isotretinoina|roacutan|analgesico\w*|dipirona|paracetamol|ibuprofeno|receita|posologia|"
        r"comprimido\w*|dose|doses|o que (eu )?(posso )?tomar)\b"), "medicamentos"),
    ("sintoma", re.compile(r"\b(dor|dores|febre|coceira|sangramento|sangrando|inchaco|tontura|nausea|enjoo|tosse|vomito|"
                           r"palpitacao|palpitacoes|falta de ar)\b"), "sintomas de saúde"),
    ("condicao_de_saude", re.compile(
        r"\b(dermatite|psoriase|rosacea|micose|infeccao|infeccionad\w*|ferida|herpes|eczema|candidiase|alergia|"
        r"pressao alta|hipertensao|colesterol|diabetes|tireoide|cancer|depressao|ansiedade)\b"), "uma condição de saúde"),
]

REFILL_WORDS = re.compile(r"\b(remedio|remedios|medicamento|medicamentos|medicacao|medicacoes|uso continuo)\b")


def assess(text: str, pregnancy: bool, primary_goal: str | None, refill_flow: bool = False) -> dict:
    """refill_flow = a frase é um pedido de reposição do que a pessoa já usa (decidido pelo NLU)."""
    q = norm(text)
    if refill_flow:
        # só passa se NÃO houver pedido de recomendação, dose, sintoma ou condição
        risky = RECOMMEND.search(q) or BLOCK_RULES[1][1].search(q)
        if not risky:
            return {"decision": "allow"}
    for category, rx, subject in BLOCK_RULES:
        if rx.search(q):
            alt = {"acne": "Quero cuidados cosméticos para acne",
                   "manchas": "Quero cuidados cosméticos para manchas",
                   "suplementos": "Quero um kit de suplementos"}.get(primary_goal or "")
            return {
                "decision": "blocked", "category": category,
                "message": f"Esse tipo de pedido envolve {subject}. Aqui eu só monto kits de cuidados, suplementos e higiene, "
                           "e ajudo a repor o que você já usa. Para medicamentos, sintomas e condições de saúde, "
                           "converse com um farmacêutico ou médico.",
                "referral": REFERRAL, **({"alternativeQuery": alt} if alt else {}),
            }
    if pregnancy:
        return {"decision": "caution", "category": "gestacao_e_ativos",
                "message": "Você mencionou gestação ou amamentação. Retiramos dos kits os produtos que pedem orientação "
                           "profissional nesse período. Converse com seu médico ou dermatologista antes de usar qualquer ativo.",
                "referral": REFERRAL}
    return {"decision": "allow"}
