from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from normalize_papers import (  # noqa: E402
    extract_sections,
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


def meta_artifact(*, version: str = "meta-v4") -> dict[str, object]:
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
            "relation_candidates": [
                {
                    "type": "compares_to",
                    "target_name": "BaselineNet",
                    "description": "主对照方法。",
                    "confidence_hint": "high",
                    "evidence_mode": "explicit",
                }
            ],
        },
    }


def registry_payload() -> dict[str, object]:
    return {
        "source": "https://translate.icydev.cn",
        "updated_at": "2026-04-22T00:59:39+00:00",
        "items": [
            {
                "paper_id": "baseline-net-paper",
                "title": "BaselineNet: A Strong Baseline for Image-to-3D",
                "year": "2024",
                "venue": "CVPR",
                "dedupe_key": "baselinenet a strong baseline for image to 3d::2024::cvpr",
                "fallback_key": "baselinenet a strong baseline for image to 3d::2024",
                "record_path": "baseline-net-paper.json",
            }
        ],
    }


def local_target_record() -> dict[str, object]:
    return {
        "id": "baseline-net-paper",
        "source": {
            "conversation_ids": ["conv-2"],
            "paper_path": "papers/baseline-net-paper.md",
            "route_path": "#/paper/baseline-net-paper",
        },
        "bibliography": {
            "title": "BaselineNet: A Strong Baseline for Image-to-3D",
            "authors": ["Author B"],
            "year": 2024,
            "venue": "CVPR",
            "citation_count": 5,
            "identifiers": {"doi": None, "arxiv": None},
            "links": {"pdf": None, "project": None, "code": None, "data": None},
        },
        "abstracts": {"raw": None, "zh": None},
        "story": {"paper_one_liner": None, "problem": None, "method": None, "result": None},
        "research_problem": {"summary": None, "gaps": [], "goal": None},
        "core_contributions": [],
        "method": {
            "summary": None,
            "pipeline_steps": [],
            "innovations": [],
            "ingredients": [],
            "inputs": ["Image"],
            "outputs": ["3D Asset"],
            "representations": ["Mesh"],
        },
        "evaluation": {"headline": None, "datasets": [], "metrics": [], "baselines": [], "key_findings": [], "setup_summary": None},
        "claims": [],
        "conclusion": {"author": None, "limitations": []},
        "editorial": {
            "verdict": None,
            "summary": None,
            "why_read": [],
            "strengths": [],
            "cautions": [],
            "reading_route": "overview",
            "research_position": None,
            "graph_worthy": False,
            "next_read": [],
        },
        "taxonomy": {
            "themes": ["3D Generation"],
            "tasks": ["Image-to-3D"],
            "methods": ["Reconstruction"],
            "modalities": ["Image", "3D"],
            "representations": ["Mesh"],
            "novelty_types": [],
        },
        "comparison": {"aspects": [], "next_read": []},
        "assets": {"figures": [], "tables": []},
        "relations": [],
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
            config_path.write_text(json.dumps({"extractor_version": "meta-v4"}), encoding="utf-8")
            meta_path.write_text(json.dumps(meta_artifact(), ensure_ascii=False), encoding="utf-8")

            version = read_extractor_version(config_path)
            self.assertEqual(version, "meta-v4")
            self.assertTrue(meta_artifact_is_current(meta_path, version))
            self.assertFalse(meta_artifact_is_current(meta_path, "meta-v5"))

    def test_validate_meta_payload_accepts_v4_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            meta_path = Path(tempdir) / "demo-paper.json"
            payload = meta_artifact()
            meta_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

            validated = validate_meta_payload(meta_path, payload, "demo-paper", "meta-v4")
            self.assertEqual(validated["meta"]["story"]["paper_one_liner"], "一篇把单图 3D 生成做得更稳的论文。")
            self.assertEqual(validated["meta"]["editorial"]["reading_route"], "method")
            self.assertIn("Diffusion Model", validated["meta"]["taxonomy"]["methods"])
            self.assertEqual(validated["meta"]["relation_candidates"][0]["target_name"], "BaselineNet")

    def test_validate_meta_payload_rejects_incomplete_relation_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            meta_path = Path(tempdir) / "demo-paper.json"
            payload = meta_artifact()
            payload["meta"]["relation_candidates"][0].pop("target_name")  # type: ignore[index]
            meta_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

            with self.assertRaises(ValueError):
                validate_meta_payload(meta_path, payload, "demo-paper", "meta-v4")

    def test_normalize_raw_file_builds_canonical_record(self) -> None:
        def fake_fetch(url: str, headers: dict[str, str]) -> dict[str, object]:
            if "query=Demo+Paper" in url:
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
            raise AssertionError(f"Unexpected fetch url: {url}")

        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            raw_path = root / "raw.json"
            meta_path = root / "meta.json"
            raw_path.write_text(json.dumps(raw_payload(), ensure_ascii=False), encoding="utf-8")
            meta_path.write_text(json.dumps(meta_artifact(), ensure_ascii=False), encoding="utf-8")

            record = normalize_raw_file(raw_path, meta_path=meta_path, extractor_version="meta-v4", fetcher=fake_fetch)

            self.assertEqual(record["id"], "demo-paper")
            self.assertEqual(record["source"]["conversation_ids"], ["conv-1"])
            self.assertEqual(record["bibliography"]["title"], "Demo Paper")
            self.assertEqual(record["bibliography"]["identifiers"]["doi"], "10.1000/demo")
            self.assertEqual(record["abstracts"]["zh"], "我们提出 Demo 方法，并在公开基准上显著优于 baseline。代码见 https://github.com/demo/repo 。")
            self.assertIn("Image-to-3D", record["taxonomy"]["tasks"])
            self.assertNotIn("reading_digest", record)
            self.assertNotIn("paper_neighbors", record)

    def test_normalize_raw_file_resolves_local_relation(self) -> None:
        def fake_fetch(url: str, headers: dict[str, str]) -> dict[str, object]:
            if "query=Demo+Paper" in url:
                return {
                    "title": "Demo Paper",
                    "authors": [{"name": "Author A"}],
                    "year": 2024,
                    "venue": "CVPR",
                    "citationCount": 9,
                    "abstract": "Original abstract",
                    "externalIds": {"DOI": "10.1000/demo"},
                    "openAccessPdf": {"url": "https://s2.local/demo.pdf"},
                }
            raise AssertionError(f"Unexpected fetch url: {url}")

        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            raw_path = root / "raw.json"
            meta_path = root / "meta.json"
            registry_path = root / "baseline-net-paper.json"
            raw_path.write_text(json.dumps(raw_payload(), ensure_ascii=False), encoding="utf-8")
            meta_path.write_text(json.dumps(meta_artifact(), ensure_ascii=False), encoding="utf-8")
            registry_path.write_text(json.dumps(local_target_record(), ensure_ascii=False), encoding="utf-8")
            registry_items = registry_payload()["items"]  # type: ignore[index]
            registry_items[0]["record_path"] = str(registry_path)
            record = normalize_raw_file(
                raw_path,
                meta_path=meta_path,
                extractor_version="meta-v4",
                registry_items=registry_items,
                fetcher=fake_fetch,
            )

            self.assertEqual(record["relations"][0]["target_kind"], "local")
            self.assertEqual(record["relations"][0]["target_paper_id"], "baseline-net-paper")
            self.assertEqual(record["relations"][0]["confidence"], 0.9)

    def test_normalize_raw_file_resolves_external_relation(self) -> None:
        def fake_fetch(url: str, headers: dict[str, str]) -> dict[str, object]:
            if "query=Demo+Paper" in url:
                return {
                    "title": "Demo Paper",
                    "authors": [{"name": "Author A"}],
                    "year": 2024,
                    "venue": "CVPR",
                    "citationCount": 9,
                    "abstract": "Original abstract",
                    "externalIds": {"DOI": "10.1000/demo"},
                    "openAccessPdf": {"url": "https://s2.local/demo.pdf"},
                }
            if "query=BaselineNet" in url:
                return {
                    "paperId": "external-baseline-paper-id",
                    "title": "BaselineNet",
                    "authors": [{"name": "Author Z"}],
                    "year": 2023,
                    "venue": "NeurIPS",
                    "citationCount": 20,
                    "abstract": "External baseline abstract",
                    "externalIds": {"DOI": "10.1000/baseline"},
                    "openAccessPdf": {"url": "https://s2.local/baseline.pdf"},
                }
            raise AssertionError(f"Unexpected fetch url: {url}")

        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            raw_path = root / "raw.json"
            meta_path = root / "meta.json"
            raw_path.write_text(json.dumps(raw_payload(), ensure_ascii=False), encoding="utf-8")
            meta_path.write_text(json.dumps(meta_artifact(), ensure_ascii=False), encoding="utf-8")

            record = normalize_raw_file(
                raw_path,
                meta_path=meta_path,
                extractor_version="meta-v4",
                registry_items=[],
                fetcher=fake_fetch,
            )

            self.assertEqual(record["relations"][0]["target_kind"], "external")
            self.assertEqual(record["relations"][0]["target_semantic_scholar_paper_id"], "external-baseline-paper-id")
            self.assertEqual(record["relations"][0]["target_url"], "https://www.semanticscholar.org/paper/external-baseline-paper-id")
            self.assertEqual(record["relations"][0]["confidence"], 0.82)

    def test_normalize_raw_file_drops_unresolved_relation(self) -> None:
        def fake_fetch(url: str, headers: dict[str, str]) -> dict[str, object]:
            if "query=Demo+Paper" in url:
                return {
                    "title": "Demo Paper",
                    "authors": [{"name": "Author A"}],
                    "year": 2024,
                    "venue": "CVPR",
                    "citationCount": 9,
                    "abstract": "Original abstract",
                    "externalIds": {"DOI": "10.1000/demo"},
                    "openAccessPdf": {"url": "https://s2.local/demo.pdf"},
                }
            return {"data": []}

        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            raw_path = root / "raw.json"
            meta_path = root / "meta.json"
            raw_path.write_text(json.dumps(raw_payload(), ensure_ascii=False), encoding="utf-8")
            meta_path.write_text(json.dumps(meta_artifact(), ensure_ascii=False), encoding="utf-8")

            record = normalize_raw_file(
                raw_path,
                meta_path=meta_path,
                extractor_version="meta-v4",
                registry_items=[],
                fetcher=fake_fetch,
            )

            self.assertEqual(record["relations"], [])

    def test_extract_sections_falls_back_to_section_category_and_heading(self) -> None:
        conversation = {
            "messages": [
                {
                    "message_kind": "bot_reply",
                    "visible_to_user": True,
                    "section_category": "abstract",
                    "content": "# 摘要\n\n这是摘要。",
                },
                {
                    "message_kind": "bot_reply",
                    "visible_to_user": True,
                    "section_category": "body",
                    "content": "# 1. 引言\n\n这是引言。",
                },
                {
                    "message_kind": "bot_reply",
                    "visible_to_user": True,
                    "section_category": "body",
                    "content": "# 3. 方法\n\n这是方法。",
                },
            ]
        }

        sections = extract_sections(conversation)

        self.assertEqual(sections["abstract"], ["这是摘要。"])
        self.assertEqual(sections["introduction"], ["这是引言。"])
        self.assertEqual(sections["method"], ["这是方法。"])


if __name__ == "__main__":
    unittest.main()
