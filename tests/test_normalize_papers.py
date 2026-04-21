from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.error import URLError


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
            "figures": [
                {
                    "figure_label": "Figure 1",
                    "caption": "Method overview.",
                }
            ],
            "tables": [
                {
                    "table_label": "Table 1",
                    "caption": "Quantitative comparison on benchmark.",
                }
            ],
            "tags": [
                {"category_code": "T", "tag_label_en": "Image-to-3D"},
                {"category_code": "S", "tag_label_en": "Diffusion Model"},
                {"category_code": "M", "tag_label_en": "Image"},
            ],
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


def meta_artifact(*, version: str = "meta-v1") -> dict[str, object]:
    return {
        "paper_id": "demo-paper",
        "extractor_version": version,
        "source_conversation_id": "conv-1",
        "source_semantic_updated_at": "2026-04-21T09:30:00+08:00",
        "extracted_at": "2026-04-21T10:00:00+08:00",
        "meta": {
            "summary": {
                "one_liner": "把单图 3D 生成做得更稳的一篇扩散路线论文。",
                "abstract_summary": "论文围绕单图到 3D 资产生成，重点在提升生成稳定性与质量。",
                "research_value": {
                    "summary": "适合作为单图 3D 生成扩散路线的阅读入口。",
                    "points": ["能快速定位方法亮点。", "可作为后续对比样本。"],
                },
                "worth_long_term_graph": True,
            },
            "reading_digest": {
                "value_statement": "更适合拿来判断这条 Image-to-3D 扩散路线值不值得继续跟。",
                "best_for": "适合想快速判断单图 3D 生成路线的读者。",
                "why_read": ["方法动作清楚。", "结果信号直接。", "可顺手拿来做路线对照。"],
                "recommended_route": "method",
                "positioning": {
                    "task": ["Image-to-3D"],
                    "method": ["Diffusion Model"],
                    "modality": ["image", "3D"],
                    "novelty": ["representation"],
                },
                "narrative": {
                    "problem": "单图 3D 生成容易在质量和稳定性上失衡。",
                    "method": "用扩散路线稳住 3D 资产生成过程。",
                    "result": "在公开基准上拿到更稳的生成质量。",
                },
                "result_headline": "公开基准上的生成质量和稳定性都更强。",
            },
            "storyline": {
                "problem": "单图 3D 生成容易在质量和稳定性上失衡。",
                "method": "用扩散路线稳住 3D 资产生成过程。",
                "outcome": "在公开基准上拿到更稳的生成质量。",
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
            "key_claims": [
                {
                    "claim": "方法在公开基准上的生成质量优于主要对照方法。",
                    "type": "experiment",
                    "support": ["section:4. Experiments", "table:Table 1"],
                    "confidence": "high",
                }
            ],
            "method_core": {
                "approach_summary": "核心做法是把单图 3D 生成建成一条更稳的扩散生成流程。",
                "pipeline_steps": ["编码输入图像。", "逐步生成 3D 表征。", "输出最终 3D 资产。"],
                "innovations": ["把稳定性目标直接纳入生成流程。", "让单图条件更稳地约束 3D 输出。"],
                "ingredients": ["Diffusion Model", "Image Encoder"],
                "representation": ["Mesh"],
                "supervision": ["reconstruction loss"],
                "differences": ["更强调生成稳定性而不是只追求单次质量峰值。"],
            },
            "inputs_outputs": {
                "inputs": ["image"],
                "outputs": ["3D asset"],
                "modalities": ["image", "3D"],
            },
            "benchmarks_or_eval": {
                "datasets": ["Objaverse"],
                "metrics": ["F1"],
                "baselines": ["BaselineNet"],
                "findings": ["方法在公开基准上表现更稳。"],
                "best_results": ["公开基准上的整体质量更强。"],
                "experiment_setup_summary": "在公开 Image-to-3D 基准上，与主流方法做统一比较。",
            },
            "author_conclusion": "作者认为该方法能更稳定地提升单图 3D 生成质量。",
            "editor_note": {
                "summary": "更适合作为路线判断样本。",
                "points": ["可先对比 BaselineNet。"],
            },
            "editorial_review": {
                "verdict": "值得精读",
                "strengths": ["方法动作清楚。", "结果信号直接。"],
                "cautions": ["评测覆盖面还不算很宽。"],
                "research_position": "可作为单图 3D 生成扩散路线的代表样本。",
                "next_read_hint": "接着对比 BaselineNet。",
            },
            "limitations": ["评测场景还不够广。"],
            "novelty_type": ["representation"],
            "research_tags": {
                "themes": ["3D Generation"],
                "tasks": ["Image-to-3D"],
                "methods": ["Diffusion Model"],
                "modalities": ["image", "3D"],
                "representations": ["Mesh"],
            },
            "topics": [],
            "retrieval_profile": {
                "problem_spaces": ["3D Generation"],
                "task_axes": ["Image-to-3D"],
                "approach_axes": ["Diffusion Model"],
                "input_axes": ["image"],
                "output_axes": ["3D asset"],
                "modality_axes": ["image", "3D"],
                "comparison_axes": ["BaselineNet"],
            },
            "comparison_context": {
                "explicit_baselines": ["BaselineNet"],
                "contrast_methods": ["Latent Diffusion"],
                "comparison_aspects": [
                    {
                        "aspect": "stability",
                        "difference": "更强调生成稳定性而不是只追求峰值质量。",
                    }
                ],
                "recommended_next_read": "BaselineNet",
            },
            "paper_relations": [],
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
            config_path.write_text(json.dumps({"extractor_version": "meta-v1"}), encoding="utf-8")
            meta_path.write_text(json.dumps(meta_artifact(), ensure_ascii=False), encoding="utf-8")

            version = read_extractor_version(config_path)
            self.assertEqual(version, "meta-v1")
            self.assertTrue(meta_artifact_is_current(meta_path, version))
            self.assertFalse(meta_artifact_is_current(meta_path, "meta-v2"))

    def test_validate_meta_payload_accepts_valid_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            meta_path = Path(tempdir) / "demo-paper.json"
            payload = meta_artifact()
            meta_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

            validated = validate_meta_payload(meta_path, payload, "demo-paper", "meta-v1")

        self.assertEqual(validated["extractor_version"], "meta-v1")
        self.assertEqual(validated["meta"]["reading_digest"]["recommended_route"], "method")
        self.assertEqual(validated["meta"]["research_tags"]["tasks"], ["Image-to-3D"])

    def test_validate_meta_payload_rejects_overlong_fields_and_sentence_labels(self) -> None:
        payload = meta_artifact()
        meta = payload["meta"]  # type: ignore[index]
        assert isinstance(meta, dict)
        reading_digest = meta["reading_digest"]
        assert isinstance(reading_digest, dict)
        reading_digest["value_statement"] = "很长" * 50
        positioning = reading_digest["positioning"]
        assert isinstance(positioning, dict)
        positioning["task"] = ["我们通过更稳的路线解决这个任务。"]

        with tempfile.TemporaryDirectory() as tempdir:
            meta_path = Path(tempdir) / "demo-paper.json"
            with self.assertRaisesRegex(ValueError, "value_statement|short label"):
                validate_meta_payload(meta_path, payload, "demo-paper", "meta-v1")

    def test_validate_meta_payload_rejects_version_mismatch(self) -> None:
        payload = meta_artifact(version="meta-v2")

        with tempfile.TemporaryDirectory() as tempdir:
            meta_path = Path(tempdir) / "demo-paper.json"
            with self.assertRaisesRegex(ValueError, "extractor_version"):
                validate_meta_payload(meta_path, payload, "demo-paper", "meta-v1")

    def test_normalize_prefers_conversation_pdf_over_semantic_pdf_and_assembles_meta_fields(self) -> None:
        def fake_fetch(url: str, headers: dict[str, str]) -> dict[str, object]:
            return {
                "title": "Demo Paper",
                "authors": [{"name": "Author A"}],
                "year": 2024,
                "venue": "CVPR",
                "citationCount": 10,
                "abstract": "Original abstract",
                "externalIds": {"DOI": "10.1000/demo"},
                "openAccessPdf": {"url": "https://s2.local/demo.pdf"},
            }

        with tempfile.TemporaryDirectory() as tempdir:
            raw_path = Path(tempdir) / "demo.json"
            meta_path = Path(tempdir) / "demo-paper.json"
            raw_path.write_text(json.dumps(raw_payload(), ensure_ascii=False), encoding="utf-8")
            meta_path.write_text(json.dumps(meta_artifact(), ensure_ascii=False), encoding="utf-8")

            record = normalize_raw_file(
                raw_path,
                meta_path=meta_path,
                extractor_version="meta-v1",
                fetcher=fake_fetch,
            )

        self.assertEqual(record["links"]["pdf"], "https://translate.local/paper.pdf")
        self.assertEqual(record["links"]["code"], "https://github.com/demo/repo")
        self.assertEqual(record["abstract_raw"], "Original abstract")
        self.assertEqual(record["citation_count"], 10)
        self.assertEqual(record["authors"], ["Author A"])
        self.assertEqual(record["reading_digest"]["recommended_route"], "method")
        self.assertEqual(record["research_problem"]["goal"], "提升单图 3D 资产生成的稳定性与质量。")
        self.assertEqual(record["method_core"]["representation"], ["Mesh"])
        self.assertEqual(record["research_tags"]["tasks"], ["Image-to-3D"])
        self.assertEqual(record["figure_table_index"]["figures"][0]["role"], "method_overview")
        self.assertEqual(record["figure_table_index"]["tables"][0]["role"], "quantitative_result")

    def test_normalize_falls_back_to_semantic_pdf_and_network_errors_do_not_abort(self) -> None:
        def fake_fetch(url: str, headers: dict[str, str]) -> dict[str, object]:
            return {
                "title": "Demo Paper",
                "authors": [],
                "year": 2024,
                "venue": "CVPR",
                "citationCount": None,
                "abstract": "Original abstract",
                "openAccessPdf": {"url": "https://s2.local/demo.pdf"},
            }

        with tempfile.TemporaryDirectory() as tempdir:
            raw_path = Path(tempdir) / "demo.json"
            meta_path = Path(tempdir) / "demo-paper.json"
            raw_path.write_text(json.dumps(raw_payload(pdf_url=None), ensure_ascii=False), encoding="utf-8")
            meta_path.write_text(json.dumps(meta_artifact(), ensure_ascii=False), encoding="utf-8")

            record = normalize_raw_file(
                raw_path,
                meta_path=meta_path,
                extractor_version="meta-v1",
                fetcher=fake_fetch,
            )

        self.assertEqual(record["links"]["pdf"], "https://s2.local/demo.pdf")
        self.assertIn("figures", record["figure_table_index"])
        self.assertIn("tables", record["figure_table_index"])

        def failing_fetch(url: str, headers: dict[str, str]) -> dict[str, object]:
            raise URLError("network down")

        with tempfile.TemporaryDirectory() as tempdir:
            raw_path = Path(tempdir) / "demo.json"
            meta_path = Path(tempdir) / "demo-paper.json"
            raw_path.write_text(json.dumps(raw_payload(pdf_url=None), ensure_ascii=False), encoding="utf-8")
            meta_path.write_text(json.dumps(meta_artifact(), ensure_ascii=False), encoding="utf-8")

            record = normalize_raw_file(
                raw_path,
                meta_path=meta_path,
                extractor_version="meta-v1",
                fetcher=failing_fetch,
            )

        self.assertIsNone(record["abstract_raw"])
        self.assertIsNone(record["links"]["pdf"])
        self.assertEqual(record["authors"], [])

    def test_normalize_requires_meta_artifact_and_preserves_existing_enrichment(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            raw_path = Path(tempdir) / "demo.json"
            raw_path.write_text(json.dumps(raw_payload(pdf_url=None), ensure_ascii=False), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Missing meta artifact"):
                normalize_raw_file(
                    raw_path,
                    meta_path=Path(tempdir) / "missing.json",
                    extractor_version="meta-v1",
                )

        def failing_fetch(url: str, headers: dict[str, str]) -> dict[str, object]:
            raise URLError("network down")

        existing_record = {
            "authors": ["Author A", "Author B"],
            "abstract_raw": "Existing abstract",
            "citation_count": 12,
            "links": {
                "pdf": "https://translate.local/paper.pdf",
                "doi": "10.1000/demo",
                "arxiv": "2401.00001",
                "project": "https://project.local/demo",
                "code": "https://github.com/demo/repo",
                "data": "https://huggingface.co/datasets/demo",
            },
        }

        with tempfile.TemporaryDirectory() as tempdir:
            raw_path = Path(tempdir) / "demo.json"
            meta_path = Path(tempdir) / "demo-paper.json"
            raw_path.write_text(json.dumps(raw_payload(pdf_url=None), ensure_ascii=False), encoding="utf-8")
            meta_path.write_text(json.dumps(meta_artifact(), ensure_ascii=False), encoding="utf-8")

            record = normalize_raw_file(
                raw_path,
                meta_path=meta_path,
                extractor_version="meta-v1",
                fetcher=failing_fetch,
                existing_record=existing_record,
            )

        self.assertEqual(record["authors"], ["Author A", "Author B"])
        self.assertEqual(record["abstract_raw"], "Existing abstract")
        self.assertEqual(record["citation_count"], 12)
        self.assertEqual(record["links"]["doi"], "10.1000/demo")
        self.assertEqual(record["links"]["arxiv"], "2401.00001")
        self.assertEqual(record["links"]["project"], "https://project.local/demo")
        self.assertEqual(record["links"]["code"], "https://github.com/demo/repo")
        self.assertEqual(record["links"]["data"], "https://huggingface.co/datasets/demo")


if __name__ == "__main__":
    unittest.main()
