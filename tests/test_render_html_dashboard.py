from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from render_html_dashboard import publish_site  # noqa: E402


class RenderHtmlDashboardTests(unittest.TestCase):
    def test_publish_site_copies_dist_without_inlining_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            temp_path = Path(tempdir)
            dist_dir = temp_path / "dist"
            site_dir = temp_path / "site"
            (dist_dir / "assets").mkdir(parents=True)
            (dist_dir / "index.html").write_text(
                "<html><head><title>Translate Paper Forest</title></head><body><div id='root'></div></body></html>",
                encoding="utf-8",
            )
            (dist_dir / "assets" / "main.js").write_text("console.log('ok');", encoding="utf-8")
            (site_dir / "papers").mkdir(parents=True)
            (site_dir / "papers" / "legacy.html").write_text("legacy", encoding="utf-8")
            (site_dir / "papers" / "keep.md").write_text("# keep", encoding="utf-8")
            (site_dir / "papers" / "keep.json").write_text('{"paper_id":"keep"}', encoding="utf-8")
            (site_dir / "paper-neighbors.json").write_text('{"paper_count":1}', encoding="utf-8")

            index_path = publish_site(dist_dir=dist_dir, site_dir=site_dir)

            self.assertEqual(index_path, site_dir / "index.html")
            self.assertTrue((site_dir / "assets" / "main.js").exists())
            self.assertFalse((site_dir / "papers" / "legacy.html").exists())
            self.assertTrue((site_dir / "papers" / "keep.md").exists())
            self.assertTrue((site_dir / "papers" / "keep.json").exists())
            self.assertTrue((site_dir / "paper-neighbors.json").exists())

            rendered = (site_dir / "index.html").read_text(encoding="utf-8")
            self.assertIn("Translate Paper Forest", rendered)
            self.assertNotIn("paper-neighbors-data", rendered)


if __name__ == "__main__":
    unittest.main()
