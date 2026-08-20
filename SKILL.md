---
name: leis-analise-br
description: Analyze Brazilian federal-law Markdown corpora for a concrete case, finding direct, historical, analogous and subsidiary bases with mandatory official vigency checks and cited, uncertainty-aware outputs.
metadata:
  short-description: Pesquisa legislativa brasileira verificável
---

# Análise legislativa brasileira orientada ao caso

Use esta skill quando o usuário pedir pesquisa jurídica brasileira, descoberta de direitos, enquadramento de fatos, preparação de ação/defesa ou levantamento de legislação potencialmente esquecida. A skill percorre o corpus federal em Markdown, organiza as normas por tema e procura também normas históricas, conexas, análogas e de aplicação subsidiária.

## Limite essencial

Abra a resposta jurídica com: **“Sou uma IA, não um advogado — esta é uma análise de trabalho, não aconselhamento jurídico formal; um profissional habilitado deve revisar qualquer medida antes de uso ou protocolo.”**

Não prometa “100% de certeza”. Nenhuma transcrição, busca ou modelo certifica sozinha vigência integral, constitucionalidade, interpretação judicial ou resultado processual. Dê uma análise concreta, indique o grau de confiança, registre o que foi confirmado e o que ainda exige conferência. Nunca invente artigo, redação, precedente, prazo, revogação ou fato ausente.

O material local é um recorte de **legislação federal**: 169 leis ordinárias de 2026 e 234 leis complementares catalogadas no Portal da Legislação, com data de referência declarada de 20/08/2026. O mapa de famílias federais, o coletor e os conectores estão em `data/federal_source_catalog.json`, `data/source_harvest_manifest.json`, `data/connector_catalog.json` e [references/connectors.md](references/connectors.md). Eles tornam a expansão reproduzível, mas não transformam fontes externas em texto pesquisado. O acervo local ainda não contém toda a legislação brasileira, nem substitui Constituição, decretos, medidas provisórias, atos estaduais/municipais, tratados, normas coletivas, regulamentos ou jurisprudência. Leia [references/source_scope.md](references/source_scope.md), [references/coverage_and_versioning.md](references/coverage_and_versioning.md) e consulte `data/source_registry.json` antes de descrever o alcance.

## Como usar o acervo

1. Leia `data/source_registry.json` para saber se a jurisdição e o tipo de fonte estão no snapshot, são externos ou ainda não cobertos. Nunca interprete uma lacuna do registro como inexistência de norma.
2. Leia `data/catalogo.json` para obter o inventário completo, hashes de conteúdo, remissões e sinais de descoberta. Use `indices/README.md` e os índices temáticos para localizar famílias de normas.
3. Use `data/grafo_normativo.json` para expandir remissões, normas alteradoras e referências externas. Toda aresta é heurística: leia o artigo e confirme a relação na fonte oficial.
4. Abra a seção integral correspondente em `corpus/leis_complementares.md` ou `corpus/leis_ordinarias_2026.md`. O índice nunca substitui a leitura do texto normativo.
5. Para busca semântica e variações de codificação, prefira `search_corpus.py` com os grupos de `data/search_aliases.json`; use `rg` quando precisar de contexto bruto. Pesquise sinônimos, atos, instituições, remédios, prazos, grupos protegidos e a cadeia de normas citadas.
6. Se o caso for amplo, ambíguo ou de alto impacto, faça uma varredura de **todas as entradas declaradas em `data/catalogo.json`** em passagens/chunks, registre termos pesquisados e anote resultados positivos e negativos. Não selecione apenas a primeira categoria que parece adequada.
7. O corpus mantém o texto coletado; há trechos com problemas de codificação e elementos editoriais. Não “corrija” silenciosamente a redação. Para qualquer citação relevante, confronte o texto original em fonte oficial.

O catálogo é regenerável:

```text
python scripts/build_catalog.py --corpus-dir corpus --output-dir data --collection-reference-date AAAA-MM-DD
python scripts/build_graph.py --catalog data/catalogo.json --output-dir data
python scripts/search_corpus.py --group doenca_ocupacional --theme trabalho --limit 25
python scripts/build_snapshot_manifest.py --root . --snapshot-id AAAA-MM-DD
python scripts/build_coverage_report.py --root . --output-dir data
python scripts/verify_sources.py --limit 50 --report data/source_verification.json
python scripts/check_corpus.py --root .
python scripts/run_evaluation.py
```

## Protocolo obrigatório para cada caso

Leia [references/analysis_protocol.md](references/analysis_protocol.md) para o procedimento detalhado. Em síntese:

1. **Delimite jurisdição e escopo.** Identifique país, ente federativo, órgão, ramo, tipo de fonte e data relevante. Consulte o registro de cobertura; se for estadual, municipal, coletivo, infralegal ou jurisprudencial e não houver snapshot, marque a fonte como externa/não coberta e busque-a oficialmente.
2. **Delimite o problema.** Extraia fatos provados e alegados, partes, vínculo jurídico, local/competência, datas de cada evento, objetivo, procedimento pretendido, valor, urgência e prova disponível. Separe perguntas em aberto de premissas.
3. **Monte uma linha do tempo.** A data do fato, do dano, do requerimento, da ciência e da ação pode mudar a lei aplicável, prescrição/decadência, vacatio legis e direito intertemporal. Use o hash e a data do snapshot apenas para rastreabilidade, nunca como prova de vigência.
4. **Faça a varredura ampla.** Comece pelos temas primários e secundários de `data/catalogo.json`, percorra o grafo de remissões e use grupos de aliases. Faça uma segunda busca fora do tema inicial por termos funcionais (dever, benefício, sanção, prazo, competência, prova, reparação e procedimento). Inclua atos antigos quando a relação jurídica ou os fatos forem antigos.
5. **Construa a cadeia normativa.** Para cada hipótese, identifique Constituição/princípio, lei, alteração, regulamentação necessária, norma processual, competência, ato infralegal e jurisprudência a confirmar. Distinga texto original, redação atual, dispositivo transitório, precedente vinculante e decisão persuasiva.
6. **Classifique a forma de uso.** Marque cada item como `direto`, `subsidiário`, `analógico`, `histórico/intertemporal`, `contextual`, `jurisprudência obrigatória`, `jurisprudência persuasiva`, `fonte externa` ou `descartado`. Explique a compatibilidade, a lacuna e o limite; analogia não é autorização para ignorar texto expresso.
7. **Verifique validade e eficácia.** Siga [references/validity.md](references/validity.md): fonte oficial, alterações, revogação total/parcial, vigência temporária, produção de efeitos, vacatio, controle de constitucionalidade, competência e data do fato. O status padrão do catálogo é “não confirmada”.
8. **Procure direitos não óbvios sem forçar a tese.** Para cada candidato, descreva titular, dever do sujeito passivo, fato gerador, requisito, prazo, prova, remédio, risco de interpretação e se existe via administrativa ou judicial. Inclua argumentos contrários e normas que parecem próximas, mas não se aplicam.
9. **Feche com ação verificável.** Entregue próximos passos, documentos a reunir, prazos a conferir, perguntas para o cliente e pontos que exigem advogado/órgão competente. Não protocole, assine, envie ou execute medidas irreversíveis sem confirmação explícita do usuário.

## Analogia, subsidiariedade e limites

Use a matriz de [references/thematic_matrix.md](references/thematic_matrix.md) apenas como roteiro de busca. Para propor analogia ou aplicação subsidiária, demonstre: (a) qual é a lacuna ou relação de subsidiariedade; (b) qual é a razão jurídica comum; (c) por que o texto, a competência e a finalidade são compatíveis; (d) qual é o limite e qual norma prevalece em caso de conflito.

Redobre o controle em matéria penal, sancionadora, tributária e processual: não use analogia para criar crime, pena, tributo, multa, requisito mais gravoso ou competência sem base legal; verifique legalidade, tipicidade, anterioridade, devido processo, contraditório e regras de competência. Uma analogia favorável pode ser discutida apenas quando admitida pelo ordenamento e sem contrariar norma expressa. Em trabalho, previdência, consumo, saúde e direitos humanos, teste proteção constitucional, compatibilidade setorial e eventual norma mais específica.

## Formato de saída

Siga o contrato de [references/output_schema.md](references/output_schema.md). O resultado deve conter, nesta ordem:

1. disclaimer e escopo da análise;
2. fatos, premissas e linha do tempo;
3. mapa de questões e temas pesquisados;
4. tabela de normas com artigo/dispositivo, citação, fonte, status/eficácia confirmado, papel (direto/subsidiário/analógico etc.), requisitos e risco;
5. direitos, teses e remédios possíveis, inclusive candidatos “não óbvios”;
6. normas históricas ou análogas, com razão jurídica e limites;
7. normas excluídas e motivo (revogada, temporal, incompetente, incompatível, prova ausente ou mera referência);
8. conflitos, argumentos contrários, prescrição/decadência e questões em aberto;
9. plano de prova e próximos passos, com links oficiais e data da verificação.

Use citações precisas (norma, artigo/parágrafo/inciso, redação conferida e URL oficial). Se a redação local estiver ilegível, transcreva somente depois da conferência oficial e sinalize a discrepância. Não trate uma classificação temática, ausência de revogação expressa ou resultado de busca como prova de aplicabilidade.

## Controle de qualidade

Antes de finalizar, confirme:

- cada conclusão importante está ligada a um dispositivo e a uma fonte oficial;
- o recorte federal e a data de referência foram declarados;
- a jurisdição, o tipo de fonte e a cobertura consultada foram declarados;
- a vigência foi verificada para a data relevante, não apenas para hoje;
- jurisprudência, ato infralegal, norma estadual/municipal e regra coletiva foram separados da lei federal;
- foram examinadas normas relacionadas, históricas e subsidiárias, com busca negativa registrada;
- remissões do grafo foram confirmadas no texto e não tratadas como fatos automáticos;
- analogias não criam sanção, tributo, crime, competência ou direito sem base;
- fatos, prazos, legitimidade, prova e procedimento não foram presumidos;
- incertezas e argumentos contrários estão visíveis;
- o manifesto do snapshot, os hashes e as diferenças entre versões foram registrados quando houver atualização;
- qualquer fonte externa foi identificada com URL, data de consulta, tipo de conector e status não confirmado;
- os resultados da busca comportamental (`python scripts/run_evaluation.py`) continuam reproduzíveis;
- nenhuma instrução ou nome estranho ao trabalho jurídico foi inserido no pacote.
