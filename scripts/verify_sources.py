#!/usr/bin/env python3
"""Check official-source reachability and record evidence without deciding law."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def signals(text: str) -> list[str]:
    folded = text.casefold()
    patterns = {
        "revocation_or_amendment_marker": r"revogad|revoga|redação dada|alterad|acrescent",
        "temporal_effect_marker": r"vigência|entra em vigor|produção de efeitos|produz efeitos|prazo determinado",
        "constitutional_review_marker": r"adi|adin|adc|adpf|repercussão geral|controle de constitucionalidade",
    }
    return [name for name, pattern in patterns.items() if re.search(pattern, folded)]


def fetch(url: str, timeout: int, max_bytes: int) -> dict:
    retrieved_at = datetime.now(timezone.utc).isoformat()
    request = Request(url, headers={"User-Agent": "leis-analise-br-source-check/1.0"})
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read(max_bytes)
            text = body.decode(response.headers.get_content_charset() or "utf-8", errors="replace")
            return {
                "status": "reachable",
                "http_status": getattr(response, "status", 200),
                "retrieved_at": retrieved_at,
                "content_sha256": hashlib.sha256(body).hexdigest(),
                "bytes_sampled": len(body),
                "signals": signals(text),
                "validity_status": "não determinada automaticamente — revisão oficial necessária",
            }
    except HTTPError as exc:
        return {"status": "http_error", "http_status": exc.code, "retrieved_at": retrieved_at, "error": str(exc)}
    except (URLError, TimeoutError, OSError) as exc:
        return {"status": "unreachable", "retrieved_at": retrieved_at, "error": str(exc)}


def unique_urls(catalog: Path | None, registry: Path | None) -> list[dict]:
    items: dict[str, dict] = {}
    if catalog and catalog.exists():
        payload = json.loads(catalog.read_text(encoding="utf-8"))
        for record in payload.get("records", []):
            url = record.get("source_url")
            if url and url not in items:
                items[url] = {"source_url": url, "source_id": record.get("id"), "kind": record.get("kind")}
    if registry and registry.exists():
        payload = json.loads(registry.read_text(encoding="utf-8"))
        for source in payload.get("sources", []):
            url = source.get("url")
            if url and url not in items:
                items[url] = {
                    "source_url": url,
                    "source_id": source.get("id"),
                    "kind": "official_registry_source",
                    "coverage_status": source.get("coverage_status"),
                    "requires_status_recheck": source.get("requires_status_recheck", True),
                }
    return list(items.values())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=Path("data/catalogo.json"))
    parser.add_argument("--registry", type=Path, default=Path("data/source_registry.json"))
    parser.add_argument("--report", type=Path, default=Path("data/source_verification.json"))
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--max-bytes", type=int, default=2_000_000)
    parser.add_argument("--offline", action="store_true", help="não faz rede; registra fontes como não verificadas")
    args = parser.parse_args()
    items = unique_urls(args.catalog, args.registry)[: max(0, args.limit)]
    results = []
    for item in items:
        if args.offline:
            result = {"status": "not_checked_offline", "validity_status": "não verificada"}
        else:
            result = fetch(item["source_url"], args.timeout, args.max_bytes)
        results.append({**item, **result})
    report = {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "network_used": not args.offline,
        "warning": "Reachability, hashes and text markers are evidence only; they do not certify vigência or applicability.",
        "checked_count": len(results),
        "results": results,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"checked": len(results), "report": str(args.report)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
