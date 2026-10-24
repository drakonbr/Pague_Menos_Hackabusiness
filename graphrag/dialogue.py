"""Motor de conversa: junta entendimento, segurança, recuperação, compositor e texto de resposta.

Sem estado no servidor: o cliente devolve o `context` de cada resposta na próxima mensagem.
Privacidade: o motor NÃO lê dados da pessoa (persona.json fica no aparelho); o contexto guarda só ids e preferências.
Medicamento é busca como outra qualquer (doc 16): sem bloqueio e sem mandar procurar médico ou farmacêutico.
"""
from __future__ import annotations

import hashlib
from collections import Counter
import json
import logging
import os
import re
import threading

from . import embed
from .composer import Composer, build_ctx, list_pt
from .concepts import MED_MISSING, MED_SHELF
from .data import Catalog, load_catalog
from .lexicon import STATE_WORDS, canon_state
from .graph import KnowledgeGraph, build_graph
from .ingest import IngestReport, ingest_records, load_catalog_with_delta, write_delta
from .llm import Reader, phrase
from .ontology import validate_graph
from .nlu import ActClassifier, Understander, Understanding, _MED, _PREGNANT
from .nlu_corpus import TRAIN
from .retrieval import Retriever, load_weights
from .rewrite import rewrite_query
from .safety import assess
from .scope import MAX_LIST, VOTE_REL, Scope, ScopeResolver
from .spell import COMMON, Speller
from .text import STOPWORDS, money, norm, raw_tokens

SKIN_OPTIONS = [{"value": v, "label": l} for v, l in
                [("oleosa", "Oleosa"), ("mista", "Mista"), ("seca", "Seca"), ("normal", "Normal"), ("sensível", "Sensível")]]
DERMO_GOALS = {"acne", "manchas", "skincare_basico", "protecao_solar", "anti_idade", "pele_sensivel", "oleosidade"}
RERANK_LAMBDA = 0.9           # medido em eval/rerank_eval.py: variedade um pouco maior sem perder relevância
BARE_TERM_ACTS = {"trocar_item", "pergunta_produto", "similar"}
# o classificador de atos às vezes lê "quero dormir melhor" como negação e "suor demais na axila" como frete; se a frase
# fala de algo que existe (ou falta) na prateleira e não aponta para um kit já mostrado, é busca.
SOFT_ACTS = {"negacao", "afirmacao", "saudacao", "agradecimento", "ajuda"}
CTX_ACTS = {"trocar_item", "pergunta_produto", "similar", "entrega_frete"}
DELIVERY_CUE = re.compile(r"\b(frete|entreg\w*|prazo|retir\w*|chega\w*|receb\w*|envio|enviar)\b")
POINTING_CUE = re.compile(r"\?|\b(troc\w*|mud\w*|substitu\w*|outr[oa]s?|ess[ea]s?(?!\s+(?:dias|tempos?|semanas|meses|ultimos))|est[ea]s?|isso|isto|aquel\w+|"
                          r"parecid\w*|similar\w*|equival\w*)\b")
TIER_NAME = {"economico": "Econômico", "essencial": "Essencial", "completo": "Completo"}
# a frase fala de remédio ou sintoma: se nada no catálogo atende, a resposta é só MED_MISSING (doc 16)
MED_CUE = re.compile(r"\b(remedio|remedios|medicamento|medicamentos|medicacao|comprimido|comprimidos|capsula|xarope|"
                     r"pomada|gotas|tomar|tomo|dor|dores|doendo|sintoma|sintomas|estou com|to com)\b")
# sinais de que a pessoa pede alívio ou remédio (sem "tô com", que aparece em qualquer queixa): só com eles a conferência
# pode virar lista de remédios sobre uma resposta que não era de saúde
HEALTH_CUE = re.compile(r"\b(remedio|remedios|medicamento|medicamentos|medicacao|comprimido|comprimidos|capsula|xarope|pomada|gotas|"
                        r"dor|dores|doendo|doi|sintoma|sintomas|febre|tosse|enjoo|azia|nausea)\b")   # sem "tomar": "tomo sol" não é remédio
log = logging.getLogger("graphrag.rag")
# palavras de fala corrente que o catálogo não tem e que não dizem o que a pessoa quer: não contam como "não entendi"
FILLER = frozenset("fico fica ficou fique ficar vive vivo anda andou tomo sao pras pros tao tava tamos estao sinto sentindo seja parece parecem deixe deixa leve".split())
NEGATORS_RAG = frozenset("nao nem sem nunca jamais menos nada nenhum nenhuma".split())
CLAUSE_BREAK = frozenset("e mas porem ou".split())      # a negação não atravessa uma conjunção ("sem brilho E melada")
GENERIC_GOALS = frozenset({"skincare_basico"})            # objetivo "de reserva": o grafo caiu nele sem pista melhor
GRAPH_KEYS = ("goals", "primaryGoal", "budgetCents", "skinType", "preferences", "pregnancy")
# "não", "não, obrigado", "não gostei": o grafo entendeu (negação); só chama a DeepSeek se sobrar conteúdo
COURTESY = {"nao", "obrigado", "obrigada", "valeu", "gostei", "curti", "quero", "nada", "isso", "esse", "essa", "por", "favor",
            "agora", "ainda", "mais", "assim", "ok", "beleza", "tudo", "bem", "nem", "e", "o", "a", "de", "pra", "para",
            "era", "so", "mesmo", "sim", "certo", "entendi"}
ADJUST_CUE = re.compile(r"\b(tir\w*|sem|troc\w*|remov\w*|mud\w*|menos|nada de)\b")


class Engine:
    def __init__(self, cat: Catalog, graph: KnowledgeGraph, wv, clf: ActClassifier, weights: dict | None = None, llm=None):
        self.cat, self.graph, self.wv, self.clf = cat, graph, wv, clf
        self.rag = Reader(cat, llm) if llm else None        # DeepSeek só quando o grafo não entende (#34)
        # #42: o que vale quando o pedido não traz allowExternal (cliente antigo). Em produção: RAG_EXTERNAL_DEFAULT=off
        self.external_default = os.environ.get("RAG_EXTERNAL_DEFAULT", "on").strip().lower() != "off"
        self.stats: Counter = Counter()                     # chamadas por motivo, para medir o custo (/v1/health)
        self._stats_lock = threading.Lock()
        self.weights = weights or load_weights()
        self.nlu = Understander(cat, wv, clf)
        self.ret = Retriever(cat, graph, wv, self.weights)
        self.comp = Composer(cat)
        self.speller = Speller(cat)
        self.scope = ScopeResolver(cat, self.speller.catalog_vocab)
        self.store_names = {s["id"]: s["name"] for s in cat.stores}

    # ------------------------------------------------------------ construção
    @classmethod
    def build(cls, use_artifacts: bool = True, delta_path=None, llm=None) -> "Engine":
        """Catálogo-base + delta de produtos ingeridos (graphrag/artifacts/delta_products.json, se existir)."""
        cat, delta = load_catalog_with_delta(delta_path)
        sents = embed.build_corpus(cat)
        wv = embed.load() if use_artifacts else None
        # com delta, o vocabulário treinado pode não conhecer as palavras novas: mantém os vetores (o produto novo usa
        # as palavras que existem) em vez de retreinar a cada subida. `python -m graphrag.train` incorpora as novas.
        if wv is None or (delta is None and len(wv.vocab) != len({t for s in sents for t in s})):
            wv = embed.train(sents)
        clf = (ActClassifier.load() if use_artifacts else None) or ActClassifier().fit(TRAIN)
        return cls(cat, build_graph(cat), wv, clf, llm=llm)

    def ingest(self, records: list[dict], persist: bool = True, delta_path=None) -> IngestReport:
        """Ingestão incremental em um motor em execução: valida, resolve entidades, atualiza catálogo e grafo e refaz os
        índices. Os vetores de palavras não são retreinados. Troca os componentes só no fim (consultas em andamento
        continuam coerentes)."""
        rep = ingest_records(self.cat, records, set(self.wv.vocab))
        if rep.changed:
            graph = build_graph(self.cat)
            errs = validate_graph(graph.g)
            assert not errs, f"ingestão deixou o grafo fora da ontologia: {errs[:3]}"
            ret, comp = Retriever(self.cat, graph, self.wv, self.weights), Composer(self.cat)
            self.speller = Speller(self.cat)
            self.scope = ScopeResolver(self.cat, self.speller.catalog_vocab)
            nlu = Understander(self.cat, self.wv, self.clf)
            self.graph, self.ret, self.comp, self.nlu = graph, ret, comp, nlu
            if persist:
                write_delta(rep.applied, delta_path)
        return rep

    # ------------------------------------------------------------ utilidades
    @staticmethod
    def _rid(req: dict) -> str:
        return "r_" + hashlib.sha1(json.dumps(req, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:6]

    def _missing(self, intent: dict) -> list[str]:
        m = []
        if not intent.get("skinType") and intent.get("primaryGoal") in DERMO_GOALS:
            m.append("skinType")
        if intent.get("budgetCents") is None:
            m.append("budget")
        return m

    def _intent_from(self, u: Understanding, req: dict, prev: dict | None) -> dict:
        intent = {"goals": u.goals, "primaryGoal": u.primary_goal,
                  "budgetCents": u.budget_cents, "skinType": u.skin, "preferences": list(u.preferences),
                  "pregnancy": u.pregnancy, "storeId": req.get("storeId") if "storeId" in req else (prev or {}).get("storeId")}
        if "budgetCents" in req:
            intent["budgetCents"] = req["budgetCents"]
        if "skinType" in req:
            intent["skinType"] = req["skinType"]
        if req.get("preferences"):
            intent["preferences"] = sorted(set(intent["preferences"]) | set(req["preferences"]))
        intent["missing"] = self._missing(intent)
        return intent

    def _rehydrate(self, compact: list[dict], ctx) -> list[dict]:
        kits = []
        for k in compact or []:
            items = []
            for it in k["items"]:
                p = self.cat.by_id.get(it["productId"])
                if p:
                    items.append({"step": it["step"], "product": p, "reason": it.get("reason", ""),
                                  "alternativesCount": 0})
            if items:
                kit = {"id": k["id"], "tier": k["tier"], "title": k["title"], "goal": k["goal"], "items": items,
                       "storeId": k.get("storeId"), "rationale": k.get("rationale", "")}
                kits.append(self.comp._totals(kit, ctx))
        return kits

    @staticmethod
    def _compact(kits: list[dict]) -> list[dict]:
        return [{"id": k["id"], "tier": k["tier"], "title": k["title"], "goal": k["goal"], "storeId": k.get("storeId"),
                 "rationale": k.get("rationale", ""), "totalCents": k["totalCents"],
                 "items": [{"step": i["step"], "productId": i["product"]["id"]} for i in k["items"]]} for k in kits]

    def _focus_kit(self, kits: list[dict], tier: str | None) -> dict | None:
        if not kits:
            return None
        for t in (tier, "essencial"):
            for k in kits:
                if k["tier"] == t:
                    return k
        return kits[0]

    def _out(self, req, query, safety, intent, act, reply, *, kits_status="not_applicable", kits=None, closest=None,
             products=None, notes=None, suggestions=None, action=None, ctx_out=None, clarification=None,
             catalog_notice=None, scope_info=None) -> dict:
        res = {"requestId": self._rid(req), "query": query, "safety": safety, "intent": intent, "act": act,
               "kitsStatus": kits_status, "kits": kits or [], "closestKit": closest, "products": products or [],
               "notes": notes or [], "reply": reply, "suggestions": (suggestions or [])[:5],
               "action": action or {"type": "none"}, "context": ctx_out or {}}
        if clarification:
            res["clarification"] = clarification
        if catalog_notice:
            res["catalogNotice"] = catalog_notice
        if scope_info:
            res["scope"] = scope_info
        return res

    def _ctx_out(self, intent, u_req, excluded, requested, kits, act, turn, focus_tier=None, focus_product=None, scope=None):
        c = {"intent": intent, "requested": requested, "excluded": excluded, "kits": self._compact(kits),
             "lastAct": act, "turn": turn + 1}
        if scope is not None and scope.kind != "unknown":
            c["scope"] = {"kind": scope.kind, "steps": sorted(scope.steps), "concerns": sorted(scope.concerns),
                          "ingredients": list(scope.ingredients), "concepts": [c.id for c in scope.concept_filters]}
        if focus_tier:
            c["focusTier"] = focus_tier
        if focus_product:
            c["focusProductId"] = focus_product
        return c

    # ------------------------------------------------------------ entrada principal
    def search(self, req: dict, rag: bool = True) -> dict:
        """rag=False: nunca chama a DeepSeek (o replay do histórico do chat usa assim, para ser uma chamada por busca)."""
        orig_query = req.get("query", "")
        query, fixes = self.speller.fix(orig_query)
        res = self._search(req, query, orig_query)
        miss = res.pop("_miss", None)
        # #42: só vai à DeepSeek com allowExternal exatamente true (ou ausente, se o padrão for ligado); 0, "false" e null desligam
        usable = rag and self.rag and req.get("allowExternal", self.external_default) is True
        words: list[str] = []
        if usable and not miss and res.get("act") == "busca":
            words = self._unknown(query, fixes)           # o grafo respondeu, mas viu palavra que não conhece: confere
            miss = "fraco" if words else None
        if miss and usable:
            res = self._rag(req, orig_query, res, miss, words)
        res["query"] = orig_query
        if fixes and canon_state(norm(orig_query)) == norm(orig_query):      # texto reescrito pela regra do corpo não é "correção"
            res["correctedQuery"] = query
        return res

    def _count(self, key: str) -> None:
        with self._stats_lock:
            self.stats[key] += 1

    def _unknown(self, fixed_query: str, fixes: list) -> list[str]:
        """Palavras que fazem o grafo duvidar de si: de conteúdo e desconhecidas do catálogo, ou que o corretor trocou de um
        jeito suspeito (muda a 1ª letra ou o tamanho: "fanho" virou "banho"; o erro de digitação comum não conta).
        Só dispara a conferência; quem troca a resposta é _rag, e só se a DeepSeek explicar uma delas com algo que o
        grafo não cobriu."""
        words = [t for t in raw_tokens(fixed_query) if len(t) >= 4 and t not in STOPWORDS and t not in COMMON and t not in FILLER
                 and t not in STATE_WORDS]
        doubt = [a for a, b in fixes if a[:1] != b[:1] or abs(len(a) - len(b)) >= 2]
        return doubt + [t for t in words if t not in self.speller.vocab]

    def _covered(self, res: dict, field: str, ident: str) -> bool:
        """O que o grafo respondeu já cobre este id do catálogo? Escopo largo (mais de 3 etapas) não cobre etapa nenhuma."""
        sc = (res.get("context") or {}).get("scope") or {}
        goals = set(res["intent"].get("goals") or []) | ({res["intent"].get("primaryGoal")} - {None})
        concerns = set(sc.get("concerns", [])) | {c for g in goals for c in self.cat.goal_by_id[g]["concerns"]}
        steps = set(sc.get("steps", [])) if len(sc.get("steps", [])) <= 3 else set()
        if field == "objetivos":
            return ident in goals or bool(set(self.cat.goal_by_id[ident]["concerns"]) & concerns)
        if field == "preocupacoes":
            return ident in concerns
        if field == "etapas":
            return ident in steps
        return ident in set(sc.get("ingredients", []))

    @staticmethod
    def _negated(text: str, word: str) -> bool:
        toks = re.findall(r"[a-z0-9]+", norm(text))
        for k, t in enumerate(toks):
            if t != word:
                continue
            for b in range(k - 1, max(-1, k - 6), -1):        # olha até 5 palavras para trás, parando na conjunção
                if toks[b] in CLAUSE_BREAK:
                    break
                if toks[b] in NEGATORS_RAG:
                    return True
        return False

    def _label(self, field: str, ident: str) -> str:
        c = self.cat
        return {"objetivos": lambda: c.goal_by_id[ident]["label"].lower(), "preocupacoes": lambda: c.concerns[ident],
                "etapas": lambda: c.steps[ident].lower(), "ingredientes": lambda: c.ingredients[ident]["name"].lower()}[field]()

    def _substitute(self, text: str, explained: list) -> str:
        t = norm(text)
        for w, field, ident in explained:
            t = re.sub(rf"\b{re.escape(w)}\b", self._label(field, ident), t)
        return t

    @staticmethod
    def _health_answer(res: dict) -> bool:
        return any(_health(p) for p in res.get("products", []))

    def _rag(self, req: dict, text: str, res: dict, miss: str, words: list[str] | None = None) -> dict:
        """O grafo não entendeu: a DeepSeek traduz o pedido para ids do catálogo, montamos uma frase só com rótulos do
        catálogo e o grafo busca de novo (kits, regras e conversa continuam os do motor). Nada na tela diz que foi a
        DeepSeek; a frase entendida só vai para o registro do servidor."""
        cin = req.get("context") or {}
        conv = self._conv_labels(cin) if (cin.get("kits") or cin.get("scope")) else ""
        p = self.rag.read(text, conv, words or ())
        if p is None:
            return res                                   # sem resposta da API: fica a do grafo
        self._count(miss)
        if miss == "fraco":
            # o grafo respondeu: só muda se a DeepSeek EXPLICAR uma palavra desconhecida com algo do catálogo que o grafo não
            # cobriu. Sem explicação (palavra de enchimento) ou já coberto: vale o grafo, intacto.
            # palavra negada ("que NÃO fique melado", "sem cheiro") descreve o que a pessoa não quer: nunca vira pedido
            ex = [(w, f, i) for w, f, i in p["explicadas"] if not self._negated(text, w)]
            if not ex or all(self._covered(res, f, i) for _w, f, i in ex):
                self._count("confirmou")
                return res
        if miss == "fraco":
            # a nova busca usa SÓ o que a DeepSeek explicou, não toda a leitura dela. Dois jeitos, cada um onde funciona:
            # explicou um OBJETIVO do catálogo ("melada" = oleosidade): busca pelo objetivo, que dá o peso certo ao conceito;
            # explicou outra coisa ("resseque" = ressecamento): troca a palavra na frase e mantém o resto ("xampu", "cabelo")
            # o caminho do objetivo descarta o resto da frase: só quando o grafo estava no escuro (objetivo de reserva, voto fraco)
            sc = (res.get("context") or {}).get("scope") or {}
            dark = res["intent"].get("primaryGoal") in GENERIC_GOALS or sc.get("kind") in ("vote", "unknown", None)
            if dark and any(f == "objetivos" or i in self.cat.goal_by_id for _w, f, i in ex):
                only = {**p, **{f: [i for _w, g, i in ex if g == f] for f in ("objetivos", "preocupacoes", "etapas", "ingredientes")}}
                q2 = phrase(self.cat, only, adjust=False)
            else:
                q2 = self.speller.fix(self._substitute(text, ex))[0]
        else:
            q2 = phrase(self.cat, p, adjust=bool(conv))
        if q2 and _PREGNANT.search(norm(text)):
            q2 += ", estou grávida"                      # gestação vale na nova busca: aviso e filtros de sempre (K11)
        if q2:
            r2 = self._search({**req, "query": q2}, q2, q2)
            g2 = r2["intent"].get("primaryGoal")              # None quando virou lista (objetivo de remédio, #40)
            diverged = miss != "fraco" and bool(p["objetivos"]) and not conv and g2 is not None and g2 not in p["objetivos"]
            # trava: a conferência nunca vira lista de remédios sobre uma resposta que não era de saúde, a menos que a
            # pessoa fale de dor, remédio ou sintoma ("corpo pesado e cansado" não é pedido de anti-inflamatório)
            unsafe = (miss == "fraco" and self._health_answer(r2) and not self._health_answer(res)
                      and not HEALTH_CUE.search(norm(text)))
            if unsafe:
                self._count("recusou")
            if not r2.pop("_miss", None) and not diverged and not unsafe:
                log.info("rag entendeu (%s): %s", miss, q2)
                same = ([p["id"] for p in r2["products"]], r2["intent"].get("primaryGoal")) == ([p["id"] for p in res["products"]], res["intent"].get("primaryGoal"))
                self._count("igual" if same else "trocou")
                r2["rag"] = True
                return r2
        if miss == "med_shelf":                          # só "remédio" genérico e nada no catálogo serve
            return self._med_missing(req, text, res["safety"], res["intent"], int(cin.get("turn", 0)))
        return res

    def _conv_labels(self, cin: dict) -> str:
        """O que a conversa já sabe, só em rótulos do catálogo (nada do que a pessoa digitou)."""
        i, parts = cin.get("intent") or {}, []
        if i.get("primaryGoal") in self.cat.goal_by_id:
            parts.append("objetivo: " + self.cat.goal_by_id[i["primaryGoal"]]["label"])
        if i.get("skinType"):
            parts.append("pele: " + i["skinType"])
        if i.get("budgetCents"):
            parts.append(f"orçamento: até R$ {i['budgetCents'] // 100}")
        if i.get("preferences"):
            parts.append("preferências: " + ", ".join(i["preferences"]))
        ex = [self.cat.ingredients[x]["name"] for x in cin.get("excluded", []) if x in self.cat.ingredients]
        if ex:
            parts.append("evitar: " + ", ".join(ex))
        return "; ".join(parts) or "itens já mostrados"

    def _search(self, req: dict, query: str, orig_query: str = "") -> dict:
        cin = req.get("context") or {}
        prev_intent = cin.get("intent")
        has_ctx = bool(prev_intent and (cin.get("kits") or prev_intent.get("primaryGoal") or cin.get("scope")))
        turn = int(cin.get("turn", 0))
        u = self.nlu.understand(query, has_context=has_ctx)
        act = u.act
        # termo solto na barra ("ômega 3", "sabonete", "sérum"): sem conversa anterior e sem pista de que aponta para algo
        # já mostrado (troque, esse, ?...), não há o que trocar nem sobre o que perguntar: é uma busca nova.
        if (not has_ctx and act in BARE_TERM_ACTS and not POINTING_CUE.search(norm(query))
                and len(raw_tokens(query)) <= 5):
            act = u.act = "busca"
        if act in SOFT_ACTS | CTX_ACTS and len(raw_tokens(query)) <= 18 and not (has_ctx and u.product_ids):
            nq = norm(query)
            heard = self.scope.match(query) or u.has_domain_signal
            if heard and (act in SOFT_ACTS or (not has_ctx and not POINTING_CUE.search(nq.replace("?", ""))
                                                and not (act == "entrega_frete" and DELIVERY_CUE.search(nq)))):
                act = u.act = "busca"
        if act == "repor_medicamento" and not _MED.search(norm(query)) and (self.scope.match(query) or u.has_domain_signal):
            act = u.act = "busca"                       # "acabar com os cravos" não é reposição de remédio
        blank_intent = {"goals": [], "primaryGoal": None, "budgetCents": None, "skinType": None, "preferences": [],
                        "pregnancy": False, "storeId": req.get("storeId"), "missing": []}
        carry = prev_intent or blank_intent
        if "storeId" in req:
            carry = {**carry, "storeId": req["storeId"]}

        # --- segurança primeiro
        # a segurança lê o texto ORIGINAL também: o corretor nunca pode transformar um termo de saúde em outra palavra
        safety = assess(orig_query or query, u.pregnancy, u.primary_goal, refill_flow=(act == "repor_medicamento"))
        if safety["decision"] == "allow" and orig_query and orig_query != query:
            safety = assess(query, u.pregnancy, u.primary_goal, refill_flow=(act == "repor_medicamento"))

        handler = {
            "saudacao": self._greet, "agradecimento": self._thanks, "ajuda": self._help, "negacao": self._deny,
            "reiniciar": self._restart, "afirmacao": self._affirm, "repor_medicamento": self._refill,
            "entrega_frete": self._delivery, "similar": self._similar_chat, "pergunta_produto": self._ask_product,
            "trocar_item": self._swap_chat, "refinar": self._refine,
        }.get(act)
        res = handler(req, query, u, safety, cin, carry, turn) if handler else \
            self._search_new(req, query, u, safety, cin, carry, turn)
        if (not res.get("_miss") and act in ("pergunta_produto", "similar", "trocar_item") and not has_ctx
                and not res.get("products") and not res.get("kits")):
            res["_miss"] = "busca"                       # pergunta sobre um produto que não existe na conversa: o grafo não entendeu
        res["rewrittenQuery"] = rewrite_query(self.cat, u, res)
        return res

    # ------------------------------------------------------------ conversa simples
    def _basic(self, req, query, safety, carry, cin, turn, act, reply, suggestions, action=None, reset=False):
        ctx = {"intent": carry, "kits": [], "lastAct": act, "turn": turn + 1} if reset else (
            {**cin, "lastAct": act, "turn": turn + 1} if cin else {"intent": carry, "kits": [], "lastAct": act, "turn": turn + 1})
        return self._out(req, query, safety, carry, act, reply, suggestions=suggestions, action=action, ctx_out=ctx)

    def _greet(self, req, query, u, safety, cin, carry, turn):
        return self._basic(req, query, safety, carry, cin, turn, "saudacao",
                           "Oi! Eu encontro remédios e monto kits de cuidados com a pele, suplementos e higiene, "
                           "e ajudo a repor o que você já usa. Me conte o que você procura e, se quiser, quanto pretende gastar.",
                           ["Remédio para dor de cabeça", "Kit de suplementos", "Pele com manchas até R$ 150", "Repor meus medicamentos"])

    def _thanks(self, req, query, u, safety, cin, carry, turn):
        return self._basic(req, query, safety, carry, cin, turn, "agradecimento",
                           "Por nada! Se quiser ajustar o kit, trocar algum item ou ver o total com entrega, é só pedir.",
                           ["Total com entrega", "Mais barato", "Trocar um item"])

    def _help(self, req, query, u, safety, cin, carry, turn):
        return self._basic(req, query, safety, carry, cin, turn, "ajuda",
                           "Posso: achar remédios pelo sintoma ou pelo nome (ex.: dor de cabeça, dipirona); montar 3 opções de "
                           "kit (Econômico, Essencial e Completo) de pele, suplementos ou higiene a partir do que você escreve; ajustar por preço, tipo de pele "
                           "ou preferência; trocar um item; mostrar o total com frete e a retirada mais próxima; e repor os "
                           "medicamentos de uso contínuo que você já usa.",
                           ["Remédio para gripe", "Kit de suplementos", "Pele oleosa até R$ 100", "Repor meus medicamentos"])

    def _deny(self, req, query, u, safety, cin, carry, turn):
        res = self._basic(req, query, safety, carry, cin, turn, "negacao",
                          "Tudo bem. Quer ver outra opção, mudar o orçamento ou começar uma busca nova?",
                          ["Mais barato", "Outra opção", "Recomeçar"])
        rest = [t for t in raw_tokens(norm(query)) if t not in COURTESY]
        if (cin.get("kits") or cin.get("scope")) and rest:
            res["_miss"] = "ajuste"                      # "não quero ácido" depois dos kits é ajuste que o grafo não leu
        return res

    def _restart(self, req, query, u, safety, cin, carry, turn):
        blank = {"goals": [], "primaryGoal": None, "budgetCents": None, "skinType": None, "preferences": [],
                 "pregnancy": False, "storeId": carry.get("storeId"), "missing": []}
        return self._basic(req, query, safety, blank, {}, 0, "reiniciar",
                           "Pronto, recomeçamos. O que você procura hoje?",
                           ["Kit de suplementos", "Higiene premium", "Rotina anti idade"], reset=True)

    def _affirm(self, req, query, u, safety, cin, carry, turn):
        ctx = build_ctx(self.cat, carry, cin.get("requested", []), cin.get("excluded", []))
        kits = self._rehydrate(cin.get("kits"), ctx) if ctx else []
        kit = self._focus_kit(kits, u.tier or cin.get("focusTier"))
        if not kit:
            return self._basic(req, query, safety, carry, cin, turn, "afirmacao",
                               "Combinado. O que você gostaria de ver primeiro?", ["Kit de suplementos", "Higiene premium"])
        return self._out(req, query, safety, carry, "afirmacao",
                         f"Ótimo! Separei o kit {TIER_NAME[kit['tier']]} ({money(kit['totalCents'])}). "
                         "Toque em “Adicionar à cesta” para seguir e escolher a entrega.",
                         kits_status="ok", kits=kits, suggestions=["Total com entrega", "Trocar um item"],
                         action={"type": "add_kit_to_cart", "tier": kit["tier"], "kitId": kit["id"]},
                         ctx_out={**cin, "lastAct": "afirmacao", "turn": turn + 1, "focusTier": kit["tier"]})

    # ------------------------------------------------------------ reposição (sem recomendar)
    def _refill(self, req, query, u, safety, cin, carry, turn):
        return self._out(req, query, safety, carry, "repor_medicamento",
                         "Abri a sua reposição de uso contínuo. Confira as quantidades que restam, escolha retirar na loja ou "
                         "entrega expressa e, se algum item estiver em falta na loja mais próxima, posso mostrar um equivalente "
                         "disponível, com o mesmo princípio ativo e a mesma dose.",
                         suggestions=["Tem equivalente disponível?", "Qual a entrega mais rápida?", "Total com frete"],
                         action={"type": "open_refill"},
                         ctx_out={**cin, "lastAct": "repor_medicamento", "turn": turn + 1} if cin else
                         {"intent": carry, "kits": [], "lastAct": "repor_medicamento", "turn": turn + 1})

    # ------------------------------------------------------------ busca nova
    def _search_new(self, req, query, u: Understanding, safety, cin, carry, turn):
        rel = self.ret.score(u, query)
        scope = self.scope.resolve(u, query, rel)
        if scope.kind == "unknown":
            return self._not_found(req, query, safety, carry, cin, turn)
        intent = self._intent_from(u, req, None)
        if "storeId" not in req:
            intent["storeId"] = carry.get("storeId")
        if scope.kind == "absent":
            return self._absent(req, query, u, safety, intent, scope, rel, turn)
        if not self._kits_ok(scope, intent):
            return self._shelf_list(req, query, u, safety, intent, scope, rel, turn)

        ctx = build_ctx(self.cat, intent, u.requested_ingredients, u.excluded_ingredients, rel, self.weights["ret_in_kit"])
        rid = self._rid(req)
        comp = self.comp.compose(ctx, rid)
        prods = self._scope_products(scope, intent, u, rel, ctx=ctx)
        clar = None
        if "skinType" in intent["missing"]:
            clar = {"id": "skinType", "question": "Como é a sua pele?", "options": SKIN_OPTIONS}
        reply = self._reply_kits(comp, intent, ctx, u)
        sug = self._suggest_after(comp, intent)
        notice = self._notice(scope)
        if notice and not notice.get("med"):
            reply = notice["message"] + " " + reply
        if notice and notice.get("med"):
            reply = MED_MISSING + " " + reply
        if not comp["kits"] and comp["status"] == "not_applicable":
            # nenhum kit fecha com essas preferências: em vez de uma lista solta (que misturava outras etapas), mostra só
            # os produtos das etapas desse objetivo que respeitam o pedido e diz com clareza o que aconteceu.
            steps = sorted({s for g in intent["goals"] for s in self.cat.goal_by_id[g]["required_steps"]
                            + self.cat.goal_by_id[g]["optional_steps"]})
            focused = self.comp.rank_products(ctx, steps, rel, limit=MAX_LIST)
            if focused:
                reply = (f"Não consegui fechar um kit completo com essas preferências, mas encontrei {len(focused)} "
                         "produtos que combinam com o seu pedido. Quer ver, ou prefere flexibilizar alguma preferência?")
                sug = ["Montar um kit com isso", "Mais barato", "Tirar uma preferência"]
                return self._out(req, query, safety, intent, "busca", reply, kits_status=comp["status"], products=focused,
                                 notes=[], suggestions=sug, action={"type": "show_products"}, clarification=clar,
                                 catalog_notice=notice, scope_info=self._scope_info(scope, len(focused)),
                                 ctx_out=self._ctx_out(intent, req, u.excluded_ingredients, u.requested_ingredients, [],
                                                       "busca", turn, scope=scope))
        return self._out(req, query, safety, intent, "busca", reply, kits_status=comp["status"], kits=comp["kits"],
                         closest=comp["closestKit"], products=prods, notes=comp["notes"], suggestions=sug,
                         action={"type": "show_kits"} if comp["kits"] else None, clarification=clar,
                         catalog_notice=notice, scope_info=self._scope_info(scope, len(prods)),
                         ctx_out=self._ctx_out(intent, req, u.excluded_ingredients, u.requested_ingredients, comp["kits"],
                                               "busca", turn, scope=scope))

    # ---- escopo, lista e avisos
    def _kits_ok(self, scope: Scope, intent: dict) -> bool:
        """Kit só quando há objetivo e a busca cobre o objetivo inteiro (ou fala de preocupação/ingrediente).
        'Higiene bucal' é uma etapa de um objetivo de quatro: mostra os itens, sem kit forçado."""
        goal = intent.get("primaryGoal")
        if not goal or goal not in self.cat.goal_by_id or not self.comp.kit_possible(goal):
            return False                                 # K13: objetivo de remédio mostra só a lista avulsa
        if scope.kind in ("concern", "goal", "ingredient"):
            return True
        if scope.kind == "shelf":
            return set(self.cat.goal_by_id[goal]["required_steps"]) <= scope.steps
        return False

    def _scope_products(self, scope: Scope, intent: dict, u: Understanding, rel: dict, ctx=None, limit: int = MAX_LIST) -> list[dict]:
        probe = ctx or build_probe(intent, u)
        cands = [p for p in self.comp.pool if self.scope.in_scope(scope, p)]
        strict = [p for p in cands if self.comp.base_eligible(p, probe, False)]
        use = strict or [p for p in cands if self.comp.base_eligible(p, probe, True)]
        if scope.kind == "shelf" and scope.ingredients:
            # "sérum de vitamina c": dentro da prateleira, quem tem o ingrediente; se ninguém tem, a prateleira toda
            use = [p for p in use if self.scope.has_ing(p, scope.ingredients)] or use
        if scope.kind in ("vote", "goal") and use:
            # sem enchimento: só entra o que tem nota perto da do melhor item desta prateleira
            top = max(rel.get(p["id"], 0.0) for p in use)
            use = [p for p in use if rel.get(p["id"], 0.0) >= VOTE_REL * top]

        def spec(p):
            return max((2 if c.types else 1 for c in scope.concept_filters
                        if self.scope.in_scope(Scope("shelf", concept_filters=[c], steps=set(c.steps)), p)), default=0)

        def key(p):
            s = self.comp.score(p, ctx) if ctx else 0.0
            return (p["id"] not in u.product_ids, -spec(p), -(10 * rel.get(p["id"], 0.0) + s), p["priceCents"], p["id"])
        return sorted(use, key=key)[:limit]

    def _scope_label(self, scope: Scope) -> str:
        if scope.shelves:
            return list_pt(scope.shelves[:3])
        if scope.kind == "concern":
            return list_pt([self.cat.concerns.get(c, c) for c in sorted(scope.concerns)][:3]) or "cuidados com a pele"
        if scope.kind == "ingredient":
            return list_pt([self.cat.ingredients[i]["name"].lower() for i in scope.ingredients if i in self.cat.ingredients][:3])
        if scope.steps:
            return list_pt([self.cat.steps[s].lower() for s in sorted(scope.steps) if s in self.cat.steps][:3])
        return "o que você descreveu"

    def _scope_info(self, scope: Scope, n: int) -> dict:
        return {"kind": scope.kind, "label": self._scope_label(scope), "items": n}

    def _notice(self, scope: Scope) -> dict | None:
        if not scope.missing:
            return None
        labels = list_pt([c.label for c in scope.missing])
        shelf = list_pt(list(dict.fromkeys(c.shelf for c in scope.missing if c.shelf and c.near))[:2])   # só prateleira vizinha de verdade
        if all(c.shelf == MED_SHELF for c in scope.missing):
            return {"missing": [c.label for c in scope.missing], "shelf": None, "message": MED_MISSING, "med": True}
        return {"missing": [c.label for c in scope.missing], "shelf": shelf or None,
                "message": f"Não temos {labels} no catálogo."}

    def _dept_suggestions(self, scope: Scope, intent: dict) -> list[str]:
        sug = ["Mais barato"]
        steps = scope.steps
        meds = [p for p in self.cat.products if _health(p)]
        med_steps, med_concerns = {p["step"] for p in meds}, {c for p in meds for c in p["concerns"]}
        other_ings = {i for p in self.cat.products if not _health(p) for i in p["ingredients"]}
        if ((steps and steps <= med_steps) or (not steps and scope.concerns and scope.concerns <= med_concerns)
                or (not steps and scope.ingredients and not set(scope.ingredients) & other_ings)):   # "psyllium"
            return ["Mais barato", "Remédio para gripe", "Remédio para dor de cabeça"]
        if steps & {"higiene_corpo", "higiene_cabelo", "higiene_oral", "desodorante"}:
            sug.insert(0, "Higiene premium")
        elif steps & {"omega3", "colageno", "magnesio", "vitaminas"}:
            sug.insert(0, "Kit de suplementos")
        elif steps & {"protecao_solar", "protecao_corporal"}:
            sug.insert(0, "Kit de proteção solar")
        else:
            sug.insert(0, "Montar uma rotina de skin care")
        return sug + ["Sem fragrância"]

    def _shelf_list(self, req, query, u, safety, intent, scope, rel, turn):
        # sem kit: o objetivo não fica no contexto, para "mais barato" depois filtrar esta lista e não montar outro kit
        intent = {**intent, "goals": [], "primaryGoal": None,
                  "missing": [m for m in intent.get("missing", []) if m != "skinType"]}
        prods = self._scope_products(scope, intent, u, rel)
        notice = self._notice(scope)
        label = self._scope_label(scope)
        if not prods:
            return self._not_found(req, query, safety, intent, {}, turn, label=label)
        n = len(prods)
        generic_med = scope.shelves == [MED_SHELF] and not scope.concerns     # só a palavra "remédio", sem o quê
        reply = f"Encontrei {n} {'item' if n == 1 else 'itens'} de {label}."
        if notice:
            reply = f"{notice['message']} {reply}"
        meds = any(_health(p) for p in prods)
        if meds and re.search(r"\bkits?\b", norm(query)):
            reply = "Remédios não entram em kit, então mostro os itens avulsos. " + reply   # #40, sem mandar procurar ninguém
        reply += " Toque numa sugestão para ajustar a lista." if meds else " Toque numa sugestão para montar um kit ou ajustar a lista."
        res = self._out(req, query, safety, intent, "busca", reply, products=prods,
                        suggestions=self._dept_suggestions(scope, intent), action={"type": "show_products"},
                        catalog_notice=notice, scope_info=self._scope_info(scope, n),
                        ctx_out=self._ctx_out(intent, req, u.excluded_ingredients, u.requested_ingredients, [], "busca", turn,
                                              scope=scope))
        if generic_med:
            res["_miss"] = "med_shelf"
        return res

    def _absent(self, req, query, u, safety, intent, scope, rel, turn):
        notice = self._notice(scope)
        if notice.get("med"):
            return self._med_missing(req, query, safety, intent, turn, notice)
        intent = {**intent, "goals": [], "primaryGoal": None,
                  "missing": [m for m in intent.get("missing", []) if m != "skinType"]}
        prods = self._scope_products(scope, intent, u, rel, limit=12) if scope.steps else []
        if prods:
            shelf = notice["shelf"] or self._scope_label(scope)
            reply = f"{notice['message']} Posso mostrar o que temos de {shelf}: {len(prods)} {'item' if len(prods) == 1 else 'itens'}."
            return self._out(req, query, safety, intent, "busca", reply, products=prods,
                             suggestions=self._dept_suggestions(scope, intent), action={"type": "show_products"},
                             catalog_notice={**notice, "nearest": shelf}, scope_info=self._scope_info(scope, len(prods)),
                             ctx_out=self._ctx_out(intent, req, u.excluded_ingredients, u.requested_ingredients, [], "busca",
                                                   turn, scope=scope))
        reply = (f"{notice['message']} Por aqui eu ajudo com cuidados com a pele, suplementos e higiene "
                 "(banho, cabelo, boca e desodorante).")
        return self._out(req, query, safety, intent, "busca", reply,
                         suggestions=["Higiene premium", "Kit de suplementos", "Pele oleosa até R$ 100"],
                         catalog_notice=notice, scope_info={"kind": "absent", "label": notice["missing"][0], "items": 0},
                         ctx_out={"intent": intent, "requested": [], "excluded": [], "kits": [], "lastAct": "busca",
                                  "turn": turn + 1})

    def _med_missing(self, req, query, safety, carry, turn, notice=None):
        notice = notice or {"missing": ["medicamento pedido"], "shelf": None, "message": MED_MISSING, "med": True}
        return self._out(req, query, safety, carry, "busca", MED_MISSING, catalog_notice=notice,
                         scope_info={"kind": "absent", "label": notice["missing"][0], "items": 0},
                         ctx_out={"intent": carry, "requested": [], "excluded": [], "kits": [], "lastAct": "busca",
                                  "turn": turn + 1})

    def _not_found(self, req, query, safety, carry, cin, turn, label=None):
        res = self._not_found_reply(req, query, safety, carry, cin, turn, label)
        res["_miss"] = "busca"                           # o grafo não entendeu: a DeepSeek pode tentar (#34)
        return res

    def _not_found_reply(self, req, query, safety, carry, cin, turn, label=None):
        if MED_CUE.search(norm(query)):
            return self._med_missing(req, query, safety, carry, turn)
        what = f"itens de {label}" if label else "esse item"
        reply = (f"Não encontrei {what} no catálogo. Tente por categoria, como “higiene bucal”, “pele oleosa até R$ 100” "
                 "ou “kit de suplementos”.")
        notice = {"missing": [label or "item pedido"], "shelf": None, "message": f"Não encontrei {what} no catálogo."}
        return self._out(req, query, safety, carry, "busca", reply,
                         suggestions=["Higiene bucal", "Kit de suplementos", "Pele oleosa até R$ 100", "Protetor solar"],
                         catalog_notice=notice, scope_info={"kind": "unknown", "label": label or "", "items": 0},
                         ctx_out={"intent": carry, "requested": [], "excluded": [], "kits": [], "lastAct": "busca",
                                  "turn": turn + 1})

    # ------------------------------------------------------------ refinar
    def _refine(self, req, query, u: Understanding, safety, cin, carry, turn):
        intent = dict(carry)
        intent["preferences"] = sorted(set(intent.get("preferences", [])) | set(u.preferences))
        if "preferences" in req and req["preferences"] is not None:
            intent["preferences"] = sorted(set(intent["preferences"]) | set(req["preferences"]))
        if u.skin:
            intent["skinType"] = u.skin
        if u.pregnancy:
            intent["pregnancy"] = True
        excluded = sorted(set(cin.get("excluded", [])) | set(u.excluded_ingredients))
        requested = sorted((set(cin.get("requested", [])) | set(u.requested_ingredients)) - set(excluded))
        ctx0 = build_ctx(self.cat, intent, requested, excluded)
        prev_kits = self._rehydrate(cin.get("kits"), ctx0) if ctx0 else []
        if u.budget_mentioned:
            intent["budgetCents"] = u.budget_cents
        elif u.cheaper and prev_kits:
            base = self._focus_kit(prev_kits, cin.get("focusTier"))
            intent["budgetCents"] = max(1, round(base["totalCents"] * 0.85))
        elif u.richer and prev_kits:
            base = max(prev_kits, key=lambda k: k["totalCents"])
            intent["budgetCents"] = round(base["totalCents"] * 1.4)
        if "budgetCents" in req:
            intent["budgetCents"] = req["budgetCents"]
        if "skinType" in req:
            intent["skinType"] = req["skinType"]
        if "storeId" in req:
            intent["storeId"] = req["storeId"]
        intent["missing"] = self._missing(intent)
        heard = (u.tier or u.skin or u.goals or u.preferences or u.budget_mentioned or u.cheaper or u.richer
                 or u.excluded_ingredients or u.requested_ingredients or u.pregnancy)
        noop = (not heard and excluded == sorted(cin.get("excluded", [])) and requested == sorted(cin.get("requested", []))
                and all(_same(intent.get(k), carry.get(k)) for k in GRAPH_KEYS))   # nada mudou e nada foi reconhecido
        if not intent.get("primaryGoal") and cin.get("scope"):
            return self._refine_list(req, query, u, safety, cin, intent, requested, excluded, turn)
        if not intent.get("primaryGoal"):
            return self._basic(req, query, safety, intent, cin, turn, "refinar",
                               "Entendi. Me diga primeiro o que você procura (por exemplo, pele oleosa, suplementos ou higiene) "
                               "e eu já aplico isso.", ["Kit de suplementos", "Higiene premium", "Pele oleosa"])
        proxy = Understanding(text=query, goals=intent["goals"], primary_goal=intent["primary_goal"] if "primary_goal" in intent else intent["primaryGoal"],
                              concerns=u.concerns, skin=intent.get("skinType"), preferences=intent["preferences"],
                              requested_ingredients=requested, excluded_ingredients=excluded, steps=[])
        rel = self.ret.score(proxy, query)
        ctx = build_ctx(self.cat, intent, requested, excluded, rel, self.weights["ret_in_kit"])
        comp = self.comp.compose(ctx, self._rid(req))
        focus = u.tier if u.tier and any(k["tier"] == u.tier for k in comp["kits"]) else None
        reply = self._reply_kits(comp, intent, ctx, u, refined=True, excluded=excluded, only=focus)
        clar = {"id": "skinType", "question": "Como é a sua pele?", "options": SKIN_OPTIONS} if "skinType" in intent["missing"] else None
        res = self._out(req, query, safety, intent, "refinar", reply, kits_status=comp["status"], kits=comp["kits"],
                        closest=comp["closestKit"], products=self.comp.rank_products(ctx, [], rel, limit=12),
                        notes=comp["notes"], suggestions=self._suggest_after(comp, intent),
                        action={"type": "show_kits", **({"tier": focus} if focus else {})} if comp["kits"] else None,
                        clarification=clar,
                        ctx_out=self._ctx_out(intent, req, excluded, requested, comp["kits"], "refinar", turn, focus_tier=focus))
        if noop:
            res["_miss"] = "ajuste"                      # "coisa mais top": lido como ajuste, mas nada mudou
        return res

    def _refine_list(self, req, query, u, safety, cin, intent, requested, excluded, turn):
        """"mais barato", "sem álcool", "vegano" depois de uma LISTA de itens (sem kit): refaz a mesma prateleira com o ajuste."""
        scope = self.scope.restore(cin["scope"])
        intent = {**intent, "goals": [], "primaryGoal": None}
        u.excluded_ingredients, u.requested_ingredients = excluded, requested
        proxy = Understanding(text=query, requested_ingredients=requested, excluded_ingredients=excluded,
                              steps=sorted(scope.steps), preferences=intent["preferences"], skin=intent.get("skinType"))
        rel = self.ret.score(proxy, query)
        prods = self._scope_products(scope, intent, u, rel)
        notes = []
        if u.budget_mentioned and u.budget_cents:
            before = len(prods)
            prods = [p for p in prods if p["priceCents"] <= u.budget_cents]
            notes.append(f"Mostrando só itens até {money(u.budget_cents)}.")
            intent["budgetCents"] = u.budget_cents
        if u.cheaper:
            prods = sorted(prods, key=lambda p: (p["priceCents"], p["id"]))
            notes.append("Ordenei do mais barato para o mais caro.")
        label = self._scope_label(scope)
        if not prods:
            reply = f"Com esses ajustes não sobrou nenhum item de {label}. Quer tirar alguma preferência?"
            sug = ["Tirar uma preferência", "Recomeçar"]
        else:
            n = len(prods)
            extra = f" Sem {list_pt([self.cat.ingredients[i]['name'].lower() for i in excluded if i in self.cat.ingredients])}." \
                if excluded and any(i in self.cat.ingredients for i in excluded) else ""
            pref = f" Filtro: {list_pt(intent['preferences'])}." if intent.get("preferences") else ""
            reply = f"Ajustei: {n} {'item' if n == 1 else 'itens'} de {label}.{pref}{extra} {' '.join(notes)}".strip()
            sug = self._dept_suggestions(scope, intent)
        return self._out(req, query, safety, intent, "refinar", reply, products=prods, notes=notes, suggestions=sug,
                         action={"type": "show_products"} if prods else None, scope_info=self._scope_info(scope, len(prods)),
                         ctx_out=self._ctx_out(intent, req, excluded, requested, [], "refinar", turn, scope=scope))

    # ------------------------------------------------------------ trocar item
    def _swap_chat(self, req, query, u, safety, cin, carry, turn):
        ctx = build_ctx(self.cat, carry, cin.get("requested", []), cin.get("excluded", []))
        kits = self._rehydrate(cin.get("kits"), ctx) if ctx else []
        kit = self._focus_kit(kits, u.tier or cin.get("focusTier"))
        if not kit:
            return self._basic(req, query, safety, carry, cin, turn, "trocar_item",
                               "Ainda não tenho um kit para trocar itens. Me diga o que você procura e eu monto.",
                               ["Kit de suplementos", "Higiene premium", "Pele oleosa até R$ 100"])
        steps_in_kit = [i["step"] for i in kit["items"]]
        step = next((s for s in u.steps if s in steps_in_kit), None)
        if step is None and u.product_ids:
            step = next((i["step"] for i in kit["items"] if i["product"]["id"] in u.product_ids), None)
        if step is None:
            names = [self.cat.steps[s].lower() for s in steps_in_kit]
            return self._out(req, query, safety, carry, "trocar_item",
                             f"Qual item do kit {TIER_NAME[kit['tier']]} você quer trocar? Ele tem: {list_pt(names)}.",
                             kits_status="ok", kits=kits, suggestions=[f"Trocar {n}" for n in names[:4]],
                             ctx_out={**cin, "lastAct": "trocar_item", "turn": turn + 1})
        sctx = build_ctx(self.cat, carry, cin.get("requested", []), cin.get("excluded", []),
                         None, self.weights["ret_in_kit"])
        opts = [o for o in self.comp.swap_options(kit, step, sctx) if o["compatible"]]
        if u.cheaper:
            opts = sorted([o for o in opts if o["deltaCents"] < 0], key=lambda o: o["deltaCents"]) or opts
        top = opts[:3]
        label = self.cat.steps[step].lower()
        if not top:
            return self._out(req, query, safety, carry, "trocar_item",
                             f"Não encontrei outra opção de {label} que combine com o restante do kit nessa loja.",
                             kits_status="ok", kits=kits, suggestions=["Recomeçar", "Mais barato"],
                             ctx_out={**cin, "lastAct": "trocar_item", "turn": turn + 1})
        def fmt(o):
            d = o["deltaCents"]
            sign = "mesmo preço" if d == 0 else (f"+{money(d)}" if d > 0 else f"−{money(-d)}")
            return f"{o['product']['name']} ({sign})"
        reply = f"Para trocar {label} no kit {TIER_NAME[kit['tier']]}, estas combinam: " + "; ".join(fmt(o) for o in top) + ". Toque em uma para trocar."
        return self._out(req, query, safety, carry, "trocar_item", reply, kits_status="ok", kits=kits,
                         suggestions=[f"Trocar por {o['product']['name'][:26]}" for o in top][:3],
                         action={"type": "swap_options", "tier": kit["tier"], "kitId": kit["id"], "step": step,
                                 "options": [{"productId": o["product"]["id"], "deltaCents": o["deltaCents"]} for o in top]},
                         ctx_out={**cin, "lastAct": "trocar_item", "turn": turn + 1, "focusTier": kit["tier"]})

    # ------------------------------------------------------------ entrega e total com frete
    def delivery_quote(self, total_cents: int) -> list[dict]:
        out = []
        for d in self.cat.delivery:
            fee = 0 if (d["freeFromCents"] is not None and total_cents >= d["freeFromCents"]) else d["feeCents"]
            out.append({"id": d["id"], "label": d["label"], "eta": d["eta"], "feeCents": fee, "totalCents": total_cents + fee,
                        "stockSource": d["stockSource"]})
        return out

    def _delivery(self, req, query, u, safety, cin, carry, turn):
        ctx = build_ctx(self.cat, carry, cin.get("requested", []), cin.get("excluded", []))
        kits = self._rehydrate(cin.get("kits"), ctx) if ctx else []
        kit = self._focus_kit(kits, u.tier or cin.get("focusTier"))
        free = self.cat.free_shipping_cents
        if not kit:
            reply = (f"Retirar na loja é sem taxa e fica pronto em até 60 minutos. A entrega expressa chega em até 2 h e a "
                     f"agendada você escolhe o dia; as duas têm frete grátis a partir de {money(free)}. "
                     "Monte um kit e eu mostro o total com cada forma de entrega.")
            return self._out(req, query, safety, carry, "entrega_frete", reply,
                             suggestions=["Kit de suplementos", "Higiene premium"],
                             action={"type": "delivery_info"}, ctx_out={**cin, "lastAct": "entrega_frete", "turn": turn + 1} if cin else
                             {"intent": carry, "kits": [], "lastAct": "entrega_frete", "turn": turn + 1})
        quote = self.delivery_quote(kit["totalCents"])
        pickup = next(q for q in quote if q["id"] == "retirada")
        ships = [q for q in quote if q["id"] != "retirada"]
        missing = free - kit["totalCents"]
        tip = f" Faltam {money(missing)} para frete grátis na entrega." if missing > 0 else " Seu kit já tem frete grátis na entrega."
        reply = (f"O kit {TIER_NAME[kit['tier']]} custa {money(kit['totalCents'])}. Com retirada na loja o total é {money(pickup['totalCents'])} "
                 f"(sem frete); com entrega fica entre {money(min(q['totalCents'] for q in ships))} e {money(max(q['totalCents'] for q in ships))}." + tip)
        return self._out(req, query, safety, carry, "entrega_frete", reply, kits_status="ok", kits=kits,
                         suggestions=["Retirar na loja mais próxima", "Mais barato", "Trocar um item"],
                         action={"type": "delivery_quote", "tier": kit["tier"], "kitTotalCents": kit["totalCents"], "options": quote},
                         ctx_out={**cin, "lastAct": "entrega_frete", "turn": turn + 1, "focusTier": kit["tier"]})

    # ------------------------------------------------------------ similares e equivalentes
    def similars(self, product_id: str, store_id: str | None = None, limit: int = 6) -> dict:
        p = self.cat.by_id.get(product_id)
        if p is None:
            raise ValueError("Produto inexistente.")
        stock = lambda q: self.cat.stock_at(q["id"], store_id)
        stores_with = lambda q: [s["id"] for s in self.cat.stores if self.cat.stock_at(q["id"], s["id"]) > 0]
        opts = []
        if p["equivalence"]:                  # reposição: equivalentes (mesmo princípio ativo e dose)
            for eid in self.graph.equivalents(product_id):
                e = self.cat.by_id[eid]
                opts.append({"product": e, "kind": "equivalente", "presentation": e["equivalence"]["presentation"],
                             "sameActive": True, "sameDose": e["equivalence"]["dose"] == p["equivalence"]["dose"],
                             "deltaCents": e["priceCents"] - p["priceCents"], "inStock": stock(e) > 0,
                             "storeIdsWithStock": stores_with(e), "needsPharmacistConfirmation": False})
            opts.sort(key=lambda o: (not o["inStock"], o["deltaCents"], o["product"]["id"]))
        else:
            for sid, w in self.graph.similar(product_id, k=12):
                e = self.cat.by_id[sid]
                opts.append({"product": e, "kind": "parecido", "score": w, "deltaCents": e["priceCents"] - p["priceCents"],
                             "inStock": stock(e) > 0, "storeIdsWithStock": stores_with(e), "needsPharmacistConfirmation": False})
            opts.sort(key=lambda o: (not o["inStock"], -o["score"], o["product"]["id"]))
        return {"productId": product_id, "domain": p["domain"], "storeId": store_id, "inStockHere": stock(p) > 0,
                "options": opts[:limit]}

    def _similar_chat(self, req, query, u, safety, cin, carry, turn):
        focus = None
        if u.product_ids:
            focus = u.product_ids[0]
        elif cin.get("focusProductId"):
            focus = cin["focusProductId"]
        elif req.get("focusProductId"):
            focus = req["focusProductId"]
        ctx = build_ctx(self.cat, carry, cin.get("requested", []), cin.get("excluded", []))
        kits = self._rehydrate(cin.get("kits"), ctx) if ctx else []
        if focus is None and kits:
            kit = self._focus_kit(kits, u.tier or cin.get("focusTier"))
            step = next((s for s in u.steps if any(i["step"] == s for i in kit["items"])), None)
            if step:
                focus = next(i["product"]["id"] for i in kit["items"] if i["step"] == step)
        if focus is None:
            reply = "De qual produto você quer ver opções parecidas? Toque no item no kit ou me diga o nome."
            if req.get("refillContext"):
                reply = "Toque no medicamento da sua reposição que está em falta e eu mostro os equivalentes com o mesmo princípio ativo e dose."
            return self._out(req, query, safety, carry, "similar", reply, kits_status="ok" if kits else "not_applicable",
                             kits=kits, suggestions=["Mais barato", "Trocar um item"],
                             ctx_out={**cin, "lastAct": "similar", "turn": turn + 1} if cin else
                             {"intent": carry, "kits": [], "lastAct": "similar", "turn": turn + 1})
        sim = self.similars(focus, carry.get("storeId"))
        p = self.cat.by_id[focus]
        n_in = sum(1 for o in sim["options"] if o["inStock"])
        if p["equivalence"]:
            if sim["options"]:
                reply = (f"Encontrei {len(sim['options'])} equivalentes com o mesmo princípio ativo e a mesma dose, "
                         f"{n_in} com estoque agora. Eles aparecem abaixo com preço, apresentação e lojas com estoque.")
            else:
                reply = "Não encontrei equivalente para esse item."
        else:
            reply = (f"Achei {len(sim['options'])} opções parecidas com {p['name']}"
                     + (f", {n_in} com estoque" if sim['options'] else "") + ". Toque numa para ver os detalhes.")
        return self._out(req, query, safety, carry, "similar", reply, kits_status="ok" if kits else "not_applicable",
                         kits=kits, products=[o["product"] for o in sim["options"]], suggestions=["Qual a entrega mais rápida?", "Mais barato"],
                         action={"type": "show_similars", "productId": focus, "options": [
                             {k: v for k, v in o.items() if k != "product"} | {"productId": o["product"]["id"]} for o in sim["options"]]},
                         ctx_out={**cin, "lastAct": "similar", "turn": turn + 1, "focusProductId": focus} if cin else
                         {"intent": carry, "kits": [], "lastAct": "similar", "turn": turn + 1, "focusProductId": focus})

    # ------------------------------------------------------------ pergunta sobre produto
    def _ask_product(self, req, query, u, safety, cin, carry, turn):
        ctx = build_ctx(self.cat, carry, cin.get("requested", []), cin.get("excluded", []))
        kits = self._rehydrate(cin.get("kits"), ctx) if ctx else []
        kit = self._focus_kit(kits, u.tier or cin.get("focusTier"))
        p = None
        if u.product_ids:
            p = self.cat.by_id[u.product_ids[0]]
        elif kit:
            step = next((s for s in u.steps if any(i["step"] == s for i in kit["items"])), None)
            if step:
                p = next(i["product"] for i in kit["items"] if i["step"] == step)
            elif cin.get("focusProductId"):
                p = self.cat.by_id.get(cin["focusProductId"])
        elif cin.get("focusProductId"):
            p = self.cat.by_id.get(cin["focusProductId"])
        if p is None:
            res = self._out(req, query, safety, carry, "pergunta_produto",
                            "Sobre qual produto é a dúvida? Toque nele no kit ou me diga o nome.",
                            kits_status="ok" if kits else "not_applicable", kits=kits, suggestions=["Total com entrega", "Trocar um item"],
                            ctx_out={**cin, "lastAct": "pergunta_produto", "turn": turn + 1} if cin else
                            {"intent": carry, "kits": [], "lastAct": "pergunta_produto", "turn": turn + 1})
            if kits and ("?" not in query or ADJUST_CUE.search(norm(query))):
                res["_miss"] = "ajuste"                  # "tira o que tem álcool" lido como pergunta sem produto
            elif not cin:
                res["_miss"] = "busca"                   # sem conversa e sem produto: nada para perguntar, o grafo não entendeu
            return res
        reply = self.answer_about(p, query, u)
        return self._out(req, query, safety, carry, "pergunta_produto", reply, kits_status="ok" if kits else "not_applicable",
                         kits=kits, suggestions=["Tem similar?", "Trocar esse item", "Total com entrega"],
                         ctx_out={**cin, "lastAct": "pergunta_produto", "turn": turn + 1, "focusProductId": p["id"]} if cin else
                         {"intent": carry, "kits": [], "lastAct": "pergunta_produto", "turn": turn + 1, "focusProductId": p["id"]})

    def answer_about(self, p: dict, query: str, u: Understanding) -> str:
        """Responde só com fatos do catálogo (claims, ingredientes, FPS, modo de uso, avisos). Nada de promessa terapêutica."""
        q, cat, name = norm(query), self.cat, p["name"]
        ings = [cat.ingredients[i]["name"] for i in p["ingredients"] if i in cat.ingredients]
        if re.search(r"\b(fps|fator de protecao)\b", q):
            return f"{name} tem FPS {p['fps']}." if p["fps"] else f"{name} não é um protetor solar (sem FPS informado)."
        if re.search(r"\b(vegano|vegana)\b", q):
            return f"{name} {'é vegano' if 'vegano' in p['claims'] else 'não tem a alegação vegano no cadastro'}."
        if re.search(r"\boil free\b|\bsem oleo\b", q):
            return f"{name} {'é oil free' if 'oil free' in p['claims'] else 'não é oil free'}."
        if re.search(r"\b(fragrancia|perfume|cheiro)\b", q):
            return f"{name} {'é sem fragrância' if 'sem fragrância' in p['claims'] else 'pode conter fragrância'}."
        if re.search(r"\b(alcool)\b", q):
            return f"{name} {'é sem álcool' if 'sem álcool' in p['claims'] else 'não tem a alegação sem álcool'}."
        if re.search(r"\b(como usar|modo de uso|uso diario|passo a passo)\b", q) or re.search(r"\bposso usar\b", q):
            per = {"dia": "de dia", "noite": "à noite", "dia_noite": "de dia ou à noite"}[p["usagePeriod"]]
            return f"{name}: uso {per}. {p['howToUse']}"
        if re.search(r"\b(sensivel|seca|oleosa|mista|normal)\b", q) or re.search(r"\bserve\b", q):
            return f"{name} é indicado para pele {list_pt(p['skinTypes'])}."
        if re.search(r"\b(gestante|gravida|amamentando)\b", q):
            return (cat.warnings["consultar_se_gestante"] if "consultar_se_gestante" in p["warnings"]
                    else f"{name} não traz aviso específico para gestação no cadastro.")
        if re.search(r"\b(ativo|ativos|tem de|composicao|ingrediente|retinol|vitamina c|niacinamida|acucar|sulfato)\b", q):
            req_ing = [cat.ingredients[i]["name"] for i in u.requested_ingredients if i in cat.ingredients]
            if req_ing:
                have = [n for n in req_ing if n in ings]
                return (f"Sim, {name} tem {list_pt([n.lower() for n in have])}." if have
                        else f"Não, {name} não tem {list_pt([n.lower() for n in req_ing])} no cadastro. Ativos: {list_pt([i.lower() for i in ings]) or 'não informados'}.")
            return f"Ativos de {name}: {list_pt([i.lower() for i in ings]) or 'não informados'}."
        if re.search(r"\b(alerta|aviso|cuidado|por que)\b", q):
            ws = [cat.warnings[w] for w in p["warnings"]]
            return " ".join(ws) if ws else f"{name} não tem avisos especiais no cadastro."
        return f"{p['description']} {p['howToUse']}".strip()

    # ------------------------------------------------------------ textos de resposta
    def _reply_kits(self, comp, intent, ctx, u, refined=False, excluded=(), only=None) -> str:
        goal = self.cat.goal_by_id[intent["primaryGoal"]]["label"].lower()
        budget = f" até {money(intent['budgetCents'])}" if intent.get("budgetCents") is not None else ""
        store = f" com estoque na {self.store_names[intent['storeId']]}" if intent.get("storeId") in self.store_names else ""
        st = comp["status"]
        if st == "not_applicable":
            return comp["notes"][0] if comp["notes"] else "Não consegui montar um kit com esses critérios. Quer afrouxar alguma preferência?"
        if st == "none_in_budget":
            k = comp["closestKit"]
            over = k["totalCents"] - intent["budgetCents"]
            return (f"Com{budget} não fechei um kit completo de {goal}. O mais próximo custa {money(k['totalCents'])}, "
                    f"{money(over)} acima. Quer subir o orçamento ou tirar alguma preferência?")
        kits = comp["kits"]
        if only:
            kits = [k for k in kits if k["tier"] == only] or kits
        parts = [f"{TIER_NAME[k['tier']]} {money(k['totalCents'])}" for k in kits]
        head = "Ajustei" if refined else "Montei"
        extra = ""
        if refined and excluded:
            names = [self.cat.ingredients[i]["name"].lower() for i in excluded if i in self.cat.ingredients]
            if names:
                extra = f" Sem {list_pt(names)}."
        if ctx.pregnancy:
            extra += " Retirei o que tem restrição na gestação."
        n = len(kits)
        return (f"{head} {n} opç{'ão' if n == 1 else 'ões'} de {goal}{budget}{store}: {list_pt(parts)}.{extra} "
                "Quer trocar algum item, ajustar o preço ou ver o total com entrega?")

    def _suggest_after(self, comp, intent) -> list[str]:
        sug = []
        if comp["kits"]:
            sug += ["Total com entrega", "Mais barato"]
            if not intent.get("preferences") and intent.get("primaryGoal") in DERMO_GOALS | {"higiene_premium"}:
                sug.append("Sem fragrância" if intent.get("primaryGoal") != "higiene_premium" else "Sem sulfato")
            sug.append("Trocar um item")
        else:
            sug += ["Aumentar o orçamento", "Recomeçar"]
        return sug


def _health(p: dict) -> bool:
    """Área de saúde: remédio ou item das linhas de remédio (vitamina C efervescente e psyllium, suplementos desde o #40)."""
    return p["domain"] == "medicamento" or p["line"].startswith("med_")


def _same(a, b) -> bool:
    return sorted(a) == sorted(b) if isinstance(a, list) and isinstance(b, list) else a == b


def build_probe(intent, u):
    from .composer import Ctx
    return Ctx(goals=[], primary="", concerns=set(), primary_concerns=set(), skin=intent.get("skinType"), assumed_skin=None,
               prefs=list(intent.get("preferences", [])), pregnancy=bool(intent.get("pregnancy")), budget=None,
               excluded=list(u.excluded_ingredients), store_id=intent.get("storeId"))


# ---------------------------------------------------------------------------------------------- API de kits
def _kit_from_client(engine: "Engine", kit: dict, ctx) -> dict:
    """Reconstrói o kit só a partir dos ids (preço e estoque vêm do catálogo, nunca do cliente)."""
    compact = [{"id": kit["id"], "tier": kit["tier"], "title": kit.get("title", ""), "goal": kit["goal"],
                "storeId": kit.get("storeId"), "rationale": kit.get("rationale", ""),
                "items": [{"step": i["step"], "productId": i["product"]["id"], "reason": i.get("reason", "")}
                          for i in kit["items"]]}]
    out = engine._rehydrate(compact, ctx)
    if not out or any(i["product"]["domain"] == "medicamento" for i in out[0]["items"]):
        raise ValueError("Kit inválido.")                # K13: kit com remédio não vem de resposta do motor
    return out[0]


def api_swap_options(engine: Engine, kit: dict, step: str, intent: dict) -> list[dict]:
    ctx = build_ctx(engine.cat, intent, rel=None, w_rel=engine.weights["ret_in_kit"])
    if not ctx:
        return []
    return engine.comp.swap_options(_kit_from_client(engine, kit, ctx), step, ctx)


def api_swap(engine: Engine, kit: dict, step: str, product_id: str, intent: dict) -> dict:
    ctx = build_ctx(engine.cat, intent, rel=None, w_rel=engine.weights["ret_in_kit"])
    if not ctx:
        raise ValueError("Sem contexto para trocar o item.")
    return engine.comp.apply_swap(_kit_from_client(engine, kit, ctx), step, product_id, ctx)


def api_adapt(engine: Engine, kit: dict, store_id: str, intent: dict) -> dict | None:
    ctx = build_ctx(engine.cat, intent, rel=None, w_rel=engine.weights["ret_in_kit"])
    if not ctx:
        return None
    return engine.comp.adapt_to_store(_kit_from_client(engine, kit, ctx), store_id, ctx)
