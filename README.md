# Skill de análise legislativa brasileira

Este repositório é uma skill instalável para agentes de IA que precisam pesquisar o corpus federal em Markdown com foco em direitos pouco evidentes, normas históricas, analogia e aplicação subsidiária.

O ponto de entrada é [SKILL.md](SKILL.md). O corpus está em `corpus/`, o inventário em `data/catalogo.json`, o registro de cobertura em `data/source_registry.json`, o mapa federal em `data/federal_source_catalog.json`, o manifesto de coleta em `data/source_harvest_manifest.json`, os contratos de conectores em `data/connector_catalog.json`, o grafo de remissões em `data/grafo_normativo.json` e os índices temáticos em `indices/`. O material é uma transcrição técnica com data de referência de 20/08/2026; para qualquer uso profissional, confirme redação, vigência, eficácia, competência e controle de constitucionalidade nas fontes oficiais.

Para regenerar os índices após atualizar os Markdown:

```text
python scripts/build_catalog.py --corpus-dir corpus --output-dir data --collection-reference-date AAAA-MM-DD
python scripts/build_graph.py --catalog data/catalogo.json --output-dir data
python scripts/build_snapshot_manifest.py --root . --snapshot-id AAAA-MM-DD
python scripts/build_coverage_report.py --root . --output-dir data
python scripts/search_corpus.py --group doenca_ocupacional --theme trabalho
python scripts/verify_sources.py --limit 50 --report data/source_verification.json
python scripts/check_corpus.py --root .
python scripts/run_evaluation.py
```

Para descobrir atos em uma fonte oficial cadastrada, use `scripts/harvest_official.py`; leia [references/connectors.md](references/connectors.md) antes de ingerir qualquer resposta. A coleta preserva o bruto e não certifica vigência.
