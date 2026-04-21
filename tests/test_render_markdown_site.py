from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from render_markdown_site import main as render_markdown_site_main, render_paper_page  # noqa: E402


def canonical_record() -> dict[str, object]:
    return {
        "id": "demo-paper",
        "source": {"conversation_ids": ["conv-demo"], "paper_path": "papers/demo-paper.md", "route_path": "#/paper/demo-paper"},
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
        "story": {"paper_one_liner": "一句话结论", "problem": "问题", "method": "方法", "result": "结果"},
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
        "conclusion": {"author": "作者结论", "limitations": ["局限 1"]},
        "editorial": {
            "verdict": "值得精读",
            "summary": "编者按",
            "why_read": ["point"],
            "strengths": ["strength"],
            "cautions": ["caution"],
            "reading_route": "method",
            "research_position": "位置判断",
            "graph_worthy": True,
            "next_read": ["Baseline A"],
        },
        "taxonomy": {
            "themes": ["3D Generation"],
            "tasks": ["Image-to-3D"],
            "methods": ["Diffusion Model"],
            "modalities": ["Image", "3D"],
            "representations": ["Mesh"],
            "novelty_types": ["Representation Modeling"],
        },
        "comparison": {"aspects": [{"aspect": "method", "difference": "difference"}], "next_read": ["Baseline A"]},
        "assets": {"figures": [{"label": "Figure 1", "role": "method_overview", "importance": "high", "caption": "caption"}], "tables": []},
        "relations": [],
    }


class RenderMarkdownSiteTests(unittest.TestCase):
    def test_render_paper_page_uses_v2_reading_flow(self) -> None:
        detail_payload = {
            "canonical": canonical_record(),
            "neighbors": {"task": [], "method": [], "comparison": []},
        }

        rendered = render_paper_page(detail_payload)
        self.assertIn("## Story", rendered)
        self.assertIn("## 方法", rendered)
        self.assertIn("## 实验", rendered)
        self.assertIn("## 阅读判断", rendered)
        self.assertIn("## 对比线索", rendered)

    def test_render_markdown_site_writes_site_index_and_detail_json(self) -> None:
        record = canonical_record()

        with tempfile.TemporaryDirectory() as tempdir:
            temp_path = Path(tempdir)
            papers_dir = temp_path / "papers"
            site_dir = temp_path / "site"
            papers_dir.mkdir(parents=True)
            (papers_dir / "demo-paper.json").write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")

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
            self.assertTrue((site_dir / "papers" / "demo-paper.md").exists())


if __name__ == "__main__":
    unittest.main()
