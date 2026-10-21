"""Ontologia do grafo (esquema ESTRITO) e esquema de ingestão de produtos.

Dois papéis:
  1. `NodeKind`, `EdgeType` e `EDGE_RULES` dizem quais nós e arestas existem e entre quais tipos de nó cada aresta
     pode ligar. `validate_graph` confere o grafo inteiro contra essas regras (usado nos testes e na ingestão).
  2. `ProductRecord` é o formato de entrada da ingestão incremental (graphrag/ingest.py): tudo que não bate com o
     esquema é recusado ANTES de tocar no grafo. É o equivalente, sem modelo de linguagem, da "extração estruturada":
     o catálogo já é estruturado, então não há o que extrair por LLM, só validar e resolver entidades.

Preço e estoque não são nós do grafo (consulta viva, doc 06); entram no registro só para o produto poder ser vendido.
"""
from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ARTIFACTS = Path(__file__).resolve().parent / "artifacts"


class NodeKind(str, Enum):
    PRODUCT = "product"      # produto do catálogo (sem preço nem estoque)
    BRAND = "brand"          # marca
    PTYPE = "ptype"          # tipo de produto (gel de limpeza, sérum, cápsula...)
    DOMAIN = "domain"        # dermo, suplemento, higiene, medicamento
    STEP = "step"            # etapa da rotina (limpeza, ômega 3...)
    CONCERN = "concern"      # preocupação (acne, manchas...)
    INGREDIENT = "ingredient"
    WARNING = "warning"      # aviso documentado
    SKIN = "skin"            # tipo de pele
    CLAIM = "claim"          # alegação (vegano, sem fragrância...)
    GOAL = "goal"            # objetivo de compra
    EQUIV = "equiv"          # grupo de equivalência (mesmo ativo e dose; só medicamento)


class EdgeType(str, Enum):
    OF_BRAND = "OF_BRAND"
    OF_TYPE = "OF_TYPE"
    IN_DOMAIN = "IN_DOMAIN"
    COVERS = "COVERS"
    ADDRESSES = "ADDRESSES"
    CONTAINS = "CONTAINS"
    SUITS = "SUITS"
    HAS_CLAIM = "HAS_CLAIM"
    HAS_WARNING = "HAS_WARNING"
    TARGETS = "TARGETS"
    REQUIRES = "REQUIRES"
    CONFLICTS_WITH = "CONFLICTS_WITH"
    IN_EQUIV_GROUP = "IN_EQUIV_GROUP"
    EQUIVALENT_TO = "EQUIVALENT_TO"
    SIMILAR_TO = "SIMILAR_TO"


K, E = NodeKind, EdgeType
# aresta -> (tipo de origem, tipo de destino)
EDGE_RULES: dict[EdgeType, tuple[NodeKind, NodeKind]] = {
    E.OF_BRAND: (K.PRODUCT, K.BRAND), E.OF_TYPE: (K.PRODUCT, K.PTYPE), E.IN_DOMAIN: (K.PRODUCT, K.DOMAIN),
    E.COVERS: (K.PRODUCT, K.STEP), E.ADDRESSES: (K.PRODUCT, K.CONCERN), E.CONTAINS: (K.PRODUCT, K.INGREDIENT),
    E.SUITS: (K.PRODUCT, K.SKIN), E.HAS_CLAIM: (K.PRODUCT, K.CLAIM), E.HAS_WARNING: (K.PRODUCT, K.WARNING),
    E.TARGETS: (K.GOAL, K.CONCERN), E.REQUIRES: (K.GOAL, K.STEP), E.CONFLICTS_WITH: (K.INGREDIENT, K.INGREDIENT),
    E.IN_EQUIV_GROUP: (K.PRODUCT, K.EQUIV), E.EQUIVALENT_TO: (K.PRODUCT, K.PRODUCT),
    E.SIMILAR_TO: (K.PRODUCT, K.PRODUCT),
}
# vocabulário FECHADO: nós destes tipos não nascem da ingestão (só do catálogo-base); abertos podem nascer
CLOSED_KINDS = {K.STEP, K.CONCERN, K.INGREDIENT, K.WARNING, K.SKIN, K.DOMAIN, K.GOAL}
OPEN_KINDS = {K.BRAND, K.PTYPE, K.CLAIM}


class GraphNode(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(pattern=r"^[a-z]+:.+$")
    kind: NodeKind
    label: str | None = None


class GraphEdge(BaseModel):
    model_config = ConfigDict(extra="forbid")
    src: str
    dst: str
    type: EdgeType


def validate_graph(g) -> list[str]:
    """Confere um grafo networkx contra a ontologia. Lista vazia = válido."""
    errs: list[str] = []
    kinds: dict[str, NodeKind] = {}
    for n, d in g.nodes(data=True):
        try:
            node = GraphNode(id=n, kind=d.get("kind"), label=d.get("label"))
        except Exception as ex:                                   # noqa: BLE001
            errs.append(f"nó inválido {n!r}: {ex}")
            continue
        if n.split(":", 1)[0] != node.kind.value:
            errs.append(f"prefixo do id não bate com o tipo: {n!r} é {node.kind.value}")
        kinds[n] = node.kind
    for u, v, d in g.edges(data=True):
        try:
            et = EdgeType(d.get("type"))
        except ValueError:
            errs.append(f"tipo de aresta fora da ontologia: {u} -> {v} ({d.get('type')!r})")
            continue
        if u not in kinds or v not in kinds:
            errs.append(f"aresta {et.value} aponta para nó inexistente: {u} -> {v}")
            continue
        src, dst = EDGE_RULES[et]
        if (kinds[u], kinds[v]) != (src, dst):
            errs.append(f"{et.value} só liga {src.value} -> {dst.value}, mas achei {kinds[u].value} -> {kinds[v].value} ({u} -> {v})")
    return errs


# --------------------------------------------------------------------------- entrada da ingestão
Domain = Literal["dermo", "suplemento", "higiene", "medicamento"]
Form = Literal["tube", "dropper", "bottle", "jar", "caps", "box", "stick", "powder", "spray", "pump", "bar", "patch"]


class Size(BaseModel):
    model_config = ConfigDict(extra="forbid")
    value: float = Field(gt=0)
    unit: Literal["g", "ml", "un"]


class Equivalence(BaseModel):
    model_config = ConfigDict(extra="forbid")
    group: str
    presentation: Literal["referencia", "generico", "similar"]
    active: str
    dose: str


class ProductRecord(BaseModel):
    """Um produto novo (ou alterado) para entrar no grafo e no catálogo do motor. Campos em camelCase, como o contrato."""
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str | None = Field(default=None, pattern=r"^p\d{3,}$")
    name: str = Field(min_length=3, max_length=120)
    brand: str = Field(min_length=2, max_length=60)
    line: str = Field(min_length=2, max_length=60)
    step: str
    coversSteps: list[str] = Field(min_length=1)
    productType: str = Field(min_length=3, max_length=80)
    form: Form
    size: Size
    skinTypes: list[str] = Field(min_length=1)
    concerns: list[str] = Field(min_length=1)
    ingredients: list[str] = Field(default_factory=list)
    fps: int | None = Field(default=None, ge=6, le=100)
    usagePeriod: Literal["dia", "noite", "dia_noite"] = "dia"
    claims: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    description: str = Field(min_length=20, max_length=600)
    howToUse: str = Field(min_length=5, max_length=300)
    priceTier: Literal["economico", "intermediario", "premium"]
    priceCents: int = Field(gt=0, lt=10_000_000)
    listPriceCents: int | None = None
    stockQty: int = Field(ge=0, lt=100_000)
    cashbackPct: int | None = Field(default=None, ge=0, le=20)
    domain: Domain
    rx: Literal["receita_simples"] | None = None
    equivalence: Equivalence | None = None
    storeStock: dict[str, int] = Field(default_factory=dict)

    @field_validator("storeStock")
    @classmethod
    def _stock_non_negative(cls, v: dict[str, int]):
        if any(q < 0 for q in v.values()):
            raise ValueError("estoque por loja não pode ser negativo")
        return v

    @model_validator(mode="after")
    def _coherence(self):
        if self.step not in self.coversSteps:
            raise ValueError("coversSteps precisa conter a etapa principal (step)")
        if self.listPriceCents is None:
            self.listPriceCents = self.priceCents
        if self.listPriceCents < self.priceCents:
            raise ValueError("listPriceCents não pode ser menor que priceCents")
        if self.domain != "medicamento" and (self.rx is not None or self.equivalence is not None):
            raise ValueError("rx e equivalence só existem em medicamento")
        return self


def export_schema(path: Path | None = None) -> Path:
    """Grava o esquema JSON da ontologia e do registro de entrada (documentação + validação por outras ferramentas)."""
    path = path or ARTIFACTS / "ontology.schema.json"
    doc = {
        "nodeKinds": [k.value for k in NodeKind],
        "closedKinds": sorted(k.value for k in CLOSED_KINDS),
        "openKinds": sorted(k.value for k in OPEN_KINDS),
        "edgeTypes": {e.value: {"from": s.value, "to": d.value} for e, (s, d) in EDGE_RULES.items()},
        "productRecord": ProductRecord.model_json_schema(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    print("esquema gravado em", export_schema())
