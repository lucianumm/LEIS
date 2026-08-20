#!/usr/bin/env python3
"""Import a harvested official-law snapshot into a Markdown law corpus.

Only sources explicitly labelled as laws are accepted. Jurisprudence and
infralegal acts stay in their own connector snapshots and are never silently
mixed into the federal-law corpus.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlparse


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot_dir", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest_path = args.snapshot_dir / "manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    normative_type = str(payload.get("normative_type", ""))
    source_id = str(payload.get("source_id", ""))
    if normative_type and "lei" not in normative_type.casefold() and not source_id.startswith("planalto-leis-"):
        raise SystemExit("somente snapshots de leis podem entrar no corpus leis_*.md")
    sections = [
        "# Snapshot de legislação oficial",
        "",
        "> Importação preservando o texto coletado e a fonte. Vigência, eficácia e redação atual exigem conferência oficial.",
        "",
    ]
    imported = 0
    for record in payload.get("records", []):
        text_file = record.get("text_file")
        if not text_file:
            continue
        text_path = args.snapshot_dir / text_file
        if not text_path.exists():
            continue
        parsed = urlparse(record.get("official_url", ""))
        label = record.get("label") or parsed.path.rsplit("/", 1)[-1] or record["id"]
        heading = label if re.search(r"\.htm$", label, re.I) else f"{label}.htm"
        sections.extend(
            [
                "---",
                "",
                f"## {heading}",
                "",
                f"**Fonte:** [{record.get('official_url')}]({record.get('official_url')})",
                "",
                text_path.read_text(encoding="utf-8", errors="replace").strip(),
                "",
            ]
        )
        imported += 1
    if not imported:
        raise SystemExit("nenhum ato textual disponível para importação")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(sections) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "records": imported}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
