from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from normalize_papers import (  # noqa: E402
    meta_artifact_is_current,
    normalize_raw_file,
    read_extractor_version,
    semantic_scholar_title_match,
    validate_meta_payload,
)


def raw_payload(*, pdf_url: str | None = "https://translate.local/paper.pdf") -> dict[str, object]:
    return {
        "paper_id": "demo-paper",
        "source_conversation_ids": ["conv-1"],
        "conversation": {
            "id": "conv-1",
            "title": "Demo Paper",
            "created_at": "2026-04-21T00:00:00+08:00",
            "semantic_updated_at": "2026-04-21T09:30:00+08:00",
            "year": 2024,
            "venue_abbr": "CVPR",
            "citation_count": None,
            "pdf_url": pdf_url,
            "figures": [{"figure_label": "Figure 1", "caption": "Method overview."}],
            "tables": [{"table_label": "Table 1", "caption": "Quantitative comparison on benchmark."}],
            "messages": [
                {
                    "message_kind": "bot_reply",
                    "visible_to_user": True,
                    "content": "# 摘要\n\n我们提出 Demo 方法，并在公开基准上显著优于 baseline。代码见 https://github.com/demo/repo 。",
                    "translation_status": {"current_unit_id": "Abstract"},
                },
                {
                    "message_kind": "bot_reply",
                    "visible_to_user": True,
                    "content": "# 1. Introduction\n\n本文关注从单张图像生成 3D 资产的问题。",
                    "translation_status": {"current_unit_id": "1. Introduction"},
                },
                {
                    "message_kind": "bot_reply",
                    "visible_to_user": True,
                    "content": "# 3. Conclusion\n\n实验表明，该方法在质量上达到当前最优。",
                    "translation_status": {"current_unit_id": "3. Conclusion"},
                },
            ],
        },
    }


def meta_artifact(*, version: str = "meta-v3") -> dict[str, object]:
    return {
        "paper_id": "demo-paper",
        "extractor_version": version,
        "source_conversation_id": "conv-1",
        "source_semantic_updated_at": "2026-04-21T09:30:00+08:00",
        "extracted_at": "2026-04-21T10:00:00+08:00",
        "meta": {
            "story": {
                "paper_one_liner": "一篇把单图 3D 生成做得更稳的论文。",
                "problem": "单图 3D 生成仍容易在稳定性和质量之间失衡。",
                "method": "通过扩散生成路线稳定单图到 3D 的建模过程。",
                "result": "在公开基准上拿到更稳的生成质量。",
            },
            "research_problem": {
                "summary": "现有单图 3D 生成在结果质量和稳定性之间仍有明显张力。",
                "gaps": ["生成过程不稳。", "结果质量波动大。"],
                "goal": "提升单图 3D 资产生成的稳定性与质量。",
            },
            "core_contributions": [
                "提出面向单图 3D 生成的扩散式生成框架。",
                "把生成稳定性作为核心优化目标来建模。",
            ],
            "method": {
                "summary": "核心做法是把单图 3D 生成建成一条更稳的扩散生成流程。",
                "pipeline_steps": ["编码输入图像。", "逐步生成 3D 表征。", "输出最终 3D 资产。"],
                "innovations": ["把稳定性目标直接纳入生成流程。", "让单图条件更稳地约束 3D 输出。"],
                "ingredients": ["Diffusion Model", "Image Encoder"],
                "inputs": ["Image"],
                "outputs": ["3D Asset"],
                "representations": ["Mesh"],
            },
            "evaluation": {
                "headline": "方法在公开基准上的生成质量和稳定性更强。",
                "datasets": ["Objaverse"],
                "metrics": ["F1"],
                "baselines": ["BaselineNet"],
                "key_findings": ["方法在公开基准上表现更稳。"],
                "setup_summary": "在公开 Image-to-3D 基准上，与主流方法做统一比较。",
            },
            "claims": [
                {
                    "text": "方法在公开基准上的生成质量优于主要对照方法。",
                    "type": "experiment",
                    "support": ["section:4. Experiments", "table:Table 1"],
                    "confidence": "high",
                }
            ],
            "conclusion": {
                "author": "作者认为该方法能更稳定地提升单图 3D 生成质量。",
                "limitations": ["评测场景还不够广。"],
            },
            "editorial": {
                "verdict": "值得精读",
                "summary": "更适合作为路线判断样本。",
                "why_read": ["方法动作清楚。", "结果信号直接。"],
                "strengths": ["路线清楚。", "结果信号直接。"],
                "cautions": ["评测覆盖面还不算很宽。"],
                "reading_route": "method",
                "research_position": "可作为单图 3D 生成扩散路线的代表样本。",
                "graph_worthy": True,
                "next_read": ["BaselineNet"],
            },
            "taxonomy": {
                "themes": ["3D Generation"],
                "tasks": ["Image-to-3D"],
                "methods": ["Diffusion Model"],
                "modalities": ["Image", "3D"],
                "representations": ["Mesh"],
                "novelty_types": ["Representation Modeling"],
            },
            "comparison": {
                "aspects": [{"aspect": "method", "difference": "更强调生成稳定性而不是只追求峰值质量。"}],
                "next_read": ["BaselineNet"],
            },
            "assets": {
                "figures": [{"label": "Figure 1", "caption": "Method overview.", "role": "method_overview", "importance": "high"}],
                "tables": [{"label": "Table 1", "caption": "Benchmark comparison.", "role": "quantitative_result", "importance": "high"}],
            },
            "relations": [
                {
                    "type": "compares_to",
                    "target_paper_id": "baseline-net-paper",
                    "label": "BaselineNet",
                    "description": "主对照方法。",
                    "confidence": 0.9,
                }
            ],
        },
    }


class NormalizePapersTests(unittest.TestCase):
    def test_semantic_title_match_accepts_exact_title_and_year(self) -> None:
        def fake_fetch(url: str, headers: dict[str, str]) -> dict[str, object]:
            self.assertIn("Demo+Paper", url)
            return {
                "title": "Demo Paper",
                "authors": [{"name": "Author A"}, {"name": "Author B"}],
                "year": 2024,
                "venue": "CVPR",
                "citationCount": 42,
                "abstract": "Original abstract",
                "externalIds": {"DOI": "10.1000/demo", "ArXiv": "2401.00001"},
                "openAccessPdf": {"url": "https://s2.local/demo.pdf"},
            }

        result = semantic_scholar_title_match("Demo Paper", 2024, fetcher=fake_fetch)
        assert result is not None
        self.assertEqual(result.authors, ["Author A", "Author B"])
        self.assertEqual(result.abstract_raw, "Original abstract")
        self.assertEqual(result.citation_count, 42)
        self.assertEqual(result.doi, "10.1000/demo")
        self.assertEqual(result.arxiv, "2401.00001")

    def test_read_extractor_version_and_meta_artifact_current_check(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            config_path = Path(tempdir) / "extractor-config.json"
            meta_path = Path(tempdir) / "demo-paper.json"
            config_path.write_text(json.dumps({"extractor_version": "meta-v3"}), encoding="utf-8")
            meta_path.write_text(json.dumps(meta_artifact(), ensure_ascii=False), encoding="utf-8")

            version = read_extractor_version(config_path)
            self.assertEqual(version, "meta-v3")
            self.assertTrue(meta_artifact_is_current(meta_path, version))
            self.assertFalse(meta_artifact_is_current(meta_path, "meta-v4"))

    def test_validate_meta_payload_accepts_v3_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            meta_path = Path(tempdir) / "demo-paper.json"
            payload = meta_artifact()
            meta_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

            validated = validate_meta_payload(meta_path, payload, "demo-paper", "meta-v3")
            self.assertEqual(validated["meta"]["story"]["paper_one_liner"], "一篇把单图 3D 生成做得更稳的论文。")
            self.assertEqual(validated["meta"]["editorial"]["reading_route"], "method")
            self.assertIn("Diffusion Model", validated["meta"]["taxonomy"]["methods"])

    def test_normalize_raw_file_builds_canonical_record(self) -> None:
        def fake_fetch(url: str, headers: dict[str, str]) -> dict[str, object]:
            return {
                "title": "Demo Paper",
                "authors": [{"name": "Author A"}],
                "year": 2024,
                "venue": "CVPR",
                "citationCount": 9,
                "abstract": "Original abstract",
                "externalIds": {"DOI": "10.1000/demo", "ArXiv": "2401.00001"},
                "openAccessPdf": {"url": "https://s2.local/demo.pdf"},
            }

        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            raw_path = root / "raw.json"
            meta_path = root / "meta.json"
            raw_path.write_text(json.dumps(raw_payload(), ensure_ascii=False), encoding="utf-8")
            meta_path.write_text(json.dumps(meta_artifact(), ensure_ascii=False), encoding="utf-8")

            record = normalize_raw_file(raw_path, meta_path=meta_path, extractor_version="meta-v3", fetcher=fake_fetch)

            self.assertEqual(record["id"], "demo-paper")
            self.assertEqual(record["source"]["conversation_ids"], ["conv-1"])
            self.assertEqual(record["bibliography"]["title"], "Demo Paper")
            self.assertEqual(record["bibliography"]["identifiers"]["doi"], "10.1000/demo")
            self.assertEqual(record["abstracts"]["zh"], "我们提出 Demo 方法，并在公开基准上显著优于 baseline。代码见 https://github.com/demo/repo 。")
            self.assertIn("Image-to-3D", record["taxonomy"]["tasks"])
            self.assertNotIn("reading_digest", record)
            self.assertNotIn("paper_neighbors", record)


if __name__ == "__main__":
    unittest.main()
