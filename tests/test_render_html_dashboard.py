from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from render_html_dashboard import publish_site  # noqa: E402


class RenderHtmlDashboardTests(unittest.TestCase):
    def test_publish_site_copies_dist_and_inlines_payload(self) -> None:
        payload = {
            "generated_at": "2026-04-21T00:00:00Z",
            "paper_count": 0,
            "site_meta": {
                "title": "Translate Paper Forest",
                "generated_at": "2026-04-21T00:00:00Z",
                "paper_count": 0,
            },
            "navigation": {
                "home_route": "#/",
                "detail_route_template": "#/paper/{paper_id}",
                "neighbor_tabs": [],
                "filter_groups": [],
            },
            "filters": {"themes": [], "tasks": [], "methods": []},
            "papers": [],
            "recent_titles": [],
        }

        with tempfile.TemporaryDirectory() as tempdir:
            temp_path = Path(tempdir)
            dist_dir = temp_path / "dist"
            site_dir = temp_path / "site"
            (dist_dir / "assets").mkdir(parents=True)
            (dist_dir / "index.html").write_text(
                "<html><body><div id='root'></div><script id='paper-neighbors-data' type='application/json'>__PAPER_NEIGHBORS_DATA__</script></body></html>",
                encoding="utf-8",
            )
            (dist_dir / "assets" / "main.js").write_text("console.log('ok');", encoding="utf-8")
            (site_dir / "papers").mkdir(parents=True)
            (site_dir / "papers" / "legacy.html").write_text("legacy", encoding="utf-8")
            (site_dir / "papers" / "keep.md").write_text("# keep", encoding="utf-8")

            index_path = publish_site(payload, dist_dir=dist_dir, site_dir=site_dir)

            self.assertEqual(index_path, site_dir / "index.html")
            self.assertTrue((site_dir / "assets" / "main.js").exists())
            self.assertFalse((site_dir / "papers" / "legacy.html").exists())
            self.assertTrue((site_dir / "papers" / "keep.md").exists())

            rendered = (site_dir / "index.html").read_text(encoding="utf-8")
            self.assertIn("Translate Paper Forest", rendered)
            self.assertIn(json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c"), rendered)


if __name__ == "__main__":
    unittest.main()
