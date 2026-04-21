from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from render_markdown_site import main as render_markdown_site_main, render_paper_page  # noqa: E402


class RenderMarkdownSiteTests(unittest.TestCase):
    def test_render_paper_page_uses_three_layer_reading_flow(self) -> None:
        record = {
            "paper_id": "demo-paper",
            "route_path": "#/paper/demo-paper",
            "title": "Demo Paper",
            "authors": ["Author A"],
            "venue": "CVPR",
            "year": 2025,
            "citation_count": 12,
            "links": {"pdf": "https://example.com/demo.pdf"},
            "summary": {
                "one_liner": "一句话结论",
                "abstract_summary": "摘要概览",
                "research_value": {"summary": "值得继续读", "points": ["价值点"]},
                "worth_long_term_graph": True,
            },
            "reading_digest": {
                "value_statement": "这是一篇值得看的论文。",
                "best_for": "适合做 3D 阅读的人。",
                "why_read": ["方法路线清楚", "结果信号直接"],
                "recommended_route": "method",
                "positioning": {
                    "task": ["Image-to-3D"],
                    "modality": ["image", "3D"],
                    "method": ["Diffusion Model"],
                    "novelty": ["representation"],
                },
                "narrative": {
                    "problem": "问题",
                    "method": "方法",
                    "result": "结果",
                },
                "result_headline": "结果先看",
            },
            "storyline": {"problem": "问题", "method": "方法", "outcome": "结果"},
            "research_problem": {"summary": "研究问题", "gaps": ["gap"], "goal": "goal"},
            "core_contributions": ["贡献 1"],
            "key_claims": [{"claim": "claim", "type": "method", "support": ["section:Abstract"], "confidence": "high"}],
            "method_core": {
                "approach_summary": "方法总结",
                "pipeline_steps": ["step 1", "step 2"],
                "innovations": ["创新点"],
                "ingredients": ["Diffusion Model"],
                "representation": ["Mesh"],
                "supervision": [],
                "differences": ["差异点"],
            },
            "inputs_outputs": {"inputs": ["image"], "outputs": ["mesh"], "modalities": ["image", "3D"]},
            "benchmarks_or_eval": {
                "datasets": ["Objaverse"],
                "metrics": ["FID"],
                "baselines": ["Baseline A"],
                "findings": ["发现 1"],
                "best_results": ["最好结果"],
                "experiment_setup_summary": "设置摘要",
            },
            "author_conclusion": "作者结论",
            "editor_note": {"summary": "编者按", "points": ["point"]},
            "editorial_review": {
                "verdict": "值得精读",
                "strengths": ["strength"],
                "cautions": ["caution"],
                "research_position": "位置判断",
                "next_read_hint": "下一篇建议",
            },
            "limitations": ["局限 1"],
            "novelty_type": ["representation"],
            "research_tags": {
                "themes": ["3D Generation"],
                "tasks": ["Image-to-3D"],
                "methods": ["Diffusion Model"],
                "modalities": ["image", "3D"],
                "representations": ["Mesh"],
            },
            "comparison_context": {
                "explicit_baselines": ["Baseline A"],
                "contrast_methods": ["Contrast B"],
                "comparison_aspects": [{"aspect": "method", "difference": "difference"}],
                "recommended_next_read": "Baseline A",
            },
            "paper_neighbors": {"task": [], "method": [], "comparison": []},
            "figure_table_index": {"figures": [{"label": "Figure 1", "role": "method_overview", "importance": "high", "caption": "caption"}], "tables": []},
            "retrieval_profile": {"problem_spaces": ["3D Generation"]},
            "topics": [],
            "paper_relations": [],
            "abstract_raw": "raw abstract",
            "abstract_zh": "中文摘要",
        }

        rendered = render_paper_page(record)
        self.assertIn("## 决策层", rendered)
        self.assertIn("## 理解层", rendered)
        self.assertIn("<details>", rendered)
        self.assertIn("阅读路径: 先看方法", rendered)
        self.assertIn("## 编辑判断", rendered)
        self.assertIn("## 核心论断", rendered)

    def test_render_markdown_site_writes_index_and_per_paper_json(self) -> None:
        record = {
            "paper_id": "demo-paper",
            "source_conversation_ids": ["conv-demo"],
            "title": "Demo Paper",
            "authors": ["Author A"],
            "year": 2025,
            "venue": "CVPR",
            "citation_count": 12,
            "links": {"pdf": "https://example.com/demo.pdf", "doi": None, "arxiv": None, "project": None, "code": None, "data": None},
            "abstract_raw": "raw abstract",
            "abstract_zh": "中文摘要",
            "summary": {
                "one_liner": "一句话结论",
                "abstract_summary": "摘要概览",
                "research_value": {"summary": "值得继续读", "points": ["价值点"]},
                "worth_long_term_graph": True,
            },
            "reading_digest": {
                "value_statement": "这是一篇值得看的论文。",
                "best_for": "适合做 3D 阅读的人。",
                "why_read": ["方法路线清楚", "结果信号直接"],
                "recommended_route": "method",
                "positioning": {
                    "task": ["Image-to-3D"],
                    "modality": ["image", "3D"],
                    "method": ["Diffusion Model"],
                    "novelty": ["representation"],
                },
                "narrative": {"problem": "问题", "method": "方法", "result": "结果"},
                "result_headline": "结果先看",
            },
            "storyline": {"problem": "问题", "method": "方法", "outcome": "结果"},
            "research_problem": {"summary": "研究问题", "gaps": ["gap"], "goal": "goal"},
            "core_contributions": ["贡献 1"],
            "key_claims": [{"claim": "claim", "type": "method", "support": ["section:Abstract"], "confidence": "high"}],
            "method_core": {
                "approach_summary": "方法总结",
                "pipeline_steps": ["step 1", "step 2"],
                "innovations": ["创新点"],
                "ingredients": ["Diffusion Model"],
                "representation": ["Mesh"],
                "supervision": [],
                "differences": ["差异点"],
            },
            "inputs_outputs": {"inputs": ["image"], "outputs": ["mesh"], "modalities": ["image", "3D"]},
            "benchmarks_or_eval": {
                "datasets": ["Objaverse"],
                "metrics": ["FID"],
                "baselines": ["Baseline A"],
                "findings": ["发现 1"],
                "best_results": ["最好结果"],
                "experiment_setup_summary": "设置摘要",
            },
            "author_conclusion": "作者结论",
            "editor_note": {"summary": "编者按", "points": ["point"]},
            "editorial_review": {
                "verdict": "值得精读",
                "strengths": ["strength"],
                "cautions": ["caution"],
                "research_position": "位置判断",
                "next_read_hint": "下一篇建议",
            },
            "limitations": ["局限 1"],
            "novelty_type": ["representation"],
            "research_tags": {
                "themes": ["3D Generation"],
                "tasks": ["Image-to-3D"],
                "methods": ["Diffusion Model"],
                "modalities": ["image", "3D"],
                "representations": ["Mesh"],
            },
            "comparison_context": {
                "explicit_baselines": ["Baseline A"],
                "contrast_methods": ["Contrast B"],
                "comparison_aspects": [{"aspect": "method", "difference": "difference"}],
                "recommended_next_read": "Baseline A",
            },
            "paper_neighbors": {"task": [], "method": [], "comparison": []},
            "figure_table_index": {"figures": [], "tables": []},
            "retrieval_profile": {"problem_spaces": ["3D Generation"]},
            "topics": [],
            "paper_relations": [],
        }

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
            index_payload = json.loads((site_dir / "paper-neighbors.json").read_text(encoding="utf-8"))
            detail_payload = json.loads((site_dir / "papers" / "demo-paper.json").read_text(encoding="utf-8"))
            self.assertIn("papers", index_payload)
            self.assertIn("reading_digest", index_payload["papers"][0])
            self.assertNotIn("storyline", index_payload["papers"][0])
            self.assertIn("storyline", detail_payload)
            self.assertTrue((site_dir / "papers" / "demo-paper.md").exists())


if __name__ == "__main__":
    unittest.main()
