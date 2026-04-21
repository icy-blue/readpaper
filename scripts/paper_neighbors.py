#!/usr/bin/env python3
"""Shared helpers for paper-neighbor-first paper records and site payloads."""

from __future__ import annotations

import json
import re
import unicodedata
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DISPLAY_LABELS = {
    "paper_id": "论文 ID",
    "venue": "会议 / 期刊",
    "year": "年份",
    "citation_count": "引用数",
    "translate_created_at": "收录时间",
    "pdf_url": "PDF 链接",
    "problem": "研究问题",
    "approach": "核心思路",
    "innovation": "主要创新",
    "ingredients": "关键组成",
    "representation": "表征形式",
    "supervision": "监督与约束",
    "differences": "与近邻工作的差异",
    "inputs": "输入",
    "outputs": "输出",
    "modalities": "模态",
    "datasets": "数据集",
    "metrics": "评测指标",
    "baselines": "对比方法",
    "findings": "主要发现",
    "themes": "主题",
    "tasks": "任务",
    "methods": "方法",
    "representations": "表征",
    "explicit_baselines": "显式对比方法",
    "contrast_methods": "对比方法线索",
    "contrast_notes": "对比说明",
    "matched_terms": "命中线索",
    "current_methods": "当前方法",
    "candidate_methods": "对方方法",
    "score": "相关度",
}

MATCH_SOURCE_LABELS = {
    "task_overlap": "任务相似",
    "method_overlap": "方法相似",
    "baseline_match": "显式对比",
    "contrast_method_match": "线索对比",
    "fallback_contrast": "回退对比",
    "neighbor": "近邻",
}

SUPPORT_PREFIX_LABELS = {
    "section": "章节",
    "figure": "图",
    "table": "表",
}

CONFIDENCE_LABELS = {
    "high": "高",
    "medium": "中",
    "low": "低",
}


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


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def ensure_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            cleaned = item.strip()
            if cleaned not in result:
                result.append(cleaned)
    return result


def normalize_label(value: str) -> str:
    text = unicodedata.normalize("NFKC", value or "")
    return re.sub(r"\s+", " ", text).strip()


def normalize_match_text(value: str) -> str:
    text = normalize_label(value).lower()
    text = re.sub(r"[^0-9a-z\u4e00-\u9fff]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def display_label(key: str, default: str = "") -> str:
    return DISPLAY_LABELS.get(key, default or key)


def match_source_label(value: str) -> str:
    text = normalize_label(value)
    return MATCH_SOURCE_LABELS.get(text, text or "近邻")


def format_support_label(value: str) -> str:
    text = normalize_label(value)
    prefix, sep, detail = text.partition(":")
    if not sep:
        return text
    label = SUPPORT_PREFIX_LABELS.get(prefix)
    if not label:
        return text
    return f"{label}：{detail}"


def format_support_labels(values: list[str]) -> list[str]:
    return [format_support_label(value) for value in values if normalize_label(value)]


def confidence_label(value: str) -> str:
    text = normalize_label(value).lower()
    return CONFIDENCE_LABELS.get(text, normalize_label(value))


def short_title(value: str, max_length: int = 42) -> str:
    text = normalize_label(value)
    return text if len(text) <= max_length else text[: max_length - 1] + "…"


def year_sort_value(value: Any) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return -1


def paper_sort_key(item: dict[str, Any]) -> tuple[int, str]:
    return (year_sort_value(item.get("year")), normalize_label(str(item.get("title") or "")))


def paper_paths(paper_id: str) -> dict[str, str]:
    return {
        "paper_path": f"papers/{paper_id}.md",
        "html_path": f"papers/{paper_id}.html",
    }


def load_papers(papers_dir: Path) -> list[dict[str, Any]]:
    papers: list[dict[str, Any]] = []
    if not papers_dir.exists():
        return papers
    for path in sorted(papers_dir.glob("*.json")):
        payload = read_json(path, {})
        if not isinstance(payload, dict):
            continue
        payload["_path"] = str(path)
        papers.append(payload)
    papers.sort(key=paper_sort_key, reverse=True)
    return papers


def tag_group(record: dict[str, Any], group: str) -> list[str]:
    tags = record.get("research_tags", {})
    if not isinstance(tags, dict):
        return []
    return ensure_strings(tags.get(group))


def novelty_tags(record: dict[str, Any]) -> list[str]:
    return ensure_strings(record.get("novelty_type"))


def summary_block(record: dict[str, Any]) -> dict[str, Any]:
    summary = record.get("summary", {})
    return summary if isinstance(summary, dict) else {}


def dedupe_sorted(values: list[str]) -> list[str]:
    unique: list[str] = []
    for value in values:
        label = normalize_label(value)
        if label and label not in unique:
            unique.append(label)
    return unique


def sort_lookup(values: list[str]) -> list[str]:
    return sorted(dedupe_sorted(values), key=normalize_label)


def build_signal_vocabulary(records: list[dict[str, Any]]) -> list[str]:
    vocab: list[str] = []
    for record in records:
        vocab.extend(tag_group(record, "methods"))
        vocab.extend(tag_group(record, "representations"))
        eval_block = record.get("benchmarks_or_eval")
        if isinstance(eval_block, dict):
            vocab.extend(ensure_strings(eval_block.get("baselines")))
    return sort_lookup(vocab)


def contains_term(text: str, term: str) -> bool:
    normalized_text = normalize_match_text(text)
    normalized_term = normalize_match_text(term)
    if not normalized_text or not normalized_term:
        return False
    return normalized_term in normalized_text


def derive_comparison_context(record: dict[str, Any], vocabulary: list[str]) -> dict[str, list[str]]:
    eval_block = record.get("benchmarks_or_eval")
    method_core = record.get("method_core")
    baselines = ensure_strings(eval_block.get("baselines")) if isinstance(eval_block, dict) else []
    differences = ensure_strings(method_core.get("differences")) if isinstance(method_core, dict) else []
    innovation = str(method_core.get("innovation") or "").strip() if isinstance(method_core, dict) else ""
    notes = list(differences)
    if innovation and innovation not in notes:
        notes.append(innovation)

    text_pool = "\n".join(notes)
    contrast_methods: list[str] = []
    for term in vocabulary:
        if term in baselines:
            continue
        if contains_term(text_pool, term):
            contrast_methods.append(term)

    return {
        "explicit_baselines": baselines,
        "contrast_methods": contrast_methods,
        "contrast_notes": notes,
    }


def normalized_record(
    record: dict[str, Any],
    comparison_context: dict[str, list[str]],
    paper_neighbors: dict[str, list[dict[str, Any]]],
    *,
    include_site_paths: bool,
) -> dict[str, Any]:
    method_core = record.get("method_core") if isinstance(record.get("method_core"), dict) else {}
    inputs_outputs = record.get("inputs_outputs") if isinstance(record.get("inputs_outputs"), dict) else {}
    eval_block = record.get("benchmarks_or_eval") if isinstance(record.get("benchmarks_or_eval"), dict) else {}
    translate_status = record.get("translate_status") if isinstance(record.get("translate_status"), dict) else {}
    figure_table_index = record.get("figure_table_index") if isinstance(record.get("figure_table_index"), dict) else {}
    summary = summary_block(record)

    payload = {
        "paper_id": str(record.get("paper_id") or ""),
        "source_conversation_ids": ensure_strings(record.get("source_conversation_ids")),
        "title": str(record.get("title") or record.get("paper_id") or ""),
        "year": record.get("year"),
        "venue": str(record.get("venue") or "Unknown"),
        "citation_count": record.get("citation_count") or 0,
        "pdf_url": str(record.get("pdf_url") or ""),
        "translate_created_at": str(record.get("translate_created_at") or ""),
        "translate_status": translate_status,
        "summary": {
            "one_liner": str(summary.get("one_liner") or ""),
            "abstract_summary": str(summary.get("abstract_summary") or ""),
            "research_value": str(summary.get("research_value") or ""),
            "worth_long_term_graph": bool(summary.get("worth_long_term_graph")),
        },
        "key_claims": [
            {
                "claim": str(item.get("claim") or ""),
                "support": ensure_strings(item.get("support")),
                "confidence": str(item.get("confidence") or ""),
            }
            for item in record.get("key_claims", [])
            if isinstance(item, dict)
        ],
        "method_core": {
            "problem": str(method_core.get("problem") or ""),
            "approach": str(method_core.get("approach") or ""),
            "innovation": str(method_core.get("innovation") or ""),
            "ingredients": ensure_strings(method_core.get("ingredients")),
            "representation": ensure_strings(method_core.get("representation")),
            "supervision": ensure_strings(method_core.get("supervision")),
            "differences": ensure_strings(method_core.get("differences")),
        },
        "inputs_outputs": {
            "inputs": ensure_strings(inputs_outputs.get("inputs")),
            "outputs": ensure_strings(inputs_outputs.get("outputs")),
            "modalities": ensure_strings(inputs_outputs.get("modalities")),
        },
        "benchmarks_or_eval": {
            "datasets": ensure_strings(eval_block.get("datasets")),
            "metrics": ensure_strings(eval_block.get("metrics")),
            "baselines": ensure_strings(eval_block.get("baselines")),
            "findings": ensure_strings(eval_block.get("findings")),
        },
        "limitations": ensure_strings(record.get("limitations")),
        "novelty_type": ensure_strings(record.get("novelty_type")),
        "research_tags": {
            "themes": tag_group(record, "themes"),
            "tasks": tag_group(record, "tasks"),
            "methods": tag_group(record, "methods"),
            "modalities": tag_group(record, "modalities"),
            "representations": tag_group(record, "representations"),
        },
        "comparison_context": {
            "explicit_baselines": ensure_strings(comparison_context.get("explicit_baselines")),
            "contrast_methods": ensure_strings(comparison_context.get("contrast_methods")),
            "contrast_notes": ensure_strings(comparison_context.get("contrast_notes")),
        },
        "paper_neighbors": {
            "task": paper_neighbors.get("task", []),
            "method": paper_neighbors.get("method", []),
            "comparison": paper_neighbors.get("comparison", []),
        },
        "figure_table_index": figure_table_index,
    }

    if include_site_paths:
        payload.update(paper_paths(payload["paper_id"]))
    return payload


def shared_values(left: list[str], right: list[str]) -> list[str]:
    return sorted(set(left) & set(right), key=normalize_label)


def reason_from_parts(parts: list[str], fallback: str) -> str:
    return "，".join(parts) if parts else fallback


def task_neighbor_reason(shared_tasks: list[str], shared_themes: list[str], shared_modalities: list[str]) -> str:
    parts: list[str] = []
    if shared_tasks:
        parts.append("同属 " + " / ".join(shared_tasks))
    if shared_themes:
        parts.append("主题接近：" + " / ".join(shared_themes))
    if shared_modalities:
        parts.append("输入模态接近：" + " / ".join(shared_modalities))
    return reason_from_parts(parts, "任务定义接近。")


def method_neighbor_reason(
    shared_methods: list[str],
    shared_representations: list[str],
    shared_novelty: list[str],
) -> str:
    parts: list[str] = []
    if shared_methods:
        parts.append("共享方法族：" + " / ".join(shared_methods))
    if shared_representations:
        parts.append("共享表征：" + " / ".join(shared_representations))
    if shared_novelty:
        parts.append("创新点相近：" + " / ".join(shared_novelty))
    return reason_from_parts(parts, "技术路线接近。")


def comparison_reason(
    matched_terms: list[str],
    shared_tasks: list[str],
    source_label: str,
    current_methods: list[str],
    candidate_methods: list[str],
) -> str:
    parts: list[str] = []
    if matched_terms:
        parts.append(f"{source_label}命中：" + " / ".join(matched_terms))
    if shared_tasks:
        parts.append("同任务：" + " / ".join(shared_tasks))
    if current_methods and candidate_methods and set(current_methods) != set(candidate_methods):
        parts.append("方法侧重点不同")
    return reason_from_parts(parts, "适合作为对比阅读对象。")


def build_tag_filters(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, dict[str, list[str]]] = {
        "themes": defaultdict(list),
        "tasks": defaultdict(list),
        "methods": defaultdict(list),
    }
    for record in records:
        paper_id = str(record.get("paper_id") or "")
        if not paper_id:
            continue
        for group_name in groups:
            for label in tag_group(record, group_name):
                bucket = groups[group_name][label]
                if paper_id not in bucket:
                    bucket.append(paper_id)
    result: dict[str, list[dict[str, Any]]] = {}
    for group_name, mapping in groups.items():
        result[group_name] = sorted(
            (
                {
                    "label": label,
                    "count": len(paper_ids),
                    "paper_ids": paper_ids,
                }
                for label, paper_ids in mapping.items()
            ),
            key=lambda item: (-int(item["count"]), normalize_label(str(item["label"]))),
        )
    return result


def candidate_sort_title(record: dict[str, Any]) -> str:
    return normalize_label(str(record.get("title") or record.get("paper_id") or ""))


def build_candidate_index(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for record in records:
        paper_id = str(record.get("paper_id") or "")
        if paper_id:
            index[paper_id] = record
    return index


def paper_signal_lookup(record: dict[str, Any], comparison_context: dict[str, list[str]]) -> list[str]:
    return sort_lookup(
        [
            str(record.get("title") or ""),
            *tag_group(record, "methods"),
            *tag_group(record, "representations"),
            *ensure_strings(comparison_context.get("explicit_baselines")),
        ]
    )


def match_terms_against_paper(
    terms: list[str],
    candidate: dict[str, Any],
    candidate_context: dict[str, list[str]],
) -> list[str]:
    matched: list[str] = []
    title_norm = normalize_match_text(str(candidate.get("title") or ""))
    signal_norms = [normalize_match_text(value) for value in paper_signal_lookup(candidate, candidate_context)]
    for term in terms:
        normalized_term = normalize_match_text(term)
        if not normalized_term:
            continue
        if normalized_term in title_norm or any(
            normalized_term == signal or normalized_term in signal or signal in normalized_term
            for signal in signal_norms
            if signal
        ):
            if term not in matched:
                matched.append(term)
    return matched


def build_task_neighbors(record: dict[str, Any], candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[tuple[tuple[int, int, int, str], dict[str, Any]]] = []
    left_tasks = tag_group(record, "tasks")
    left_themes = tag_group(record, "themes")
    left_modalities = tag_group(record, "modalities")
    for candidate in candidates:
        shared_tasks = shared_values(left_tasks, tag_group(candidate, "tasks"))
        if not shared_tasks:
            continue
        shared_themes = shared_values(left_themes, tag_group(candidate, "themes"))
        shared_modalities = shared_values(left_modalities, tag_group(candidate, "modalities"))
        item = {
            "paper_id": str(candidate.get("paper_id") or ""),
            "title": str(candidate.get("title") or candidate.get("paper_id") or ""),
            "score": len(shared_tasks) * 100 + len(shared_themes) * 10 + len(shared_modalities),
            "match_source": "task_overlap",
            "shared_signals": {
                "tasks": shared_tasks,
                "themes": shared_themes,
                "modalities": shared_modalities,
            },
            "reason": task_neighbor_reason(shared_tasks, shared_themes, shared_modalities),
            **paper_paths(str(candidate.get("paper_id") or "")),
        }
        sort_key = (
            -len(shared_tasks),
            -len(shared_themes),
            -len(shared_modalities),
            candidate_sort_title(candidate),
        )
        items.append((sort_key, item))
    items.sort(key=lambda pair: pair[0])
    return [item for _, item in items[:3]]


def build_method_neighbors(record: dict[str, Any], candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[tuple[tuple[int, int, int, str], dict[str, Any]]] = []
    left_methods = tag_group(record, "methods")
    left_representations = tag_group(record, "representations")
    left_novelty = novelty_tags(record)
    for candidate in candidates:
        shared_methods = shared_values(left_methods, tag_group(candidate, "methods"))
        shared_representations = shared_values(left_representations, tag_group(candidate, "representations"))
        if not shared_methods and not shared_representations:
            continue
        shared_novelty = shared_values(left_novelty, novelty_tags(candidate))
        item = {
            "paper_id": str(candidate.get("paper_id") or ""),
            "title": str(candidate.get("title") or candidate.get("paper_id") or ""),
            "score": len(shared_methods) * 100 + len(shared_representations) * 10 + len(shared_novelty),
            "match_source": "method_overlap",
            "shared_signals": {
                "methods": shared_methods,
                "representations": shared_representations,
                "novelty_type": shared_novelty,
            },
            "reason": method_neighbor_reason(shared_methods, shared_representations, shared_novelty),
            **paper_paths(str(candidate.get("paper_id") or "")),
        }
        sort_key = (
            -len(shared_methods),
            -len(shared_representations),
            -len(shared_novelty),
            candidate_sort_title(candidate),
        )
        items.append((sort_key, item))
    items.sort(key=lambda pair: pair[0])
    return [item for _, item in items[:3]]


def build_comparison_neighbors(
    record: dict[str, Any],
    candidates: list[dict[str, Any]],
    comparison_context: dict[str, list[str]],
    context_lookup: dict[str, dict[str, list[str]]],
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    left_tasks = tag_group(record, "tasks")
    left_methods = tag_group(record, "methods")
    left_modalities = tag_group(record, "modalities")

    def append_candidates(
        terms: list[str],
        source_name: str,
        source_label: str,
        *,
        require_match: bool,
    ) -> None:
        ranked: list[tuple[tuple[int, int, int, str], dict[str, Any]]] = []
        for candidate in candidates:
            candidate_id = str(candidate.get("paper_id") or "")
            if not candidate_id or candidate_id in selected_ids:
                continue
            candidate_context = context_lookup.get(candidate_id, {})
            matched_terms = match_terms_against_paper(terms, candidate, candidate_context)
            if require_match and not matched_terms:
                continue
            shared_tasks = shared_values(left_tasks, tag_group(candidate, "tasks"))
            shared_methods = shared_values(left_methods, tag_group(candidate, "methods"))
            shared_modalities = shared_values(left_modalities, tag_group(candidate, "modalities"))
            if require_match or matched_terms:
                item = {
                    "paper_id": candidate_id,
                    "title": str(candidate.get("title") or candidate_id),
                    "score": len(matched_terms) * 100 + len(shared_tasks) * 10 + len(shared_methods),
                    "match_source": source_name,
                    "shared_signals": {
                        "matched_terms": matched_terms,
                        "tasks": shared_tasks,
                        "methods": shared_methods,
                        "modalities": shared_modalities,
                    },
                    "reason": comparison_reason(
                        matched_terms,
                        shared_tasks,
                        source_label,
                        left_methods,
                        tag_group(candidate, "methods"),
                    ),
                    **paper_paths(candidate_id),
                }
                sort_key = (
                    -len(matched_terms),
                    -len(shared_tasks),
                    -len(shared_methods),
                    candidate_sort_title(candidate),
                )
                ranked.append((sort_key, item))
        ranked.sort(key=lambda pair: pair[0])
        for _, item in ranked:
            if len(selected) >= 3:
                return
            selected.append(item)
            selected_ids.add(str(item["paper_id"]))

    append_candidates(
        ensure_strings(comparison_context.get("explicit_baselines")),
        "baseline_match",
        "显式对比方法",
        require_match=True,
    )
    if len(selected) < 3:
        append_candidates(
            ensure_strings(comparison_context.get("contrast_methods")),
            "contrast_method_match",
            "对比方法线索",
            require_match=True,
        )

    if len(selected) < 3:
        ranked_fallback: list[tuple[tuple[int, int, int, str], dict[str, Any]]] = []
        for candidate in candidates:
            candidate_id = str(candidate.get("paper_id") or "")
            if not candidate_id or candidate_id in selected_ids:
                continue
            shared_tasks = shared_values(left_tasks, tag_group(candidate, "tasks"))
            shared_themes = shared_values(tag_group(record, "themes"), tag_group(candidate, "themes"))
            shared_modalities = shared_values(left_modalities, tag_group(candidate, "modalities"))
            candidate_methods = tag_group(candidate, "methods")
            if not shared_tasks:
                continue
            if set(left_methods) & set(candidate_methods):
                continue
            item = {
                "paper_id": candidate_id,
                "title": str(candidate.get("title") or candidate_id),
                "score": len(shared_tasks) * 100 + len(shared_themes) * 10 + len(shared_modalities),
                "match_source": "fallback_contrast",
                "shared_signals": {
                    "tasks": shared_tasks,
                    "themes": shared_themes,
                    "modalities": shared_modalities,
                    "current_methods": left_methods,
                    "candidate_methods": candidate_methods,
                },
                "reason": comparison_reason(
                    [],
                    shared_tasks,
                    "fallback",
                    left_methods,
                    candidate_methods,
                ),
                **paper_paths(candidate_id),
            }
            sort_key = (
                -len(shared_tasks),
                -len(shared_themes),
                -len(shared_modalities),
                candidate_sort_title(candidate),
            )
            ranked_fallback.append((sort_key, item))
        ranked_fallback.sort(key=lambda pair: pair[0])
        for _, item in ranked_fallback:
            if len(selected) >= 3:
                break
            selected.append(item)
            selected_ids.add(str(item["paper_id"]))

    return selected


def backfill_records(records: list[dict[str, Any]], *, include_site_paths: bool) -> list[dict[str, Any]]:
    vocabulary = build_signal_vocabulary(records)
    comparison_lookup = {
        str(record.get("paper_id") or ""): derive_comparison_context(record, vocabulary)
        for record in records
        if str(record.get("paper_id") or "")
    }
    neighbor_lookup: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for record in records:
        paper_id = str(record.get("paper_id") or "")
        if not paper_id:
            continue
        candidates = [
            candidate
            for candidate in records
            if str(candidate.get("paper_id") or "") and str(candidate.get("paper_id") or "") != paper_id
        ]
        comparison_context = comparison_lookup.get(paper_id, {})
        neighbor_lookup[paper_id] = {
            "task": build_task_neighbors(record, candidates),
            "method": build_method_neighbors(record, candidates),
            "comparison": build_comparison_neighbors(record, candidates, comparison_context, comparison_lookup),
        }

    normalized: list[dict[str, Any]] = []
    for record in records:
        paper_id = str(record.get("paper_id") or "")
        if not paper_id:
            continue
        normalized.append(
            normalized_record(
                record,
                comparison_lookup.get(paper_id, {}),
                neighbor_lookup.get(paper_id, {"task": [], "method": [], "comparison": []}),
                include_site_paths=include_site_paths,
            )
        )
    normalized.sort(key=paper_sort_key, reverse=True)
    return normalized


def build_site_payload(records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "generated_at": utc_now(),
        "paper_count": len(records),
        "papers": records,
        "tag_filters": build_tag_filters(records),
        "recent_titles": [str(item.get("title") or "") for item in records[:8]],
    }
