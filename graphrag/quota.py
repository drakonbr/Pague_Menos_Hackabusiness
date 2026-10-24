"""Limite de uso da DeepSeek por pessoa e por dia (#64).

O endpoint é público e sem login: sem limite, qualquer pessoa gasta a chave com palavras inventadas. Cada cliente (hash do IP,
nunca o IP) tem um teto por hora e o servidor todo tem um teto por dia. Passou do teto, a busca segue só com o grafo.
Limite honesto: o contador vive na memória de cada instância. Na Vercel há várias instâncias e cada partida a frio zera o
contador; o teto real exige um armazenamento compartilhado (ou login), que este protótipo não tem.
"""
from __future__ import annotations

import os
import threading
import time
from collections import deque


class Quota:
    def __init__(self, per_client_hour: int = 20, daily: int = 1500, max_clients: int = 5000):
        self.per_client_hour, self.daily, self.max_clients = per_client_hour, daily, max_clients
        self.lock = threading.Lock()
        self.by_client: dict[str, deque] = {}
        self.day, self.day_count = "", 0

    @classmethod
    def from_env(cls) -> "Quota":
        return cls(int(os.environ.get("RAG_PER_CLIENT_HOUR", "20")), int(os.environ.get("RAG_DAILY_CAP", "1500")))

    def allow(self, client: str | None, now: float | None = None) -> bool:
        """Pede uma chamada. 0 em qualquer teto = sem limite. Sem cliente (uso local, avaliação), vale só o teto do dia."""
        now = time.time() if now is None else now
        today = time.strftime("%Y-%m-%d", time.gmtime(now))
        with self.lock:
            if today != self.day:
                self.day, self.day_count = today, 0
            if self.daily and self.day_count >= self.daily:
                return False
            if client and self.per_client_hour:
                q = self.by_client.setdefault(client, deque())
                while q and now - q[0] > 3600:
                    q.popleft()
                if len(q) >= self.per_client_hour:
                    return False
                q.append(now)
                if len(self.by_client) > self.max_clients:        # não deixa a tabela crescer sem fim
                    for k in [k for k, d in self.by_client.items() if not d or now - d[-1] > 3600][: self.max_clients // 2]:
                        self.by_client.pop(k, None)
            self.day_count += 1
            return True
