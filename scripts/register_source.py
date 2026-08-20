#!/usr/bin/env python3
"""Register one official portal in the generic harvest manifest."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlparse


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path("data/source_harvest_manifest.json"))
    parser.add_argument("--id", required=True, dest="source_id")
    parser.add_argument("--authority", required=True)
    parser.add_argument("--jurisdiction", required=True)
    parser.add_argument("--normative-type", required=True)
    parser.add_argument("--listing-url", required=True)
    parser.add_argument("--link-pattern", required=True)
    parser.add_argument("--status", default="connector_required")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,62}", args.source_id):
        raise SystemExit("id deve usar letras minúsculas, números e hífens")
    parsed = urlparse(args.listing_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise SystemExit("--listing-url deve ser uma URL HTTP(S) oficial")
    try:
        re.compile(args.link_pattern)
    except re.error as exc:
        raise SystemExit(f"--link-pattern inválido: {exc}") from exc
    payload = json.loads(args.manifest.read_text(encoding="utf-8"))
    sources = payload.setdefault("sources", [])
    if any(item.get("id") == args.source_id for item in sources):
        raise SystemExit(f"fonte já cadastrada: {args.source_id}")
    sources.append(
        {
            "id": args.source_id,
            "authority": args.authority,
            "jurisdiction": args.jurisdiction,
            "normative_type": args.normative_type,
            "listing_url": args.listing_url,
            "link_pattern": args.link_pattern,
            "status": args.status,
        }
    )
    payload["sources"] = sorted(sources, key=lambda item: item.get("id", ""))
    args.manifest.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Fonte registrada: {args.source_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
