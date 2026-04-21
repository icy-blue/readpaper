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
    build_reading_digest,
    extract_method_core,
    extract_research_problem,
    extract_storyline,
    normalize_raw_file,
    semantic_scholar_title_match,
)


def raw_payload(*, pdf_url: str | None = "https://translate.local/paper.pdf") -> dict[str, object]:
    return {
        "paper_id": "demo-paper",
        "source_conversation_ids": ["conv-1"],
        "conversation": {
            "id": "conv-1",
            "title": "Demo Paper",
            "created_at": "2026-04-21T00:00:00+08:00",
            "year": 2024,
            "venue_abbr": "CVPR",
            "citation_count": None,
            "pdf_url": pdf_url,
            "figures": [],
            "tables": [],
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
                    "translation_status": {
                        "current_unit_id": "Abstract",
                        "state": "IN_PROGRESS",
                        "completed_unit_count": 1,
                        "total_unit_count": 3,
                        "active_scope": "body",
                        "is_all_done": False,
                    },
                },
                {
                    "message_kind": "bot_reply",
                    "visible_to_user": True,
                    "content": "# 1. Introduction\n\n本文关注从单张图像生成 3D 资产的问题。",
                    "translation_status": {
                        "current_unit_id": "1. Introduction",
                        "state": "IN_PROGRESS",
                        "completed_unit_count": 2,
                        "total_unit_count": 3,
                        "active_scope": "body",
                        "is_all_done": False,
                    },
                },
                {
                    "message_kind": "bot_reply",
                    "visible_to_user": True,
                    "content": "# 3. Conclusion\n\n实验表明，该方法在质量上达到当前最优。",
                    "translation_status": {
                        "current_unit_id": "3. Conclusion",
                        "state": "BODY_DONE",
                        "completed_unit_count": 3,
                        "total_unit_count": 3,
                        "active_scope": "body",
                        "is_all_done": False,
                    },
                },
            ],
        },
    }


class NormalizePapersTests(unittest.TestCase):
    def test_extract_storyline_and_research_problem_keep_field_semantics(self) -> None:
        abstract_zh = (
            "开放世界可提示三维语义分割仍然较为脆弱，因为语义是在输入传感器坐标系中推断的。"
            "为了解决这一问题，我们提出 CoSMo3D，通过规范空间建模提升开放词汇分割的稳定性。"
            "实验表明该方法显著优于现有方法。"
        )
        introduction = (
            "现有方法仍然受限于几何—文本匹配机制，在跨类别场景中容易失效。"
            "我们的目标是建立面向开放世界 3D 部件理解的规范空间建模。"
        )
        method_text = (
            "我们提出一个双分支框架，通过 LLM 引导的类内与跨类别对齐构建规范空间先验。"
        )
        conclusion = "实验表明该方法显著优于现有方法，在开放世界可提示三维分割任务上达到当前最优。"

        storyline = extract_storyline(abstract_zh, introduction, method_text, conclusion)
        research_problem = extract_research_problem(introduction, abstract_zh)

        self.assertIsNotNone(storyline["problem"])
        self.assertTrue("脆弱" in storyline["problem"] or "受限" in storyline["problem"])
        self.assertNotIn("显著优于", storyline["problem"])
        self.assertIsNotNone(storyline["method"])
        self.assertIn("我们提出", storyline["method"])
        self.assertIsNotNone(storyline["outcome"])
        self.assertIn("显著优于", storyline["outcome"])
        self.assertIsNotNone(research_problem["summary"])
        self.assertNotIn("显著优于", research_problem["summary"])
        self.assertNotIn("我们提出", research_problem["summary"])
        self.assertEqual(research_problem["goal"], "我们的目标是建立面向开放世界 3D 部件理解的规范空间建模。")
        self.assertNotIn("心理物理学", research_problem["goal"] or "")
        self.assertTrue(all("显著优于" not in item for item in research_problem["gaps"]))

    def test_extract_method_core_and_reading_digest_produce_display_friendly_summary(self) -> None:
        method_text = (
            "## 3.2. 统一的跨类别规范数据集\n"
            "我们提出一个双分支框架，通过规范映射锚定与规范边界框校准实现开放世界 3D 部件推理。"
            "首先构建统一的跨类别规范数据集。然后学习规范空间先验。最后把规范嵌入用于部件预测。"
        )
        abstract_zh = "我们提出 CoSMo3D，通过规范空间建模提升开放词汇分割的稳定性。"
        contributions = ["我们引入跨类别规范空间先验。", "实验表明该方法显著优于现有方法。"]
        findings = ["实验表明该方法显著优于现有方法。"]

        method_core = extract_method_core(method_text, abstract_zh, contributions, findings)
        self.assertIsNotNone(method_core["approach_summary"])
        self.assertFalse((method_core["approach_summary"] or "").startswith("给定一个"))
        self.assertTrue(all("##" not in item for item in method_core["innovations"]))
        self.assertTrue(all(not item.startswith("3.2") for item in method_core["innovations"]))

        reading_digest = build_reading_digest(
            themes=["3D Understanding"],
            tasks=["Open-Vocabulary Segmentation"],
            methods=["Large Language Model"],
            modalities=["3D", "text"],
            novelty_type=["representation"],
            storyline={
                "problem": "开放世界可提示三维语义分割仍然较为脆弱。",
                "method": "我们提出 CoSMo3D，通过规范空间建模提升开放词汇分割稳定性。",
                "outcome": "实验表明该方法显著优于现有方法。",
            },
            research_problem={
                "summary": "现有方法仍然受限于几何—文本匹配机制。",
                "gaps": ["现有方法仍然受限于几何—文本匹配机制。"],
                "goal": "建立规范空间建模。",
            },
            method_core=method_core,
            findings=findings,
            best_results=findings,
            comparison_context={"explicit_baselines": ["Find3D"], "contrast_methods": [], "comparison_aspects": []},
            research_value={
                "summary": "适合作为 3D Understanding 方向的持续阅读入口。",
                "points": ["适合作为开放词汇分割方向的对比样本。", "可用于理解 Large Language Model 这条方法路线。"],
            },
            editor_note={
                "summary": "可作为 3D Understanding 方向的代表样本。",
                "points": ["可优先与 Find3D 对比阅读。", "实验表明该方法显著优于现有方法。"],
            },
        )

        self.assertNotIn("任务:", " ".join(reading_digest["why_read"]))
        self.assertNotIn("方法:", " ".join(reading_digest["why_read"]))
        self.assertNotIn("我们提出", reading_digest["value_statement"] or "")
        self.assertEqual(reading_digest["narrative"]["problem"], "开放世界可提示三维语义分割仍然较为脆弱。")
        self.assertEqual(reading_digest["narrative"]["result"], "实验表明该方法显著优于现有方法。")
        self.assertEqual(reading_digest["result_headline"], "实验表明该方法显著优于现有方法。")

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

    def test_normalize_prefers_conversation_pdf_over_semantic_pdf_and_classifies_code(self) -> None:
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
            raw_path.write_text(json.dumps(raw_payload(), ensure_ascii=False), encoding="utf-8")

            record = normalize_raw_file(raw_path, fetcher=fake_fetch)

        self.assertEqual(record["links"]["pdf"], "https://translate.local/paper.pdf")
        self.assertEqual(record["links"]["code"], "https://github.com/demo/repo")
        self.assertEqual(record["abstract_raw"], "Original abstract")
        self.assertEqual(record["citation_count"], 10)
        self.assertEqual(record["authors"], ["Author A"])
        self.assertIsInstance(record["storyline"], dict)
        self.assertIn("problem", record["storyline"])
        self.assertIsInstance(record["research_problem"], dict)
        self.assertIn("summary", record["research_problem"])
        self.assertIsInstance(record["summary"]["research_value"], dict)
        self.assertIn("summary", record["summary"]["research_value"])
        self.assertIn("reading_digest", record)
        self.assertIn("editorial_review", record)
        self.assertIn(record["reading_digest"]["recommended_route"], {"method", "evaluation", "comparison", "overview"})
        self.assertIn("positioning", record["reading_digest"])
        self.assertIn("narrative", record["reading_digest"])
        self.assertIn("verdict", record["editorial_review"])
        self.assertIn("type", record["key_claims"][0])
        self.assertIn(record["key_claims"][0]["type"], {"method", "experiment", "capability", "limitation"})
        self.assertIn("approach_summary", record["method_core"])
        self.assertIn("pipeline_steps", record["method_core"])
        self.assertIn("innovations", record["method_core"])
        self.assertIn("best_results", record["benchmarks_or_eval"])
        self.assertLessEqual(len(record["summary"]["one_liner"]), 120)
        self.assertLessEqual(len(record["reading_digest"]["value_statement"] or ""), 80)
        self.assertLessEqual(len(record["method_core"]["approach_summary"] or ""), 100)
        if record["benchmarks_or_eval"]["findings"]:
            self.assertLessEqual(len(record["benchmarks_or_eval"]["findings"][0]), 80)
        self.assertIn("comparison_aspects", record["comparison_context"])
        self.assertIn("recommended_next_read", record["comparison_context"])

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
            raw_path.write_text(json.dumps(raw_payload(pdf_url=None), ensure_ascii=False), encoding="utf-8")

            record = normalize_raw_file(raw_path, fetcher=fake_fetch)

        self.assertEqual(record["links"]["pdf"], "https://s2.local/demo.pdf")
        self.assertIn("figures", record["figure_table_index"])
        self.assertIn("tables", record["figure_table_index"])

        def failing_fetch(url: str, headers: dict[str, str]) -> dict[str, object]:
            raise URLError("network down")

        with tempfile.TemporaryDirectory() as tempdir:
            raw_path = Path(tempdir) / "demo.json"
            raw_path.write_text(json.dumps(raw_payload(pdf_url=None), ensure_ascii=False), encoding="utf-8")

            record = normalize_raw_file(raw_path, fetcher=failing_fetch)

        self.assertIsNone(record["abstract_raw"])
        self.assertIsNone(record["links"]["pdf"])
        self.assertEqual(record["authors"], [])

    def test_normalize_preserves_existing_enrichment_when_fetch_fails(self) -> None:
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
            raw_path.write_text(json.dumps(raw_payload(pdf_url=None), ensure_ascii=False), encoding="utf-8")

            record = normalize_raw_file(raw_path, fetcher=failing_fetch, existing_record=existing_record)

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
