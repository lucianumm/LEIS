#!/usr/bin/env python3
"""Run small discovery regressions without asserting a legal conclusion."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from search_corpus import load_aliases, load_sections, search


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=Path("tests/fixtures/evaluation_cases.json"))
    parser.add_argument("--catalog", type=Path, default=Path("data/catalogo.json"))
    parser.add_argument("--corpus-dir", type=Path, default=Path("corpus"))
    parser.add_argument("--aliases", type=Path, default=Path("data/search_aliases.json"))
    args = parser.parse_args()
    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    aliases = load_aliases(args.aliases)
    sections = load_sections(args.corpus_dir)
    results = []
    failed = []
    for case in cases:
        terms = list(case.get("terms", []))
        for group in case.get("groups", []):
            if group not in aliases:
                failed.append(f"{case['id']}: grupo desconhecido {group}")
                continue
            terms.extend(aliases[group])
        found = search(catalog.get("records", []), sections, terms, case.get("theme"), int(case.get("limit", 10)))
        expected = int(case.get("min_results", 1))
        ids = {item["id"] for item in found}
        missing_ids = sorted(set(case.get("must_include", [])) - ids)
        passed = len(found) >= expected and not missing_ids
        if not passed:
            failed.append(f"{case['id']}: encontrados={len(found)}, mínimo={expected}, ausentes={missing_ids}")
        results.append({"id": case["id"], "passed": passed, "result_count": len(found), "ids": [item["id"] for item in found]})
    payload = {"passed": not failed, "cases": results, "errors": failed}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
