"""Camada de segurança (doc 07, revisada no doc 16). Roda ANTES de qualquer outra coisa.

Desde 21/10 (doc 16) a busca de medicamento funciona como numa farmácia: "dor de cabeça" traz remédio para dor de
cabeça, com ou sem receita. Não há bloqueio por medicamento, sintoma ou condição, e nenhuma resposta manda procurar
médico ou farmacêutico. O que sobra aqui é a gestação: os kits tiram o que tem restrição nesse período e avisam.
"""
from __future__ import annotations


def assess(text: str, pregnancy: bool, primary_goal: str | None, refill_flow: bool = False) -> dict:
    if pregnancy:
        return {"decision": "caution", "category": "gestacao_e_ativos",
                "message": "Você mencionou gestação ou amamentação. Retiramos dos kits os produtos com restrição nesse período."}
    return {"decision": "allow"}
