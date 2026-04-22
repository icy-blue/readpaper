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


def meta_artifact(*, version: str = "meta-v7") -> dict[str, object]:
    return {
        "paper_id": "demo-paper",
        "extractor_version": version,
        "source_conversation_id": "conv-1",
        "source_semantic_updated_at": "2026-04-21T09:30:00+08:00",
        "extracted_at": "2026-04-21T10:00:00+08:00",
        "meta": {
            "story": {
                "paper_one_liner": "一篇把单图 3D 生成做得更稳的论文。",
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
            "research_risks": ["评测场景还不够广。"],
            "editorial": {
                "research_position": "可作为单图 3D 生成扩散路线的代表样本。",
                "graph_worthy": True,
            },
            "taxonomy": {
                "themes": ["3D Generation"],
                "tasks": ["Image-to-3D"],
                "methods": ["Diffusion Model"],
                "modalities": ["Image", "3D"],
                "novelty_types": ["Representation Modeling"],
            },
            "comparison": {
                "aspects": [{"aspect": "method", "difference": "更强调生成稳定性而不是只追求峰值质量。"}],
                "next_read": ["BaselineNet"],
            },
            "discovery_axes": {
                "problem": ["single-image-3d-stability"],
                "method": ["diffusion-image-to-3d"],
                "evaluation": ["objaverse-benchmark-line"],
                "risk": ["limited-eval-coverage"],
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
            "route_path": "#/?paper=baseline-net-paper&detail=1",
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
        "story": {"paper_one_liner": None},
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
        "research_risks": [],
        "editorial": {"research_position": None, "graph_worthy": False},
        "taxonomy": {
            "themes": ["3D Generation"],
            "tasks": ["Image-to-3D"],
            "methods": ["Reconstruction"],
            "modalities": ["Image", "3D"],
            "novelty_types": [],
        },
        "comparison": {"aspects": [], "next_read": []},
        "discovery_axes": {"problem": [], "method": [], "evaluation": [], "risk": []},
        "relations": [],
    }


class NormalizePapersTests(unittest.TestCase):
    def test_read_extractor_version_and_meta_artifact_current_check(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            config_path = Path(tempdir) / "extractor-config.json"
            meta_path = Path(tempdir) / "demo-paper.json"
            config_path.write_text(json.dumps({"extractor_version": "meta-v7"}), encoding="utf-8")
            meta_path.write_text(json.dumps(meta_artifact(), ensure_ascii=False), encoding="utf-8")

            version = read_extractor_version(config_path)
            self.assertEqual(version, "meta-v7")
            self.assertTrue(meta_artifact_is_current(meta_path, version))
            self.assertFalse(meta_artifact_is_current(meta_path, "meta-v8"))

    def test_validate_meta_payload_accepts_v7_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            meta_path = Path(tempdir) / "demo-paper.json"
            payload = meta_artifact()
            meta_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

            validated = validate_meta_payload(meta_path, payload, "demo-paper", "meta-v7")
            self.assertEqual(validated["meta"]["story"]["paper_one_liner"], "一篇把单图 3D 生成做得更稳的论文。")
            self.assertIn("Diffusion Model", validated["meta"]["taxonomy"]["methods"])
            self.assertEqual(validated["meta"]["research_risks"][0], "评测场景还不够广。")
            self.assertEqual(validated["meta"]["discovery_axes"]["problem"][0], "single-image-3d-stability")
            self.assertEqual(validated["meta"]["relation_candidates"][0]["target_name"], "BaselineNet")

    def test_validate_meta_payload_normalizes_chinese_display_text(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            meta_path = Path(tempdir) / "demo-paper.json"
            payload = meta_artifact()
            payload["meta"]["research_problem"]["summary"] = "常用的“先检测后匹配”注册方法在跨模态场景中面临困难,原因在于关键点检测不兼容以及特征描述不一致。"  # type: ignore[index]
            payload["meta"]["editorial"]["research_position"] = "适合作为3D Reconstruction中Point Cloud Normal Estimation路线的代表样本。"  # type: ignore[index]
            payload["meta"]["claims"][0]["text"] = "我们通过(PnP)求解器提升2D3D-MATR在KITTI数据集上的效果!"  # type: ignore[index]
            meta_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

            validated = validate_meta_payload(meta_path, payload, "demo-paper", "meta-v7")

            self.assertEqual(
                validated["meta"]["research_problem"]["summary"],
                "常用的“先检测后匹配”注册方法在跨模态场景中面临困难，原因在于关键点检测不兼容以及特征描述不一致。",
            )
            self.assertEqual(
                validated["meta"]["editorial"]["research_position"],
                "适合作为 3D Reconstruction 中 Point Cloud Normal Estimation 路线的代表样本。",
            )
            self.assertEqual(
                validated["meta"]["claims"][0]["text"],
                "我们通过（PnP）求解器提升 2D3D-MATR 在 KITTI 数据集上的效果！",
            )

    def test_validate_meta_payload_rejects_incomplete_relation_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            meta_path = Path(tempdir) / "demo-paper.json"
            payload = meta_artifact()
            payload["meta"]["relation_candidates"][0].pop("target_name")  # type: ignore[index]
            meta_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

            with self.assertRaises(ValueError):
                validate_meta_payload(meta_path, payload, "demo-paper", "meta-v5")

    def test_normalize_raw_file_builds_canonical_record(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            raw_path = root / "raw.json"
            meta_path = root / "meta.json"
            raw_path.write_text(json.dumps(raw_payload(), ensure_ascii=False), encoding="utf-8")
            meta_path.write_text(json.dumps(meta_artifact(), ensure_ascii=False), encoding="utf-8")

            record = normalize_raw_file(raw_path, meta_path=meta_path, extractor_version="meta-v7")

            self.assertEqual(record["id"], "demo-paper")
            self.assertEqual(record["source"]["conversation_ids"], ["conv-1"])
            self.assertEqual(record["bibliography"]["title"], "Demo Paper")
            self.assertEqual(record["bibliography"]["authors"], [])
            self.assertIsNone(record["bibliography"]["identifiers"]["doi"])
            self.assertIsNone(record["abstracts"]["raw"])
            self.assertEqual(record["abstracts"]["zh"], "我们提出 Demo 方法，并在公开基准上显著优于 baseline。代码见 https://github.com/demo/repo。")
            self.assertIn("Image-to-3D", record["taxonomy"]["tasks"])
            self.assertEqual(record["research_risks"], ["评测场景还不够广。"])
            self.assertNotIn("reading_digest", record)
            self.assertNotIn("paper_neighbors", record)

    def test_normalize_raw_file_resolves_local_relation(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            raw_path = root / "raw.json"
            meta_path = root / "meta.json"
            registry_path = root / "baseline-net-paper.json"
            raw_path.write_text(json.dumps(raw_payload(), ensure_ascii=False), encoding="utf-8")
            payload = meta_artifact()
            payload["meta"]["relation_candidates"] = [
                {
                    "type": "compares_to",
                    "target_name": "BaselineNet: A Strong Baseline for Image-to-3D",
                    "description": "主对照方法。",
                    "confidence_hint": "high",
                    "evidence_mode": "explicit",
                }
            ]
            meta_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            registry_path.write_text(json.dumps(local_target_record(), ensure_ascii=False), encoding="utf-8")
            registry_items = registry_payload()["items"]  # type: ignore[index]
            registry_items[0]["record_path"] = str(registry_path)
            record = normalize_raw_file(
                raw_path,
                meta_path=meta_path,
                extractor_version="meta-v7",
                registry_items=registry_items,
            )

            self.assertEqual(record["relations"][0]["target_kind"], "local")
            self.assertEqual(record["relations"][0]["target_paper_id"], "baseline-net-paper")
            self.assertNotIn("target_semantic_scholar_paper_id", record["relations"][0])
            self.assertNotIn("target_url", record["relations"][0])
            self.assertEqual(record["relations"][0]["confidence"], 0.9)

    def test_normalize_raw_file_resolves_external_relation(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            raw_path = root / "raw.json"
            meta_path = root / "meta.json"
            raw_path.write_text(json.dumps(raw_payload(), ensure_ascii=False), encoding="utf-8")
            meta_path.write_text(json.dumps(meta_artifact(), ensure_ascii=False), encoding="utf-8")

            record = normalize_raw_file(
                raw_path,
                meta_path=meta_path,
                extractor_version="meta-v7",
                registry_items=[],
            )

            self.assertEqual(record["relations"][0]["target_kind"], "external")
            self.assertEqual(record["relations"][0]["label"], "BaselineNet")
            self.assertNotIn("target_semantic_scholar_paper_id", record["relations"][0])
            self.assertNotIn("target_url", record["relations"][0])
            self.assertEqual(record["relations"][0]["confidence"], 0.82)

    def test_normalize_raw_file_falls_back_to_external_relation_without_network(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            raw_path = root / "raw.json"
            meta_path = root / "meta.json"
            raw_path.write_text(json.dumps(raw_payload(), ensure_ascii=False), encoding="utf-8")
            meta_path.write_text(json.dumps(meta_artifact(), ensure_ascii=False), encoding="utf-8")

            record = normalize_raw_file(
                raw_path,
                meta_path=meta_path,
                extractor_version="meta-v7",
                registry_items=[],
            )

            self.assertEqual(record["relations"][0]["target_kind"], "external")
            self.assertEqual(record["relations"][0]["label"], "BaselineNet")

    def test_normalize_raw_file_skips_self_relation_target(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            raw_path = root / "raw.json"
            meta_path = root / "meta.json"
            raw_path.write_text(json.dumps(raw_payload(), ensure_ascii=False), encoding="utf-8")
            payload = meta_artifact()
            payload["meta"]["relation_candidates"] = [
                {
                    "type": "compares_to",
                    "target_name": "Demo Paper",
                    "description": "错误的自指关系。",
                    "confidence_hint": "high",
                    "evidence_mode": "explicit",
                }
            ]
            meta_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

            record = normalize_raw_file(raw_path, meta_path=meta_path, extractor_version="meta-v7")

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
