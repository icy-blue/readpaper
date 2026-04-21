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
    "authors": "作者",
    "venue": "会议 / 期刊",
    "year": "年份",
    "citation_count": "引用数",
    "translate_created_at": "收录时间",
    "links": "链接",
    "pdf": "PDF 链接",
    "doi": "DOI",
    "arxiv": "arXiv",
    "project": "Project",
    "code": "Code",
    "data": "Data",
    "abstract_raw": "英文摘要",
    "abstract_zh": "中文摘要",
    "research_problem": "研究问题",
    "core_contributions": "核心贡献",
    "author_conclusion": "作者结论",
    "editor_note": "编者按",
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
    "experiment_setup_summary": "实验设置摘要",
    "themes": "主题",
    "tasks": "任务",
    "methods": "方法",
    "representations": "表征",
    "problem_spaces": "问题空间",
    "task_axes": "任务画像",
    "approach_axes": "技术路线",
    "input_axes": "输入画像",
    "output_axes": "输出画像",
    "modality_axes": "模态画像",
    "comparison_axes": "对比线索",
    "explicit_baselines": "显式对比方法",
    "contrast_methods": "对比方法线索",
    "contrast_notes": "对比说明",
    "matched_terms": "命中线索",
    "current_methods": "当前方法",
    "candidate_methods": "对方方法",
    "current_approach_axes": "当前路线",
    "candidate_approach_axes": "对方路线",
    "relation_hint": "关系提示",
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

RELATION_HINT_LABELS = {
    "task_overlap": "同任务代表方法",
    "method_overlap": "同路线近邻",
    "baseline_match": "显式对比对象",
    "contrast_method_match": "路线对比对象",
    "fallback_contrast": "同任务差异路线",
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

CURATION_LIMITATION_PREFIXES = (
    "当前记录",
    "当前摘要",
    "当前结论",
)


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


def is_curation_limitation(value: str) -> bool:
    text = normalize_label(value)
    return any(text.startswith(prefix) for prefix in CURATION_LIMITATION_PREFIXES)


def paper_limitations(value: Any) -> list[str]:
    return [item for item in ensure_strings(value) if not is_curation_limitation(item)]


def coverage_notes(record: dict[str, Any]) -> list[str]:
    translate_status = record.get("translate_status") if isinstance(record.get("translate_status"), dict) else {}
    notes = ensure_strings(translate_status.get("coverage_notes"))
    for item in ensure_strings(record.get("limitations")):
        if is_curation_limitation(item) and item not in notes:
            notes.append(item)
    return notes


def normalize_match_text(value: str) -> str:
    text = normalize_label(value).lower()
    text = re.sub(r"[^0-9a-z\u4e00-\u9fff]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def display_label(key: str, default: str = "") -> str:
    return DISPLAY_LABELS.get(key, default or key)


def match_source_label(value: str) -> str:
    text = normalize_label(value)
    return MATCH_SOURCE_LABELS.get(text, text or "近邻")


def relation_hint(value: str) -> str | None:
    text = normalize_label(value)
    return RELATION_HINT_LABELS.get(text)


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
        "route_path": f"#/paper/{paper_id}",
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


def merge_string_lists(*groups: Any, max_items: int | None = None) -> list[str]:
    merged: list[str] = []
    for group in groups:
        for item in ensure_strings(group):
            if item not in merged:
                merged.append(item)
                if max_items is not None and len(merged) >= max_items:
                    return merged
    return merged


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


def derive_problem_spaces(record: dict[str, Any]) -> list[str]:
    themes = tag_group(record, "themes")
    tasks = tag_group(record, "tasks")
    inputs_outputs = record.get("inputs_outputs") if isinstance(record.get("inputs_outputs"), dict) else {}
    outputs = ensure_strings(inputs_outputs.get("outputs"))
    return merge_string_lists(themes, tasks, outputs, max_items=3)


def build_retrieval_profile(
    record: dict[str, Any],
    comparison_context: dict[str, list[str]],
) -> dict[str, list[str]]:
    method_core = record.get("method_core") if isinstance(record.get("method_core"), dict) else {}
    inputs_outputs = record.get("inputs_outputs") if isinstance(record.get("inputs_outputs"), dict) else {}
    existing = record.get("retrieval_profile") if isinstance(record.get("retrieval_profile"), dict) else {}
    derived = {
        "problem_spaces": derive_problem_spaces(record),
        "task_axes": tag_group(record, "tasks"),
        "approach_axes": merge_string_lists(
            tag_group(record, "methods"),
            ensure_strings(method_core.get("ingredients")),
            ensure_strings(method_core.get("representation")),
            tag_group(record, "representations"),
        ),
        "input_axes": ensure_strings(inputs_outputs.get("inputs")),
        "output_axes": ensure_strings(inputs_outputs.get("outputs")),
        "modality_axes": merge_string_lists(inputs_outputs.get("modalities"), tag_group(record, "modalities")),
        "comparison_axes": merge_string_lists(
            ensure_strings(comparison_context.get("explicit_baselines")),
            ensure_strings(comparison_context.get("contrast_methods")),
        ),
    }
    return {
        "problem_spaces": merge_string_lists(existing.get("problem_spaces"), derived["problem_spaces"], max_items=3),
        "task_axes": merge_string_lists(existing.get("task_axes"), derived["task_axes"]),
        "approach_axes": merge_string_lists(existing.get("approach_axes"), derived["approach_axes"]),
        "input_axes": merge_string_lists(existing.get("input_axes"), derived["input_axes"]),
        "output_axes": merge_string_lists(existing.get("output_axes"), derived["output_axes"]),
        "modality_axes": merge_string_lists(existing.get("modality_axes"), derived["modality_axes"]),
        "comparison_axes": merge_string_lists(existing.get("comparison_axes"), derived["comparison_axes"]),
    }


def build_route_core(record: dict[str, Any]) -> list[str]:
    method_core = record.get("method_core") if isinstance(record.get("method_core"), dict) else {}
    return merge_string_lists(
        tag_group(record, "methods"),
        ensure_strings(method_core.get("ingredients")),
    )


def normalized_record(
    record: dict[str, Any],
    comparison_context: dict[str, list[str]],
    retrieval_profile: dict[str, list[str]],
    paper_neighbors: dict[str, list[dict[str, Any]]],
    *,
    include_site_paths: bool,
) -> dict[str, Any]:
    method_core = record.get("method_core") if isinstance(record.get("method_core"), dict) else {}
    inputs_outputs = record.get("inputs_outputs") if isinstance(record.get("inputs_outputs"), dict) else {}
    eval_block = record.get("benchmarks_or_eval") if isinstance(record.get("benchmarks_or_eval"), dict) else {}
    translate_status = record.get("translate_status") if isinstance(record.get("translate_status"), dict) else {}
    figure_table_index = record.get("figure_table_index") if isinstance(record.get("figure_table_index"), dict) else {}
    links = record.get("links") if isinstance(record.get("links"), dict) else {}
    summary = summary_block(record)
    translate_status_payload = dict(translate_status)
    note_values = coverage_notes(record)
    if note_values:
        translate_status_payload["coverage_notes"] = note_values

    payload = {
        "paper_id": str(record.get("paper_id") or ""),
        "source_conversation_ids": ensure_strings(record.get("source_conversation_ids")),
        "title": str(record.get("title") or record.get("paper_id") or ""),
        "authors": ensure_strings(record.get("authors")),
        "year": record.get("year"),
        "venue": str(record.get("venue") or "Unknown"),
        "citation_count": record.get("citation_count"),
        "links": {
            "pdf": str(links.get("pdf") or "") or None,
            "doi": str(links.get("doi") or "") or None,
            "arxiv": str(links.get("arxiv") or "") or None,
            "project": str(links.get("project") or "") or None,
            "code": str(links.get("code") or "") or None,
            "data": str(links.get("data") or "") or None,
        },
        "translate_created_at": str(record.get("translate_created_at") or ""),
        "translate_status": translate_status_payload,
        "abstract_raw": str(record.get("abstract_raw") or "") or None,
        "abstract_zh": str(record.get("abstract_zh") or "") or None,
        "summary": {
            "one_liner": str(summary.get("one_liner") or ""),
            "abstract_summary": str(summary.get("abstract_summary") or ""),
            "research_value": str(summary.get("research_value") or "") or None,
            "worth_long_term_graph": bool(summary.get("worth_long_term_graph")),
        },
        "research_problem": str(record.get("research_problem") or "") or None,
        "core_contributions": ensure_strings(record.get("core_contributions")),
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
            "approach": str(method_core.get("approach") or "") or None,
            "innovation": str(method_core.get("innovation") or "") or None,
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
            "experiment_setup_summary": str(eval_block.get("experiment_setup_summary") or "") or None,
        },
        "author_conclusion": str(record.get("author_conclusion") or "") or None,
        "editor_note": str(record.get("editor_note") or "") or None,
        "limitations": paper_limitations(record.get("limitations")),
        "novelty_type": ensure_strings(record.get("novelty_type")),
        "research_tags": {
            "themes": tag_group(record, "themes"),
            "tasks": tag_group(record, "tasks"),
            "methods": tag_group(record, "methods"),
            "modalities": tag_group(record, "modalities"),
            "representations": tag_group(record, "representations"),
        },
        "retrieval_profile": {
            "problem_spaces": ensure_strings(retrieval_profile.get("problem_spaces")),
            "task_axes": ensure_strings(retrieval_profile.get("task_axes")),
            "approach_axes": ensure_strings(retrieval_profile.get("approach_axes")),
            "input_axes": ensure_strings(retrieval_profile.get("input_axes")),
            "output_axes": ensure_strings(retrieval_profile.get("output_axes")),
            "modality_axes": ensure_strings(retrieval_profile.get("modality_axes")),
            "comparison_axes": ensure_strings(retrieval_profile.get("comparison_axes")),
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
        "topics": [item for item in record.get("topics", []) if isinstance(item, dict)],
        "paper_relations": [item for item in record.get("paper_relations", []) if isinstance(item, dict)],
        "figure_table_index": figure_table_index,
    }

    if include_site_paths:
        payload.update(paper_paths(payload["paper_id"]))
    return payload


def shared_values(left: list[str], right: list[str]) -> list[str]:
    return sorted(set(left) & set(right), key=normalize_label)


def reason_from_parts(parts: list[str], fallback: str) -> str:
    return "，".join(parts) if parts else fallback


def profile_values(profile: dict[str, list[str]], key: str) -> list[str]:
    return ensure_strings(profile.get(key))


def shared_profile_values(left: dict[str, list[str]], right: dict[str, list[str]], key: str) -> list[str]:
    return shared_values(profile_values(left, key), profile_values(right, key))


def has_problem_alignment(left: dict[str, list[str]], right: dict[str, list[str]]) -> bool:
    return bool(shared_profile_values(left, right, "task_axes") or shared_profile_values(left, right, "problem_spaces"))


def has_io_alignment(left: dict[str, list[str]], right: dict[str, list[str]]) -> bool:
    return bool(
        shared_profile_values(left, right, "input_axes")
        or shared_profile_values(left, right, "output_axes")
        or shared_profile_values(left, right, "modality_axes")
    )


def comparison_gate(left: dict[str, list[str]], right: dict[str, list[str]]) -> bool:
    return has_problem_alignment(left, right) and has_io_alignment(left, right)


def task_neighbor_reason(
    shared_tasks: list[str],
    shared_problem_spaces: list[str],
    shared_inputs: list[str],
    shared_outputs: list[str],
    shared_modalities: list[str],
) -> str:
    parts: list[str] = []
    if shared_tasks:
        parts.append("同属 " + " / ".join(shared_tasks))
    if shared_problem_spaces:
        parts.append("问题空间接近：" + " / ".join(shared_problem_spaces))
    if shared_inputs:
        parts.append("输入接近：" + " / ".join(shared_inputs))
    if shared_outputs:
        parts.append("输出接近：" + " / ".join(shared_outputs))
    if shared_modalities:
        parts.append("模态接近：" + " / ".join(shared_modalities))
    return reason_from_parts(parts, "任务定义接近。")


def method_neighbor_reason(
    shared_tasks: list[str],
    shared_problem_spaces: list[str],
    shared_approaches: list[str],
    shared_outputs: list[str],
) -> str:
    parts: list[str] = []
    if shared_tasks:
        parts.append("同任务：" + " / ".join(shared_tasks))
    if shared_problem_spaces:
        parts.append("同问题空间：" + " / ".join(shared_problem_spaces))
    if shared_approaches:
        parts.append("共享技术路线：" + " / ".join(shared_approaches))
    if shared_outputs:
        parts.append("输出对象接近：" + " / ".join(shared_outputs))
    return reason_from_parts(parts, "技术路线接近。")


def comparison_reason(
    matched_terms: list[str],
    source_label: str,
    shared_tasks: list[str],
    shared_problem_spaces: list[str],
    shared_inputs: list[str],
    shared_outputs: list[str],
    shared_modalities: list[str],
    current_approaches: list[str],
    candidate_approaches: list[str],
) -> str:
    parts: list[str] = []
    if matched_terms:
        parts.append(f"{source_label}命中：" + " / ".join(matched_terms))
    if shared_tasks:
        parts.append("同任务：" + " / ".join(shared_tasks))
    if shared_problem_spaces:
        parts.append("同问题空间：" + " / ".join(shared_problem_spaces))
    if shared_inputs:
        parts.append("输入接近：" + " / ".join(shared_inputs))
    if shared_outputs:
        parts.append("输出接近：" + " / ".join(shared_outputs))
    if shared_modalities:
        parts.append("模态接近：" + " / ".join(shared_modalities))
    if current_approaches and candidate_approaches and not set(current_approaches) & set(candidate_approaches):
        parts.append("技术路线侧重点不同")
    return reason_from_parts(parts, "适合作为对比阅读对象。")


def fallback_comparison_reason(
    source_label: str,
    shared_tasks: list[str],
    shared_problem_spaces: list[str],
    shared_inputs: list[str],
    shared_outputs: list[str],
    shared_modalities: list[str],
) -> str:
    parts: list[str] = []
    if shared_tasks:
        parts.append("同任务：" + " / ".join(shared_tasks))
    if shared_problem_spaces:
        parts.append("同问题空间：" + " / ".join(shared_problem_spaces))
    if shared_inputs:
        parts.append("输入接近：" + " / ".join(shared_inputs))
    if shared_outputs:
        parts.append("输出接近：" + " / ".join(shared_outputs))
    if shared_modalities:
        parts.append("模态接近：" + " / ".join(shared_modalities))
    parts.append(f"{source_label}下技术路线明显不同")
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


def match_terms_against_profile(terms: list[str], candidate_profile: dict[str, list[str]]) -> list[str]:
    matched: list[str] = []
    signal_norms = [
        normalize_match_text(value)
        for value in merge_string_lists(
            candidate_profile.get("comparison_axes"),
            candidate_profile.get("approach_axes"),
        )
    ]
    for term in terms:
        normalized_term = normalize_match_text(term)
        if not normalized_term:
            continue
        if any(
            normalized_term == signal or normalized_term in signal or signal in normalized_term
            for signal in signal_norms
            if signal
        ):
            if term not in matched:
                matched.append(term)
    return matched


def build_task_neighbors(
    record: dict[str, Any],
    candidates: list[dict[str, Any]],
    profile_lookup: dict[str, dict[str, list[str]]],
) -> list[dict[str, Any]]:
    items: list[tuple[tuple[int, int, int, int, int, str], dict[str, Any]]] = []
    left_profile = profile_lookup.get(str(record.get("paper_id") or ""), {})
    for candidate in candidates:
        candidate_profile = profile_lookup.get(str(candidate.get("paper_id") or ""), {})
        shared_tasks = shared_profile_values(left_profile, candidate_profile, "task_axes")
        if not shared_tasks:
            continue
        shared_problem_spaces = shared_profile_values(left_profile, candidate_profile, "problem_spaces")
        shared_inputs = shared_profile_values(left_profile, candidate_profile, "input_axes")
        shared_outputs = shared_profile_values(left_profile, candidate_profile, "output_axes")
        shared_modalities = shared_profile_values(left_profile, candidate_profile, "modality_axes")
        item = {
            "paper_id": str(candidate.get("paper_id") or ""),
            "title": str(candidate.get("title") or candidate.get("paper_id") or ""),
            "score": len(shared_tasks) * 100
            + len(shared_problem_spaces) * 30
            + len(shared_inputs) * 10
            + len(shared_outputs) * 10
            + len(shared_modalities) * 5,
            "match_source": "task_overlap",
            "shared_signals": {
                "task_axes": shared_tasks,
                "problem_spaces": shared_problem_spaces,
                "input_axes": shared_inputs,
                "output_axes": shared_outputs,
                "modality_axes": shared_modalities,
            },
            "reason": task_neighbor_reason(
                shared_tasks,
                shared_problem_spaces,
                shared_inputs,
                shared_outputs,
                shared_modalities,
            ),
            "relation_hint": relation_hint("task_overlap"),
            **paper_paths(str(candidate.get("paper_id") or "")),
        }
        sort_key = (
            -len(shared_tasks),
            -len(shared_problem_spaces),
            -len(shared_inputs),
            -len(shared_outputs),
            -len(shared_modalities),
            candidate_sort_title(candidate),
        )
        items.append((sort_key, item))
    items.sort(key=lambda pair: pair[0])
    return [item for _, item in items[:3]]


def build_method_neighbors(
    record: dict[str, Any],
    candidates: list[dict[str, Any]],
    profile_lookup: dict[str, dict[str, list[str]]],
) -> list[dict[str, Any]]:
    items: list[tuple[tuple[int, int, int, int, str], dict[str, Any]]] = []
    left_profile = profile_lookup.get(str(record.get("paper_id") or ""), {})
    for candidate in candidates:
        candidate_profile = profile_lookup.get(str(candidate.get("paper_id") or ""), {})
        if not has_problem_alignment(left_profile, candidate_profile):
            continue
        shared_tasks = shared_profile_values(left_profile, candidate_profile, "task_axes")
        shared_problem_spaces = shared_profile_values(left_profile, candidate_profile, "problem_spaces")
        shared_approaches = shared_profile_values(left_profile, candidate_profile, "approach_axes")
        shared_outputs = shared_profile_values(left_profile, candidate_profile, "output_axes")
        if not shared_approaches:
            continue
        item = {
            "paper_id": str(candidate.get("paper_id") or ""),
            "title": str(candidate.get("title") or candidate.get("paper_id") or ""),
            "score": len(shared_tasks) * 100
            + len(shared_problem_spaces) * 40
            + len(shared_approaches) * 30
            + len(shared_outputs) * 10,
            "match_source": "method_overlap",
            "shared_signals": {
                "task_axes": shared_tasks,
                "problem_spaces": shared_problem_spaces,
                "approach_axes": shared_approaches,
                "output_axes": shared_outputs,
            },
            "reason": method_neighbor_reason(
                shared_tasks,
                shared_problem_spaces,
                shared_approaches,
                shared_outputs,
            ),
            "relation_hint": relation_hint("method_overlap"),
            **paper_paths(str(candidate.get("paper_id") or "")),
        }
        sort_key = (
            -len(shared_tasks),
            -len(shared_problem_spaces),
            -len(shared_approaches),
            -len(shared_outputs),
            candidate_sort_title(candidate),
        )
        items.append((sort_key, item))
    items.sort(key=lambda pair: pair[0])
    return [item for _, item in items[:3]]


def build_comparison_neighbors(
    record: dict[str, Any],
    candidates: list[dict[str, Any]],
    comparison_context: dict[str, list[str]],
    profile_lookup: dict[str, dict[str, list[str]]],
    route_lookup: dict[str, list[str]],
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    left_profile = profile_lookup.get(str(record.get("paper_id") or ""), {})

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
            candidate_profile = profile_lookup.get(candidate_id, {})
            if not comparison_gate(left_profile, candidate_profile):
                continue
            matched_terms = match_terms_against_profile(terms, candidate_profile)
            if require_match and not matched_terms:
                continue
            shared_tasks = shared_profile_values(left_profile, candidate_profile, "task_axes")
            shared_problem_spaces = shared_profile_values(left_profile, candidate_profile, "problem_spaces")
            shared_inputs = shared_profile_values(left_profile, candidate_profile, "input_axes")
            shared_outputs = shared_profile_values(left_profile, candidate_profile, "output_axes")
            shared_modalities = shared_profile_values(left_profile, candidate_profile, "modality_axes")
            if require_match or matched_terms:
                item = {
                    "paper_id": candidate_id,
                    "title": str(candidate.get("title") or candidate_id),
                    "score": len(matched_terms) * 100
                    + len(shared_tasks) * 40
                    + len(shared_problem_spaces) * 30
                    + len(shared_inputs) * 10
                    + len(shared_outputs) * 10
                    + len(shared_modalities) * 5,
                    "match_source": source_name,
                    "shared_signals": {
                        "comparison_axes": matched_terms,
                        "task_axes": shared_tasks,
                        "problem_spaces": shared_problem_spaces,
                        "input_axes": shared_inputs,
                        "output_axes": shared_outputs,
                        "modality_axes": shared_modalities,
                    },
                    "reason": comparison_reason(
                        matched_terms,
                        source_label,
                        shared_tasks,
                        shared_problem_spaces,
                        shared_inputs,
                        shared_outputs,
                        shared_modalities,
                        route_lookup.get(str(record.get("paper_id") or ""), []),
                        route_lookup.get(candidate_id, []),
                    ),
                    "relation_hint": relation_hint(source_name),
                    **paper_paths(candidate_id),
                }
                sort_key = (
                    -len(matched_terms),
                    -len(shared_tasks),
                    -len(shared_problem_spaces),
                    -(len(shared_inputs) + len(shared_outputs) + len(shared_modalities)),
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
            candidate_profile = profile_lookup.get(candidate_id, {})
            if not comparison_gate(left_profile, candidate_profile):
                continue
            shared_tasks = shared_profile_values(left_profile, candidate_profile, "task_axes")
            shared_problem_spaces = shared_profile_values(left_profile, candidate_profile, "problem_spaces")
            shared_inputs = shared_profile_values(left_profile, candidate_profile, "input_axes")
            shared_outputs = shared_profile_values(left_profile, candidate_profile, "output_axes")
            shared_modalities = shared_profile_values(left_profile, candidate_profile, "modality_axes")
            current_approaches = route_lookup.get(str(record.get("paper_id") or ""), [])
            candidate_approaches = route_lookup.get(candidate_id, [])
            if not shared_tasks and not shared_problem_spaces:
                continue
            if not current_approaches or not candidate_approaches:
                continue
            if set(current_approaches) & set(candidate_approaches):
                continue
            item = {
                "paper_id": candidate_id,
                "title": str(candidate.get("title") or candidate_id),
                "score": len(shared_tasks) * 100
                + len(shared_problem_spaces) * 40
                + len(shared_inputs) * 10
                + len(shared_outputs) * 10
                + len(shared_modalities) * 5,
                "match_source": "fallback_contrast",
                "shared_signals": {
                    "task_axes": shared_tasks,
                    "problem_spaces": shared_problem_spaces,
                    "input_axes": shared_inputs,
                    "output_axes": shared_outputs,
                    "modality_axes": shared_modalities,
                    "current_approach_axes": current_approaches,
                    "candidate_approach_axes": candidate_approaches,
                },
                "reason": fallback_comparison_reason(
                    "同任务 / 同问题空间",
                    shared_tasks,
                    shared_problem_spaces,
                    shared_inputs,
                    shared_outputs,
                    shared_modalities,
                ),
                "relation_hint": relation_hint("fallback_contrast"),
                **paper_paths(candidate_id),
            }
            sort_key = (
                -len(shared_tasks),
                -len(shared_problem_spaces),
                -(len(shared_inputs) + len(shared_outputs) + len(shared_modalities)),
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
    profile_lookup = {
        str(record.get("paper_id") or ""): build_retrieval_profile(
            record,
            comparison_lookup.get(str(record.get("paper_id") or ""), {}),
        )
        for record in records
        if str(record.get("paper_id") or "")
    }
    route_lookup = {
        str(record.get("paper_id") or ""): build_route_core(record)
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
        neighbor_lookup[paper_id] = {
            "task": build_task_neighbors(record, candidates, profile_lookup),
            "method": build_method_neighbors(record, candidates, profile_lookup),
            "comparison": build_comparison_neighbors(
                record,
                candidates,
                comparison_lookup.get(paper_id, {}),
                profile_lookup,
                route_lookup,
            ),
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
                profile_lookup.get(paper_id, {}),
                neighbor_lookup.get(paper_id, {"task": [], "method": [], "comparison": []}),
                include_site_paths=include_site_paths,
            )
        )
    normalized.sort(key=paper_sort_key, reverse=True)
    return normalized


def build_site_payload(records: list[dict[str, Any]]) -> dict[str, Any]:
    filters = build_tag_filters(records)
    generated_at = utc_now()
    return {
        "generated_at": generated_at,
        "paper_count": len(records),
        "site_meta": {
            "title": "Translate Paper Forest",
            "generated_at": generated_at,
            "paper_count": len(records),
        },
        "navigation": {
            "home_route": "#/",
            "detail_route_template": "#/paper/{paper_id}",
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
        "papers": records,
        "filters": filters,
        "tag_filters": filters,
        "recent_titles": [str(item.get("title") or "") for item in records[:8]],
    }
