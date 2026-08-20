# Protocolo de vigência, eficácia e direito intertemporal

O catálogo marca toda norma como **não confirmada**. Para cada norma que sustenta uma conclusão, produza um registro de verificação com a data e a fonte consultada.

Use `data/source_registry.json` para declarar se a fonte está no snapshot, é externa ou ainda não coberta. O campo `content_sha256` identifica o texto local consultado, mas não prova vigência. Para uma nova versão, preserve o hash anterior e compare o diff antes de alterar uma conclusão histórica.

## Estados que podem ser usados no relatório

| Estado | Uso correto |
|---|---|
| `vigente — redação conferida` | Fonte oficial indica vigência para a data relevante e a redação usada foi conferida. |
| `vigente com efeitos futuros/condicionados` | A norma existe, mas a produção de efeitos depende de data, regulamento, condição ou transição. |
| `vigência temporária encerrada` | O prazo, exercício, estado de calamidade ou evento de eficácia terminou. |
| `revogada total` | A fonte oficial confirma revogação integral; avalie efeitos passados e direito intertemporal. |
| `revogada parcial / dispositivo alterado` | Apenas parte foi revogada ou substituída; cite somente o trecho ainda aplicável. |
| `não confirmada` | A fonte, o status, a redação consolidada ou a eficácia não foram conferidos. Não use como base conclusiva. |
| `inconstitucionalidade/eficácia controvertida` | Há decisão, liminar, controle concentrado ou controvérsia relevante a confirmar; descreva o alcance. |

## Checklist mínimo

1. Identifique a fonte oficial e abra a página do ato; não dependa apenas do Markdown.
2. Confira número, espécie, data de publicação, ementa, texto integral/consolidado e alterações posteriores.
3. Procure revogação expressa, revogação parcial, dispositivos “revogado”, redações dadas por atos posteriores e remissões quebradas.
4. Leia vigência, produção de efeitos, vacatio legis, prazos finais, exercícios financeiros e cláusulas de transição. “Entra em vigor na publicação” não resolve eficácia de todos os dispositivos.
5. Compare a data de cada fato, requerimento e ajuizamento com a linha do tempo normativa. Para ato histórico, explique qual regra intertemporal conserva ou limita efeitos.
6. Verifique competência legislativa, hierarquia, regulamentação indispensável e eventual conflito com Constituição, tratado ou norma mais específica.
7. Consulte a Base da Legislação e, quando necessário, DOU e fonte de controle de constitucionalidade. Registre a data da consulta, URL e o trecho/resultado relevante.
8. Diferencie `não encontrei revogação` de `vigente`: a primeira é uma busca incompleta; a segunda exige confirmação.
9. Quando a base for jurisprudencial ou infralegal, registre órgão, tipo de ato/precedente, processo ou identificador, data de publicação, tese, situação e inteiro teor separadamente da vigência legislativa.

10. Use `scripts/verify_sources.py` somente como registro de evidência técnica (URL alcançável, data, hash e marcadores). Um HTTP 200, a existência de uma página ou a ausência de um termo de revogação não certificam vigência.

11. Se a coleta mudou, compare os manifestos de snapshot e preserve as versões anteriores. Para fatos antigos, reconstrua a redação e a eficácia aplicáveis à data do fato; o texto atual não substitui o direito intertemporal.

## Registro recomendado

```text
Norma/dispositivo:
Data relevante do caso:
Fonte oficial e URL:
Consultado em:
Redação conferida? (sim/não):
Situação indicada pela fonte:
Vigência/efeitos e transição:
Alterações ou controle de constitucionalidade:
Conclusão e grau de confiança:
```
