from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from build_site_derivatives import build_site_payload  # noqa: E402


def make_record(
    paper_id: str,
    *,
    title: str,
    theme: str,
    tasks: list[str],
    methods: list[str],
    modalities: list[str],
    baselines: list[str] | None = None,
    next_read: list[str] | None = None,
    representations: list[str] | None = None,
) -> dict[str, object]:
    return {
        "id": paper_id,
        "source": {
            "conversation_ids": [f"conv-{paper_id}"],
            "paper_path": f"papers/{paper_id}.md",
            "route_path": f"#/?paper={paper_id}&detail=1",
        },
        "bibliography": {
            "title": title,
            "authors": ["Author A"],
            "year": 2025,
            "venue": "arXiv",
            "citation_count": None,
            "identifiers": {"doi": None, "arxiv": None},
            "links": {"pdf": f"https://example.com/{paper_id}.pdf", "project": None, "code": None, "data": None},
        },
        "abstracts": {"raw": "raw", "zh": "中文摘要"},
        "story": {"paper_one_liner": "test summary"},
        "research_problem": {"summary": "summary", "gaps": ["gap"], "goal": "goal"},
        "core_contributions": ["contribution"],
        "method": {
            "summary": "test method",
            "pipeline_steps": ["step 1"],
            "innovations": ["innovation"],
            "ingredients": methods,
            "inputs": ["Image"],
            "outputs": ["3D Asset"],
            "representations": representations or [],
        },
        "evaluation": {
            "headline": "headline",
            "datasets": ["Objaverse"],
            "metrics": ["F1"],
            "baselines": baselines or [],
            "key_findings": ["finding"],
            "setup_summary": "setup",
        },
        "claims": [{"text": "claim", "type": "method", "support": ["section:Abstract"], "confidence": "high"}],
        "research_risks": ["limited-eval-coverage"],
        "editorial": {"research_position": "position", "graph_worthy": True},
        "taxonomy": {
            "themes": [theme],
            "tasks": tasks,
            "methods": methods,
            "modalities": modalities,
            "novelty_types": [],
        },
        "comparison": {"aspects": [], "next_read": next_read or []},
        "discovery_axes": {
            "problem": [tasks[0].lower()] if tasks else [],
            "method": [methods[0].lower()] if methods else [],
            "evaluation": [baselines[0].lower()] if baselines else [],
            "risk": ["limited-eval-coverage"],
        },
        "relations": [],
    }


class BuildSiteDerivativesTests(unittest.TestCase):
    def test_build_site_payload_creates_filters_and_featured_cards(self) -> None:
        primary = make_record(
            "primary",
            title="Primary Paper",
            theme="3D Generation",
            tasks=["Image-to-3D"],
            methods=["Diffusion Model"],
            modalities=["Image", "3D"],
        )
        peer = make_record(
            "peer",
            title="Peer Paper",
            theme="3D Generation",
            tasks=["Image-to-3D"],
            methods=["Diffusion Model"],
            modalities=["Image", "3D"],
        )

        site_payload, detail_payloads = build_site_payload([primary, peer])
        self.assertEqual(site_payload["paper_count"], 2)
        self.assertEqual(site_payload["filters"]["themes"][0]["label"], "3D Generation")
        self.assertTrue(site_payload["featured"])
        self.assertIn("primary", detail_payloads)
        self.assertNotIn("neighbors", primary)

    def test_build_site_payload_derives_problem_and_method_neighbors(self) -> None:
        primary = make_record(
            "primary",
            title="Primary Paper",
            theme="3D Generation",
            tasks=["Image-to-3D"],
            methods=["Diffusion Model"],
            modalities=["Image", "3D"],
            representations=["Mesh"],
        )
        peer = make_record(
            "peer",
            title="Peer Paper",
            theme="3D Generation",
            tasks=["Image-to-3D"],
            methods=["Diffusion Model"],
            modalities=["Image", "3D"],
            representations=["Mesh"],
        )

        _, detail_payloads = build_site_payload([primary, peer])
        neighbors = detail_payloads["primary"]["neighbors"]
        self.assertEqual(neighbors["problem"][0]["paper_id"], "peer")
        self.assertEqual(neighbors["method"][0]["paper_id"], "peer")

    def test_build_site_payload_uses_explicit_next_read_for_evaluation_neighbors(self) -> None:
        primary = make_record(
            "primary",
            title="Primary Paper",
            theme="3D Generation",
            tasks=["Image-to-3D"],
            methods=["Diffusion Model"],
            modalities=["Image", "3D"],
            next_read=["BaselineNet"],
        )
        baseline = make_record(
            "baseline",
            title="BaselineNet",
            theme="3D Generation",
            tasks=["Image-to-3D"],
            methods=["Transformer"],
            modalities=["Image", "3D"],
        )

        _, detail_payloads = build_site_payload([primary, baseline])
        evaluation = detail_payloads["primary"]["neighbors"]["evaluation"]
        self.assertEqual(evaluation[0]["paper_id"], "baseline")
        self.assertEqual(evaluation[0]["match_source"], "explicit_target")

    def test_build_site_payload_keeps_research_position_in_cards(self) -> None:
        primary = make_record(
            "primary",
            title="Primary Paper",
            theme="3D Generation",
            tasks=["Image-to-3D"],
            methods=["Diffusion Model"],
            modalities=["Image", "3D"],
        )
        primary["editorial"]["research_position"] = "适合作为3D Reconstruction中Point Cloud Normal Estimation路线的代表样本。"  # type: ignore[index]

        site_payload, _ = build_site_payload([primary])
        card = site_payload["papers"][0]

        self.assertEqual(card["editorial"]["research_position"], "适合作为 3D Reconstruction 中 Point Cloud Normal Estimation 路线的代表样本。")


if __name__ == "__main__":
    unittest.main()
