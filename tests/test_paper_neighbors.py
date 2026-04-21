from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from paper_neighbors import backfill_records, build_site_payload, summarize_records  # noqa: E402


def make_record(
    paper_id: str,
    *,
    title: str,
    theme: str,
    tasks: list[str],
    methods: list[str],
    inputs: list[str],
    outputs: list[str],
    modalities: list[str],
    baselines: list[str] | None = None,
    ingredients: list[str] | None = None,
    representations: list[str] | None = None,
) -> dict[str, object]:
    return {
        "paper_id": paper_id,
        "source_conversation_ids": [f"conv-{paper_id}"],
        "title": title,
        "authors": ["Author A"],
        "year": 2025,
        "venue": "arXiv",
        "citation_count": None,
        "links": {
            "pdf": f"https://example.com/{paper_id}.pdf",
            "doi": None,
            "arxiv": None,
            "project": None,
            "code": None,
            "data": None,
        },
        "abstract_raw": "test abstract raw",
        "abstract_zh": "测试摘要",
        "summary": {
            "one_liner": "test summary",
            "abstract_summary": "test abstract",
            "research_value": {
                "summary": "test value",
                "points": ["point a"],
            },
            "worth_long_term_graph": True,
        },
        "reading_digest": {
            "value_statement": "值得看的测试论文。",
            "best_for": "适合测试读者。",
            "why_read": ["理由一", "理由二"],
            "recommended_route": "method",
            "positioning": {
                "task": tasks[:2],
                "modality": modalities[:3],
                "method": methods[:2],
                "novelty": [],
            },
            "narrative": {
                "problem": "test problem",
                "method": "test method",
                "result": "test result",
            },
            "result_headline": "test result headline",
        },
        "storyline": {
            "problem": "test problem",
            "method": "test method",
            "outcome": "test outcome",
        },
        "research_problem": {
            "summary": "test problem",
            "gaps": ["gap a"],
            "goal": "test goal",
        },
        "core_contributions": ["contribution a", "contribution b"],
        "key_claims": [
            {
                "claim": "test claim",
                "type": "method",
                "support": ["section:Abstract"],
                "confidence": "high",
            }
        ],
        "method_core": {
            "approach_summary": "test approach",
            "pipeline_steps": ["step 1", "step 2"],
            "innovations": ["test innovation"],
            "ingredients": ingredients or [],
            "representation": representations or [],
            "supervision": [],
            "differences": [],
        },
        "inputs_outputs": {
            "inputs": inputs,
            "outputs": outputs,
            "modalities": modalities,
        },
        "benchmarks_or_eval": {
            "datasets": [],
            "metrics": [],
            "baselines": baselines or [],
            "findings": [],
            "best_results": [],
            "experiment_setup_summary": None,
        },
        "author_conclusion": None,
        "editor_note": {
            "summary": "editor summary",
            "points": ["editor point"],
        },
        "editorial_review": {
            "verdict": "值得浏览",
            "strengths": ["strength a"],
            "cautions": [],
            "research_position": "position a",
            "next_read_hint": "next a",
        },
        "limitations": [],
        "novelty_type": [],
        "research_tags": {
            "themes": [theme],
            "tasks": tasks,
            "methods": methods,
            "modalities": modalities,
            "representations": representations or [],
        },
        "topics": [],
        "paper_relations": [],
        "figure_table_index": {"figures": [], "tables": []},
    }


def backfilled_by_id(*records: dict[str, object]) -> dict[str, dict[str, object]]:
    result = backfill_records(list(records), include_site_paths=False)
    return {str(item["paper_id"]): item for item in result}


class PaperNeighborsTests(unittest.TestCase):
    def test_same_baseline_keyword_without_shared_task_or_io_does_not_match_comparison(self) -> None:
        detection = make_record(
            "detect",
            title="Detect Anything",
            theme="Open-World Perception",
            tasks=["Object Detection"],
            methods=["Large Multimodal Model"],
            inputs=["image", "text prompt"],
            outputs=["bounding boxes"],
            modalities=["image", "text", "multimodal"],
            baselines=["DINO"],
            ingredients=["Coordinate Tokens"],
            representations=["Bounding Box"],
        )
        generation = make_record(
            "gen3d",
            title="Generate 3D",
            theme="3D Generation",
            tasks=["Image-to-3D"],
            methods=["Diffusion Model"],
            inputs=["image prompt"],
            outputs=["mesh"],
            modalities=["image", "3D"],
            baselines=["DINO"],
            ingredients=["Structured Latents"],
            representations=["Mesh"],
        )

        papers = backfilled_by_id(detection, generation)
        self.assertEqual(papers["detect"]["paper_neighbors"]["comparison"], [])
        self.assertEqual(papers["gen3d"]["paper_neighbors"]["comparison"], [])

    def test_same_task_and_io_but_different_routes_can_fall_back_to_comparison(self) -> None:
        multimodal = make_record(
            "mllm-det",
            title="MLLM Detection",
            theme="Open-World Perception",
            tasks=["Object Detection"],
            methods=["Large Multimodal Model"],
            inputs=["image", "text prompt"],
            outputs=["bounding boxes"],
            modalities=["image", "text", "multimodal"],
            ingredients=["Coordinate Tokens"],
            representations=["Bounding Box"],
        )
        transformer = make_record(
            "anchor-det",
            title="Anchor Transformer Detection",
            theme="Open-World Perception",
            tasks=["Object Detection"],
            methods=["Anchor-free Transformer"],
            inputs=["image", "text prompt"],
            outputs=["bounding boxes"],
            modalities=["image", "text", "multimodal"],
            ingredients=["Dense Queries"],
            representations=["Bounding Box"],
        )

        papers = backfilled_by_id(multimodal, transformer)
        comparison = papers["mllm-det"]["paper_neighbors"]["comparison"]
        self.assertEqual(len(comparison), 1)
        self.assertEqual(comparison[0]["paper_id"], "anchor-det")
        self.assertEqual(comparison[0]["match_source"], "fallback_contrast")
        self.assertEqual(comparison[0]["relation_hint"], "contrast")
        self.assertIn("reason_short", comparison[0])
        self.assertIn(comparison[0]["score_level"], {"high", "medium", "low"})

    def test_same_task_with_shared_route_prefers_method_neighbors(self) -> None:
        primary = make_record(
            "primary-det",
            title="Primary Detection",
            theme="Open-World Perception",
            tasks=["Object Detection"],
            methods=["Large Multimodal Model"],
            inputs=["image", "text prompt"],
            outputs=["bounding boxes"],
            modalities=["image", "text", "multimodal"],
            ingredients=["Coordinate Tokens"],
            representations=["Bounding Box"],
        )
        peer = make_record(
            "peer-det",
            title="Peer Detection",
            theme="Open-World Perception",
            tasks=["Object Detection"],
            methods=["Large Multimodal Model"],
            inputs=["image", "text prompt"],
            outputs=["bounding boxes"],
            modalities=["image", "text", "multimodal"],
            ingredients=["Coordinate Tokens"],
            representations=["Bounding Box"],
        )

        papers = backfilled_by_id(primary, peer)
        method = papers["primary-det"]["paper_neighbors"]["method"]
        comparison = papers["primary-det"]["paper_neighbors"]["comparison"]
        self.assertEqual(len(method), 1)
        self.assertEqual(method[0]["paper_id"], "peer-det")
        self.assertEqual(method[0]["match_source"], "method_overlap")
        self.assertEqual(method[0]["relation_hint"], "same-method")
        self.assertEqual(comparison, [])

    def test_backfill_generates_retrieval_profile_for_records(self) -> None:
        legacy = make_record(
            "legacy-det",
            title="Legacy Detection",
            theme="Open-World Perception",
            tasks=["Object Detection"],
            methods=["Large Multimodal Model"],
            inputs=["image", "text prompt"],
            outputs=["bounding boxes"],
            modalities=["image", "text", "multimodal"],
            baselines=["Grounding DINO"],
            ingredients=["Coordinate Tokens"],
            representations=["Bounding Box"],
        )
        peer = make_record(
            "legacy-peer",
            title="Legacy Peer",
            theme="Open-World Perception",
            tasks=["Object Detection"],
            methods=["Anchor-free Transformer"],
            inputs=["image", "text prompt"],
            outputs=["bounding boxes"],
            modalities=["image", "text", "multimodal"],
            ingredients=["Dense Queries"],
            representations=["Bounding Box"],
        )

        papers = backfilled_by_id(legacy, peer)
        profile = papers["legacy-det"]["retrieval_profile"]
        self.assertEqual(
            set(profile.keys()),
            {
                "problem_spaces",
                "task_axes",
                "approach_axes",
                "input_axes",
                "output_axes",
                "modality_axes",
                "comparison_axes",
            },
        )
        self.assertIn("Object Detection", profile["task_axes"])
        self.assertIn("bounding boxes", profile["output_axes"])
        self.assertIn("Grounding DINO", profile["comparison_axes"])
        self.assertIsInstance(papers["legacy-det"]["comparison_context"]["comparison_aspects"], list)

    def test_backfill_adds_route_paths_when_site_paths_enabled(self) -> None:
        primary = make_record(
            "route-primary",
            title="Route Primary",
            theme="3D Generation",
            tasks=["Image-to-3D"],
            methods=["Diffusion Model"],
            inputs=["image"],
            outputs=["mesh"],
            modalities=["image", "3D"],
        )
        peer = make_record(
            "route-peer",
            title="Route Peer",
            theme="3D Generation",
            tasks=["Image-to-3D"],
            methods=["Diffusion Model"],
            inputs=["image"],
            outputs=["mesh"],
            modalities=["image", "3D"],
        )

        records = backfill_records([primary, peer], include_site_paths=True)
        record = next(item for item in records if item["paper_id"] == "route-primary")
        self.assertEqual(record["paper_path"], "papers/route-primary.md")
        self.assertEqual(record["route_path"], "#/paper/route-primary")
        self.assertEqual(record["paper_neighbors"]["method"][0]["route_path"], "#/paper/route-peer")
        self.assertIn("reason_short", record["paper_neighbors"]["method"][0])

    def test_build_site_payload_exposes_spa_metadata(self) -> None:
        primary = make_record(
            "payload-paper",
            title="Payload Paper",
            theme="3D Generation",
            tasks=["Image-to-3D"],
            methods=["Diffusion Model"],
            inputs=["image"],
            outputs=["mesh"],
            modalities=["image", "3D"],
        )

        records = backfill_records([primary], include_site_paths=True)
        payload = build_site_payload(summarize_records(records))
        self.assertEqual(payload["site_meta"]["title"], "Translate Paper Forest")
        self.assertEqual(payload["navigation"]["home_route"], "#/")
        self.assertEqual(payload["papers"][0]["route_path"], "#/paper/payload-paper")
        self.assertIn("themes", payload["filters"])
        self.assertIn("reading_digest", payload["papers"][0])
        self.assertIn("editorial_review", payload["papers"][0])
        self.assertNotIn("storyline", payload["papers"][0])
        self.assertNotIn("method_core", payload["papers"][0])


if __name__ == "__main__":
    unittest.main()
