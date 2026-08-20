#!/usr/bin/env python3
"""Build a machine-readable and human-readable coverage report."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    args = parser.parse_args()
    root = args.root
    registry = json.loads((root / "data/source_registry.json").read_text(encoding="utf-8"))
    catalog = json.loads((root / "data/catalogo.json").read_text(encoding="utf-8"))
    federal = json.loads((root / "data/federal_source_catalog.json").read_text(encoding="utf-8"))
    connectors = json.loads((root / "data/connector_catalog.json").read_text(encoding="utf-8"))
    coverage_counts = Counter(item.get("status") for item in registry.get("coverage", []))
    family_counts = Counter(item.get("coverage_status") for item in federal.get("families", []))
    report = {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "local_record_count": len(catalog.get("records", [])),
        "local_corpus_files": catalog.get("corpus_files", []),
        "registry_coverage_counts": dict(coverage_counts),
        "federal_family_counts": dict(family_counts),
        "connector_count": len(connectors.get("connectors", [])),
        "source_count": len(registry.get("sources", [])),
        "limitations": [
            "local_snapshot não certifica vigência",
            "fontes externas exigem consulta e registro de data",
            "Estados, Municípios e documentos coletivos precisam de fonte própria",
        ],
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "coverage_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Relatório de cobertura",
        "",
        f"Gerado em: **{report['generated_at']}**",
        "",
        f"Registros locais: **{report['local_record_count']}**",
        f"Arquivos de corpus: {', '.join(report['local_corpus_files'])}",
        f"Fontes registradas: **{report['source_count']}** · conectores: **{report['connector_count']}**",
        "",
        "## Situação dos escopos",
        "",
        "| Estado | Quantidade |",
        "|---|---:|",
    ]
    for key, value in sorted(coverage_counts.items()):
        lines.append(f"| {key} | {value} |")
    lines.extend(["", "## Famílias federais", "", "| Cobertura | Quantidade |", "|---|---:|"])
    for key, value in sorted(family_counts.items()):
        lines.append(f"| {key} | {value} |")
    lines.extend(["", "> Este relatório é um mapa de alcance, não um certificado de vigência ou aplicabilidade."])
    (args.output_dir / "coverage_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"records": report["local_record_count"], "coverage": dict(coverage_counts)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
