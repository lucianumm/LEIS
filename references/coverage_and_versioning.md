# Cobertura, versionamento e extensões do acervo

## Registro de cobertura

`data/source_registry.json` é a fonte de verdade sobre o que foi ingerido e o que ainda exige consulta externa. Use quatro estados:

- `local_snapshot`: há conteúdo local, mas a situação normativa ainda precisa ser confirmada;
- `official_external`: a fonte oficial está registrada, mas o texto não está no snapshot;
- `connector_required`: a família existe, porém exige conector próprio por órgão/ente;
- `not_covered`: não foi pesquisada e não pode ser usada para afirmar ausência.

Se o caso depender de uma fonte que não esteja em `local_snapshot`, inclua a URL oficial, a data de consulta e a fonte no relatório como `externa ao acervo`.

`data/federal_source_catalog.json` enumera as famílias federais que ainda precisam ser descobertas, incluindo Constituição, emendas, decretos, decretos-leis, medidas provisórias, leis delegadas e atos internacionais. `data/connector_catalog.json` e [references/connectors.md](connectors.md) definem o contrato operacional para tribunais, órgãos, Estados, Municípios e documentos coletivos.

## Campos mínimos de cada norma

O catálogo deve manter:

| Campo | Finalidade |
|---|---|
| `jurisdiction` e `coverage_type` | Impedir uso de norma federal fora da competência ou como se fosse norma local. |
| `source_url` e `source_kind` | Rastrear a publicação e distinguir portal oficial de espelho. |
| `collection_reference_date` | Saber até quando o snapshot foi coletado. |
| `content_sha256` | Detectar alteração do texto entre coletas. |
| `parser_version` e `encoding_warnings` | Reproduzir a extração e saber quando a redação exige confronto visual. |
| `date` | Apoiar o direito intertemporal; não substitui data de vigência. |
| `validity_status` e `validity_flags` | Forçar rechecagem de vigência, revogação e eficácia. |
| `referenced_norms` | Expandir a pesquisa para a cadeia normativa. |

Uma nova coleta deve preservar a versão anterior, gerar novo hash e registrar o diff. Nunca substitua silenciosamente a redação histórica usada para analisar um fato passado.

Use `scripts/build_snapshot_manifest.py` para criar o inventário imutável e `scripts/compare_snapshots.py` para listar inclusões, remoções e alterações. `scripts/verify_sources.py` pode registrar alcance e marcadores da fonte, mas não confere automaticamente todos os efeitos jurídicos.

## Contrato para novos conectores

Todo conector federal, estadual, distrital, municipal, judicial ou administrativo deve produzir, por ato:

```text
source_id
jurisdiction
authority
normative_type
identifier
official_url
publication_date
retrieved_at
status_at_source
effective_from / effective_until (quando disponíveis)
raw_text_sha256
raw_text_or_archived_copy
amendments / revocations / cited_norms
parser_version
```

Falha de rede, página indisponível, captcha ou fonte incompleta deve gerar estado `não confirmado`, nunca um texto vazio tratado como inexistência.

## Grafo e busca

`data/grafo_normativo.json` contém nós locais e referências externas. As relações são heurísticas e devem ser conferidas no artigo citado. `scripts/search_corpus.py` usa `data/search_aliases.json` para expandir sinônimos, variantes sem acento e erros de codificação; os resultados são candidatos, não conclusões.

Jurisprudência deve possuir tipo próprio (`vinculante`, `repetitivo`, `súmula`, `persuasiva`), órgão, processo, data de publicação, tese, situação e link do inteiro teor. Não misture precedente com texto legislativo no mesmo campo de vigência.
