#!/usr/bin/env python3
"""Build a heuristic reference graph from the catalogue.

Edges are discovery aids.  They do not prove amendment, repeal, hierarchy or
applicability; the agent must inspect the cited text and official source.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from build_catalog import fold, slug


def reference_key(reference: str) -> tuple[str, str] | None:
    text = fold(reference)
    number_match = re.search(r"(\d[\d.]*)$", text)
    if not number_match:
        return None
    number = number_match.group(1).replace(".", "")
    if "complementar" in text:
        kind = "lei-complementar"
    elif "decreto-lei" in text:
        kind = "decreto-lei"
    elif "decreto" in text:
        kind = "decreto"
    elif "emenda constitucional" in text:
        kind = "emenda-constitucional"
    elif "constituicao" in text:
        kind = "constituicao"
    else:
        kind = "lei-ordinaria"
    return kind, number


def relation_for(record: dict, reference: str) -> str:
    context = fold(f"{record.get('title', '')} {record.get('ementa', '')}")
    if "revog" in context:
        return "possível-revogação"
    if "alter" in context or "acrescent" in context or "modific" in context:
        return "possível-alteração"
    if "regulament" in context:
        return "possível-regulamentação"
    return "remissão"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=Path("data/catalogo.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    args = parser.parse_args()

    payload = json.loads(args.catalog.read_text(encoding="utf-8"))
    records = payload.get("records", [])
    args.output_dir.mkdir(parents=True, exist_ok=True)

    nodes: dict[str, dict] = {}
    by_kind_number: dict[tuple[str, str], str] = {}
    for record in records:
        node_id = record["id"]
        nodes[node_id] = {
            "id": node_id,
            "node_type": "local_norm",
            "jurisdiction": record.get("jurisdiction", "federal"),
            "kind": record.get("kind"),
            "number": record.get("number"),
            "title": record.get("title"),
            "source_url": record.get("source_url"),
            "corpus_file": record.get("corpus_file"),
            "corpus_anchor": record.get("corpus_anchor"),
            "primary_theme": record.get("primary_theme"),
            "content_sha256": record.get("content_sha256"),
        }
        if record.get("number"):
            kind_key = "lei-complementar" if record["kind"] == "lei complementar" else "lei-ordinaria"
            by_kind_number[(kind_key, str(record["number"]))] = node_id

    edges: list[dict] = []
    external_count = 0
    relation_counts: Counter[str] = Counter()
    referenced_counts: Counter[str] = Counter()
    for record in records:
        for reference in record.get("referenced_norms", []):
            key = reference_key(reference)
            if not key:
                continue
            target_id = by_kind_number.get(key)
            if not target_id:
                target_id = f"external-{slug(reference)}"
                if target_id not in nodes:
                    external_count += 1
                    nodes[target_id] = {
                        "id": target_id,
                        "node_type": "external_reference",
                        "jurisdiction": "não confirmada",
                        "label": reference,
                        "requires_official_lookup": True,
                    }
            relation = relation_for(record, reference)
            relation_counts[relation] += 1
            referenced_counts[reference] += 1
            edges.append(
                {
                    "source": record["id"],
                    "target": target_id,
                    "reference": reference,
                    "relation": relation,
                    "confidence": "heurística — confirmar no texto e na fonte oficial",
                }
            )

    graph = {
        "schema_version": "1.0",
        "generated_on": payload.get("generated_on"),
        "warning": "Grafo de descoberta; relações jurídicas devem ser confirmadas no texto integral e na fonte oficial.",
        "node_count": len(nodes),
        "edge_count": len(edges),
        "local_node_count": sum(1 for node in nodes.values() if node["node_type"] == "local_norm"),
        "external_node_count": external_count,
        "relation_counts": dict(relation_counts),
        "most_referenced": [{"reference": ref, "count": count} for ref, count in referenced_counts.most_common(100)],
        "nodes": list(nodes.values()),
        "edges": edges,
    }
    (args.output_dir / "grafo_normativo.json").write_text(json.dumps(graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Grafo normativo de remissões",
        "",
        "> Grafo heurístico para descoberta de normas relacionadas. Uma aresta não prova alteração, revogação, hierarquia ou aplicabilidade.",
        "",
        f"Nós locais: **{graph['local_node_count']}** · referências externas: **{graph['external_node_count']}** · arestas: **{graph['edge_count']}**.",
        "",
        "## Relações extraídas",
        "",
        "| Relação | Quantidade |",
        "|---|---:|",
    ]
    for relation, count in relation_counts.most_common():
        lines.append(f"| {relation} | {count} |")
    lines.extend(["", "## Referências mais frequentes", "", "| Referência | Menções |", "|---|---:|"])
    for item in graph["most_referenced"][:50]:
        lines.append(f"| {item['reference']} | {item['count']} |")
    (args.output_dir / "grafo_normativo.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"nodes": len(nodes), "edges": len(edges), "external_nodes": external_count}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
