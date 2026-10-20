"""Corretor de digitação, feito do zero: "shampu", "soalr", "protetor solr" viram palavras que o catálogo conhece.

Vocabulário = palavras dos produtos (nome, tipo, descrição, ingredientes), dos conceitos e do léxico. Uma palavra que
NÃO está no vocabulário e tem 4+ letras troca por uma conhecida a 1 edição de distância (inserir, tirar, trocar ou
inverter letras vizinhas); a mais frequente vence. Palavras curtas, números e palavras comuns do português nunca mudam.
Só mexe no que o catálogo não conhece, então não "estraga" o que já está certo.
"""
from __future__ import annotations

import re
from collections import Counter

from .concepts import CONCEPTS
from .data import Catalog
from .lexicon import (CONCERN_ALIASES, INGREDIENT_ALIASES, PARAPHRASE_CORPUS, PREFERENCE_ALIASES, SKIN_ALIASES)
from .text import STOPWORDS, norm

COMMON = frozenset("""
quero preciso procuro tenho estou fazer comprar compra comprei ajuda ajudar tomar usar uso usando levar viajar viagem
algo coisa coisas produto produtos bom boa bons boas melhor melhores muito muita muitos muitas pouco pouca tudo toda todo
todos todas direito consigo consegue dormir acordo mostrar mostra mostre lista opcao opcoes preco precos barato barata
caro cara kit kits cesta carrinho entrega frete prazo retirar retirada loja lojas dia noite manha tarde semana mes
reais real quanto custa valor total junto juntos tambem outro outra outros outras algum alguma alguns algumas
esse essa isso aquele aquela segundo terceiro primeiro agora hoje amanha ontem sempre nunca tipo tipos marca marcas
sabe saber gosto gosta gostar queria gostaria pode podem poderia favor obrigado obrigada ola tchau oi
pelo pela pelos pelas num numa nuns numas dum duma desde sob contra perante apos depois antes durante enquanto porque pois
assim entao pro pra tanto tanta tantos tantas qualquer quaisquer cada outrem nenhum nenhuma nada algo alguem ninguem
sempre ainda logo antes depois dentro fora perto longe junto cima baixo embaixo debaixo acima abaixo frente atras
ficar fica ficou ficam fiquei deixar deixa deixou usar usei usou passa passo passar passei cuida cuidar cuidado cuidados
tratar trata tratamento melhorar melhora melhorou melhoria diminuir diminui aumentar aumenta evitar evita tirar tira tiro
acabar acabei acabou acaba parar para pare proteger proteja protege protecao nutrir nutre limpar limpa lavar lava
diaria diario diarias diarios rotina completa completo basica basico simples forte fortes fraco fraca fracos fracas
sensivel sensiveis seca secas seco secos oleosa oleoso mista misto normal nova novo novos novas velho velha
filha filho mae pai irma irmao avo marido esposa namorada namorado amiga amigo presente presentes
cheirosa cheiroso gostoso gostosa macia macio lisa liso lisinha lisinho brilho brilhar brilhando viço vico
rosto rostos corpo corpos pele peles cabelo cabelos fios boca bocas dente dentes olhos olho labios labio maos mao pes
""".split())


def _edits1(w: str) -> set[str]:
    letters = "abcdefghijklmnopqrstuvwxyz0123456789"
    splits = [(w[:i], w[i:]) for i in range(len(w) + 1)]
    dele = {a + b[1:] for a, b in splits if b}
    trans = {a + b[1] + b[0] + b[2:] for a, b in splits if len(b) > 1}
    subs = {a + c + b[1:] for a, b in splits if b for c in letters}
    ins = {a + c + b for a, b in splits for c in letters}
    return dele | trans | subs | ins


def _lev_le2(a: str, b: str) -> int:
    """Distância de edição (com troca de vizinhas), cortada em 3."""
    if abs(len(a) - len(b)) > 2:
        return 3
    prev2, prev = None, list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb))
            if prev2 is not None and i > 1 and j > 1 and ca == b[j - 2] and a[i - 2] == cb:
                cur[j] = min(cur[j], prev2[j - 2] + 1)
        prev2, prev = prev, cur
    return min(prev[-1], 3)


class Speller:
    def __init__(self, cat: Catalog):
        freq: Counter = Counter()

        def feed(text: str, w: int = 1):
            for t in re.findall(r"[a-z0-9]+", norm(text)):
                freq[t] += w

        for p in cat.products:
            if p["domain"] == "medicamento":
                continue          # a busca em texto livre não enxerga medicamento (privacidade)
            feed(p["name"], 3); feed(p["productType"], 3); feed(p["brand"], 1); feed(p["description"], 1)
            feed(" ".join(p["claims"]), 1)
        for ing in cat.ingredients.values():
            feed(ing["name"], 2)
        self.catalog_vocab = frozenset(freq)        # só o que o catálogo diz (sem conceitos de itens que não existem)
        for c in CONCEPTS:
            for ph in c.phrases:
                feed(ph, 3)
        for table in (CONCERN_ALIASES, SKIN_ALIASES, PREFERENCE_ALIASES, INGREDIENT_ALIASES):
            for aliases in table.values():
                for a in aliases:
                    feed(a, 2)
        for s in PARAPHRASE_CORPUS:
            feed(s, 1)
        self.freq = freq
        self.vocab = frozenset(freq)

    def correct_word(self, w: str) -> str:
        if len(w) < 5 or w.isdigit() or w in self.vocab or w in STOPWORDS or w in COMMON:
            return w
        # palavra mais curta que a digitada ("secao" -> "seco") só vale em palavra longa: em palavra curta é troca de assunto
        cands = [c for c in _edits1(w) if c in self.vocab and len(c) >= 4 and c not in STOPWORDS and c not in COMMON
                 and c + "s" != w and w + "s" != c                      # plural/singular não é erro de digitação
                 and (len(c) >= len(w) or len(w) >= 8)]
        if cands:
            return max(cands, key=lambda c: (self.freq[c], -abs(len(c) - len(w)), c))
        if len(w) >= 7:                                   # palavras longas aceitam 2 edições ("shampu" -> "shampoo")
            near = [(d, c) for c in self.vocab if len(c) >= 6 and c not in STOPWORDS and c not in COMMON
                    and c + "s" != w and w + "s" != c and (d := _lev_le2(w, c)) <= 2]
            if near:
                best = min(d for d, _ in near)
                return max((c for d, c in near if d == best), key=lambda c: (self.freq[c], c))
        return w

    def fix(self, text: str) -> tuple[str, list[tuple[str, str]]]:
        """Devolve o texto corrigido (sem acentos, minúsculo, como o motor já normaliza) e a lista (antes, depois)."""
        changes: list[tuple[str, str]] = []
        out = []
        for w in norm(text).split(" "):
            core = re.sub(r"[^a-z0-9]", "", w)
            if core and core == w:
                c = self.correct_word(w)
                if c != w:
                    changes.append((w, c)); w = c
            out.append(w)
        return " ".join(out), changes
