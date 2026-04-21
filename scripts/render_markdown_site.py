#!/usr/bin/env python3
"""Render a paper-neighbor-first Markdown reading site."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from paper_neighbors import (
    backfill_records,
    build_site_payload,
    confidence_label,
    display_label,
    ensure_strings,
    format_support_labels,
    load_papers,
    match_source_label,
    summarize_records,
    write_json,
    write_text,
)


LEGACY_SITE_FILES = (
    "forest.json",
    "theme-map.md",
    "method-map.md",
    "timeline.md",
    "relationship-graph.md",
)


def render_support_line(values: list[str]) -> str:
    return ", ".join(format_support_labels(values)) if values else "暂无"


def render_links_block(links: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for key in ("pdf", "doi", "arxiv", "project", "code", "data"):
        value = str(links.get(key) or "").strip()
        if value:
            lines.append(f"- {display_label(key)}: {value}")
    return lines


def render_linked_papers(paper_ids: list[str], paper_lookup: dict[str, dict[str, Any]]) -> str:
    links: list[str] = []
    for paper_id in paper_ids:
        paper = paper_lookup.get(str(paper_id), {})
        title = str(paper.get("title") or paper_id)
        links.append(f'[{title}](index.html#/paper/{paper_id})')
    return " / ".join(links) if links else "暂无"


def render_filter_group(
    title: str,
    items: list[dict[str, Any]],
    paper_lookup: dict[str, dict[str, Any]],
) -> list[str]:
    lines = [f"## {title}", ""]
    if not items:
        lines.extend(["暂无可筛选标签。", ""])
        return lines

    chips = []
    for item in items[:12]:
        anchor = str(item.get("label") or "").lower().replace(" ", "-")
        chips.append(f'[{item.get("label") or ""} ({item.get("count") or 0})](#{anchor})')
    lines.append("- 快速跳转: " + " / ".join(chips))
    lines.append("")

    for item in items:
        label = str(item.get("label") or "")
        anchor = label.lower().replace(" ", "-")
        lines.append(f"### {label} ({item.get('count') or 0})")
        lines.append(f"<a id=\"{anchor}\"></a>")
        lines.append("")
        lines.append(f"- 论文: {render_linked_papers(ensure_strings(item.get('paper_ids')), paper_lookup)}")
        lines.append("")
    return lines


def render_comparison_context(record: dict[str, Any]) -> list[str]:
    context = record.get("comparison_context", {}) if isinstance(record.get("comparison_context"), dict) else {}
    lines = ["## 对比上下文", ""]
    baselines = ensure_strings(context.get("explicit_baselines"))
    contrast_methods = ensure_strings(context.get("contrast_methods"))
    comparison_aspects = context.get("comparison_aspects") if isinstance(context.get("comparison_aspects"), list) else []
    recommended_next_read = str(context.get("recommended_next_read") or "").strip()
    if baselines:
        lines.append(f"- {display_label('explicit_baselines')}: " + " / ".join(baselines))
    if contrast_methods:
        lines.append(f"- {display_label('contrast_methods')}: " + " / ".join(contrast_methods))
    if comparison_aspects:
        for item in comparison_aspects:
            if not isinstance(item, dict):
                continue
            aspect = str(item.get("aspect") or "").strip()
            difference = str(item.get("difference") or "").strip()
            if aspect and difference:
                lines.append(f"- {aspect}: {difference}")
    if recommended_next_read:
        lines.append(f"- {display_label('recommended_next_read')}: {recommended_next_read}")
    if not baselines and not contrast_methods and not comparison_aspects and not recommended_next_read:
        lines.append("- 暂无可计算的对比上下文。")
    lines.append("")
    return lines


def render_route_label(value: str) -> str:
    mapping = {
        "method": "先看方法",
        "evaluation": "先看实验",
        "comparison": "先看对比",
        "overview": "先看概述",
    }
    return mapping.get(value, value or "先看概述")


def render_neighbor_section(title: str, items: list[dict[str, Any]]) -> list[str]:
    lines = [f"## {title}", ""]
    if not items:
        lines.extend(["- 信号不足，当前库中没有足够可靠的近邻。", ""])
        return lines
    for item in items:
        local_target = Path(str(item.get("paper_path") or "")).name if str(item.get("paper_path") or "") else ""
        label = f"[{item.get('title') or ''}]({local_target})" if local_target else str(item.get("title") or "")
        lines.append(
            f"- {label} | {display_label('score')} {item.get('score') or 0} | {match_source_label(str(item.get('match_source') or 'neighbor'))} | {item.get('reason_short') or item.get('reason') or ''}"
        )
        relation_hint = str(item.get("relation_hint") or "").strip()
        if relation_hint:
            lines.append(f"  {display_label('relation_hint')}: {relation_hint}")
        score_level = str(item.get("score_level") or "").strip()
        if score_level:
            lines.append(f"  score_level: {score_level}")
        shared_signals = item.get("shared_signals") if isinstance(item.get("shared_signals"), dict) else {}
        detail_parts = []
        for key, values in shared_signals.items():
            cleaned = ensure_strings(values)
            if cleaned:
                detail_parts.append(f"{display_label(str(key))}=" + " / ".join(cleaned))
        if detail_parts:
            lines.append("  信号: " + " | ".join(detail_parts))
    lines.append("")
    return lines


def render_index(payload: dict[str, Any], paper_lookup: dict[str, dict[str, Any]]) -> str:
    tag_filters = payload.get("filters", {}) if isinstance(payload.get("filters"), dict) else {}
    papers = payload.get("papers", []) if isinstance(payload.get("papers"), list) else []
    lines = [
        "# Translate Paper Forest",
        "",
        "- 主入口: [网页首页](index.html#/)",
        f"- 生成时间: {payload.get('generated_at') or ''}",
        f"- 论文总数: {payload.get('paper_count') or 0}",
        "- 当前主流程: 先检索论文，再进入单篇阅读页沿任务 / 方法 / 对比方法三个维度展开近邻阅读。",
        "- 前端站点已切换为单页应用，不再生成每篇论文独立 HTML。",
        "",
        "## 最近论文",
        "",
    ]
    if papers:
        for paper in papers[:10]:
            paper_id = str(paper.get("paper_id") or "")
            lines.append(
                f"- [{paper.get('title') or paper_id}](index.html#/paper/{paper_id}) | {paper.get('venue') or ''} {paper.get('year') or ''}"
            )
    else:
        lines.append("- 暂无已处理论文。")
    lines.extend(["", "## 导航", "", "- [站点首页](index.html#/)", ""])
    lines.extend(render_filter_group("按主题筛选", ensure_strings_dicts(tag_filters.get("themes")), paper_lookup))
    lines.extend(render_filter_group("按任务筛选", ensure_strings_dicts(tag_filters.get("tasks")), paper_lookup))
    lines.extend(render_filter_group("按方法筛选", ensure_strings_dicts(tag_filters.get("methods")), paper_lookup))
    return "\n".join(lines) + "\n"


def ensure_strings_dicts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def remove_legacy_site_files(site_dir: Path) -> None:
    for name in LEGACY_SITE_FILES:
        path = site_dir / name
        if path.exists():
            path.unlink()


def render_paper_page(record: dict[str, Any]) -> str:
    title = str(record.get("title") or record.get("paper_id") or "Untitled")
    reading_digest = record.get("reading_digest", {}) if isinstance(record.get("reading_digest"), dict) else {}
    editorial_review = record.get("editorial_review", {}) if isinstance(record.get("editorial_review"), dict) else {}
    summary = record.get("summary", {}) if isinstance(record.get("summary"), dict) else {}
    method_core = record.get("method_core", {}) if isinstance(record.get("method_core"), dict) else {}
    eval_block = record.get("benchmarks_or_eval", {}) if isinstance(record.get("benchmarks_or_eval"), dict) else {}
    figure_table_index = record.get("figure_table_index", {}) if isinstance(record.get("figure_table_index"), dict) else {}
    inputs_outputs = record.get("inputs_outputs", {}) if isinstance(record.get("inputs_outputs"), dict) else {}
    claims = record.get("key_claims") if isinstance(record.get("key_claims"), list) else []
    neighbors = record.get("paper_neighbors") if isinstance(record.get("paper_neighbors"), dict) else {}
    links = record.get("links", {}) if isinstance(record.get("links"), dict) else {}
    authors = ensure_strings(record.get("authors"))
    contributions = ensure_strings(record.get("core_contributions"))
    topics = ensure_strings_dicts(record.get("topics"))
    relations = ensure_strings_dicts(record.get("paper_relations"))

    lines = [
        f"# {title}",
        "",
        f"- 网页阅读版: [index.html{record.get('route_path') or '#/'}](../index.html{record.get('route_path') or '#/'})",
        f"- {display_label('paper_id')}: {record.get('paper_id') or ''}",
        f"- {display_label('authors')}: " + (" / ".join(authors) if authors else "暂无"),
        f"- {display_label('venue')}: {record.get('venue') or ''}",
        f"- {display_label('year')}: {record.get('year') or ''}",
        f"- {display_label('citation_count')}: {record.get('citation_count') if record.get('citation_count') is not None else '暂无'}",
        "",
        "## 链接",
        "",
    ]
    link_lines = render_links_block(links)
    if link_lines:
        lines.extend(link_lines)
    else:
        lines.append("- 暂无可用链接。")

    lines.extend([
        "",
        "## 决策层",
        "",
    ])
    value_statement = str(reading_digest.get("value_statement") or "").strip()
    best_for = str(reading_digest.get("best_for") or "").strip()
    recommended_route = str(reading_digest.get("recommended_route") or "").strip()
    result_headline = str(reading_digest.get("result_headline") or "").strip()
    verdict = str(editorial_review.get("verdict") or "").strip()
    if value_statement:
        lines.append(value_statement)
        lines.append("")
    if summary.get("one_liner"):
        lines.append(f"- 一句话结论: {summary.get('one_liner')}")
    if best_for:
        lines.append(f"- 适合谁读: {best_for}")
    if recommended_route:
        lines.append(f"- 阅读路径: {render_route_label(recommended_route)}")
    if verdict:
        lines.append(f"- 编辑结论: {verdict}")
    if result_headline:
        lines.append(f"- 结果先看: {result_headline}")
    for item in ensure_strings(reading_digest.get("why_read")):
        lines.append(f"- 为什么继续读: {item}")
    narrative = reading_digest.get("narrative") if isinstance(reading_digest.get("narrative"), dict) else {}
    narrative_parts = [
        f"{key}: {value}"
        for key, value in [
            ("问题", narrative.get("problem")),
            ("方法", narrative.get("method")),
            ("结果", narrative.get("result")),
        ]
        if isinstance(value, str) and value.strip()
    ]
    if narrative_parts:
        lines.append("- 三段故事线: " + " | ".join(narrative_parts))
    lines.append("")

    abstract_raw = str(record.get("abstract_raw") or "").strip()
    abstract_zh = str(record.get("abstract_zh") or "").strip()

    abstract_summary = str(summary.get("abstract_summary") or "")
    research_value = summary.get("research_value") if isinstance(summary.get("research_value"), dict) else {}
    research_value_summary = str(research_value.get("summary") or "").strip() if isinstance(research_value, dict) else ""
    research_value_points = ensure_strings(research_value.get("points")) if isinstance(research_value, dict) else []
    storyline = record.get("storyline", {}) if isinstance(record.get("storyline"), dict) else {}
    lines.extend(["## 理解层", ""])
    if abstract_summary:
        lines.append(f"- 摘要概览: {abstract_summary}")
    if research_value_summary:
        lines.append(f"- 阅读价值: {research_value_summary}")
    for item in research_value_points:
        lines.append(f"- 价值线索: {item}")
    if storyline:
        storyline_parts = [
            f"{key}: {value}"
            for key, value in [("问题", storyline.get("problem")), ("方法", storyline.get("method")), ("结果", storyline.get("outcome"))]
            if isinstance(value, str) and value.strip()
        ]
        if storyline_parts:
            lines.append("- 三段故事: " + " | ".join(storyline_parts))
    lines.append("")

    research_problem = record.get("research_problem", {}) if isinstance(record.get("research_problem"), dict) else {}
    research_problem_summary = str(research_problem.get("summary") or "").strip() if isinstance(research_problem, dict) else ""
    research_problem_gaps = ensure_strings(research_problem.get("gaps")) if isinstance(research_problem, dict) else []
    research_problem_goal = str(research_problem.get("goal") or "").strip() if isinstance(research_problem, dict) else ""
    if research_problem_summary or research_problem_gaps or research_problem_goal:
        lines.extend(["## 研究问题", ""])
        if research_problem_summary:
            lines.append(f"- 问题摘要: {research_problem_summary}")
        for item in research_problem_gaps:
            lines.append(f"- 研究缺口: {item}")
        if research_problem_goal:
            lines.append(f"- 研究目标: {research_problem_goal}")
        lines.append("")

    if contributions:
        lines.extend(["## 核心贡献", ""])
        for item in contributions:
            lines.append(f"- {item}")
        lines.append("")

    lines.extend(["## 方法核心", ""])
    approach_summary = str(method_core.get("approach_summary") or "").strip()
    if approach_summary:
        lines.append(f"- {display_label('approach_summary')}: {approach_summary}")
    pipeline_steps = ensure_strings(method_core.get("pipeline_steps"))
    for item in pipeline_steps:
        lines.append(f"- 方法流程: {item}")
    for item in ensure_strings(method_core.get("innovations")):
        lines.append(f"- 主要创新: {item}")
    for key in ("ingredients", "representation", "supervision", "differences"):
        values = ensure_strings(method_core.get(key))
        if values:
            lines.append(f"- {display_label(key)}: " + " / ".join(values))

    if inputs_outputs:
        lines.extend(["", "## 输入输出", ""])
        for key in ("inputs", "outputs", "modalities"):
            values = ensure_strings(inputs_outputs.get(key))
            if values:
                lines.append(f"- {display_label(key)}: " + " / ".join(values))

    lines.extend(["", "## 评估快照", ""])
    for key in ("datasets", "metrics", "baselines", "findings", "best_results"):
        values = ensure_strings(eval_block.get(key))
        if values:
            lines.append(f"- {display_label(key)}: " + " / ".join(values))
    experiment_setup_summary = str(eval_block.get("experiment_setup_summary") or "").strip()
    if experiment_setup_summary:
        lines.append(f"- {display_label('experiment_setup_summary')}: {experiment_setup_summary}")

    author_conclusion = str(record.get("author_conclusion") or "").strip()
    if author_conclusion:
        lines.extend(["", "## 作者结论", "", author_conclusion])

    editor_note = record.get("editor_note") if isinstance(record.get("editor_note"), dict) else {}
    editor_note_summary = str(editor_note.get("summary") or "").strip() if isinstance(editor_note, dict) else ""
    editor_note_points = ensure_strings(editor_note.get("points")) if isinstance(editor_note, dict) else []
    lines.extend(["", "## 编辑判断", ""])
    if verdict:
        lines.append(f"- 结论: {verdict}")
    for item in ensure_strings(editorial_review.get("strengths")):
        lines.append(f"- 值得看: {item}")
    for item in ensure_strings(editorial_review.get("cautions")):
        lines.append(f"- 需注意: {item}")
    research_position = str(editorial_review.get("research_position") or "").strip()
    next_read_hint = str(editorial_review.get("next_read_hint") or "").strip()
    if research_position:
        lines.append(f"- 阅读定位: {research_position}")
    if next_read_hint:
        lines.append(f"- 下一篇建议: {next_read_hint}")
    if editor_note_summary:
        lines.append(f"- 编者按: {editor_note_summary}")
    for item in editor_note_points:
        lines.append(f"- 阅读备注: {item}")
    lines.append("")

    lines.extend(render_comparison_context(record))
    lines.extend(["<details>", "<summary>资料层</summary>", ""])

    lines.extend(["## 核心论断", ""])
    if claims:
        for item in claims:
            if not isinstance(item, dict):
                continue
            lines.append(f"- {item.get('claim') or ''}")
            claim_type = str(item.get("type") or "").strip()
            if claim_type:
                lines.append(f"  type: {claim_type}")
            support = ensure_strings(item.get("support"))
            confidence = str(item.get("confidence") or "")
            if support:
                lines.append(f"  支撑: {render_support_line(support)}")
            if confidence:
                lines.append(f"  置信度: {confidence_label(confidence)}")
    else:
        lines.append("- 暂无核心论断。")
    lines.append("")

    if abstract_raw:
        lines.extend(["## 英文摘要", "", abstract_raw, ""])
    if abstract_zh:
        lines.extend(["## 中文摘要", "", abstract_zh, ""])

    limitations = ensure_strings(record.get("limitations"))
    lines.extend(["## 局限", ""])
    if limitations:
        for item in limitations:
            lines.append(f"- {item}")
    else:
        lines.append("- 暂无论文局限记录。")
    lines.append("")

    novelty = ensure_strings(record.get("novelty_type"))
    if novelty:
        lines.extend(["## 创新类型", "", "- " + " / ".join(novelty), ""])

    lines.extend(["## 研究标签", ""])
    research_tags = record.get("research_tags", {}) if isinstance(record.get("research_tags"), dict) else {}
    for key in ("themes", "tasks", "methods", "modalities", "representations"):
        values = ensure_strings(research_tags.get(key))
        if values:
            lines.append(f"- {display_label(key)}: " + " / ".join(values))
    lines.append("")

    if topics:
        lines.extend(["## 主题节点", ""])
        for item in topics:
            name = str(item.get("name") or item.get("slug") or "")
            role = str(item.get("role") or "").strip()
            lines.append(f"- {name}" + (f" | {role}" if role else ""))
        lines.append("")

    if relations:
        lines.extend(["## 论文关系", ""])
        for item in relations:
            target = str(item.get("target_paper_id") or "")
            relation_type = str(item.get("relation_type") or "")
            description = str(item.get("description") or "")
            confidence = item.get("confidence")
            line = f"- {target} | {relation_type}"
            if description:
                line += f" | {description}"
            if confidence is not None:
                line += f" | confidence={confidence}"
            lines.append(line)
        lines.append("")

    lines.extend(render_neighbor_section("相似论文：任务维度", ensure_strings_dicts(neighbors.get("task"))))
    lines.extend(render_neighbor_section("相似论文：技术方法维度", ensure_strings_dicts(neighbors.get("method"))))
    lines.extend(render_neighbor_section("相似论文：对比方法维度", ensure_strings_dicts(neighbors.get("comparison"))))

    lines.extend(["## 图表索引", ""])
    figures = figure_table_index.get("figures")
    tables = figure_table_index.get("tables")
    if isinstance(figures, list):
        for item in figures[:12]:
            if isinstance(item, dict):
                lines.append(
                    f"- 图：{item.get('label') or 'Figure'} | {item.get('role') or ''} | {item.get('importance') or ''}: {item.get('caption') or ''}"
                )
    if isinstance(tables, list):
        for item in tables[:12]:
            if isinstance(item, dict):
                lines.append(
                    f"- 表：{item.get('label') or 'Table'} | {item.get('role') or ''} | {item.get('importance') or ''}: {item.get('caption') or ''}"
                )
    lines.append("")

    retrieval = record.get("retrieval_profile") if isinstance(record.get("retrieval_profile"), dict) else {}
    if retrieval:
        lines.extend(["## 检索画像", ""])
        for key in ("problem_spaces", "task_axes", "approach_axes", "input_axes", "output_axes", "modality_axes", "comparison_axes"):
            values = ensure_strings(retrieval.get(key))
            if values:
                lines.append(f"- {display_label(key)}: " + " / ".join(values))
        lines.append("")

    lines.extend(["</details>"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Render Markdown site from paper-neighbor-first records.")
    parser.add_argument("--papers-dir", required=True, help="Directory containing normalized paper JSON files.")
    parser.add_argument("--site-dir", required=True, help="Directory to write the Markdown site.")
    args = parser.parse_args()

    papers = load_papers(Path(args.papers_dir))
    site_dir = Path(args.site_dir)
    paper_site_dir = site_dir / "papers"
    paper_site_dir.mkdir(parents=True, exist_ok=True)
    remove_legacy_site_files(site_dir)

    records = backfill_records(papers, include_site_paths=True)
    summary_records = summarize_records(records)
    payload = build_site_payload(summary_records)
    paper_lookup = {
        str(item.get("paper_id") or ""): item
        for item in records
        if str(item.get("paper_id") or "")
    }

    write_json(site_dir / "paper-neighbors.json", payload)
    write_text(site_dir / "index.md", render_index(payload, paper_lookup))

    for record in records:
        paper_id = str(record.get("paper_id") or "")
        if not paper_id:
            continue
        write_text(paper_site_dir / f"{paper_id}.md", render_paper_page(record))
        write_json(paper_site_dir / f"{paper_id}.json", record)

    print(f"Rendered Markdown site to {site_dir}")
    print(f"Paper count: {len(records)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
