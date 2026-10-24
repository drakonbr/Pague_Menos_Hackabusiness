"""Persona sintética "Renata Almeida" (docs/14-persona-renata.md) -> catalog/data/persona.json.

A persona foi criada pelo grupo (PDF "Persona: Renata Almeida"). Aqui ela vira dados de uso do app:
perfil, endereço, consentimentos de privacidade, medicamentos de uso contínuo (lista dela, no aparelho)
e histórico de compras. Tudo fictício. Nada vem de pessoa real.

PRIVACIDADE POR DESENHO (premissa do projeto, não do PDF): `continuousMedications` e o histórico de
pedidos de saúde NUNCA vão para o motor de busca/GraphRAG. O app os guarda no aparelho e só envia ao
motor identificadores de produto quando ela pede a troca por similar.
"""
from __future__ import annotations

import json
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def find(products, name_part):
    hits = [p for p in products if name_part in p["name"]]
    assert len(hits) == 1, (name_part, [h["name"] for h in hits])
    return hits[0]["id"]


def main():
    products = load("products.json")
    pid = lambda part: find(products, part)

    persona = {
        "id": "renata",
        "note": "Persona fictícia criada pelo grupo (Renata Almeida). Dados sintéticos para demonstração.",
        "name": "Renata Almeida",
        "firstName": "Renata",
        "age": 49,
        "occupation": "Coordenadora de Logística (híbrido)",
        "quote": "Quero cuidar da minha saúde sem que isso consuma o meu tempo.",
        "address": {
            "label": "Principal",
            "street": "Rua das Hortênsias, 410, apto 802",
            "neighborhood": "Madalena",
            "city": "Recife",
            "uf": "PE",
            "cep": "50610-000",
            "lat": -8.0589,
            "lng": -34.9066,
            "note": "Endereço e CEP fictícios.",
        },
        "interests": ["anti_idade", "suplementos", "higiene_premium"],
        "preferences": {
            "deliveryPriority": ["retirada", "expressa", "agendada"],
            "priceView": "total_com_frete",       # "preço total justo": item + frete
            "wantsSimilarOptions": True,
            "fewTaps": True,
        },
        "privacy": {
            "consent": {
                "refillReminders": True,                    # avisar quando o medicamento está acabando
                "personalizeWithPurchaseHistory": True,     # recomendações com base em compras NÃO ligadas a saúde
                "useHealthDataForRecommendations": False,   # nunca usar saúde para recomendar
                "shareHealthDataWithPartners": False,
                "useExternalLanguageService": True,         # #42: frase que o motor não entende pode ir a um serviço de linguagem externo (LGPD: informado e desligável)
            },
            "healthDataStays": "no_aparelho",
        },
        # Lista dela, mantida só no aparelho. `unitsLeft` = comprimidos restantes no dia do login simulado.
        "continuousMedications": [
            {"productId": pid("Tensivalol potássico 50 mg (genérico) — 30"), "unitsPerDay": 1, "unitsLeft": 5,
             "packUnits": 30, "label": "Pressão (uso contínuo)"},
            {"productId": pid("Lipostanol cálcico 20 mg (genérico) — 30"), "unitsPerDay": 1, "unitsLeft": 2,
             "packUnits": 30, "label": "Colesterol (uso contínuo)"},
        ],
        "orderHistory": [
            {"id": "o-0814", "date": "2026-08-14", "deliveryId": "expressa", "health": False,
             "items": [{"productId": pid("Ômega 3 1000 mg"), "qty": 1},
                       {"productId": pid("Colágeno Hidrolisado em Pó Neutro"), "qty": 1}]},
            {"id": "o-0902", "date": "2026-09-02", "deliveryId": "retirada", "health": False,
             "items": [{"productId": pid("Sérum Vitamina C + Peptídeos"), "qty": 1},
                       {"productId": pid("Protetor Solar Facial FPS 60 Antissinais"), "qty": 1}]},
            {"id": "o-0925", "date": "2026-09-25", "deliveryId": "retirada", "health": True,
             "items": [{"productId": pid("Tensivalol potássico 50 mg (genérico) — 30"), "qty": 1},
                       {"productId": pid("Lipostanol cálcico 20 mg (genérico) — 30"), "qty": 1}]},
        ],
        "assistantProfile": {
            "style": "direto, poucos toques, sem expor saúde",
            "neverMention": ["medicamentos", "condições de saúde"],
        },
    }
    (DATA / "persona.json").write_text(json.dumps(persona, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"OK: persona {persona['name']} ({len(persona['continuousMedications'])} medicamentos de uso contínuo, "
          f"{len(persona['orderHistory'])} pedidos)")


if __name__ == "__main__":
    main()
