from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.error import URLError


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from normalize_papers import normalize_raw_file, semantic_scholar_title_match  # noqa: E402


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
        self.assertIn("type", record["key_claims"][0])
        self.assertIn(record["key_claims"][0]["type"], {"method", "experiment", "capability", "limitation"})
        self.assertIn("approach_summary", record["method_core"])
        self.assertIn("pipeline_steps", record["method_core"])
        self.assertIn("innovations", record["method_core"])
        self.assertIn("best_results", record["benchmarks_or_eval"])
        self.assertLessEqual(len(record["summary"]["one_liner"]), 120)
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
