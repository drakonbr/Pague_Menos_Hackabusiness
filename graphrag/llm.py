"""RAG com DeepSeek (itens #33 a #38 da auditoria): só entra quando o grafo NÃO entende o pedido.

O grafo sempre roda primeiro e, se achou, a resposta dele vale. Quando ele não entende, a DeepSeek traduz o que a
pessoa escreveu para ids do catálogo (objetivo, preocupação, ingrediente, etapa, preferência, pele, orçamento). Tudo o
que não existe no catálogo é descartado; com o que sobra, montamos uma frase só com rótulos do catálogo e o grafo busca
de novo. Assim quem escolhe produto e monta kit continua sendo o compositor (K1 a K12): a DeepSeek só entende.

Sem chave, com a API fora do ar ou demorando, nada muda: o motor responde como responderia sem ela.
Privacidade: antes de enviar, saem e-mail, números longos (telefone, CPF, CEP), nome, endereço e idade (doc 14).
"""
from __future__ import annotations

import json
import logging
import os
import re
import threading
import time
import urllib.request
from collections import OrderedDict
from pathlib import Path

from .data import Catalog
from .lexicon import PREFERENCE_ALIASES
from .text import norm

log = logging.getLogger("graphrag.rag")

API_URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-chat"
TIMEOUT_S = 4.0                 # por operação de rede; uma só chamada por busca (o replay do chat não chama)
MAX_TEXT = 500                  # mesmo limite de /v1/search-chat: frase maior é cortada antes de enviar
MAX_PER_MIN = 60                # ponytail: teto por processo; com tráfego real, limite por pessoa/IP
SKINS = ["oleosa", "mista", "seca", "normal", "sensível"]
GOAL_PHRASE = {"suplementos": "kit de suplementos"}       # "suplementos e vitaminas" sozinho vira lista, não kit
SKIP_CONCERNS = {"reposicao"}                              # reposição tem fluxo próprio (Meus medicamentos)

SYSTEM_PROMPT = """Você traduz pedidos de clientes de uma farmácia para os termos de busca de um catálogo.
Responda SÓ com um objeto JSON, sem texto fora dele.

Regras:
1. Use apenas ids que existem nas listas abaixo. Se nada servir, devolva listas vazias.
2. Não recomende produto, marca, dose nem tratamento. Não escreva frases para a cliente.
3. Nunca sugira procurar médico, farmacêutico ou outro profissional.
4. Não repita nome, idade, telefone, endereço ou qualquer dado pessoal.
5. "sem X", "não quero X", "alergia a X": se X é um ingrediente da lista, vai para "evitar" (nunca para
   "ingredientes"); se é uma preferência da lista ("sem álcool", "sem fragrância", "vegano"...), vai para
   "preferencias".
6. Valor em reais ("até 80 reais", "R$ 50") vai para "orcamento_centavos"; sem valor, null.
7. Se houver "Conversa até aqui", o pedido pode ser um ajuste do que já foi buscado
   ("tira o que tem perfume", "mais barato", "pele sensível"): devolva só o que muda,
   em "ajuste", e mantenha o resto vazio.
8. Tipo de pele, se dito, vai para "pele" (um id de TIPOS_DE_PELE); senão, null.
10. Se vier "Palavras que o catálogo não conhece", diga em "palavras" qual id das listas cada uma quer dizer
    (ex.: {{"melada": "oleosidade"}}). Se for só enchimento ou não corresponder a nada das listas, não a inclua.
9. Só marque um objetivo se o pedido for claramente sobre ele. Quando a pessoa fala de um tipo de produto ou de
   uma parte do corpo (ex.: suor na axila = desodorante), use "etapas" e "preocupacoes", sem objetivo.

Listas do catálogo (id: rótulo):
OBJETIVOS: {goals}
PREOCUPACOES: {concerns}
INGREDIENTES: {ingredients}
ETAPAS: {steps}
PREFERENCIAS: {preferences}
TIPOS_DE_PELE: {skin_types}

Formato da resposta:
{{"objetivos": [], "preocupacoes": [], "ingredientes": [], "etapas": [],
 "evitar": [], "preferencias": [], "orcamento_centavos": null, "pele": null,
 "ajuste": {{"evitar": [], "preferencias": [], "orcamento": "mais_barato | mais_caro | null", "pele": null}},
 "palavras": {{}}}}"""

_EMAIL = re.compile(r"\S+@\S+\.\S+")
_PHONE = re.compile(r"(?:\+?\d[\d\s().-]{7,}\d)")
_NAME = re.compile(r"\b((?i:meu nome [ée]|me chamo))\s+[\wÀ-ú]+(?:\s+[A-ZÀ-Ú][\wÀ-ú]*)*")   # 1ª palavra + sobrenomes
_NAME2 = re.compile(r"\b((?i:sou a|sou o))\s+[A-ZÀ-Ú][\wÀ-ú]*(?:\s+[A-ZÀ-Ú][\wÀ-ú]*)*")
_ADDR = re.compile(r"\b(rua|r\.|avenida|av\.|travessa|alameda|rodovia|estrada|praça)\s+[^,.;\n]*", re.I)
_AGE = re.compile(r"\b\d{1,3}\s+anos\b(?!\s+de\b)", re.I)             # "2 anos de acne" fica


def scrub(text: str) -> str:
    """Tira dado pessoal antes de mandar para fora: e-mail, números longos (telefone, CPF, CEP), nome, endereço e idade.
    ponytail: regras simples; nome sem pista ("Maria, tô com tosse") passa. Com dados reais, usar um detector de PII."""
    text = _EMAIL.sub("[email]", text[:MAX_TEXT])
    text = _NAME.sub(lambda m: m.group(1) + " [nome]", text)
    text = _NAME2.sub(lambda m: m.group(1) + " [nome]", text)
    text = _ADDR.sub("[endereço]", text)
    text = _AGE.sub("[idade]", text)
    return _PHONE.sub("[numero]", text).strip()


def rag_banner(engine) -> str:
    """Uma linha para o início do servidor: sem chave a busca continua, mas entende menos, e isso não pode ser silencioso (#60)."""
    if engine.rag:
        return "RAG com DeepSeek: LIGADO (só quando o grafo não entende ou vê palavra desconhecida)"
    return ("ATENÇÃO, RAG com DeepSeek: DESLIGADO. Sem DEEPSEEK_API_KEY no ambiente nem em .env.local, frases fora do "
            "vocabulário do catálogo ficam sem resposta melhor (\"Não encontrei esse item\").")


def _env_key() -> str | None:
    key = os.environ.get("DEEPSEEK_API_KEY")
    if key:
        return key.strip()
    env = Path(__file__).resolve().parents[1] / ".env.local"          # só no PC; na Vercel vem da variável de ambiente
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.startswith("DEEPSEEK_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"') or None
    return None


class DeepSeek:
    """Cliente mínimo da API (formato OpenAI). Qualquer erro, chave inválida ou demora devolve None."""

    def __init__(self, key: str, timeout: float = TIMEOUT_S, url: str = API_URL, model: str = MODEL):
        self.key, self.timeout, self.url, self.model = key, timeout, url, model
        self.calls, self.lock, self.recent = 0, threading.Lock(), []

    @classmethod
    def from_env(cls) -> "DeepSeek | None":
        key = _env_key()
        return cls(key) if key else None

    def complete(self, system: str, user: str) -> str | None:
        with self.lock:
            now = time.monotonic()
            self.recent = [t for t in self.recent if now - t < 60]
            if len(self.recent) >= MAX_PER_MIN:
                log.warning("deepseek: teto de %d chamadas por minuto", MAX_PER_MIN)
                return None
            self.recent.append(now)
            self.calls += 1
        body = json.dumps({"model": self.model, "temperature": 0, "max_tokens": 400,
                           "response_format": {"type": "json_object"},
                           "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]})
        req = urllib.request.Request(self.url, data=body.encode(), method="POST",
                                     headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.key}"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                return json.loads(r.read())["choices"][0]["message"]["content"]
        except Exception as e:                       # rede, HTTP 4xx/5xx, tempo, resposta fora do formato
            log.warning("deepseek indisponível: %s", type(e).__name__)
            return None


class Reader:
    """Interpreta um pedido com a DeepSeek e devolve só ids que existem no catálogo (ou None)."""

    def __init__(self, cat: Catalog, client, cache_size: int = 512):
        self.cat, self.client, self.cache_size = cat, client, cache_size
        self.cache: OrderedDict[tuple, dict | None] = OrderedDict()
        self.lock = threading.Lock()
        self.allowed = {
            "objetivos": {g["id"]: g["label"] for g in cat.goals},
            "preocupacoes": {k: v for k, v in cat.concerns.items() if k not in SKIP_CONCERNS},
            "ingredientes": {k: v["name"] for k, v in cat.ingredients.items()},
            "etapas": dict(cat.steps),
            "preferencias": {p: p for p in PREFERENCE_ALIASES},
        }
        self.allowed["evitar"] = self.allowed["ingredientes"]
        # aceita id ou rótulo (sem acento, minúsculo) na resposta
        key = lambda x: norm(str(x).replace("_", " "))
        self.key = key
        self.lookup = {f: {**{key(k): k for k in d}, **{key(v): k for k, v in d.items()}} for f, d in self.allowed.items()}
        fmt = lambda d: "; ".join(f"{k}: {v}" for k, v in d.items())
        self.system = SYSTEM_PROMPT.format(goals=fmt(self.allowed["objetivos"]), concerns=fmt(self.allowed["preocupacoes"]),
                                           ingredients=fmt(self.allowed["ingredientes"]), steps=fmt(self.allowed["etapas"]),
                                           preferences="; ".join(PREFERENCE_ALIASES), skin_types="; ".join(SKINS))

    def _ids(self, field: str, values) -> list[str]:
        out = []
        for v in values if isinstance(values, list) else []:
            k = self.lookup[field].get(self.key(v))
            if k and k not in out:
                out.append(k)
        return out

    @staticmethod
    def _skin(v) -> str | None:
        v = norm(str(v or ""))
        return next((s for s in SKINS if norm(s) == v), None)

    def _validate(self, raw: str | None, unknown: tuple = ()) -> dict | None:
        try:
            d = json.loads(raw or "")
        except (TypeError, ValueError):
            return None
        if not isinstance(d, dict):
            return None
        out = {f: self._ids(f, d.get(f)) for f in ("objetivos", "preocupacoes", "ingredientes", "etapas", "evitar", "preferencias")}
        out["preferencias"] += [x for x in self._ids("preferencias", d.get("evitar")) if x not in out["preferencias"]]
        b = d.get("orcamento_centavos")
        out["orcamento_centavos"] = int(b) if isinstance(b, (int, float)) and 100 <= b <= 10_000_000 else None
        out["pele"] = self._skin(d.get("pele"))
        a = d.get("ajuste") if isinstance(d.get("ajuste"), dict) else {}
        orc = a.get("orcamento")
        a_prefs = self._ids("preferencias", (a.get("preferencias") or []) + (a.get("evitar") or []))
        # significado que a DeepSeek deu às palavras que o catálogo não conhece (só ids que existem)
        out["explicadas"] = []
        asked = {self.key(w) for w in unknown}
        for w, v in (d.get("palavras") or {}).items() if isinstance(d.get("palavras"), dict) else []:
            if self.key(w) not in asked:
                continue
            for field in ("objetivos", "preocupacoes", "etapas", "ingredientes"):
                k = self.lookup[field].get(self.key(v))
                if k:
                    out["explicadas"].append((self.key(w), field, k))
                    break
        out["ajuste"] = {"evitar": self._ids("evitar", a.get("evitar")), "preferencias": a_prefs,
                         "orcamento": orc if orc in ("mais_barato", "mais_caro") else None, "pele": self._skin(a.get("pele"))}
        return out

    def read(self, text: str, conversation: str = "", unknown: tuple | list = ()) -> dict | None:
        clean = scrub(text)
        seen = set(re.findall(r"[a-z0-9]+", norm(clean)))
        unknown = tuple(w for w in dict.fromkeys(unknown) if norm(w) in seen)       # só palavras que realmente seguem na frase enviada
        key = (clean, conversation, unknown)
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
                return self.cache[key]
        user = (f"Pedido: {key[0]}" + (f"\nPalavras que o catálogo não conhece: {', '.join(unknown)}" if unknown else "")
                + (f"\nConversa até aqui: {conversation}" if conversation else ""))
        raw = self.client.complete(self.system, user)
        if raw is None:
            return None                                  # falha da API não vai para o cache: a próxima tenta de novo
        parsed = self._validate(raw, unknown)
        with self.lock:
            self.cache[key] = parsed
            if len(self.cache) > self.cache_size:
                self.cache.popitem(last=False)
        return parsed


def phrase(cat: Catalog, p: dict, adjust: bool) -> str:
    """Frase só com rótulos do catálogo, que o grafo entende. Ajuste no meio da conversa usa as formas de refinamento
    ("sem X", "mais barato", "minha pele é X"); pedido novo usa objetivo, preocupação, etapa e ingrediente."""
    ing = lambda i: cat.ingredients[i]["name"].lower()
    a = dict(p["ajuste"])
    if adjust and not (p["objetivos"] or p["preocupacoes"] or p["etapas"] or p["ingredientes"]):
        # modificador solto no meio da conversa ("sem álcool" fora de "ajuste") também é ajuste
        a["evitar"] = list(dict.fromkeys(a["evitar"] + p["evitar"]))
        a["preferencias"] = list(dict.fromkeys(a["preferencias"] + p["preferencias"]))
        a["pele"] = a["pele"] or p["pele"]
    if adjust and any(a.values()):
        parts = [f"sem {ing(i)}" for i in a["evitar"]] + list(a["preferencias"])
        parts += {"mais_barato": ["mais barato"], "mais_caro": ["mais completo"]}.get(a["orcamento"], [])
        parts += [f"minha pele é {a['pele']}"] if a["pele"] else []
        return " e ".join(parts)
    parts = [GOAL_PHRASE.get(g, cat.goal_by_id[g]["label"].lower()) for g in p["objetivos"]]
    covered_c = {c for g in p["objetivos"] for c in cat.goal_by_id[g].get("concerns", [])}
    covered_s = {s for g in p["objetivos"] for s in cat.goal_by_id[g]["required_steps"] + cat.goal_by_id[g]["optional_steps"]}
    # etapa e preocupação juntas: "dente sensível" = higiene bucal + sensibilidade (antes só a preocupação chegava ao grafo)
    parts += [cat.steps[s].lower() for s in p["etapas"] if s not in covered_s]
    parts += [cat.concerns[c] for c in p["preocupacoes"] if c not in covered_c]
    parts += [ing(i) for i in p["ingredientes"]]
    if not parts:
        return ""                                    # nada do catálogo serve: o grafo mantém a resposta dele
    parts += [f"sem {ing(i)}" for i in p["evitar"]] + list(p["preferencias"])
    if p["pele"]:
        parts.append(f"pele {p['pele']}")
    if p["orcamento_centavos"]:
        parts.append(f"até R$ {p['orcamento_centavos'] // 100}")
    return ", ".join(parts)
