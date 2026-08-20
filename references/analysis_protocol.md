# Protocolo de análise exaustiva orientada ao caso

Este roteiro transforma um relato em pesquisa legislativa auditável. Ele deve ser aplicado mesmo quando o usuário aponta uma única área, pois direitos podem estar em normas de outra matéria.

## 1. Fatos e perguntas

- Faça um resumo factual sem qualificações jurídicas prematuras.
- Separe fatos comprovados, alegações, inferências e lacunas.
- Identifique partes, vínculo (trabalhista, contratual, administrativo, penal etc.), lugar, órgão, atividade, grupo protegido e valor.
- Construa datas: origem da relação, evento lesivo, ciência, requerimento, resposta, cessação, tentativa extrajudicial e prazo pretendido.
- Converta o objetivo em perguntas testáveis: “há dever?”, “quem é titular?”, “qual requisito?”, “qual remédio?”, “qual prova?”, “qual prazo?” e “qual consequência se a tese falhar?”.
- Registre a jurisdição e a camada da fonte: lei federal, norma estadual/municipal, ato infralegal, jurisprudência, convenção coletiva ou regra contratual.

## 2. Busca em camadas

1. Consulte `data/source_registry.json` e marque o que é local, externo ou não coberto antes de pesquisar.
   Use `data/federal_source_catalog.json` para não esquecer famílias federais fora do snapshot e `data/connector_catalog.json` para escolher o conector exigido.
2. Use `data/catalogo.json` para localizar tema primário, temas secundários, normas citadas, hashes e marcadores temporais.
3. Percorra `data/grafo_normativo.json` para localizar normas alteradoras, remissões e referências externas; confirme cada relação no texto.
4. Leia todas as entradas dos temas ligados ao fato e as seções completas das normas candidatas.
5. Expanda os termos: sinônimos jurídicos e coloquiais, nome do benefício, órgão responsável, grupo protegido, modalidade de dano, sanção, prova, prazo e procedimento.
   Inclua também variantes de codificação presentes no corpus, como `doença`/`doenea`/`doenęa`, e termos funcionais de saúde e trabalho (`acidente do trabalho`, `doença profissional`, `insalubridade`, `periculosidade`, `CAT` e `nexo causal`).
6. Pesquise números e remissões encontrados (lei alterada, código, artigo, decreto, medida provisória e Constituição).
7. Faça uma varredura de contraprova no corpus: normas que excluem o direito, impõem exceção, restringem legitimidade ou fixam prazo diferente.
8. Para jurisprudência e atos infralegais, registre órgão, tipo, processo/ato, tese, data, situação e inteiro teor; não os misture com a redação de lei.
9. Se a matéria exigir atos fora do corpus, busque a fonte oficial e marque-a como `externa ao acervo`.

10. Se houver acesso à rede, registre a evidência técnica com `scripts/verify_sources.py`; se não houver, marque a fonte como não verificada. Use `scripts/harvest_official.py` somente com manifesto e URL oficial, preservando o HTML bruto.

Registre os termos, arquivos, âncoras, fontes externas, data, `snapshot_id`, hashes e resultado. Um resultado negativo útil deve dizer o que foi pesquisado e qual limite permanece. Uma atualização deve ser comparada com `scripts/compare_snapshots.py`; não descarte a versão anterior.

## 3. Mapa de aplicação

Para cada norma relevante, preencha:

| Campo | Pergunta |
|---|---|
| Regra | Qual artigo/dispositivo governa o fato? |
| Titular/devedor | Quem pode exigir e quem deve cumprir? |
| Requisitos | Quais elementos precisam ser demonstrados? |
| Consequência | Benefício, obrigação, nulidade, reparação, defesa ou sanção? |
| Procedimento | Via administrativa/judicial, competência, legitimidade e rito? |
| Prova | Que documento, testemunha, perícia ou dado demonstra cada elemento? |
| Tempo | Qual data de vigência, prazo, prescrição/decadência e transição? |
| Papel | Direto, subsidiário, analógico, histórico/intertemporal, contextual ou descartado? |
| Risco | Texto contrário, exceção, conflito, constitucionalidade ou jurisprudência? |

## 4. Tese não óbvia

Uma descoberta só é útil quando transforma o texto em hipótese verificável. Explique a ponte entre fato e norma, a razão de não ser apenas uma coincidência de palavras, o requisito que pode faltar e a forma de contestação. Inclua pelo menos uma alternativa mais conservadora e uma razão para rejeitar cada falso positivo.

## 5. Aplicação subsidiária e analogia

Use o índice temático para procurar leis vizinhas, mas fundamente a transposição no texto e na finalidade. Demonstre lacuna, razão comum, compatibilidade e limite. Não use analogia para superar legalidade estrita, criar crime/pena/tributo/multa, alterar competência ou afastar requisito expresso. Em direito processual, justifique a compatibilidade do rito; em relações de trabalho, consumo, saúde e previdência, confronte a norma especial e o regime protetivo.

## 6. Fechamento

Entregue a tabela de normas, a análise de requisitos, o bloco de teses e contrapontos, a verificação de vigência e o plano de prova. Termine com perguntas que o cliente ou advogado precisa responder e com os pontos que devem ser confirmados antes de protocolar.
