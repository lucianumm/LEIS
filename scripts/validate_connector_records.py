#!/usr/bin/env python3
"""Validate JSONL records emitted by a jurisdiction/source connector."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlparse


REQUIRED = {
    "source_id",
    "jurisdiction",
    "authority",
    "normative_type",
    "identifier",
    "official_url",
    "publication_date",
    "retrieved_at",
    "status_at_source",
    "raw_text_sha256",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("records", type=Path)
    args = parser.parse_args()
    errors: list[str] = []
    count = 0
    for line_number, line in enumerate(args.records.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        count += 1
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"linha {line_number}: JSON inválido ({exc})")
            continue
        missing = sorted(REQUIRED - set(record))
        if missing:
            errors.append(f"linha {line_number}: campos ausentes: {', '.join(missing)}")
        parsed = urlparse(str(record.get("official_url", "")))
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            errors.append(f"linha {line_number}: official_url não é HTTP(S)")
        digest = str(record.get("raw_text_sha256", ""))
        if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest.lower()):
            errors.append(f"linha {line_number}: raw_text_sha256 inválido")
        if record.get("status_at_source") in {"vigente", "válida", "aplicável"} and not record.get("status_evidence_url"):
            errors.append(f"linha {line_number}: status afirmativo sem status_evidence_url")
    if errors:
        print("\n".join(f"ERRO: {item}" for item in errors))
        return 1
    print(f"OK: {count} registros de conector válidos")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
