#!/usr/bin/env python3
"""Discover and optionally archive official normative sources.

The collector preserves raw responses and writes provenance sidecars. It is
deliberately generic: each court, agency, state or municipality supplies its
own listing URL and link pattern in the manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


class LinkCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self.current_href: str | None = None
        self.current_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "a":
            self.current_href = dict(attrs).get("href")
            self.current_text = []

    def handle_data(self, data: str) -> None:
        if self.current_href is not None:
            self.current_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self.current_href:
            self.links.append((self.current_href, " ".join(" ".join(self.current_text).split())))
            self.current_href = None
            self.current_text = []


class VisibleText(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.hidden = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style", "noscript", "template"}:
            self.hidden += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript", "template"} and self.hidden:
            self.hidden -= 1

    def handle_data(self, data: str) -> None:
        if not self.hidden:
            value = " ".join(html.unescape(data).split())
            if value:
                self.parts.append(value)


def fetch(url: str, timeout: int, max_bytes: int) -> tuple[bytes, str]:
    if url.startswith("file://"):
        from urllib.parse import unquote, urlparse

        path_value = unquote(urlparse(url).path)
        if len(path_value) >= 3 and path_value[0] == "/" and path_value[2] == ":":
            path_value = path_value[1:]
        path = Path(path_value)
        return path.read_bytes()[:max_bytes], "utf-8"
    request = Request(url, headers={"User-Agent": "leis-analise-br-harvester/1.0"})
    with urlopen(request, timeout=timeout) as response:
        return response.read(max_bytes), response.headers.get_content_charset() or "utf-8"


def source_by_id(manifest: dict, source_id: str) -> dict:
    for source in manifest.get("sources", []):
        if source.get("id") == source_id:
            return source
    raise SystemExit(f"Fonte não encontrada no manifesto: {source_id}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path("data/source_harvest_manifest.json"))
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("data/harvested"))
    parser.add_argument("--snapshot-id", default=datetime.now(timezone.utc).date().isoformat())
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--fetch-acts", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--max-bytes", type=int, default=10_000_000)
    parser.add_argument("--delay", type=float, default=0.2)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    source = source_by_id(manifest, args.source_id)
    listing_url = source.get("listing_url")
    if not listing_url:
        raise SystemExit("A fonte precisa de listing_url")
    body, charset = fetch(listing_url, args.timeout, args.max_bytes)
    text = body.decode(charset, errors="replace")
    parser_html = LinkCollector()
    parser_html.feed(text)
    link_pattern = re.compile(source.get("link_pattern", r"^https?://"), re.I)
    seen: set[str] = set()
    discovered = []
    for href, label in parser_html.links:
        url = urljoin(listing_url, href)
        if not link_pattern.search(url) or url in seen:
            continue
        seen.add(url)
        discovered.append({"label": label, "url": url})
        if len(discovered) >= max(0, args.limit):
            break
    if args.dry_run:
        print(json.dumps({"source_id": args.source_id, "listing_url": listing_url, "discovered": discovered}, ensure_ascii=False, indent=2))
        return 0

    base = args.output_dir / args.source_id / args.snapshot_id
    raw_dir = base / "raw"
    text_dir = base / "text"
    raw_dir.mkdir(parents=True, exist_ok=True)
    text_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for item in discovered:
        retrieved_at = datetime.now(timezone.utc).isoformat()
        record_id = hashlib.sha256(item["url"].encode("utf-8")).hexdigest()[:16]
        record = {
            "id": record_id,
            "source_id": args.source_id,
            "jurisdiction": source.get("jurisdiction"),
            "normative_type": source.get("normative_type"),
            "official_url": item["url"],
            "label": item["label"],
            "retrieved_at": retrieved_at,
            "status_at_source": "não confirmado — requer leitura do ato e fonte oficial",
            "raw_file": None,
            "text_file": None,
            "raw_sha256": None,
            "parser_version": "1.0",
        }
        if args.fetch_acts:
            try:
                raw, act_charset = fetch(item["url"], args.timeout, args.max_bytes)
                raw_path = raw_dir / f"{record_id}.html"
                raw_path.write_bytes(raw)
                visible = VisibleText()
                visible.feed(raw.decode(act_charset, errors="replace"))
                text_path = text_dir / f"{record_id}.md"
                text_path.write_text("\n\n".join(visible.parts) + "\n", encoding="utf-8")
                record.update(
                    {
                        "raw_file": raw_path.relative_to(base).as_posix(),
                        "text_file": text_path.relative_to(base).as_posix(),
                        "raw_sha256": hashlib.sha256(raw).hexdigest(),
                    }
                )
            except (HTTPError, URLError, OSError, UnicodeError) as exc:
                record["fetch_error"] = str(exc)
        records.append(record)
        time.sleep(max(0.0, args.delay))
    (base / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "source_id": args.source_id,
                "authority": source.get("authority"),
                "jurisdiction": source.get("jurisdiction"),
                "normative_type": source.get("normative_type"),
                "listing_url": listing_url,
                "snapshot_id": args.snapshot_id,
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "records": records,
                "warning": "Descoberta e arquivamento não certificam vigência, autenticidade material ou aplicabilidade.",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"source_id": args.source_id, "records": len(records), "base": str(base)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
