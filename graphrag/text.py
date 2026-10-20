"""Texto em português: normalização, tokens, radical simples e valores em reais.

Tudo escrito à mão, sem biblioteca de PLN nem modelo externo.
"""
from __future__ import annotations

import re
import unicodedata

STOPWORDS = frozenset("""
a o as os um uma uns umas de da do das dos em na no nas nos para pra por com sem sobre ate e ou mas que se
eu me meu minha meus minhas voce vc voces ele ela eles elas seu sua seus suas isso isto esse essa esses essas
este esta estes estas aquele aquela ao aos mais muito muita pouco tambem ja so mesmo mesma entre como quando
onde qual quais quem cujo ser estar ter haver tem tenho tinha vai vou fazer faz quero queria gostaria preciso
precisava poderia pode podem favor obrigada obrigado ola oi tudo bem la aqui ai ta tá
""".split())


def norm(s: str) -> str:
    """minúsculas, sem acento, espaços colapsados."""
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s).strip()


def raw_tokens(s: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", norm(s))


def stem(w: str) -> str:
    """Radical bem simples: plural, flexão de gênero e alguns sufixos. Só precisa ser CONSISTENTE."""
    if len(w) <= 3 or w.isdigit():
        return w
    for suf, rep in (("oes", "ao"), ("aes", "ao"), ("ais", "al"), ("eis", "el"), ("ois", "ol"),
                     ("res", "r"), ("zes", "z"), ("ns", "m")):
        if w.endswith(suf) and len(w) > len(suf) + 2:
            w = w[: -len(suf)] + rep
            break
    else:
        if w.endswith("s") and not w.endswith("ss") and len(w) > 3:
            w = w[:-1]
    for suf in ("mente", "inho", "inha", "issimo", "issima"):
        if w.endswith(suf) and len(w) > len(suf) + 3:
            w = w[: -len(suf)]
    if len(w) > 4 and w[-1] in "aoe":
        w = w[:-1]
    return w


def tokens(s: str, keep_stop: bool = False) -> list[str]:
    out = []
    for t in raw_tokens(s):
        if not keep_stop and t in STOPWORDS:
            continue
        out.append(stem(t))
    return out


def stemmed_all(s: str) -> list[str]:
    """Todos os tokens com radical, inclusive stopwords (para casar frases)."""
    return [stem(t) for t in raw_tokens(s)]


# ------------------------------------------------------------------ dinheiro
_UNITS = {"um": 1, "uma": 1, "dois": 2, "duas": 2, "tres": 3, "quatro": 4, "cinco": 5, "seis": 6, "sete": 7,
          "oito": 8, "nove": 9, "dez": 10, "onze": 11, "doze": 12, "treze": 13, "catorze": 14, "quatorze": 14,
          "quinze": 15, "dezesseis": 16, "dezessete": 17, "dezoito": 18, "dezenove": 19}
_TENS = {"vinte": 20, "trinta": 30, "quarenta": 40, "cinquenta": 50, "sessenta": 60, "setenta": 70,
         "oitenta": 80, "noventa": 90}
_HUND = {"cem": 100, "cento": 100, "duzentos": 200, "trezentos": 300, "quatrocentos": 400, "quinhentos": 500,
         "seiscentos": 600, "setecentos": 700, "oitocentos": 800, "novecentos": 900}
_BUDGET_CUE = r"(?:ate|no maximo|maximo(?: de)?|por ate|menos de|abaixo de|limite de|orcamento de|gastar|teto de)"


def _words_to_int(words: list[str]) -> int | None:
    total, seen = 0, False
    for w in words:
        if w in _HUND:
            total += _HUND[w]; seen = True
        elif w in _TENS:
            total += _TENS[w]; seen = True
        elif w in _UNITS:
            total += _UNITS[w]; seen = True
        elif w == "e":
            continue
        else:
            return None
    return total if seen else None


def parse_money_cents(text: str) -> int | None:
    """'até R$ 120', '120 reais', 'cem reais', 'ate 80,50', 'no máximo 300'. None se não há valor."""
    q = norm(text)
    m = re.search(r"r\$\s*(\d{1,5}(?:[.,]\d{1,2})?)", q)
    if not m:
        m = re.search(r"(\d{1,5}(?:[.,]\d{1,2})?)\s*(?:reais|real|conto|contos|pila|pilas)\b", q)
    if not m:
        m = re.search(_BUDGET_CUE + r"\s+(?:r\$\s*)?(\d{1,5}(?:[.,]\d{1,2})?)\b", q)
    if m:
        raw = m.group(1)
        if re.fullmatch(r"\d{1,3}\.\d{3}", raw):          # 1.200 = mil e duzentos
            raw = raw.replace(".", "")
        v = float(raw.replace(",", "."))
        return int(round(v * 100)) if v > 0 else None
    m = re.search(r"((?:(?:" + "|".join(sorted(list(_HUND) + list(_TENS) + list(_UNITS), key=len, reverse=True))
                  + r")(?: e )?)+)\s*(?:reais|real)\b", q)
    if m:
        v = _words_to_int(m.group(1).split())
        return v * 100 if v else None
    return None


def money(cents: int) -> str:
    """R$ 1.234,56"""
    reais, c = divmod(int(cents), 100)
    return f"R$ {reais:,}".replace(",", ".") + f",{c:02d}"


def join_pt(items: list[str]) -> str:
    items = [i for i in items if i]
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " e " + items[-1]
