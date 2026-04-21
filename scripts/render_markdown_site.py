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
    write_json,
    write_text,
)


def render_support_line(values: list[str]) -> str:
    return ", ".join(format_support_labels(values)) if values else "暂无"


def render_linked_papers(paper_ids: list[str], paper_lookup: dict[str, dict[str, Any]]) -> str:
    links: list[str] = []
    for paper_id in paper_ids:
        paper = paper_lookup.get(str(paper_id), {})
        title = str(paper.get("title") or paper_id)
        links.append(f'[{title}](papers/{paper_id}.md)')
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
    contrast_notes = ensure_strings(context.get("contrast_notes"))
    if baselines:
        lines.append(f"- {display_label('explicit_baselines')}: " + " / ".join(baselines))
    if contrast_methods:
        lines.append(f"- {display_label('contrast_methods')}: " + " / ".join(contrast_methods))
    if contrast_notes:
        lines.append(f"- {display_label('contrast_notes')}: " + " / ".join(contrast_notes))
    if not baselines and not contrast_methods and not contrast_notes:
        lines.append("- 暂无可计算的对比上下文。")
    lines.append("")
    return lines


def render_neighbor_section(title: str, items: list[dict[str, Any]]) -> list[str]:
    lines = [f"## {title}", ""]
    if not items:
        lines.extend(["- 信号不足，当前库中没有足够可靠的近邻。", ""])
        return lines
    for item in items:
        local_target = Path(str(item.get("paper_path") or "")).name if str(item.get("paper_path") or "") else ""
        label = f"[{item.get('title') or ''}]({local_target})" if local_target else str(item.get("title") or "")
        lines.append(
            f"- {label} | {display_label('score')} {item.get('score') or 0} | {match_source_label(str(item.get('match_source') or 'neighbor'))} | {item.get('reason') or ''}"
        )
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
    tag_filters = payload.get("tag_filters", {}) if isinstance(payload.get("tag_filters"), dict) else {}
    papers = payload.get("papers", []) if isinstance(payload.get("papers"), list) else []
    lines = [
        "# Translate Paper Forest",
        "",
        "- 主入口: [HTML 首页](index.html)",
        f"- 生成时间: {payload.get('generated_at') or ''}",
        f"- 论文总数: {payload.get('paper_count') or 0}",
        "- 当前主流程: 先看单篇论文，再沿任务 / 方法 / 对比方法三个维度展开近邻阅读。",
        "- 旧的全局森林视图已降级为兼容占位页，不再作为主导航。",
        "",
        "## 最近论文",
        "",
    ]
    if papers:
        for paper in papers[:10]:
            paper_id = str(paper.get("paper_id") or "")
            lines.append(
                f"- [{paper.get('title') or paper_id}](papers/{paper_id}.md) | {paper.get('venue') or ''} {paper.get('year') or ''}"
            )
    else:
        lines.append("- 暂无已处理论文。")
    lines.extend(["", "## 导航", "", "- [单篇阅读 HTML](index.html)", ""])
    lines.extend(render_filter_group("按主题筛选", ensure_strings_dicts(tag_filters.get("themes")), paper_lookup))
    lines.extend(render_filter_group("按任务筛选", ensure_strings_dicts(tag_filters.get("tasks")), paper_lookup))
    lines.extend(render_filter_group("按方法筛选", ensure_strings_dicts(tag_filters.get("methods")), paper_lookup))
    return "\n".join(lines) + "\n"


def ensure_strings_dicts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def render_paper_page(record: dict[str, Any]) -> str:
    title = str(record.get("title") or record.get("paper_id") or "Untitled")
    summary = record.get("summary", {}) if isinstance(record.get("summary"), dict) else {}
    method_core = record.get("method_core", {}) if isinstance(record.get("method_core"), dict) else {}
    eval_block = record.get("benchmarks_or_eval", {}) if isinstance(record.get("benchmarks_or_eval"), dict) else {}
    figure_table_index = record.get("figure_table_index", {}) if isinstance(record.get("figure_table_index"), dict) else {}
    inputs_outputs = record.get("inputs_outputs", {}) if isinstance(record.get("inputs_outputs"), dict) else {}
    claims = record.get("key_claims") if isinstance(record.get("key_claims"), list) else []
    neighbors = record.get("paper_neighbors") if isinstance(record.get("paper_neighbors"), dict) else {}

    lines = [
        f"# {title}",
        "",
        f"- HTML 阅读版: [{Path(str(record.get('html_path') or '')).name}]({Path(str(record.get('html_path') or '')).name})",
        f"- {display_label('paper_id')}: {record.get('paper_id') or ''}",
        f"- {display_label('venue')}: {record.get('venue') or ''}",
        f"- {display_label('year')}: {record.get('year') or ''}",
        f"- {display_label('citation_count')}: {record.get('citation_count') or 0}",
        f"- {display_label('pdf_url')}: {record.get('pdf_url') or ''}",
        "",
        "## 一句话结论",
        "",
        str(summary.get("one_liner") or "暂无"),
        "",
    ]

    abstract_summary = str(summary.get("abstract_summary") or "")
    research_value = str(summary.get("research_value") or "")
    if abstract_summary:
        lines.extend(["## 摘要概览", "", abstract_summary, ""])
    if research_value:
        lines.extend(["## 长期价值", "", research_value, ""])

    lines.extend(["## 核心论断", ""])
    if claims:
        for item in claims:
            if not isinstance(item, dict):
                continue
            lines.append(f"- {item.get('claim') or ''}")
            support = ensure_strings(item.get("support"))
            confidence = str(item.get("confidence") or "")
            if support:
                lines.append(f"  支撑: {render_support_line(support)}")
            if confidence:
                lines.append(f"  置信度: {confidence_label(confidence)}")
    else:
        lines.append("- 暂无核心论断。")

    lines.extend(["", "## 方法核心", ""])
    for key in ("problem", "approach", "innovation"):
        value = str(method_core.get(key) or "").strip()
        if value:
            lines.append(f"- {display_label(key)}: {value}")
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
    for key in ("datasets", "metrics", "baselines", "findings"):
        values = ensure_strings(eval_block.get(key))
        if values:
            lines.append(f"- {display_label(key)}: " + " / ".join(values))

    limitations = ensure_strings(record.get("limitations"))
    lines.extend(["", "## 局限", ""])
    if limitations:
        for item in limitations:
            lines.append(f"- {item}")
    else:
        lines.append("- 暂无")

    novelty = ensure_strings(record.get("novelty_type"))
    if novelty:
        lines.extend(["", "## 创新类型", "", "- " + " / ".join(novelty), ""])

    lines.extend(["## 研究标签", ""])
    research_tags = record.get("research_tags", {}) if isinstance(record.get("research_tags"), dict) else {}
    for key in ("themes", "tasks", "methods", "modalities", "representations"):
        values = ensure_strings(research_tags.get(key))
        if values:
            lines.append(f"- {display_label(key)}: " + " / ".join(values))
    lines.append("")

    lines.extend(render_comparison_context(record))
    lines.extend(render_neighbor_section("相似论文：任务维度", ensure_strings_dicts(neighbors.get("task"))))
    lines.extend(render_neighbor_section("相似论文：技术方法维度", ensure_strings_dicts(neighbors.get("method"))))
    lines.extend(render_neighbor_section("相似论文：对比方法维度", ensure_strings_dicts(neighbors.get("comparison"))))

    lines.extend(["## 图表索引", ""])
    figures = figure_table_index.get("figures")
    tables = figure_table_index.get("tables")
    if isinstance(figures, list):
        for item in figures[:12]:
            if isinstance(item, dict):
                lines.append(f"- 图：{item.get('label') or 'Figure'}: {item.get('caption') or ''}")
    if isinstance(tables, list):
        for item in tables[:12]:
            if isinstance(item, dict):
                lines.append(f"- 表：{item.get('label') or 'Table'}: {item.get('caption') or ''}")
    return "\n".join(lines) + "\n"


def render_compat_page(title: str, html_name: str) -> str:
    return "\n".join(
        [
            f"# {title}",
            "",
            f"- HTML 阅读版: [{html_name}]({html_name})",
            "- 该页面已降级为兼容占位页。",
            "- 当前推荐路径: 从首页进入单篇论文，再沿任务 / 方法 / 对比方法三个维度查看近邻。",
            "",
            "## 说明",
            "",
            "全局森林视图不再是主入口。本轮输出重点是单篇论文页与每篇论文的多维近邻。",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Render Markdown site from paper-neighbor-first records.")
    parser.add_argument("--papers-dir", required=True, help="Directory containing normalized paper JSON files.")
    parser.add_argument("--site-dir", required=True, help="Directory to write the Markdown site.")
    args = parser.parse_args()

    papers = load_papers(Path(args.papers_dir))
    site_dir = Path(args.site_dir)
    paper_site_dir = site_dir / "papers"
    paper_site_dir.mkdir(parents=True, exist_ok=True)

    records = backfill_records(papers, include_site_paths=True)
    payload = build_site_payload(records)
    paper_lookup = {
        str(item.get("paper_id") or ""): item
        for item in records
        if str(item.get("paper_id") or "")
    }

    write_json(site_dir / "paper-neighbors.json", payload)
    write_text(site_dir / "index.md", render_index(payload, paper_lookup))
    write_text(site_dir / "theme-map.md", render_compat_page("主题视图", "theme-map.html"))
    write_text(site_dir / "method-map.md", render_compat_page("方法视图", "method-map.html"))
    write_text(site_dir / "timeline.md", render_compat_page("时间视图", "timeline.html"))
    write_text(site_dir / "relationship-graph.md", render_compat_page("关系视图", "relationship-graph.html"))

    for record in records:
        paper_id = str(record.get("paper_id") or "")
        if not paper_id:
            continue
        write_text(paper_site_dir / f"{paper_id}.md", render_paper_page(record))

    print(f"Rendered Markdown site to {site_dir}")
    print(f"Paper count: {len(records)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
