"""Vetores de palavras TREINADOS DO ZERO no catálogo (sem modelo externo, sem download).

Método clássico e transparente: matriz de co-ocorrência (janela deslizante, peso 1/distância) -> PMI positivo
com suavização do contexto -> SVD truncado. É o mesmo princípio do word2vec (Levy & Goldberg, 2014), só que
em álgebra linear direta e determinístico.

O corpus de treino é montado por `build_corpus`: descrições, tipos, ingredientes, preocupações, etapas e
objetivos do catálogo + o léxico escrito à mão (graphrag/lexicon.py), de modo que gírias ("pele que brilha")
caiam perto de "oleosidade" e "poros".

Limite assumido: corpus pequeno (centenas de frases). Serve para aproximar vocabulário de DOMÍNIO; não é um
modelo de linguagem geral. O contrato permite trocar este módulo por um modelo maior sem mudar o resto.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from . import lexicon
from .concepts import CONCEPTS
from .corpus_extra import EXTRA_PARAPHRASES
from .data import Catalog
from .text import stem, tokens

ARTIFACTS = Path(__file__).resolve().parent / "artifacts"
DIM = 48
WINDOW = 5
SMOOTH = 0.75


def build_corpus(cat: Catalog) -> list[list[str]]:
    sents: list[str] = []
    goal_of_concern: dict[str, list[str]] = defaultdict(list)
    for g in cat.goals:
        for c in g["concerns"]:
            goal_of_concern[c].append(g["label"])
    types_of_concern: dict[str, Counter] = defaultdict(Counter)
    for p in cat.products:
        for c in p["concerns"]:
            types_of_concern[c][p["productType"]] += 1

    for p in cat.products:
        if p["domain"] == "medicamento":
            continue  # medicamento não participa da busca por texto livre (nem do vocabulário aprendido)
        concerns = " ".join(cat.concerns.get(c, c) for c in p["concerns"])
        ings = " ".join(f"{cat.ingredients[i]['name']} {cat.ingredients[i]['function']}" for i in p["ingredients"])
        goals = " ".join(g for c in p["concerns"] for g in goal_of_concern.get(c, []))
        sents.append(f"{p['name']} {p['brand']} {p['productType']} {cat.steps.get(p['step'], '')}")
        sents.append(f"{p['description']} {p['howToUse']}")
        sents.append(f"{p['productType']} {concerns} {ings} {' '.join(p['claims'])} {' '.join(p['skinTypes'])}")
        sents.append(f"{goals} {concerns} {p['productType']} {cat.steps.get(p['step'], '')}")
    for g in cat.goals:
        steps = " ".join(cat.steps[s] for s in g["required_steps"] + g["optional_steps"])
        sents.append(f"{g['label']} {' '.join(g['synonyms'])} {' '.join(cat.concerns[c] for c in g['concerns'])} {steps}")
    for cid, aliases in lexicon.CONCERN_ALIASES.items():
        label = cat.concerns.get(cid, cid)
        ptypes = " ".join(t for t, _ in types_of_concern.get(cid, Counter()).most_common(3))
        goals = " ".join(goal_of_concern.get(cid, []))
        for k in range(0, len(aliases), 3):
            chunk = " ".join(aliases[k:k + 3])
            sents.append(f"{chunk} {label} {goals} {ptypes}")
            sents.append(f"{label} {chunk}")
    for skin, aliases in lexicon.SKIN_ALIASES.items():
        sents.append(f"pele {skin} {' '.join(aliases)}")
    for claim, aliases in lexicon.PREFERENCE_ALIASES.items():
        sents.append(f"{claim} {' '.join(aliases)}")
    for ing, aliases in lexicon.INGREDIENT_ALIASES.items():
        if ing in cat.ingredients:
            sents.append(f"{cat.ingredients[ing]['name']} {' '.join(aliases)} {cat.ingredients[ing]['function']}")
    sents.extend(lexicon.PARAPHRASE_CORPUS)
    sents.extend(lexicon.PARAPHRASE_CORPUS)   # peso dobrado: é a fala "do dia a dia"
    sents.extend(EXTRA_PARAPHRASES)
    sents.extend(EXTRA_PARAPHRASES)
    # cada conceito de prateleira: seus jeitos de falar juntos com o nome da prateleira e as etapas/tipos dele
    for c in CONCEPTS:
        steps = " ".join(cat.steps.get(st, st) for st in c.steps)
        for k in range(0, len(c.phrases), 4):
            sents.append(f"{' '.join(c.phrases[k:k + 4])} {c.label} {c.shelf} {steps} {' '.join(c.types)}")
    return [tokens(s) for s in sents if s.strip()]


class WordVectors:
    def __init__(self, vocab: list[str], vecs: np.ndarray, idf: np.ndarray):
        self.vocab = vocab
        self.index = {w: i for i, w in enumerate(vocab)}
        self.vecs = vecs
        self.idf = idf

    def __contains__(self, w: str) -> bool:
        return w in self.index

    def vector(self, toks: list[str]) -> np.ndarray:
        """Média ponderada por idf dos vetores das palavras conhecidas, normalizada. Vetor zero se nenhuma é conhecida."""
        acc = np.zeros(self.vecs.shape[1], dtype=np.float64)
        n = 0
        for t in toks:
            i = self.index.get(t)
            if i is None:
                continue
            acc += self.idf[i] * self.vecs[i]
            n += 1
        norm = np.linalg.norm(acc)
        return acc / norm if norm > 0 else acc

    def neighbors(self, word: str, k: int = 8) -> list[tuple[str, float]]:
        i = self.index.get(stem(word))
        if i is None:
            return []
        v = self.vecs[i]
        sims = self.vecs @ v / (np.linalg.norm(self.vecs, axis=1) * np.linalg.norm(v) + 1e-12)
        order = np.argsort(-sims)
        return [(self.vocab[j], float(sims[j])) for j in order if j != i][:k]


def train(sentences: list[list[str]], dim: int = DIM, window: int = WINDOW) -> WordVectors:
    counts = Counter(t for s in sentences for t in s)
    vocab = sorted(counts)
    idx = {w: i for i, w in enumerate(vocab)}
    V = len(vocab)
    C = np.zeros((V, V), dtype=np.float64)
    for s in sentences:
        ids = [idx[t] for t in s]
        for a, wa in enumerate(ids):
            for b in range(max(0, a - window), min(len(ids), a + window + 1)):
                if a == b:
                    continue
                C[wa, ids[b]] += 1.0 / abs(a - b)
    total = C.sum()
    pw = C.sum(axis=1) / total
    pc = C.sum(axis=0) ** SMOOTH
    pc = pc / pc.sum()
    with np.errstate(divide="ignore", invalid="ignore"):
        pmi = np.log((C / total) / (pw[:, None] * pc[None, :]))
    ppmi = np.where(np.isfinite(pmi) & (pmi > 0), pmi, 0.0)
    U, S, _ = np.linalg.svd(ppmi, full_matrices=False)
    d = min(dim, len(S))
    vecs = U[:, :d] * np.sqrt(S[:d])
    # sinal determinístico: o maior componente de cada eixo fica positivo
    sign = np.sign(vecs[np.abs(vecs).argmax(axis=0), np.arange(d)])
    sign[sign == 0] = 1
    vecs = vecs * sign
    # idf por frase (palavras raras pesam mais; palavras em todo lugar, menos)
    df = Counter()
    for s in sentences:
        for t in set(s):
            df[t] += 1
    n = len(sentences)
    idf = np.array([np.log((n + 1) / (df[w] + 1)) + 1.0 for w in vocab])
    return WordVectors(vocab, vecs.astype(np.float64), idf)


def fingerprint(sentences: list[list[str]]) -> str:
    h = hashlib.sha256()
    for s in sentences:
        h.update((" ".join(s) + "\n").encode())
    return h.hexdigest()[:16]


def save(wv: WordVectors, sentences: list[list[str]], path: Path | None = None) -> Path:
    path = path or ARTIFACTS / "embeddings.npz"
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, vocab=np.array(wv.vocab), vecs=wv.vecs.astype(np.float32), idf=wv.idf.astype(np.float32))
    manifest = {"dim": int(wv.vecs.shape[1]), "vocab": len(wv.vocab), "sentences": len(sentences),
                "tokens": int(sum(len(s) for s in sentences)), "corpusSha": fingerprint(sentences),
                "window": WINDOW, "smooth": SMOOTH, "method": "PPMI + SVD (do zero, sem modelo externo)"}
    (path.parent / "embeddings.manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return path


def load(path: Path | None = None) -> WordVectors | None:
    path = path or ARTIFACTS / "embeddings.npz"
    if not path.exists():
        return None
    z = np.load(path, allow_pickle=False)
    return WordVectors([str(x) for x in z["vocab"]], z["vecs"].astype(np.float64), z["idf"].astype(np.float64))
