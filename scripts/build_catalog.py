#!/usr/bin/env python3
"""Build a searchable thematic catalogue from the Markdown law corpus.

The corpus is intentionally preserved verbatim.  This script only extracts
metadata and creates indexes; it never labels a norm as legally valid merely
because it appears in the collection.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Iterable


SECTION_RE = re.compile(r"(?m)^##\s+([^\n]+?)\s*$")
SOURCE_RE = re.compile(r"\*\*Fonte:\*\*\s*\[([^\]]+)\]\(([^)]+)\)", re.I)
TITLE_RE = re.compile(r"\bLEI(?:\s+COMPLEMENTAR)?\s+N[^\d\n]{0,8}[\d.]+", re.I)
NUMBER_RE = re.compile(r"\bN[^\d\n]{0,8}([\d][\d.]*)", re.I)
DATE_RE = re.compile(
    r"\bDE\s+(\d{1,2})(?:\s*[º°ªş║])?\s+DE\s+([A-ZÀ-ÚĒĻ][A-ZÀ-ÚĻĒa-zà-úēļ]{2,})\s+DE\s+(\d{4})",
    re.I,
)

MONTHS = {
    "janeiro": 1,
    "fevereiro": 2,
    "marco": 3,
    "abril": 4,
    "maio": 5,
    "junho": 6,
    "julho": 7,
    "agosto": 8,
    "setembro": 9,
    "outubro": 10,
    "novembro": 11,
    "dezembro": 12,
}

CORPUS_REFERENCE_DATE = "2026-08-20"
PARSER_VERSION = "3.0"


# Terms are deliberately conservative.  They are discovery signals, not a
# legal conclusion.  A law may belong to several themes.
THEMES: dict[str, tuple[str, ...]] = {
    "trabalho": (
        "trabalho",
        "trabalhador",
        "empregado",
        "empregador",
        "salario",
        "remuneracao",
        "jornada",
        "sindical",
        "aprendiz",
        "fgts",
        "seguro-desemprego",
        "acidente do trabalho",
        "acidente de trabalho",
        "doenca ocupacional",
        "doenea ocupacional",
        "doenca profissional",
        "doenea profissional",
        "insalubridade",
        "periculosidade",
        "nexo causal",
        "nexo tecnico",
        "comunicacao de acidente",
    ),
    "previdenciario": (
        "previdencia",
        "previdenciario",
        "segurado",
        "aposentadoria",
        "aposentado",
        "pensao por morte",
        "beneficio previdenciario",
        "regime geral",
        "inss",
        "acidente do trabalho",
        "auxilio-acidente",
        "auxilio por incapacidade",
        "nexo tecnico",
    ),
    "criminal": (
        "codigo penal",
        "crime",
        "criminal",
        "penal",
        "prisao",
        "penitenciario",
        "policial penal",
        "violencia",
        "trafico",
        "lavagem de dinheiro",
    ),
    "processual": (
        "processo civil",
        "processual",
        "acao judicial",
        "recurso",
        "competencia jurisdicional",
        "procedimento",
        "juizado",
        "tribunal",
        "justica",
        "arbitragem",
    ),
    "civil": (
        "codigo civil",
        "responsabilidade civil",
        "obrigacao",
        "contrato",
        "propriedade",
        "posse",
        "indenizacao",
        "pessoa juridica",
    ),
    "familia_e_sucessoes": (
        "familia",
        "casamento",
        "divorcio",
        "alimentos",
        "guarda",
        "adocao",
        "sucessao",
        "heranca",
    ),
    "consumidor": (
        "consumidor",
        "fornecedor",
        "relacao de consumo",
        "defesa do consumidor",
        "superendividamento",
    ),
    "tributario": (
        "tributo",
        "imposto",
        "contribuicao social",
        "contribuicao para",
        "contribuicao de melhoria",
        "receita federal",
        "icms",
        "iss",
        "ibs",
        "cbs",
        "ipi",
        "irpj",
        "irpf",
        "simples nacional",
        "aduaneiro",
    ),
    "financeiro_orcamentario": (
        "orcamento",
        "credito publico",
        "divida publica",
        "tesouro nacional",
        "banco central",
        "fundo constitucional",
        "operacao de credito",
        "transferencia voluntaria",
        "responsabilidade fiscal",
    ),
    "empresarial": (
        "empresa",
        "empresarial",
        "sociedade empresaria",
        "companhia",
        "falencia",
        "recuperacao judicial",
        "microempresa",
        "empreendedor",
        "cooperativa",
    ),
    "administrativo": (
        "administracao publica",
        "servidor publico",
        "servico publico",
        "autarquia",
        "licitacao",
        "contrato administrativo",
        "cargo publico",
        "orgao publico",
        "concessao",
        "permissao",
    ),
    "constitucional": (
        "constituicao federal",
        "direito fundamental",
        "cidadania",
        "nacionalidade",
        "separacao dos poderes",
        "federalismo",
        "controle de constitucionalidade",
    ),
    "direitos_humanos": (
        "direitos humanos",
        "igualdade",
        "discriminacao",
        "dignidade da pessoa humana",
        "mulher",
        "crianca",
        "adolescente",
        "idoso",
        "refugiado",
        "pessoa com deficiencia",
        "acessibilidade",
    ),
    "saude": (
        "saude",
        "sus",
        "hospital",
        "medico",
        "medicamento",
        "paciente",
        "epidem",
        "vigilancia sanitaria",
        "atendimento pre-hospitalar",
        "plano de saude",
        "saude ocupacional",
        "medicina do trabalho",
        "acidente de trabalho",
        "doenca ocupacional",
        "doenea ocupacional",
    ),
    "ambiental": (
        "meio ambiente",
        "ambiental",
        "floresta",
        "biodiversidade",
        "residuo",
        "saneamento",
        "fauna",
        "flora",
        "recursos hidricos",
        "mudanca climatica",
    ),
    "agrario": (
        "agricultura",
        "agricultor",
        "rural",
        "produtor rural",
        "reforma agraria",
        "imovel rural",
        "pecuaria",
        "pesca",
        "agricultura familiar",
        "agropec",
    ),
    "educacao_ciencia": (
        "educacao",
        "ensino",
        "escola",
        "universidade",
        "pesquisa cientifica",
        "ciencia e tecnologia",
        "estudante",
    ),
    "digital_dados_telecom": (
        "internet",
        "telecomunic",
        "dados pessoais",
        "protecao de dados",
        "tecnologia da informacao",
        "informatica",
        "inteligencia artificial",
        "comunicacao eletronica",
        "radiodifusao",
    ),
    "transporte_infraestrutura": (
        "transporte",
        "transito",
        "rodovia",
        "ferrovi",
        "aviacao",
        "aeroporto",
        "porto",
        "mobilidade urbana",
        "infraestrutura",
        "energia eletrica",
    ),
    "eleitoral": (
        "eleicao",
        "eleitoral",
        "eleitor",
        "plebiscito",
        "referendo",
        "partido politico",
        "voto",
    ),
    "militar_defesa": (
        "forcas armadas",
        "militar",
        "defesa nacional",
        "exercito",
        "marinha",
        "aeronautica",
        "seguranca nacional",
    ),
    "cultura_desporto_turismo": (
        "cultura",
        "patrimonio cultural",
        "desporto",
        "esporte",
        "turismo",
        "museu",
    ),
    "propriedade_intelectual": (
        "propriedade intelectual",
        "patente",
        "marca",
        "direito autoral",
        "cultivares",
    ),
    "internacional": (
        "tratado internacional",
        "convencao internacional",
        "acordo internacional",
        "cooperacao internacional",
        "diplomatic",
    ),
}


THEME_LABELS = {
    "trabalho": "Trabalho",
    "previdenciario": "Previdenciário",
    "criminal": "Criminal",
    "processual": "Processual",
    "civil": "Civil",
    "familia_e_sucessoes": "Família e sucessões",
    "consumidor": "Consumidor",
    "tributario": "Tributário",
    "financeiro_orcamentario": "Financeiro e orçamentário",
    "empresarial": "Empresarial",
    "administrativo": "Administrativo",
    "constitucional": "Constitucional",
    "direitos_humanos": "Direitos humanos e grupos protegidos",
    "saude": "Saúde",
    "ambiental": "Ambiental",
    "agrario": "Agrário e agropecuário",
    "educacao_ciencia": "Educação, ciência e tecnologia",
    "digital_dados_telecom": "Digital, dados e telecomunicações",
    "transporte_infraestrutura": "Transporte e infraestrutura",
    "eleitoral": "Eleitoral",
    "militar_defesa": "Militar e defesa",
    "cultura_desporto_turismo": "Cultura, desporto e turismo",
    "propriedade_intelectual": "Propriedade intelectual",
    "internacional": "Internacional",
    "outros": "Outros / institucional",
}


# The matrix is used for discovery only.  It tells the agent which bodies of
# law to inspect for subsidiary or analogous arguments; it is not an authority
# for applying one theme to another.
SUBSIDIARY: dict[str, tuple[str, ...]] = {
    "trabalho": ("previdenciario", "civil", "processual", "constitucional", "direitos_humanos", "saude"),
    "previdenciario": ("constitucional", "saude", "trabalho", "processual", "direitos_humanos", "tributario"),
    "criminal": ("processual", "constitucional", "direitos_humanos", "digital_dados_telecom", "saude"),
    "processual": ("constitucional", "civil", "criminal", "administrativo", "trabalho"),
    "civil": ("constitucional", "processual", "consumidor", "empresarial", "ambiental"),
    "familia_e_sucessoes": ("civil", "constitucional", "direitos_humanos", "processual", "previdenciario"),
    "consumidor": ("civil", "empresarial", "digital_dados_telecom", "saude", "processual"),
    "tributario": ("constitucional", "empresarial", "financeiro_orcamentario", "agrario", "processual"),
    "financeiro_orcamentario": ("tributario", "administrativo", "constitucional", "empresarial"),
    "empresarial": ("civil", "tributario", "trabalho", "consumidor", "processual"),
    "administrativo": ("constitucional", "processual", "financeiro_orcamentario", "trabalho", "ambiental"),
    "constitucional": ("direitos_humanos", "administrativo", "processual", "eleitoral", "tributario"),
    "direitos_humanos": ("constitucional", "civil", "criminal", "trabalho", "saude", "familia_e_sucessoes"),
    "saude": ("constitucional", "consumidor", "administrativo", "trabalho", "previdenciario", "ambiental"),
    "ambiental": ("constitucional", "administrativo", "civil", "criminal", "agrario", "empresarial"),
    "agrario": ("ambiental", "civil", "tributario", "trabalho", "empresarial"),
    "educacao_ciencia": ("constitucional", "administrativo", "trabalho", "direitos_humanos", "digital_dados_telecom"),
    "digital_dados_telecom": ("consumidor", "civil", "criminal", "constitucional", "empresarial", "processual"),
    "transporte_infraestrutura": ("administrativo", "ambiental", "civil", "trabalho", "tributario"),
    "eleitoral": ("constitucional", "administrativo", "processual", "criminal", "financeiro_orcamentario"),
    "militar_defesa": ("constitucional", "administrativo", "criminal", "previdenciario", "trabalho"),
    "cultura_desporto_turismo": ("civil", "trabalho", "tributario", "administrativo", "direitos_humanos"),
    "propriedade_intelectual": ("civil", "empresarial", "digital_dados_telecom", "processual", "tributario"),
    "internacional": ("constitucional", "administrativo", "civil", "criminal", "direitos_humanos"),
    "outros": ("constitucional", "administrativo", "processual"),
}


def fold(value: str) -> str:
    """Accent-insensitive text for search; source text is never rewritten."""

    value = value.replace("Ļ", "L").replace("Ē", "E").replace("║", "")
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.lower().replace("ş", "s").replace("º", "o").replace("ª", "a")
    value = re.sub(r"\s+", " ", value)
    return value


def slug(value: str) -> str:
    value = fold(value).strip().replace(" ", "-")
    return re.sub(r"[^a-z0-9_-]", "", value)


def clean_cell(value: str, limit: int = 900) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    if len(value) > limit:
        value = value[: limit - 1].rstrip() + "…"
    return value.replace("|", "\\|")


def parse_date(title: str, body: str) -> str | None:
    # The date in the official act heading is authoritative for this
    # metadata.  Searching the body first would accidentally capture the
    # date of a law being amended (for example, "Altera a Lei ..., de 1994").
    for match in DATE_RE.finditer(title):
        month = MONTHS.get(fold(match.group(2)))
        if month:
            try:
                return date(int(match.group(3)), month, int(match.group(1))).isoformat()
            except ValueError:
                pass
    # A few legacy Planalto headings omit the second "DE" and use a comma:
    # "LEI COMPLEMENTAR Nş 192, 11 DE MARÇO DE 2022".  The title is still
    # the source of truth, so accept that editorial variation without
    # searching arbitrary dates in the body.
    malformed = re.compile(
        r"\bN[^\d\n]{0,8}[\d.]+\s*[,;]\s*(\d{1,2})(?:\s*[º°ªş║])?\s+DE\s+"
        r"([A-ZÀ-ÚĒĻ][A-ZÀ-ÚĻĒa-zà-úēļ]{2,})\s+DE\s+(\d{4})",
        re.I,
    )
    for match in malformed.finditer(title):
        month = MONTHS.get(fold(match.group(2)))
        if month:
            try:
                return date(int(match.group(3)), month, int(match.group(1))).isoformat()
            except ValueError:
                pass
    # A small fallback is useful for malformed/legacy headings, but still
    # restricts the search to the official header area rather than the body.
    for match in DATE_RE.finditer(body[:1000]):
        month = MONTHS.get(fold(match.group(2)))
        if month:
            try:
                return date(int(match.group(3)), month, int(match.group(1))).isoformat()
            except ValueError:
                pass
    return None


def extract_ementa(lines: list[str], title_index: int | None) -> str:
    start = (title_index + 1) if title_index is not None else 0
    chunks: list[str] = []
    started = False
    for line in lines[start:]:
        text = line.strip()
        if not text:
            if started:
                break
            continue
        norm = fold(text)
        if re.match(r"^(o )?(presidente|congresso|senado|fa[cç]o saber|nos termos)", norm):
            break
        if re.match(r"^art\.?\s*1", norm) or norm.startswith("artigo 1"):
            break
        if norm.startswith("este texto nao substitui"):
            break
        if text.startswith("**Fonte:") or norm.startswith("presidencia da republica"):
            continue
        if not started:
            # Planalto headers sometimes prepend an editorial label to the
            # same line as the ementa.  Remove only that label; preserve the
            # substantive remainder (important for old acts with "Mensagem
            # de veto" or "Produção de efeito").
            for prefix in (
                "mensagem de veto",
                "texto para impressao",
                "producao de efeito",
                "producao de efeitos",
                "regulamento",
                "vigencia",
                "texto compilado",
            ):
                if norm == prefix:
                    text = ""
                    norm = ""
                    break
                if norm.startswith(prefix + " "):
                    text = text[len(prefix) :].lstrip(" :-")
                    norm = fold(text)
                    break
            if not text:
                continue
        # The first line after the official title is the ementa.  Keep a
        # continuation line when the ementa wraps, but do not absorb the body.
        started = True
        chunks.append(text)
        if len(" ".join(chunks)) >= 1000:
            break
    return clean_cell(" ".join(chunks), 1000).replace("\\|", "|")


def extract_title_index(lines: list[str]) -> int | None:
    for i, line in enumerate(lines[:80]):
        if TITLE_RE.search(line):
            return i
    return None


def extract_number(heading: str, title: str) -> str | None:
    match = NUMBER_RE.search(title)
    if not match:
        match = re.search(r"(\d{2,6})", heading)
    return match.group(1).replace(".", "") if match else None


def source_url(body: str) -> str | None:
    match = SOURCE_RE.search(body)
    if match:
        return match.group(2).strip()
    match = re.search(r"https?://[^\s)]+", body)
    return match.group(0).rstrip(".,;") if match else None


def encoding_warnings(value: str) -> list[str]:
    """Return conservative signals for source encoding damage.

    The verbatim corpus is never rewritten.  These markers only tell the
    agent when an official-source comparison is especially important.
    """

    markers = {
        "latin1_mojibake": "ÃÂ",
        "source_replacement_chars": "�",
        "editorial_cp1252": "ĻĒ║ńķŃŅŀŊŔ",
    }
    return [name for name, chars in markers.items() if any(char in value for char in chars)]


def classify(text: str, extra_text: str = "") -> tuple[dict[str, int], str, list[str]]:
    normalized = fold(text)
    extra_normalized = fold(extra_text)
    scores: dict[str, int] = {}
    for theme, terms in THEMES.items():
        score = 0
        for term in terms:
            # Stems ending in a letter are intentionally substring matches;
            # this catches inflections without pretending to be NLP.
            # Title/ementa are weighted more heavily than the opening body:
            # amendment targets and annexes should not drown out the act's
            # own subject, while Art. 1 and the first operative provisions
            # still rescue generic ementas.
            score += min(normalized.count(term), 10) * 4
            # Only a few opening-body hits may supplement the ementa.  A
            # hard cap prevents repeated cross-references in Art. 2+ or an
            # annex from becoming the primary subject of the act.
            score += min(extra_normalized.count(term), 3)
        if score:
            scores[theme] = score
    if not scores or max(scores.values()) < 2:
        return scores, "outros", []
    ranked = sorted(scores, key=lambda item: (-scores[item], item))
    primary = ranked[0]
    secondary = [item for item in ranked[1:] if scores[item] >= max(2, scores[primary] // 3)][:5]
    return scores, primary, secondary


def temporal_flags(body: str) -> tuple[list[str], list[str]]:
    flags: list[str] = []
    markers: list[str] = []
    for raw_line in body.splitlines():
        line = raw_line.strip()
        norm = fold(line)
        if any(token in norm for token in ("revogad", "revogacao", "revoga-se", "redacao dada", "incluido pela")):
            if "menção a revogação ou alteração" not in flags:
                flags.append("menção a revogação ou alteração")
            if len(markers) < 4:
                markers.append(line[:300])
        if any(token in norm for token in ("vigencia", "producao de efeitos", "entra em vigor", "ate o final", "exercicio de 20", "prazo determinado")):
            if "marcador temporal/eficácia" not in flags:
                flags.append("marcador temporal/eficácia")
            if len(markers) < 4:
                markers.append(line[:300])
    return flags, markers


def referenced_norms(body: str) -> list[str]:
    pattern = re.compile(
        r"\b(Leis?(?:\s+Complementares?)?|Decretos?(?:-Leis?)?|"
        r"Emendas?\s+Constitucionais?|Constitui[cç][aã]o)\s+"
        r"(?:(?:n|no|nos)\s*[º°ªa-z║ş]*\s*)?"
        r"((?:\d[\d.]*(?:\s*(?:e|,|/)\s*)?)+)",
        re.I,
    )
    out: list[str] = []
    seen: set[str] = set()
    for match in pattern.finditer(body):
        label = re.sub(r"\s+", " ", match.group(1)).strip()
        display_label = {
            "Leis": "Lei",
            "Leis Complementares": "Lei Complementar",
            "Decretos": "Decreto",
            "Decretos-Leis": "Decreto-Lei",
            "Emendas Constitucionais": "Emenda Constitucional",
        }.get(label, label)
        numbers = re.findall(r"\d[\d.]*", match.group(2))
        # Ementas commonly write a plural reference as
        # “Leis n os 8.212, de ..., e 8.213, de ...”.  The intervening date
        # means the simple group above stops at the first number.  Pick up
        # later dotted law numbers introduced by “e”, while excluding day or
        # year numbers from the date.
        tail = body[match.end() : match.end() + 400]
        for extra in re.findall(r"\be\s+(\d[\d.]*)", tail, re.I):
            if "." in extra and extra not in numbers:
                numbers.append(extra)
        for number in numbers:
            value = f"{display_label} {number}"
            key = fold(value)
            if key not in seen:
                seen.add(key)
                out.append(value)
            if len(out) >= 30:
                return out
    return out


def parse_corpus(path: Path, collection_reference_date: str = CORPUS_REFERENCE_DATE) -> list[dict]:
    text = path.read_text(encoding="utf-8", errors="replace")
    matches = list(SECTION_RE.finditer(text))
    records: list[dict] = []
    for index, match in enumerate(matches):
        heading = match.group(1).strip()
        body_end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.end() : body_end].strip()
        if not re.search(r"\.htm\s*$", heading, re.I) or not SOURCE_RE.search(body):
            continue
        lines = [line.strip() for line in body.splitlines()]
        title_index = extract_title_index(lines)
        title = lines[title_index] if title_index is not None else heading
        kind = "lei complementar" if "complement" in path.stem else "lei ordinária"
        # Ementa/title are the strongest thematic signal.  The full body is
        # deliberately not scored here because amendment targets can swamp
        # the subject of the act itself (e.g. a tax law cited by a municipal
        # or labour statute).  The complete body remains available to the
        # agent through the corpus for substantive analysis.
        ementa = extract_ementa(lines, title_index)
        opening_body = "\n".join(body.splitlines()[:220])
        scores, primary, secondary = classify(title + "\n" + ementa, opening_body)
        flags, markers = temporal_flags(body)
        source = source_url(body)
        references = referenced_norms(body)
        content_sha256 = hashlib.sha256(body.encode("utf-8")).hexdigest()
        encoding_flags = encoding_warnings(title + "\n" + ementa + "\n" + body[:4000])
        record = {
            "id": f"{slug(kind)}-{extract_number(heading, title) or slug(heading)}",
            "jurisdiction": "federal",
            "coverage_type": "legislação federal — leis",
            "kind": kind,
            "number": extract_number(heading, title),
            "heading": heading,
            "title": clean_cell(title, 240).replace("\\|", "|"),
            "ementa": ementa,
            "date": parse_date(title, body),
            "source_url": source,
            "source_kind": "portal oficial — snapshot Markdown",
            "collection_reference_date": collection_reference_date,
            "parser_version": PARSER_VERSION,
            "snapshot_status": "local_snapshot — conferência oficial obrigatória",
            "corpus_file": path.name,
            "corpus_anchor": slug(heading),
            "content_sha256": content_sha256,
            "encoding_warnings": encoding_flags,
            "historical_versions": [],
            "primary_theme": primary,
            "secondary_themes": secondary,
            "theme_scores": scores,
            "subsidiary_themes": list(dict.fromkeys(SUBSIDIARY.get(primary, SUBSIDIARY["outros"]))),
            "validity_status": "não confirmada — verificar fonte oficial e eficácia temporal",
            "validity_flags": flags,
            "temporal_markers": markers,
            "referenced_norms": references,
            "referenced_norm_count": len(references),
        }
        records.append(record)
    return records


def record_link(record: dict, prefix: str = "..") -> str:
    corpus = f"{prefix}/corpus/{record['corpus_file']}#{record['corpus_anchor']}"
    if record.get("source_url"):
        return f"[texto no corpus]({corpus}) · [fonte oficial]({record['source_url']})"
    return f"[texto no corpus]({corpus})"


def write_outputs(records: list[dict], output_dir: Path, corpus_dir: Path, collection_reference_date: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    index_dir = output_dir.parent / "indices"
    index_dir.mkdir(parents=True, exist_ok=True)
    metadata = {
        "schema_version": "3.0",
        "parser_version": PARSER_VERSION,
        "generated_on": date.today().isoformat(),
        "collection_reference_date": collection_reference_date,
        "coverage": {
            "jurisdiction": ["federal"],
            "normative_types": ["lei ordinária", "lei complementar"],
            "status": "parcial — ver data/source_registry.json",
        },
        "reference_warning": "Catálogo de descoberta. Não certifica vigência, constitucionalidade ou aplicabilidade.",
        "corpus_files": sorted({record["corpus_file"] for record in records}),
        "record_count": len(records),
        "counts_by_kind": dict(Counter(record["kind"] for record in records)),
        "counts_by_primary_theme": dict(Counter(record["primary_theme"] for record in records)),
        "records": records,
    }
    (output_dir / "catalogo.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    catalog_lines = [
        "# Catálogo de descoberta legislativa",
        "",
        "> Catálogo gerado a partir dos textos Markdown do corpus. A classificação é heurística e serve para localizar normas; a vigência e a aplicação devem ser confirmadas na fonte oficial.",
        "",
        f"Registros analisados: **{len(records)}**.",
        "",
        "| Tipo | Norma | Data | Tema primário | Temas secundários | Ementa | Fonte |",
        "|---|---|---:|---|---|---|---|",
    ]
    for record in sorted(records, key=lambda item: (item["kind"], int(item["number"] or 0), item["heading"])):
        label = f"{record['kind'].title()} nº {record['number'] or record['heading']}"
        catalog_lines.append(
            "| "
            + " | ".join(
                [
                    record["kind"],
                    label,
                    record["date"] or "—",
                    THEME_LABELS.get(record["primary_theme"], record["primary_theme"]),
                    ", ".join(THEME_LABELS.get(item, item) for item in record["secondary_themes"]) or "—",
                    clean_cell(record["ementa"], 420),
                    record_link(record),
                ]
            )
            + " |"
        )
    (output_dir / "catalogo.md").write_text("\n".join(catalog_lines) + "\n", encoding="utf-8")

    by_theme: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        by_theme[record["primary_theme"]].append(record)
        for theme in record["secondary_themes"]:
            by_theme[theme].append(record)
    all_themes = list(THEME_LABELS)
    summary_lines = [
        "# Índices temáticos",
        "",
        "> Cada norma fica em um tema primário e pode aparecer em temas secundários. A presença no índice não significa que a norma seja aplicável ao caso concreto.",
        "",
        "| Tema | Registros | Índice | Aplicações subsidiárias a procurar |",
        "|---|---:|---|---|",
    ]
    for theme in all_themes:
        items = sorted(by_theme.get(theme, []), key=lambda item: (int(item["number"] or 0), item["heading"]))
        target = f"{slug(theme)}.md"
        subsidiaries = ", ".join(THEME_LABELS.get(item, item) for item in SUBSIDIARY.get(theme, ())) or "—"
        summary_lines.append(f"| {THEME_LABELS[theme]} | {len(items)} | [{target}]({target}) | {subsidiaries} |")
        lines = [
            f"# {THEME_LABELS[theme]}",
            "",
            f"Registros neste índice (primários ou secundários): **{len(items)}**.",
            "",
            "> Use este arquivo para descoberta. Antes de citar uma norma, leia o texto completo no corpus e confirme vigência, redação atual, eficácia e competência na fonte oficial.",
            "",
            "| Norma | Data | Papel do índice | Ementa | Fonte | Sinais temporais |",
            "|---|---:|---|---|---|---|",
        ]
        for item in items:
            role = "primário" if item["primary_theme"] == theme else "secundário"
            signals = "; ".join(item["validity_flags"]) or "nenhum sinal extraído"
            label = f"{item['kind'].title()} nº {item['number'] or item['heading']}"
            lines.append(
                f"| {label} | {item['date'] or '—'} | {role} | {clean_cell(item['ementa'], 500)} | {record_link(item)} | {clean_cell(signals, 180)} |"
            )
        (index_dir / target).write_text("\n".join(lines) + "\n", encoding="utf-8")
    (index_dir / "README.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-dir", type=Path, default=Path("corpus"))
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    parser.add_argument("--collection-reference-date", default=CORPUS_REFERENCE_DATE)
    args = parser.parse_args()
    try:
        date.fromisoformat(args.collection_reference_date)
    except ValueError as exc:
        raise SystemExit("--collection-reference-date deve estar em YYYY-MM-DD") from exc
    paths = sorted(args.corpus_dir.glob("leis_*.md"))
    if not paths:
        raise SystemExit(f"Nenhum arquivo leis_*.md encontrado em {args.corpus_dir}")
    records: list[dict] = []
    for path in paths:
        records.extend(parse_corpus(path, args.collection_reference_date))
    if not records:
        raise SystemExit("Nenhuma norma foi extraída; confira o formato do corpus")
    write_outputs(records, args.output_dir, args.corpus_dir, args.collection_reference_date)
    print(json.dumps({"records": len(records), "files": [path.name for path in paths]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
