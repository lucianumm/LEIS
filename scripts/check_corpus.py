#!/usr/bin/env python3
"""Validate the generated law catalogue and provenance invariants."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--expected-records", type=int, default=None)
    args = parser.parse_args()
    errors: list[str] = []
    catalog_path = args.root / "data" / "catalogo.json"
    if not catalog_path.exists():
        errors.append(f"catálogo ausente: {catalog_path}")
    else:
        data = json.loads(catalog_path.read_text(encoding="utf-8"))
        records = data.get("records", [])
        declared_count = data.get("record_count")
        expected_records = args.expected_records if args.expected_records is not None else declared_count
        if expected_records is None:
            errors.append("catálogo sem record_count declarado")
        elif len(records) != expected_records:
            errors.append(f"registros: esperado {expected_records}, encontrado {len(records)}")
        ids = [record.get("id") for record in records]
        if len(ids) != len(set(ids)):
            errors.append("IDs de normas duplicados")
        for record in records:
            if not record.get("source_url", "").lower().startswith(("http://www.planalto.gov.br", "https://www.planalto.gov.br")):
                errors.append(f"fonte não oficial/ausente: {record.get('id')}")
            if not record.get("corpus_anchor"):
                errors.append(f"âncora ausente: {record.get('id')}")
            if record.get("validity_status") != "não confirmada — verificar fonte oficial e eficácia temporal":
                errors.append(f"status de validade indevidamente afirmativo: {record.get('id')}")
            if record.get("jurisdiction") != "federal":
                errors.append(f"jurisdição inesperada: {record.get('id')}")
            if not re.fullmatch(r"[0-9a-f]{64}", record.get("content_sha256", "")):
                errors.append(f"hash de conteúdo ausente/inválido: {record.get('id')}")
            if record.get("referenced_norm_count") != len(record.get("referenced_norms", [])):
                errors.append(f"contagem de remissões inconsistente: {record.get('id')}")
            if not record.get("parser_version"):
                errors.append(f"parser_version ausente: {record.get('id')}")

    source_registry_path = args.root / "data" / "source_registry.json"
    if not source_registry_path.exists():
        errors.append(f"registro de fontes ausente: {source_registry_path}")
    else:
        registry = json.loads(source_registry_path.read_text(encoding="utf-8"))
        sources = registry.get("sources", [])
        coverage = registry.get("coverage", [])
        if not sources or not coverage:
            errors.append("registro de fontes sem fontes ou escopos")
        source_ids = {source.get("id") for source in sources}
        for source in sources:
            if not source.get("id") or not source.get("authority"):
                errors.append("fonte sem id/autoridade")
            if not source.get("url", "").startswith("https://"):
                errors.append(f"fonte sem URL HTTPS: {source.get('id')}")
            for local_path in source.get("local_paths", []):
                if not (args.root / local_path).exists():
                    errors.append(f"caminho local de fonte ausente: {local_path}")
        for scope in coverage:
            for source_id in scope.get("source_ids", []):
                if source_id not in source_ids:
                    errors.append(f"escopo referencia fonte inexistente: {source_id}")
        for registry_key in ("federal_source_catalog", "harvest_manifest", "connector_catalog", "verification_script", "snapshot_manifest"):
            target = registry.get(registry_key)
            if target and not (args.root / target).exists():
                errors.append(f"registro aponta para arquivo ausente: {target}")

    for relative in (
        "data/federal_source_catalog.json",
        "data/source_harvest_manifest.json",
        "data/connector_catalog.json",
        "data/snapshot_manifest.json",
        "data/coverage_report.json",
    ):
        if not (args.root / relative).exists():
            errors.append(f"arquivo operacional ausente: {relative}")

    harvest_path = args.root / "data" / "source_harvest_manifest.json"
    if harvest_path.exists():
        harvest = json.loads(harvest_path.read_text(encoding="utf-8"))
        harvest_ids = {source.get("id") for source in harvest.get("sources", [])}
        if not harvest_ids or len(harvest_ids) != len(harvest.get("sources", [])):
            errors.append("manifesto de coleta sem IDs únicos")
        for source in harvest.get("sources", []):
            if not source.get("listing_url") or not source.get("link_pattern"):
                errors.append(f"fonte de coleta incompleta: {source.get('id')}")

    connector_path = args.root / "data" / "connector_catalog.json"
    if connector_path.exists():
        connector = json.loads(connector_path.read_text(encoding="utf-8"))
        connector_ids = {item.get("id") for item in connector.get("connectors", [])}
        if not connector_ids or len(connector_ids) != len(connector.get("connectors", [])):
            errors.append("catálogo de conectores sem IDs únicos")
        for item in connector.get("connectors", []):
            if not item.get("implementation") or not item.get("status"):
                errors.append(f"conector incompleto: {item.get('id')}")

    federal_path = args.root / "data" / "federal_source_catalog.json"
    if federal_path.exists():
        federal = json.loads(federal_path.read_text(encoding="utf-8"))
        families = federal.get("families", [])
        family_ids = {item.get("id") for item in families}
        if not families or len(family_ids) != len(families):
            errors.append("catálogo federal sem famílias únicas")
        for item in families:
            if not item.get("official_listing_url") or not item.get("coverage_status"):
                errors.append(f"família federal incompleta: {item.get('id')}")

    snapshot_path = args.root / "data" / "snapshot_manifest.json"
    if snapshot_path.exists() and catalog_path.exists():
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        if snapshot.get("record_count") != len(records):
            errors.append("snapshot não corresponde ao catálogo")
        snapshot_ids = {item.get("id") for item in snapshot.get("records", [])}
        if snapshot_ids != set(ids):
            errors.append("snapshot não representa os IDs do catálogo")

    coverage_report_path = args.root / "data" / "coverage_report.json"
    if coverage_report_path.exists() and catalog_path.exists():
        coverage_report = json.loads(coverage_report_path.read_text(encoding="utf-8"))
        if coverage_report.get("local_record_count") != len(records):
            errors.append("relatório de cobertura não corresponde ao catálogo")

    aliases_path = args.root / "data" / "search_aliases.json"
    if not aliases_path.exists():
        errors.append(f"aliases ausentes: {aliases_path}")
    else:
        aliases = json.loads(aliases_path.read_text(encoding="utf-8"))
        if not aliases.get("groups") or any(not values for values in aliases["groups"].values()):
            errors.append("grupos de aliases vazios")

    graph_path = args.root / "data" / "grafo_normativo.json"
    if not graph_path.exists():
        errors.append(f"grafo ausente: {graph_path}")
    else:
        graph = json.loads(graph_path.read_text(encoding="utf-8"))
        nodes = graph.get("nodes", [])
        node_ids = {node.get("id") for node in nodes}
        if graph.get("node_count") != len(nodes):
            errors.append("contagem de nós do grafo inconsistente")
        if graph.get("edge_count") != len(graph.get("edges", [])):
            errors.append("contagem de arestas do grafo inconsistente")
        for edge in graph.get("edges", []):
            if edge.get("source") not in node_ids or edge.get("target") not in node_ids:
                errors.append("aresta do grafo aponta para nó inexistente")
                break
        local_nodes = [node for node in nodes if node.get("node_type") == "local_norm"]
        if len(local_nodes) != len(records):
            errors.append("grafo não representa todos os registros locais")

    corpus = args.root / "corpus"
    law_files = sorted(corpus.glob("leis_*.md"))
    required_files = {"leis_complementares.md", "leis_ordinarias_2026.md"}
    if not required_files.issubset({path.name for path in law_files}):
        errors.append("arquivos-base de corpus ausentes")
    if not law_files:
        errors.append("nenhum arquivo de corpus encontrado")
    for path in law_files:
        text = path.read_text(encoding="utf-8", errors="replace")
        if not re.search(r"(?m)^##\s+[^\n]+\.htm\s*$", text):
            errors.append(f"sem seções normativas reconhecíveis: {path.name}")

    # Keep an unrelated proper name out of the skill package; inflected
    # Portuguese legal words inside the verbatim corpus are fine.
    forbidden = "ma" + "n" + "us"
    for path in args.root.rglob("*"):
        if not path.is_file() or ".git" in path.parts or path.suffix.lower() not in {".md", ".py", ".json", ".yaml", ".yml"}:
            continue
        if path.parent.name == "corpus":
            continue
        if re.search(rf"(?i)\b{re.escape(forbidden)}\b", path.read_text(encoding="utf-8", errors="replace")):
            errors.append(f"menção proibida encontrada fora do corpus: {path}")

    if errors:
        print("\n".join(f"ERRO: {error}" for error in errors), file=sys.stderr)
        return 1
    expected_label = args.expected_records if args.expected_records is not None else declared_count
    print(f"OK: catálogo e corpus válidos ({expected_label} registros esperados)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
