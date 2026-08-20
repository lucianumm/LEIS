#!/usr/bin/env python3
"""Compare two snapshot manifests and report provenance changes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def record_map(path: Path) -> dict[str, dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {item["id"]: item for item in payload.get("records", []) if item.get("id")}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    before = record_map(args.before)
    after = record_map(args.after)
    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    changed = sorted(
        record_id
        for record_id in set(before) & set(after)
        if before[record_id].get("content_sha256") != after[record_id].get("content_sha256")
        or before[record_id].get("source_url") != after[record_id].get("source_url")
    )
    result = {
        "before": str(args.before),
        "after": str(args.after),
        "added": added,
        "removed": removed,
        "changed": changed,
        "unchanged_count": len(set(before) & set(after)) - len(changed),
    }
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Adicionadas: {len(added)}")
        print(f"Removidas: {len(removed)}")
        print(f"Alteradas: {len(changed)}")
        print(f"Inalteradas: {result['unchanged_count']}")
        for label in ("added", "removed", "changed"):
            if result[label]:
                print(f"{label}: {', '.join(result[label])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
