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
    "links": "链接",
    "pdf": "PDF 链接",
    "doi": "DOI",
    "arxiv": "arXiv",
    "project": "项目页",
    "code": "代码",
    "data": "数据",
    "abstract_raw": "英文摘要",
    "abstract_zh": "中文摘要",
    "reading_digest": "阅读摘要",
    "editorial_review": "编辑判断",
    "research_problem": "研究问题",
    "storyline": "故事线",
    "core_contributions": "核心贡献",
    "author_conclusion": "作者结论",
    "editor_note": "编者按",
    "approach_summary": "核心思路",
    "pipeline_steps": "方法流程",
    "innovations": "主要创新",
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
    "best_results": "高亮结果",
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
    "comparison_aspects": "对比维度",
    "recommended_next_read": "推荐下一篇",
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
    "task_overlap": "same-task",
    "method_overlap": "same-method",
    "baseline_match": "contrast",
    "contrast_method_match": "contrast",
    "fallback_contrast": "contrast",
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

DISPLAY_VALUE_LABELS = {
    "point cloud": "点云",
    "text": "文本",
    "image": "图像",
    "video": "视频",
    "bounding box": "边界框",
    "normals": "法向量",
    "representation": "表示建模",
    "architecture": "架构设计",
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


def shorten_text(value: str | None, max_chars: int) -> str | None:
    text = normalize_label(value or "")
    if not text:
        return None
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip("，,；;：: ") + "…"


def normalize_label(value: str) -> str:
    text = unicodedata.normalize("NFKC", value or "")
    return re.sub(r"\s+", " ", text).strip()


def clean_display_text(value: str | None, max_chars: int | None = None) -> str | None:
    text = normalize_label(value or "")
    text = re.sub(r"^#+\s*", "", text)
    text = re.sub(r"^\d+(?:\.\d+)*[.)]?\s+", "", text)
    if not text:
        return None
    if max_chars is None or len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip("，,；;：: ") + "…"


def display_value(value: str | None) -> str | None:
    text = clean_display_text(value)
    if not text:
        return None
    return DISPLAY_VALUE_LABELS.get(text.lower(), text)


def clean_display_list(values: Any, *, max_chars: int, limit: int | None = None) -> list[str]:
    cleaned: list[str] = []
    for item in ensure_strings(values):
        text = clean_display_text(display_value(item), max_chars=max_chars)
        if text and text not in cleaned:
            cleaned.append(text)
            if limit is not None and len(cleaned) >= limit:
                break
    return cleaned


def is_curation_limitation(value: str) -> bool:
    text = normalize_label(value)
    return any(text.startswith(prefix) for prefix in CURATION_LIMITATION_PREFIXES)


def paper_limitations(value: Any) -> list[str]:
    return [item for item in ensure_strings(value) if not is_curation_limitation(item)]


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


def summary_research_value(summary: dict[str, Any]) -> dict[str, Any]:
    value = summary.get("research_value")
    if isinstance(value, dict):
        return {
            "summary": str(value.get("summary") or "") or None,
            "points": ensure_strings(value.get("points")),
        }
    if isinstance(value, str) and value.strip():
        return {"summary": value.strip(), "points": []}
    return {"summary": None, "points": []}


def reading_digest_block(record: dict[str, Any]) -> dict[str, Any]:
    value = record.get("reading_digest")
    if isinstance(value, dict):
        positioning = value.get("positioning") if isinstance(value.get("positioning"), dict) else {}
        narrative = value.get("narrative") if isinstance(value.get("narrative"), dict) else {}
        return {
            "value_statement": str(value.get("value_statement") or "") or None,
            "best_for": str(value.get("best_for") or "") or None,
            "why_read": ensure_strings(value.get("why_read")),
            "recommended_route": str(value.get("recommended_route") or "") or "overview",
            "positioning": {
                "task": ensure_strings(positioning.get("task")),
                "modality": ensure_strings(positioning.get("modality")),
                "method": ensure_strings(positioning.get("method")),
                "novelty": ensure_strings(positioning.get("novelty")),
            },
            "narrative": {
                "problem": str(narrative.get("problem") or "") or None,
                "method": str(narrative.get("method") or "") or None,
                "result": str(narrative.get("result") or "") or None,
            },
            "result_headline": str(value.get("result_headline") or "") or None,
        }

    summary = summary_block(record)
    research_value = summary_research_value(summary)
    storyline = storyline_block(record)
    research_problem = research_problem_block(record)
    method_core = method_core_block(record)
    eval_block = record.get("benchmarks_or_eval") if isinstance(record.get("benchmarks_or_eval"), dict) else {}
    novelty = novelty_tags(record)
    tags = record.get("research_tags") if isinstance(record.get("research_tags"), dict) else {}
    why_read = merge_string_lists(
        research_value.get("points"),
        ensure_strings(method_core.get("innovations")),
        ensure_strings(eval_block.get("best_results")),
        ensure_strings(eval_block.get("findings")),
        max_items=3,
    )
    return {
        "value_statement": research_value.get("summary") or storyline.get("method") or research_problem.get("summary"),
        "best_for": None,
        "why_read": why_read,
        "recommended_route": "overview",
        "positioning": {
            "task": ensure_strings(tags.get("tasks"))[:2],
            "modality": ensure_strings(tags.get("modalities"))[:3],
            "method": ensure_strings(tags.get("methods"))[:2],
            "novelty": novelty[:2],
        },
        "narrative": {
            "problem": storyline.get("problem") or research_problem.get("summary"),
            "method": storyline.get("method") or method_core.get("approach_summary"),
            "result": storyline.get("outcome") or (ensure_strings(eval_block.get("best_results"))[:1] or [None])[0],
        },
        "result_headline": (ensure_strings(eval_block.get("best_results"))[:1] or ensure_strings(eval_block.get("findings"))[:1] or [storyline.get("outcome")])[0],
    }


def editorial_review_block(record: dict[str, Any]) -> dict[str, Any]:
    value = record.get("editorial_review")
    if isinstance(value, dict):
        verdict = str(value.get("verdict") or "") or None
        return {
            "verdict": verdict,
            "strengths": ensure_strings(value.get("strengths")),
            "cautions": ensure_strings(value.get("cautions")),
            "research_position": str(value.get("research_position") or "") or None,
            "next_read_hint": str(value.get("next_read_hint") or "") or None,
        }

    editor_note = editor_note_block(record)
    limitations = paper_limitations(record.get("limitations"))
    comparison_context = comparison_context_block(record)
    next_read_target = str(comparison_context.get("recommended_next_read") or "") or None
    return {
        "verdict": "值得浏览" if editor_note or next_read_target else None,
        "strengths": ensure_strings((editor_note or {}).get("points")),
        "cautions": limitations[:3],
        "research_position": str((editor_note or {}).get("summary") or "") or None,
        "next_read_hint": f"可继续对比 {next_read_target}。" if next_read_target else None,
    }


def storyline_block(record: dict[str, Any]) -> dict[str, Any]:
    storyline = record.get("storyline")
    if isinstance(storyline, dict):
        return {
            "problem": str(storyline.get("problem") or "") or None,
            "method": str(storyline.get("method") or "") or None,
            "outcome": str(storyline.get("outcome") or "") or None,
        }
    return {"problem": None, "method": None, "outcome": None}


def research_problem_block(record: dict[str, Any]) -> dict[str, Any]:
    value = record.get("research_problem")
    if isinstance(value, dict):
        return {
            "summary": str(value.get("summary") or "") or None,
            "gaps": ensure_strings(value.get("gaps")),
            "goal": str(value.get("goal") or "") or None,
        }
    if isinstance(value, str) and value.strip():
        return {"summary": value.strip(), "gaps": [], "goal": None}
    return {"summary": None, "gaps": [], "goal": None}


def method_core_block(record: dict[str, Any]) -> dict[str, Any]:
    method_core = record.get("method_core")
    if not isinstance(method_core, dict):
        method_core = {}
    approach_summary = str(
        method_core.get("approach_summary")
        or method_core.get("approach")
        or ""
    ) or None
    innovations = ensure_strings(method_core.get("innovations"))
    if not innovations:
        innovations = ensure_strings([method_core.get("innovation")]) if method_core.get("innovation") else []
    return {
        "approach_summary": approach_summary,
        "pipeline_steps": ensure_strings(method_core.get("pipeline_steps")),
        "innovations": innovations,
        "ingredients": ensure_strings(method_core.get("ingredients")),
        "representation": ensure_strings(method_core.get("representation")),
        "supervision": ensure_strings(method_core.get("supervision")),
        "differences": ensure_strings(method_core.get("differences")),
    }


def editor_note_block(record: dict[str, Any]) -> dict[str, Any] | None:
    value = record.get("editor_note")
    if isinstance(value, dict):
        payload = {
            "summary": str(value.get("summary") or "") or None,
            "points": ensure_strings(value.get("points")),
        }
        if payload["summary"] or payload["points"]:
            return payload
        return None
    if isinstance(value, str) and value.strip():
        return {"summary": value.strip(), "points": []}
    return None


def comparison_context_block(record: dict[str, Any]) -> dict[str, Any]:
    value = record.get("comparison_context")
    if not isinstance(value, dict):
        value = {}
    aspects = value.get("comparison_aspects")
    normalized_aspects: list[dict[str, str]] = []
    if isinstance(aspects, list):
        for item in aspects:
            if isinstance(item, dict):
                aspect = str(item.get("aspect") or "") or None
                difference = str(item.get("difference") or "") or None
                if aspect and difference:
                    normalized_aspects.append({"aspect": aspect, "difference": difference})
    if not normalized_aspects:
        for note in ensure_strings(value.get("contrast_notes")):
            normalized_aspects.append({"aspect": "difference", "difference": note})
    return {
        "explicit_baselines": ensure_strings(value.get("explicit_baselines")),
        "contrast_methods": ensure_strings(value.get("contrast_methods")),
        "comparison_aspects": normalized_aspects[:4],
        "recommended_next_read": str(value.get("recommended_next_read") or "") or None,
    }


def figure_item_block(item: dict[str, Any], *, default_role: str) -> dict[str, str] | None:
    label = str(item.get("label") or "") or None
    caption = str(item.get("caption") or "") or None
    if not label and not caption:
        return None
    role = str(item.get("role") or default_role)
    importance = str(item.get("importance") or ("high" if default_role in {"method_overview", "quantitative_result"} else "medium"))
    return {
        "label": label or "",
        "caption": caption or "",
        "role": role,
        "importance": importance,
    }


def figure_table_index_block(record: dict[str, Any]) -> dict[str, list[dict[str, str]]]:
    figure_table_index = record.get("figure_table_index")
    if not isinstance(figure_table_index, dict):
        figure_table_index = {}
    figures: list[dict[str, str]] = []
    tables: list[dict[str, str]] = []
    for item in figure_table_index.get("figures", []) if isinstance(figure_table_index.get("figures"), list) else []:
        if isinstance(item, dict):
            normalized = figure_item_block(item, default_role="method_overview")
            if normalized:
                figures.append(normalized)
    for item in figure_table_index.get("tables", []) if isinstance(figure_table_index.get("tables"), list) else []:
        if isinstance(item, dict):
            normalized = figure_item_block(item, default_role="quantitative_result")
            if normalized:
                tables.append(normalized)
    return {"figures": figures, "tables": tables}


def score_level(score: int) -> str:
    if score >= 160:
        return "high"
    if score >= 80:
        return "medium"
    return "low"


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


def derive_comparison_context(record: dict[str, Any], vocabulary: list[str]) -> dict[str, Any]:
    eval_block = record.get("benchmarks_or_eval")
    method_core = method_core_block(record)
    existing = comparison_context_block(record)
    baselines = ensure_strings(eval_block.get("baselines")) if isinstance(eval_block, dict) else []
    differences = ensure_strings(method_core.get("differences"))
    innovations = ensure_strings(method_core.get("innovations"))
    notes = list(differences)
    for innovation in innovations:
        if innovation not in notes:
            notes.append(innovation)

    text_pool = "\n".join(notes)
    contrast_methods: list[str] = []
    for term in vocabulary:
        if term in baselines:
            continue
        if contains_term(text_pool, term):
            contrast_methods.append(term)

    return {
        "explicit_baselines": merge_string_lists(existing.get("explicit_baselines"), baselines),
        "contrast_methods": merge_string_lists(existing.get("contrast_methods"), contrast_methods),
        "comparison_aspects": existing.get("comparison_aspects") or [{"aspect": "difference", "difference": note} for note in notes[:3]],
        "recommended_next_read": str(existing.get("recommended_next_read") or "") or (baselines[0] if baselines else None),
    }


def derive_problem_spaces(record: dict[str, Any]) -> list[str]:
    themes = tag_group(record, "themes")
    tasks = tag_group(record, "tasks")
    inputs_outputs = record.get("inputs_outputs") if isinstance(record.get("inputs_outputs"), dict) else {}
    outputs = ensure_strings(inputs_outputs.get("outputs"))
    return merge_string_lists(themes, tasks, outputs, max_items=3)


def build_retrieval_profile(
    record: dict[str, Any],
    comparison_context: dict[str, Any],
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
    comparison_context: dict[str, Any],
    retrieval_profile: dict[str, list[str]],
    paper_neighbors: dict[str, list[dict[str, Any]]],
    *,
    include_site_paths: bool,
) -> dict[str, Any]:
    method_core = method_core_block(record)
    inputs_outputs = record.get("inputs_outputs") if isinstance(record.get("inputs_outputs"), dict) else {}
    eval_block = record.get("benchmarks_or_eval") if isinstance(record.get("benchmarks_or_eval"), dict) else {}
    figure_table_index = figure_table_index_block(record)
    links = record.get("links") if isinstance(record.get("links"), dict) else {}
    summary = summary_block(record)
    research_value = summary_research_value(summary)
    research_problem = research_problem_block(record)
    editor_note = editor_note_block(record)
    reading_digest = reading_digest_block(record)
    editorial_review = editorial_review_block(record)
    storyline = storyline_block(record)
    comparison_context_payload = comparison_context_block(
        {
            **record,
            "comparison_context": comparison_context,
        }
    )

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
        "abstract_raw": str(record.get("abstract_raw") or "") or None,
        "abstract_zh": str(record.get("abstract_zh") or "") or None,
        "summary": {
            "one_liner": clean_display_text(str(summary.get("one_liner") or ""), max_chars=110) or "",
            "abstract_summary": clean_display_text(str(summary.get("abstract_summary") or ""), max_chars=150),
            "research_value": {
                "summary": clean_display_text(str(research_value.get("summary") or ""), max_chars=72),
                "points": clean_display_list(research_value.get("points"), max_chars=64, limit=3),
            },
            "worth_long_term_graph": bool(summary.get("worth_long_term_graph")),
        },
        "reading_digest": {
            "value_statement": clean_display_text(str(reading_digest.get("value_statement") or ""), max_chars=84),
            "best_for": clean_display_text(str(reading_digest.get("best_for") or ""), max_chars=72),
            "why_read": clean_display_list(reading_digest.get("why_read"), max_chars=64, limit=3),
            "recommended_route": str(reading_digest.get("recommended_route") or "overview"),
            "positioning": {
                "task": clean_display_list((reading_digest.get("positioning") or {}).get("task"), max_chars=28, limit=4)
                if isinstance(reading_digest.get("positioning"), dict)
                else [],
                "modality": clean_display_list((reading_digest.get("positioning") or {}).get("modality"), max_chars=24, limit=4)
                if isinstance(reading_digest.get("positioning"), dict)
                else [],
                "method": clean_display_list((reading_digest.get("positioning") or {}).get("method"), max_chars=28, limit=4)
                if isinstance(reading_digest.get("positioning"), dict)
                else [],
                "novelty": clean_display_list((reading_digest.get("positioning") or {}).get("novelty"), max_chars=24, limit=4)
                if isinstance(reading_digest.get("positioning"), dict)
                else [],
            },
            "narrative": {
                "problem": clean_display_text(str((reading_digest.get("narrative") or {}).get("problem") or ""), max_chars=90)
                if isinstance(reading_digest.get("narrative"), dict)
                else None,
                "method": clean_display_text(str((reading_digest.get("narrative") or {}).get("method") or ""), max_chars=90)
                if isinstance(reading_digest.get("narrative"), dict)
                else None,
                "result": clean_display_text(str((reading_digest.get("narrative") or {}).get("result") or ""), max_chars=90)
                if isinstance(reading_digest.get("narrative"), dict)
                else None,
            },
            "result_headline": clean_display_text(str(reading_digest.get("result_headline") or ""), max_chars=96),
        },
        "storyline": {
            "problem": clean_display_text(str(storyline.get("problem") or ""), max_chars=84),
            "method": clean_display_text(str(storyline.get("method") or ""), max_chars=84),
            "outcome": clean_display_text(str(storyline.get("outcome") or ""), max_chars=84),
        },
        "research_problem": {
            "summary": clean_display_text(str(research_problem.get("summary") or ""), max_chars=100),
            "gaps": clean_display_list(research_problem.get("gaps"), max_chars=84, limit=4),
            "goal": clean_display_text(str(research_problem.get("goal") or ""), max_chars=100),
        },
        "core_contributions": clean_display_list(record.get("core_contributions"), max_chars=90, limit=4),
        "key_claims": [
            {
                "claim": clean_display_text(str(item.get("claim") or ""), max_chars=120) or "",
                "type": clean_display_text(str(item.get("type") or "method"), max_chars=24) or "method",
                "support": ensure_strings(item.get("support")),
                "confidence": clean_display_text(str(item.get("confidence") or ""), max_chars=16) or "",
            }
            for item in record.get("key_claims", [])
            if isinstance(item, dict)
        ],
        "method_core": {
            "approach_summary": clean_display_text(str(method_core.get("approach_summary") or ""), max_chars=110),
            "pipeline_steps": clean_display_list(method_core.get("pipeline_steps"), max_chars=105, limit=4),
            "innovations": clean_display_list(method_core.get("innovations"), max_chars=90, limit=4),
            "ingredients": clean_display_list(method_core.get("ingredients"), max_chars=32, limit=6),
            "representation": clean_display_list(method_core.get("representation"), max_chars=32, limit=6),
            "supervision": clean_display_list(method_core.get("supervision"), max_chars=48, limit=4),
            "differences": clean_display_list(method_core.get("differences"), max_chars=90, limit=4),
        },
        "inputs_outputs": {
            "inputs": clean_display_list(inputs_outputs.get("inputs"), max_chars=28, limit=6),
            "outputs": clean_display_list(inputs_outputs.get("outputs"), max_chars=28, limit=6),
            "modalities": clean_display_list(inputs_outputs.get("modalities"), max_chars=24, limit=6),
        },
        "benchmarks_or_eval": {
            "datasets": clean_display_list(eval_block.get("datasets"), max_chars=30, limit=8),
            "metrics": clean_display_list(eval_block.get("metrics"), max_chars=20, limit=8),
            "baselines": clean_display_list(eval_block.get("baselines"), max_chars=28, limit=8),
            "findings": clean_display_list(eval_block.get("findings"), max_chars=90, limit=4),
            "best_results": clean_display_list(eval_block.get("best_results"), max_chars=90, limit=4),
            "experiment_setup_summary": clean_display_text(str(eval_block.get("experiment_setup_summary") or ""), max_chars=140),
        },
        "author_conclusion": clean_display_text(str(record.get("author_conclusion") or ""), max_chars=180),
        "editor_note": editor_note,
        "editorial_review": {
            "verdict": clean_display_text(str(editorial_review.get("verdict") or ""), max_chars=16),
            "strengths": clean_display_list(editorial_review.get("strengths"), max_chars=80, limit=4),
            "cautions": clean_display_list(editorial_review.get("cautions"), max_chars=80, limit=4),
            "research_position": clean_display_text(str(editorial_review.get("research_position") or ""), max_chars=84),
            "next_read_hint": clean_display_text(str(editorial_review.get("next_read_hint") or ""), max_chars=60),
        },
        "limitations": clean_display_list(paper_limitations(record.get("limitations")), max_chars=90, limit=4),
        "novelty_type": clean_display_list(record.get("novelty_type"), max_chars=24, limit=4),
        "research_tags": {
            "themes": tag_group(record, "themes"),
            "tasks": tag_group(record, "tasks"),
            "methods": tag_group(record, "methods"),
            "modalities": clean_display_list(tag_group(record, "modalities"), max_chars=24, limit=6),
            "representations": clean_display_list(tag_group(record, "representations"), max_chars=28, limit=6),
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
            "explicit_baselines": clean_display_list(comparison_context_payload.get("explicit_baselines"), max_chars=28, limit=8),
            "contrast_methods": clean_display_list(comparison_context_payload.get("contrast_methods"), max_chars=28, limit=8),
            "comparison_aspects": [
                {
                    "aspect": clean_display_text(str(item.get("aspect") or ""), max_chars=28) or "",
                    "difference": clean_display_text(str(item.get("difference") or ""), max_chars=96) or "",
                }
                for item in comparison_context_payload.get("comparison_aspects", [])
                if isinstance(item, dict)
            ],
            "recommended_next_read": clean_display_text(str(comparison_context_payload.get("recommended_next_read") or ""), max_chars=36),
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
            "reason_short": shorten_text(
                task_neighbor_reason(
                    shared_tasks,
                    shared_problem_spaces,
                    shared_inputs,
                    shared_outputs,
                    shared_modalities,
                ),
                50,
            ),
            "score_level": score_level(
                len(shared_tasks) * 100
                + len(shared_problem_spaces) * 30
                + len(shared_inputs) * 10
                + len(shared_outputs) * 10
                + len(shared_modalities) * 5
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
            "reason_short": shorten_text(
                method_neighbor_reason(
                    shared_tasks,
                    shared_problem_spaces,
                    shared_approaches,
                    shared_outputs,
                ),
                50,
            ),
            "score_level": score_level(
                len(shared_tasks) * 100
                + len(shared_problem_spaces) * 40
                + len(shared_approaches) * 30
                + len(shared_outputs) * 10
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
    comparison_context: dict[str, Any],
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
                    "reason_short": shorten_text(
                        comparison_reason(
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
                        50,
                    ),
                    "score_level": score_level(
                        len(matched_terms) * 100
                        + len(shared_tasks) * 40
                        + len(shared_problem_spaces) * 30
                        + len(shared_inputs) * 10
                        + len(shared_outputs) * 10
                        + len(shared_modalities) * 5
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
                "reason_short": shorten_text(
                    fallback_comparison_reason(
                        "同任务 / 同问题空间",
                        shared_tasks,
                        shared_problem_spaces,
                        shared_inputs,
                        shared_outputs,
                        shared_modalities,
                    ),
                    50,
                ),
                "score_level": score_level(
                    len(shared_tasks) * 100
                    + len(shared_problem_spaces) * 40
                    + len(shared_inputs) * 10
                    + len(shared_outputs) * 10
                    + len(shared_modalities) * 5
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
