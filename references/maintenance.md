# Manutenção e atualização

## Snapshot imutável

Depois de uma coleta:

```text
python scripts/build_catalog.py --corpus-dir corpus --output-dir data --collection-reference-date AAAA-MM-DD
python scripts/build_graph.py --catalog data/catalogo.json --output-dir data
python scripts/build_snapshot_manifest.py --root . --snapshot-id 2026-08-20
```

O manifesto guarda hash do arquivo e de cada norma. Não substitua silenciosamente uma versão usada em um fato passado. Para comparar versões:

```text
python scripts/compare_snapshots.py data/snapshot_manifest_anterior.json data/snapshot_manifest.json
```

## Conferência de fonte

`scripts/verify_sources.py` apenas verifica acessibilidade, hash e marcadores textuais. Ele não decide revogação, constitucionalidade ou eficácia:

```text
python scripts/verify_sources.py --limit 50 --report data/source_verification.json
python scripts/verify_sources.py --offline --report data/source_verification-offline.json
```

Toda resposta deve declarar a data da consulta e distinguir texto local, fonte externa alcançada e fonte não verificada.

## Atualização segura

O workflow de validação executa testes em cada alteração. O workflow de atualização gera um relatório de fontes; não faz commit automático de texto normativo, pois qualquer mudança deve ser revisada, comparada e publicada com o hash correspondente.
