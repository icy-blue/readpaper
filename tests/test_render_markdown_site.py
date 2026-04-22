from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from render_markdown_site import main as render_markdown_site_main, render_index  # noqa: E402


def canonical_record() -> dict[str, object]:
    return {
        "id": "demo-paper",
        "source": {"conversation_ids": ["conv-demo"], "paper_path": "papers/demo-paper.md", "route_path": "#/?paper=demo-paper&detail=1"},
        "bibliography": {
            "title": "Demo Paper",
            "authors": ["Author A"],
            "year": 2025,
            "venue": "CVPR",
            "citation_count": 12,
            "identifiers": {"doi": "10.1000/demo", "arxiv": "2501.00001"},
            "links": {"pdf": "https://example.com/demo.pdf", "project": None, "code": "https://github.com/demo/repo", "data": None},
        },
        "abstracts": {"raw": "raw abstract", "zh": "中文摘要"},
        "story": {"paper_one_liner": "一句话结论"},
        "research_problem": {"summary": "研究问题", "gaps": ["gap"], "goal": "goal"},
        "core_contributions": ["贡献 1"],
        "method": {
            "summary": "方法总结",
            "pipeline_steps": ["step 1", "step 2"],
            "innovations": ["创新点"],
            "ingredients": ["Diffusion Model"],
            "inputs": ["Image"],
            "outputs": ["Mesh"],
            "representations": ["Mesh"],
        },
        "evaluation": {
            "headline": "结果先看",
            "datasets": ["Objaverse"],
            "metrics": ["FID"],
            "baselines": ["Baseline A"],
            "key_findings": ["发现 1"],
            "setup_summary": "设置摘要",
        },
        "claims": [{"text": "claim", "type": "method", "support": ["section:Abstract"], "confidence": "high"}],
        "research_risks": ["局限 1"],
        "editorial": {
            "research_position": "位置判断",
            "graph_worthy": True,
        },
        "taxonomy": {
            "themes": ["3D Generation"],
            "tasks": ["Image-to-3D"],
            "methods": ["Diffusion Model"],
            "modalities": ["Image", "3D"],
            "novelty_types": ["Representation Modeling"],
        },
        "comparison": {"aspects": [{"aspect": "method", "difference": "difference"}], "next_read": ["Baseline A"]},
        "discovery_axes": {
            "problem": ["image-to-3d-stability"],
            "method": ["diffusion-image-to-3d"],
            "evaluation": ["objaverse-benchmark-line"],
            "risk": ["limited-eval-coverage"],
        },
        "relations": [],
    }


class RenderMarkdownSiteTests(unittest.TestCase):
    def test_render_index_uses_homepage_only_reading_flow(self) -> None:
        payload = {
            "generated_at": "2026-04-22T10:00:00+08:00",
            "paper_count": 1,
            "papers": [canonical_record()],
            "filters": {
                "themes": [{"label": "3D Generation", "count": 1}],
                "tasks": [{"label": "Image-to-3D", "count": 1}],
                "methods": [{"label": "Diffusion Model", "count": 1}],
            },
        }

        rendered = render_index(payload)

        self.assertIn("只保留主页", rendered)
        self.assertIn("Demo Paper | CVPR 2025", rendered)
        self.assertNotIn("index.html#/paper/", rendered)

    def test_render_markdown_site_writes_site_index_and_detail_json_only(self) -> None:
        record = canonical_record()

        with tempfile.TemporaryDirectory() as tempdir:
            temp_path = Path(tempdir)
            papers_dir = temp_path / "papers"
            site_dir = temp_path / "site"
            papers_dir.mkdir(parents=True)
            (papers_dir / "demo-paper.json").write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
            (site_dir / "papers").mkdir(parents=True)
            (site_dir / "papers" / "legacy-paper.md").write_text("# legacy", encoding="utf-8")

            argv = sys.argv
            try:
                sys.argv = [
                    "render_markdown_site.py",
                    "--papers-dir",
                    str(papers_dir),
                    "--site-dir",
                    str(site_dir),
                ]
                exit_code = render_markdown_site_main()
            finally:
                sys.argv = argv

            self.assertEqual(exit_code, 0)
            index_payload = json.loads((site_dir / "site-index.json").read_text(encoding="utf-8"))
            detail_payload = json.loads((site_dir / "papers" / "demo-paper.json").read_text(encoding="utf-8"))
            self.assertIn("papers", index_payload)
            self.assertIn("featured", index_payload)
            self.assertIn("canonical", detail_payload)
            self.assertIn("neighbors", detail_payload)
            self.assertFalse((site_dir / "papers" / "demo-paper.md").exists())
            self.assertFalse((site_dir / "papers" / "legacy-paper.md").exists())


if __name__ == "__main__":
    unittest.main()
