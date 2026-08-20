# Escopo, proveniência e limites do corpus

## O que está incluído

O diretório `corpus/` preserva transcrições em Markdown obtidas do Portal da Legislação do Planalto:

| Arquivo | Conteúdo | Quantidade declarada |
|---|---|---:|
| `leis_ordinarias_2026.md` | Leis ordinárias federais de 2026 constantes da listagem consultada | 169 |
| `leis_complementares.md` | Leis complementares catalogadas na listagem consultada | 234 |
| `indice_coleta.md` | Categoria, arquivo, URL de origem e volume textual | 403 registros |
| `criterios_e_fontes.md` | Data, fontes e cautelas da coleta | — |

O catálogo gerado em `data/catalogo.json` deve conter 403 registros enquanto esses arquivos não forem atualizados. A classificação temática é heurística e uma norma pode aparecer em vários índices.

O registro operacional `data/source_registry.json` separa o snapshot local de fontes oficiais externas e de famílias que ainda precisam de conectores. `data/federal_source_catalog.json` enumera categorias federais ainda não ingeridas; `data/source_harvest_manifest.json` e `scripts/harvest_official.py` tornam a descoberta reproduzível; `data/snapshot_manifest.json` conserva hashes para comparação. O grafo em `data/grafo_normativo.json` amplia remissões, mas não transforma uma referência externa em texto pesquisado.

## O que não está incluído

O acervo não é uma consolidação de toda a legislação brasileira. Não presume conter todas as leis ordinárias históricas, decretos, decretos-leis, medidas provisórias, leis delegadas, atos internacionais, Constituição, normas estaduais ou municipais, regulamentos, convenções coletivas, atos administrativos, súmulas ou jurisprudência.

Uma lacuna do corpus não significa inexistência do direito. Quando a questão exigir fonte ausente, busque-a diretamente em bases oficiais e registre que ela não pertence ao acervo local.

Jurisprudência, atos infralegais, normas regulamentadoras, legislação estadual/distrital/municipal, convenções coletivas e regulamentos privados estão registrados como fontes externas ou não cobertas. O agente deve identificar a jurisdição antes de concluir que o snapshot é suficiente. Os conectores e campos mínimos estão em `data/connector_catalog.json` e [references/connectors.md](connectors.md).

## Fontes preferenciais para conferência

Verifique o texto e a situação normativa, conforme o caso, em:

1. [Portal da Legislação Federal do Planalto](https://www4.planalto.gov.br/legislacao)
2. [Base da Legislação Federal Brasileira — Presidência](https://legislacao.presidencia.gov.br/)
3. [Diário Oficial da União](https://www.in.gov.br/)

Use a URL oficial específica do ato no resultado. A data de coleta indicada nos arquivos é 20/08/2026; mudanças posteriores exigem nova consulta.

## Preservação do texto

As páginas de origem tiveram elementos HTML tachados, navegação e scripts removidos. Isso não certifica que toda redação revogada, eficácia limitada ou alteração tácita tenha sido identificada. `leis_complementares.md` também contém trechos com codificação imperfeita; não normalize a redação como se fosse texto oficial. Citações para uso profissional devem ser conferidas na página oficial e, quando relevante, no DOU.
