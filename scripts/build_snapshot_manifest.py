#!/usr/bin/env python3
"""Create an immutable manifest for a local legal snapshot.

The manifest stores hashes and provenance, not a conclusion about validity.
It lets a later collection be compared without overwriting the version used
for an earlier analysis.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--catalog", type=Path, default=Path("data/catalogo.json"))
    parser.add_argument("--output", type=Path, default=Path("data/snapshot_manifest.json"))
    parser.add_argument("--snapshot-id", help="ID estável; por padrão, data UTC")
    parser.add_argument("--parent-snapshot-id")
    args = parser.parse_args()

    catalog_path = args.root / args.catalog
    payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    snapshot_id = args.snapshot_id or datetime.now(timezone.utc).date().isoformat()
    corpus_dir = args.root / "corpus"
    files = []
    for path in sorted(corpus_dir.glob("leis_*.md")):
        files.append(
            {
                "path": path.relative_to(args.root).as_posix(),
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )

    metadata_files = []
    for relative in (
        "data/source_registry.json",
        "data/federal_source_catalog.json",
        "data/source_harvest_manifest.json",
        "data/connector_catalog.json",
    ):
        path = args.root / relative
        if path.exists():
            metadata_files.append({"path": relative, "size": path.stat().st_size, "sha256": sha256_file(path)})

    records = []
    for record in payload.get("records", []):
        records.append(
            {
                "id": record.get("id"),
                "kind": record.get("kind"),
                "number": record.get("number"),
                "jurisdiction": record.get("jurisdiction"),
                "source_url": record.get("source_url"),
                "corpus_file": record.get("corpus_file"),
                "content_sha256": record.get("content_sha256"),
                "parser_version": record.get("parser_version"),
            }
        )

    manifest = {
        "schema_version": "1.0",
        "snapshot_id": snapshot_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "collection_reference_date": payload.get("collection_reference_date"),
        "parser_version": payload.get("parser_version"),
        "parent_snapshot_id": args.parent_snapshot_id,
        "record_count": len(records),
        "files": files,
        "metadata_files": metadata_files,
        "records": records,
        "validity_notice": "Hashes prove identity of the snapshot; they do not prove vigência, constitucionalidade or applicability.",
    }
    output = args.root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"snapshot_id": snapshot_id, "records": len(records), "files": len(files)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
