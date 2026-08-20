#!/usr/bin/env python3
"""Dependency-free structural validation for CI and local installs."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path, nargs="?", default=Path("."))
    args = parser.parse_args()
    root = args.root.resolve()
    errors: list[str] = []
    skill = root / "SKILL.md"
    if not skill.exists():
        errors.append("SKILL.md ausente")
    else:
        text = skill.read_text(encoding="utf-8", errors="replace")
        if not text.startswith("---") or "name:" not in text.split("---", 2)[1]:
            errors.append("frontmatter inválido")
        match = re.search(r"^name:\s*([a-z0-9-]+)\s*$", text, re.M)
        if not match or len(match.group(1)) > 64:
            errors.append("nome inválido")
        if not re.search(r"^description:\s*\S+", text, re.M):
            errors.append("description ausente")
        if "TODO" in text or "PLACEHOLDER" in text:
            errors.append("placeholder inacabado em SKILL.md")
        for target in re.findall(r"\]\(([^)#]+)(?:#[^)]+)?\)", text):
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            if not (root / target).exists():
                errors.append(f"referência ausente: {target}")
    for required in ("agents/openai.yaml", "data/source_registry.json", "scripts/check_corpus.py"):
        if not (root / required).exists():
            errors.append(f"arquivo obrigatório ausente: {required}")
    if errors:
        for error in errors:
            print(f"ERRO: {error}")
        return 1
    print("Skill estruturalmente válida")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
