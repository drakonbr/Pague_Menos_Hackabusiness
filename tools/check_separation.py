#!/usr/bin/env python3
"""
Confere as regras de separação entre módulos (docs/04-arquitetura.md).

  1. catalog/ não referencia app/ nem graphrag/
  2. app/src não referencia catalog/ nem graphrag/  (JSON simulado entra por tools/export_app_mock.py)
  3. graphrag/ não escreve em catalog/ (checado por ausência de código nesta fase)
  4. Fase "pré-RAG": graphrag/ só pode conter README.md

Uso:  python3 tools/check_separation.py [--phase pre-rag|any]
Sai com código 1 se alguma regra for violada.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEXT_EXT = {".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".json", ".css", ".html", ".sql", ".yaml", ".yml"}
SKIP_DIRS = {"node_modules", "dist", ".vite", "__pycache__", ".git"}


def files(base: Path):
    if not base.exists():
        return
    for p in base.rglob("*"):
        if p.is_file() and p.suffix in TEXT_EXT and not (set(p.parts) & SKIP_DIRS):
            yield p


def refs(base: Path, forbidden: list[str], skip_json_in: str | None = None):
    """Procura imports e caminhos que apontem para pastas proibidas."""
    names = "|".join(forbidden)
    pat_import = re.compile(r"\b(from|import)\s+(" + names + r")\b")
    pat_path = re.compile(r"[\"'`][./]*(" + names + r")/")
    out = []
    for f in files(base):
        if skip_json_in and f.suffix == ".json" and skip_json_in in f.parts:
            continue
        for n, line in enumerate(f.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if line.lstrip().startswith(("#", "//", "*")):
                continue
            if pat_import.search(line) or pat_path.search(line):
                out.append(f"{f.relative_to(ROOT)}:{n}: {line.strip()[:110]}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", default="pre-rag", choices=["pre-rag", "any"])
    args = ap.parse_args()

    problems: list[str] = []

    # Regra 1
    for line in refs(ROOT / "catalog", ["app", "graphrag"]):
        problems.append(f"[R1 catalog->app/graphrag] {line}")

    # Regra 2: no app, só o código-fonte conta (os JSON simulados em mocks/ são dados, não referências)
    for line in refs(ROOT / "app" / "src", ["catalog", "graphrag"], skip_json_in="mocks"):
        problems.append(f"[R2 app->catalog/graphrag] {line}")

    # Regra 4
    if args.phase == "pre-rag":
        gr = ROOT / "graphrag"
        extra = [p.name for p in gr.iterdir() if p.name not in {"README.md", ".gitkeep"}] if gr.exists() else []
        if extra:
            problems.append(f"[R4 graphrag deve conter só README.md nesta fase] encontrado: {extra}")

    # Pastas obrigatórias
    for d in ["docs", "catalog", "app", "graphrag", "contracts", "tools"]:
        if not (ROOT / d).is_dir():
            problems.append(f"[estrutura] pasta ausente: {d}/")

    if problems:
        print("FALHOU:")
        for p in problems:
            print("  -", p)
        return 1
    print(f"OK: separação respeitada (fase {args.phase}).")
    print("  catalog/ sem referência a app/graphrag;  app/src sem referência a catalog/graphrag;  graphrag/ só README.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
