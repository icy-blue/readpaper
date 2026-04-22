#!/usr/bin/env python3
"""Build site-derived payloads from canonical paper records."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from display_text import normalize_display_text


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def ensure_display_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            cleaned = normalize_display_text(item)
            if cleaned and cleaned not in result:
                result.append(cleaned)
    return result


def ensure_machine_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            cleaned = normalize_label(item)
            if cleaned and cleaned not in result:
                result.append(cleaned)
    return result


def ensure_strings(value: Any) -> list[str]:
    return ensure_display_strings(value)


def normalize_label(value: str) -> str:
    text = unicodedata.normalize("NFKC", value or "")
    return re.sub(r"\s+", " ", text).strip()


def normalize_key(value: str) -> str:
    text = normalize_label(value).lower()
    text = re.sub(r"[^0-9a-z\u4e00-\u9fff]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def year_sort_value(value: Any) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return -1


def paper_sort_key(item: dict[str, Any]) -> tuple[int, str]:
    bibliography = item.get("bibliography") if isinstance(item.get("bibliography"), dict) else {}
    title = normalize_label(str(bibliography.get("title") or item.get("id") or ""))
    return (year_sort_value(bibliography.get("year")), title)


def load_papers(papers_dir: Path) -> list[dict[str, Any]]:
    papers: list[dict[str, Any]] = []
    if not papers_dir.exists():
        return papers
    for path in sorted(papers_dir.glob("*.json")):
        payload = read_json(path, {})
        if not isinstance(payload, dict):
            continue
        papers.append(payload)
    papers.sort(key=paper_sort_key, reverse=True)
    return papers


def tag_group(record: dict[str, Any], group: str) -> list[str]:
    taxonomy = record.get("taxonomy")
    if not isinstance(taxonomy, dict):
        return []
    return ensure_machine_strings(taxonomy.get(group))


def source_block(record: dict[str, Any]) -> dict[str, Any]:
    source = record.get("source")
    if not isinstance(source, dict):
        return {"conversation_ids": [], "paper_path": "", "route_path": ""}
    return {
        "conversation_ids": ensure_machine_strings(source.get("conversation_ids")),
        "paper_path": str(source.get("paper_path") or ""),
        "route_path": str(source.get("route_path") or ""),
    }


def bibliography_block(record: dict[str, Any]) -> dict[str, Any]:
    bibliography = record.get("bibliography")
    if not isinstance(bibliography, dict):
        return {
            "title": str(record.get("id") or ""),
            "authors": [],
            "year": None,
            "venue": "",
            "citation_count": None,
            "identifiers": {"doi": None, "arxiv": None},
            "links": {"pdf": None, "project": None, "code": None, "data": None},
        }
    identifiers = bibliography.get("identifiers") if isinstance(bibliography.get("identifiers"), dict) else {}
    links = bibliography.get("links") if isinstance(bibliography.get("links"), dict) else {}
    return {
        "title": str(bibliography.get("title") or record.get("id") or ""),
        "authors": ensure_machine_strings(bibliography.get("authors")),
        "year": bibliography.get("year"),
        "venue": str(bibliography.get("venue") or ""),
        "citation_count": bibliography.get("citation_count"),
        "identifiers": {
            "doi": str(identifiers.get("doi") or "") or None,
            "arxiv": str(identifiers.get("arxiv") or "") or None,
        },
        "links": {
            "pdf": str(links.get("pdf") or "") or None,
            "project": str(links.get("project") or "") or None,
            "code": str(links.get("code") or "") or None,
            "data": str(links.get("data") or "") or None,
        },
    }


def card_view(record: dict[str, Any]) -> dict[str, Any]:
    story = record.get("story") if isinstance(record.get("story"), dict) else {}
    editorial = record.get("editorial") if isinstance(record.get("editorial"), dict) else {}
    return {
        "id": str(record.get("id") or ""),
        "source": source_block(record),
        "bibliography": bibliography_block(record),
        "story": {
            "paper_one_liner": normalize_display_text(str(story.get("paper_one_liner") or "")) or None,
            "problem": normalize_display_text(str(story.get("problem") or "")) or None,
            "method": normalize_display_text(str(story.get("method") or "")) or None,
            "result": normalize_display_text(str(story.get("result") or "")) or None,
        },
        "editorial": {
            "verdict": str(editorial.get("verdict") or "") or None,
            "summary": normalize_display_text(str(editorial.get("summary") or "")) or None,
            "why_read": ensure_display_strings(editorial.get("why_read")),
            "strengths": ensure_display_strings(editorial.get("strengths")),
            "cautions": ensure_display_strings(editorial.get("cautions")),
            "reading_route": str(editorial.get("reading_route") or "overview"),
            "research_position": normalize_display_text(str(editorial.get("research_position") or "")) or None,
            "graph_worthy": bool(editorial.get("graph_worthy")),
            "next_read": ensure_display_strings(editorial.get("next_read")),
        },
        "taxonomy": {
            "themes": tag_group(record, "themes"),
            "tasks": tag_group(record, "tasks"),
            "methods": tag_group(record, "methods"),
            "modalities": tag_group(record, "modalities"),
            "representations": tag_group(record, "representations"),
            "novelty_types": tag_group(record, "novelty_types"),
        },
    }


def matches_named_target(candidate: dict[str, Any], targets: list[str]) -> list[str]:
    bibliography = bibliography_block(candidate)
    candidate_id = normalize_key(str(candidate.get("id") or ""))
    title = normalize_key(str(bibliography.get("title") or ""))
    matched: list[str] = []
    for target in targets:
        normalized = normalize_key(target)
        if not normalized:
            continue
        if normalized == candidate_id or normalized == title or normalized in title:
            if target not in matched:
                matched.append(target)
    return matched


def score_level(score: int) -> str:
    if score >= 10:
        return "high"
    if score >= 6:
        return "medium"
    return "low"


def neighbor_item(
    candidate: dict[str, Any],
    *,
    score: int,
    match_source: str,
    reason: str,
    reason_short: str,
    shared_signals: dict[str, list[str]],
    relation_hint: str,
) -> dict[str, Any]:
    bibliography = bibliography_block(candidate)
    source = source_block(candidate)
    return {
        "paper_id": str(candidate.get("id") or ""),
        "title": str(bibliography.get("title") or candidate.get("id") or ""),
        "score": score,
        "score_level": score_level(score),
        "match_source": match_source,
        "reason": reason,
        "reason_short": reason_short,
        "relation_hint": relation_hint,
        "paper_path": str(source.get("paper_path") or ""),
        "route_path": str(source.get("route_path") or ""),
        "shared_signals": shared_signals,
    }


def sort_neighbors(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(items, key=lambda item: (-int(item.get("score") or 0), normalize_label(str(item.get("title") or ""))))[:3]


def compute_neighbors_for(record: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    current_tasks = set(tag_group(record, "tasks"))
    current_methods = set(tag_group(record, "methods"))
    current_themes = set(tag_group(record, "themes"))
    current_modalities = set(tag_group(record, "modalities"))
    current_representations = set(tag_group(record, "representations"))
    evaluation = record.get("evaluation") if isinstance(record.get("evaluation"), dict) else {}
    comparison = record.get("comparison") if isinstance(record.get("comparison"), dict) else {}
    editorial = record.get("editorial") if isinstance(record.get("editorial"), dict) else {}

    named_targets = (
        ensure_machine_strings(comparison.get("next_read"))
        + ensure_machine_strings(editorial.get("next_read"))
        + ensure_machine_strings(evaluation.get("baselines"))
    )

    task_neighbors: list[dict[str, Any]] = []
    method_neighbors: list[dict[str, Any]] = []
    comparison_neighbors: list[dict[str, Any]] = []

    for candidate in records:
        if str(candidate.get("id") or "") == str(record.get("id") or ""):
            continue

        shared_tasks = sorted(current_tasks & set(tag_group(candidate, "tasks")))
        shared_methods = sorted(current_methods & set(tag_group(candidate, "methods")))
        shared_themes = sorted(current_themes & set(tag_group(candidate, "themes")))
        shared_modalities = sorted(current_modalities & set(tag_group(candidate, "modalities")))
        shared_representations = sorted(current_representations & set(tag_group(candidate, "representations")))

        if shared_tasks:
            score = len(shared_tasks) * 6 + len(shared_themes) * 2 + len(shared_modalities) + len(shared_representations)
            task_neighbors.append(
                neighbor_item(
                    candidate,
                    score=score,
                    match_source="task_overlap",
                    reason=f"共享任务 {' / '.join(shared_tasks[:2])}，问题空间与输入输出语境接近。",
                    reason_short=f"同任务：{' / '.join(shared_tasks[:2])}",
                    shared_signals={"tasks": shared_tasks, "themes": shared_themes, "modalities": shared_modalities},
                    relation_hint="same-task",
                )
            )

        if shared_methods or shared_representations:
            score = len(shared_methods) * 6 + len(shared_representations) * 3 + len(shared_tasks) * 2 + len(shared_themes)
            method_neighbors.append(
                neighbor_item(
                    candidate,
                    score=score,
                    match_source="method_overlap",
                    reason="技术路线或表示形式重合，适合做方法侧对照。",
                    reason_short="同方法路线",
                    shared_signals={
                        "methods": shared_methods,
                        "representations": shared_representations,
                        "tasks": shared_tasks,
                    },
                    relation_hint="same-method",
                )
            )

        matched_targets = matches_named_target(candidate, named_targets)
        candidate_methods = set(tag_group(candidate, "methods"))
        if matched_targets:
            score = 12 + len(matched_targets) * 2 + len(shared_tasks)
            comparison_neighbors.append(
                neighbor_item(
                    candidate,
                    score=score,
                    match_source="explicit_target",
                    reason=f"命中显式下一篇/基线线索：{' / '.join(matched_targets[:2])}。",
                    reason_short=f"显式对照：{' / '.join(matched_targets[:1])}",
                    shared_signals={"targets": matched_targets, "tasks": shared_tasks},
                    relation_hint="contrast",
                )
            )
        elif shared_tasks and current_methods and candidate_methods and current_methods != candidate_methods:
            score = 6 + len(shared_tasks) * 2 + len(shared_modalities)
            comparison_neighbors.append(
                neighbor_item(
                    candidate,
                    score=score,
                    match_source="route_contrast",
                    reason="共享任务但采用不同方法路线，适合做对比阅读。",
                    reason_short="同任务不同路线",
                    shared_signals={"tasks": shared_tasks, "methods": sorted(candidate_methods)},
                    relation_hint="contrast",
                )
            )

    return {
        "task": sort_neighbors(task_neighbors),
        "method": sort_neighbors(method_neighbors),
        "comparison": sort_neighbors(comparison_neighbors),
    }


def build_filter_items(records: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    buckets: dict[str, list[str]] = {}
    for record in records:
        paper_id = str(record.get("id") or "")
        for label in tag_group(record, key):
            buckets.setdefault(label, [])
            if paper_id and paper_id not in buckets[label]:
                buckets[label].append(paper_id)
    items = [
        {"label": label, "count": len(paper_ids), "paper_ids": sorted(paper_ids)}
        for label, paper_ids in buckets.items()
    ]
    items.sort(key=lambda item: (-int(item["count"]), normalize_label(str(item["label"]))))
    return items


def build_site_payload(records: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    cards = [card_view(record) for record in records]
    neighbors = {str(record.get("id") or ""): compute_neighbors_for(record, records) for record in records}
    detail_payloads = {
        str(record.get("id") or ""): {
            "canonical": record,
            "neighbors": neighbors.get(str(record.get("id") or ""), {"task": [], "method": [], "comparison": []}),
        }
        for record in records
    }

    featured = [
        card
        for card in cards
        if bool(card.get("editorial", {}).get("graph_worthy")) or card.get("editorial", {}).get("verdict") == "值得精读"
    ][:3]
    recent_titles = [str(card.get("bibliography", {}).get("title") or "") for card in cards[:6]]

    site_payload = {
        "generated_at": utc_now(),
        "paper_count": len(cards),
        "site_meta": {
            "title": "Translate Paper Forest",
            "generated_at": utc_now(),
            "paper_count": len(cards),
        },
        "navigation": {
            "home_route": "#/",
            "neighbor_tabs": [
                {"key": "task", "label": "任务近邻"},
                {"key": "method", "label": "方法近邻"},
                {"key": "comparison", "label": "对比近邻"},
            ],
            "filter_groups": [
                {"key": "themes", "label": "主题"},
                {"key": "tasks", "label": "任务"},
                {"key": "methods", "label": "方法"},
            ],
        },
        "filters": {
            "themes": build_filter_items(records, "themes"),
            "tasks": build_filter_items(records, "tasks"),
            "methods": build_filter_items(records, "methods"),
        },
        "featured": featured,
        "papers": cards,
        "recent_titles": recent_titles,
    }
    return site_payload, detail_payloads


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build site-derived JSON payloads from canonical papers.")
    parser.add_argument("--papers-dir", required=True, help="Directory containing canonical paper JSON files.")
    parser.add_argument("--site-dir", required=True, help="Directory to write derived site payloads.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    papers_dir = Path(args.papers_dir)
    site_dir = Path(args.site_dir)
    site_dir.mkdir(parents=True, exist_ok=True)
    (site_dir / "papers").mkdir(parents=True, exist_ok=True)

    records = load_papers(papers_dir)
    site_payload, detail_payloads = build_site_payload(records)
    write_json(site_dir / "site-index.json", site_payload)
    for paper_id, payload in detail_payloads.items():
        write_json(site_dir / "papers" / f"{paper_id}.json", payload)

    print(f"Built site derivatives for {len(records)} papers into {site_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
