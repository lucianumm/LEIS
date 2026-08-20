from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_catalog import parse_date  # noqa: E402
from harvest_official import LinkCollector, VisibleText  # noqa: E402
from verify_sources import signals  # noqa: E402


class ToolTests(unittest.TestCase):
    def test_legacy_heading_date_is_parsed(self) -> None:
        self.assertEqual(parse_date("LEI COMPLEMENTAR Nş 192, 11 DE MARÇO DE 2022", ""), "2022-03-11")

    def test_html_discovery_preserves_links_and_visible_text(self) -> None:
        parser = LinkCollector()
        parser.feed('<a href="/ato/1"> Ato 1 </a><script>ignore</script>')
        self.assertEqual(parser.links, [("/ato/1", "Ato 1")])
        text = VisibleText()
        text.feed("<p>Texto <b>normativo</b></p><script>segredo</script>")
        self.assertIn("Texto", " ".join(text.parts))
        self.assertNotIn("segredo", " ".join(text.parts))

    def test_source_signals_are_not_legal_conclusions(self) -> None:
        found = signals("A norma foi alterada. Produção de efeitos. Vide ADI 1.")
        self.assertEqual(found, ["revocation_or_amendment_marker", "temporal_effect_marker", "constitutional_review_marker"])

    def test_snapshot_manifest_shape(self) -> None:
        payload = json.loads((ROOT / "data" / "snapshot_manifest.json").read_text(encoding="utf-8"))
        self.assertGreater(payload["record_count"], 0)
        self.assertTrue(payload["files"])
        self.assertTrue(payload["metadata_files"])
        self.assertTrue(all(len(item["content_sha256"]) == 64 for item in payload["records"]))


if __name__ == "__main__":
    unittest.main()
