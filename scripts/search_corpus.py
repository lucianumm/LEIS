#!/usr/bin/env python3
"""Search the law corpus with legal aliases and encoding-tolerant matching."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from build_catalog import SECTION_RE, fold, slug


def load_sections(corpus_dir: Path) -> dict[tuple[str, str], str]:
    sections: dict[tuple[str, str], str] = {}
    for path in sorted(corpus_dir.glob("leis_*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        matches = list(SECTION_RE.finditer(text))
        for index, match in enumerate(matches):
            heading = match.group(1).strip()
            if not re.search(r"\.htm\s*$", heading, re.I):
                continue
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            sections[(path.name, slug(heading))] = text[match.end() : end]
    return sections


def load_aliases(path: Path) -> dict[str, list[str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload.get("groups", {})


def patterns(terms: list[str]) -> list[tuple[str, re.Pattern[str]]]:
    out: list[tuple[str, re.Pattern[str]]] = []
    seen: set[str] = set()
    for term in terms:
        normalized = fold(term).strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        out.append((term, re.compile(rf"(?<!\w){re.escape(normalized)}(?!\w)")))
    return out


def search(records: list[dict], sections: dict[tuple[str, str], str], terms: list[str], theme: str | None, limit: int) -> list[dict]:
    term_patterns = patterns(terms)
    results: list[dict] = []
    for record in records:
        themes = {record.get("primary_theme"), *record.get("secondary_themes", []), *record.get("subsidiary_themes", [])}
        if theme and theme not in themes:
            continue
        body = sections.get((record["corpus_file"], record["corpus_anchor"]), "")
        searchable = {
            "title_ementa": fold(f"{record.get('title', '')} {record.get('ementa', '')}"),
            "corpus": fold(body),
        }
        matched: list[dict] = []
        score = 0
        for label, pattern in term_patterns:
            headline_hits = len(pattern.findall(searchable["title_ementa"]))
            body_hits = len(pattern.findall(searchable["corpus"]))
            if headline_hits or body_hits:
                matched.append({"term": label, "headline_hits": headline_hits, "body_hits": body_hits})
                score += headline_hits * 8 + min(body_hits, 12)
        if not matched:
            continue
        results.append(
            {
                "rank_score": score,
                "id": record["id"],
                "jurisdiction": record.get("jurisdiction", "federal"),
                "kind": record["kind"],
                "number": record.get("number"),
                "title": record.get("title"),
                "ementa": record.get("ementa"),
                "primary_theme": record.get("primary_theme"),
                "secondary_themes": record.get("secondary_themes", []),
                "validity_status": record.get("validity_status"),
                "source_url": record.get("source_url"),
                "corpus_file": record.get("corpus_file"),
                "corpus_anchor": record.get("corpus_anchor"),
                "matched_terms": matched,
            }
        )
    results.sort(key=lambda item: (-item["rank_score"], item["kind"], int(item["number"] or 0)))
    return results[:limit]


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("terms", nargs="*", help="termos ou expressões; use --group para expandir aliases")
    parser.add_argument("--group", action="append", default=[], help="grupo em data/search_aliases.json; pode repetir")
    parser.add_argument("--theme", help="tema primário, secundário ou subsidiário")
    parser.add_argument("--corpus-dir", type=Path, default=Path("corpus"))
    parser.add_argument("--catalog", type=Path, default=Path("data/catalogo.json"))
    parser.add_argument("--aliases", type=Path, default=Path("data/search_aliases.json"))
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    aliases = load_aliases(args.aliases)
    unknown = [group for group in args.group if group not in aliases]
    if unknown:
        raise SystemExit(f"Grupos desconhecidos: {', '.join(unknown)}")
    terms = list(args.terms)
    for group in args.group:
        terms.extend(aliases[group])
    if not terms:
        raise SystemExit("Informe termos ou --group")

    payload = json.loads(args.catalog.read_text(encoding="utf-8"))
    sections = load_sections(args.corpus_dir)
    results = search(payload.get("records", []), sections, terms, args.theme, max(1, args.limit))
    if args.as_json:
        print(json.dumps({"terms": terms, "theme": args.theme, "results": results}, ensure_ascii=False, indent=2))
        return 0
    print(f"Resultados: {len(results)} | termos: {', '.join(terms)}" + (f" | tema: {args.theme}" if args.theme else ""))
    for index, result in enumerate(results, 1):
        label = f"{result['kind'].title()} nº {result['number'] or result['id']}"
        matched = ", ".join(item["term"] for item in result["matched_terms"])
        print(f"{index:02d}. [{result['rank_score']:03d}] {label} — {result['primary_theme']} — {matched}")
        print(f"    {result['source_url']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
