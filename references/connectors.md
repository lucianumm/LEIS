# Conectores e fontes externas

## Regra de cobertura

`data/source_registry.json` diz se uma família foi ingerida localmente. `data/connector_catalog.json` descreve como produzir registros para fontes que ainda são externas. Nunca transforme `official_external`, `connector_required` ou `not_covered` em uma conclusão de inexistência.

## Coletor oficial genérico

`scripts/harvest_official.py` recebe um manifesto com `listing_url` e `link_pattern`. Ele:

1. descobre links da página oficial;
2. preserva a resposta bruta;
3. pode extrair uma cópia textual sem apagar o HTML original;
4. grava data de consulta, URL, hash, jurisdição e tipo de ato;
5. deixa o status jurídico como não confirmado.

Exemplos:

```text
python scripts/harvest_official.py --manifest data/source_harvest_manifest.json --source-id planalto-federal-portal --dry-run --limit 20
python scripts/harvest_official.py --manifest data/source_harvest_manifest.json --source-id planalto-leis-complementares --fetch-acts --limit 50
```

Falha de rede, captcha, página vazia ou parser incompleto deve ser registrada como erro de coleta, nunca como ausência da norma. Antes de incorporar qualquer texto, compare o `raw_sha256` e leia a fonte oficial.

## Jurisprudência e infralegal

Precedentes precisam de órgão, identificador do processo/ato, tipo, data de publicação, tese, situação, URL do inteiro teor e hash próprio. Não misture precedente com campo de vigência legislativa. Uma súmula ou precedente vinculante deve ser separado de decisão persuasiva.

## Estados, Distrito Federal e Municípios

Não há um portal nacional uniforme. Para cada ente, registre uma entrada no manifesto contendo autoridade, URL oficial, jurisdição e política de atualização. A ausência de um portal cadastrado significa `connector_required`, não ausência de legislação.

O registro pode ser feito sem editar JSON manualmente:

```text
python scripts/register_source.py --id uf-sp-legislacao --authority "Assembleia Legislativa de São Paulo" --jurisdiction "SP" --normative-type "lei estadual" --listing-url "URL_OFICIAL_DO_ENTE" --link-pattern "PADRAO_DE_LINKS"
```

Substitua a URL e o padrão por valores conferidos no portal oficial do ente. O comando recusa IDs duplicados.

## Convenções, acordos e documentos privados

Só podem ser usados quando o documento do caso estiver disponível. Registre partes, categoria econômica, território, vigência, abrangência subjetiva, cláusulas relevantes e hash do arquivo. Um contrato ou regulamento não deve ser apresentado como lei geral.
