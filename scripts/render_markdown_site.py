#!/usr/bin/env python3
"""Render Markdown site assets from canonical papers and derived site payloads."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from build_site_derivatives import build_site_payload, ensure_strings, load_papers, write_json


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def render_link_lines(bibliography: dict[str, Any]) -> list[str]:
    links = bibliography.get("links") if isinstance(bibliography.get("links"), dict) else {}
    identifiers = bibliography.get("identifiers") if isinstance(bibliography.get("identifiers"), dict) else {}
    lines: list[str] = []
    for key in ("pdf", "project", "code", "data"):
        value = str(links.get(key) or "").strip()
        if value:
            lines.append(f"- {key.upper()}: {value}")
    for key in ("doi", "arxiv"):
        value = str(identifiers.get(key) or "").strip()
        if value:
            lines.append(f"- {key}: {value}")
    return lines


def render_neighbor_section(title: str, items: list[dict[str, Any]]) -> list[str]:
    lines = [f"## {title}", ""]
    if not items:
        lines.extend(["- 暂无足够可靠的近邻。", ""])
        return lines
    for item in items:
        lines.append(
            f"- [{item.get('title') or ''}](../index.html{item.get('route_path') or ''}) | {item.get('reason_short') or item.get('reason') or ''}"
        )
        if item.get("reason"):
            lines.append(f"  说明: {item.get('reason')}")
    lines.append("")
    return lines


def render_index(payload: dict[str, Any]) -> str:
    papers = payload.get("papers", []) if isinstance(payload.get("papers"), list) else []
    filters = payload.get("filters", {}) if isinstance(payload.get("filters"), dict) else {}
    lines = [
        "# Translate Paper Forest",
        "",
        f"- 生成时间: {payload.get('generated_at') or ''}",
        f"- 论文总数: {payload.get('paper_count') or 0}",
        "- 当前结构: canonical paper records + derived site payloads。",
        "- 阅读策略: 首页先判断值不值得读，再进入单篇页看 story / method / evaluation / editorial / comparison。",
        "",
        "## 最近论文",
        "",
    ]
    if papers:
        for paper in papers[:10]:
            bibliography = paper.get("bibliography") if isinstance(paper.get("bibliography"), dict) else {}
            source = paper.get("source") if isinstance(paper.get("source"), dict) else {}
            lines.append(
                f"- [{bibliography.get('title') or paper.get('id') or ''}](index.html{source.get('route_path') or ''}) | {bibliography.get('venue') or ''} {bibliography.get('year') or ''}"
            )
    else:
        lines.append("- 暂无已处理论文。")

    lines.extend(["", "## 快速筛选", ""])
    for key, label in (("themes", "主题"), ("tasks", "任务"), ("methods", "方法")):
        items = filters.get(key) if isinstance(filters.get(key), list) else []
        if items:
            joined = " / ".join(f"{item.get('label')} ({item.get('count')})" for item in items[:12] if isinstance(item, dict))
            lines.append(f"- {label}: {joined}")
        else:
            lines.append(f"- {label}: 暂无")
    lines.append("")
    return "\n".join(lines) + "\n"


def render_paper_page(detail_payload: dict[str, Any]) -> str:
    record = detail_payload.get("canonical") if isinstance(detail_payload.get("canonical"), dict) else {}
    neighbors = detail_payload.get("neighbors") if isinstance(detail_payload.get("neighbors"), dict) else {}
    bibliography = record.get("bibliography") if isinstance(record.get("bibliography"), dict) else {}
    source = record.get("source") if isinstance(record.get("source"), dict) else {}
    story = record.get("story") if isinstance(record.get("story"), dict) else {}
    research_problem = record.get("research_problem") if isinstance(record.get("research_problem"), dict) else {}
    method = record.get("method") if isinstance(record.get("method"), dict) else {}
    evaluation = record.get("evaluation") if isinstance(record.get("evaluation"), dict) else {}
    editorial = record.get("editorial") if isinstance(record.get("editorial"), dict) else {}
    comparison = record.get("comparison") if isinstance(record.get("comparison"), dict) else {}
    conclusion = record.get("conclusion") if isinstance(record.get("conclusion"), dict) else {}
    abstracts = record.get("abstracts") if isinstance(record.get("abstracts"), dict) else {}
    assets = record.get("assets") if isinstance(record.get("assets"), dict) else {}
    claims = record.get("claims") if isinstance(record.get("claims"), list) else []
    relations = record.get("relations") if isinstance(record.get("relations"), list) else []

    lines = [
        f"# {bibliography.get('title') or record.get('id') or 'Untitled'}",
        "",
        f"- 网页阅读版: [index.html{source.get('route_path') or '#/'}](../index.html{source.get('route_path') or '#/'})",
        f"- 作者: {' / '.join(ensure_strings(bibliography.get('authors'))) or '暂无'}",
        f"- venue: {bibliography.get('venue') or ''}",
        f"- 年份: {bibliography.get('year') or ''}",
        "",
        "## Story",
        "",
    ]
    for label, value in (
        ("一句话", story.get("paper_one_liner")),
        ("问题", story.get("problem")),
        ("方法", story.get("method")),
        ("结果", story.get("result")),
    ):
        if isinstance(value, str) and value.strip():
            lines.append(f"- {label}: {value}")
    lines.append("")

    lines.extend(["## 研究问题", ""])
    if research_problem.get("summary"):
        lines.append(f"- 摘要: {research_problem.get('summary')}")
    for item in ensure_strings(research_problem.get("gaps")):
        lines.append(f"- 缺口: {item}")
    if research_problem.get("goal"):
        lines.append(f"- 目标: {research_problem.get('goal')}")
    lines.append("")

    lines.extend(["## 方法", ""])
    if method.get("summary"):
        lines.append(f"- 摘要: {method.get('summary')}")
    for item in ensure_strings(method.get("pipeline_steps")):
        lines.append(f"- 流程: {item}")
    for item in ensure_strings(method.get("innovations")):
        lines.append(f"- 创新: {item}")
    for label, key in (("关键组件", "ingredients"), ("输入", "inputs"), ("输出", "outputs"), ("表示", "representations")):
        values = ensure_strings(method.get(key))
        if values:
            lines.append(f"- {label}: {' / '.join(values)}")
    lines.append("")

    lines.extend(["## 实验", ""])
    if evaluation.get("headline"):
        lines.append(f"- 结论先看: {evaluation.get('headline')}")
    for label, key in (("数据集", "datasets"), ("指标", "metrics"), ("基线", "baselines")):
        values = ensure_strings(evaluation.get(key))
        if values:
            lines.append(f"- {label}: {' / '.join(values)}")
    for item in ensure_strings(evaluation.get("key_findings")):
        lines.append(f"- 发现: {item}")
    if evaluation.get("setup_summary"):
        lines.append(f"- 设置摘要: {evaluation.get('setup_summary')}")
    lines.append("")

    lines.extend(["## 阅读判断", ""])
    for label, value in (
        ("总评", editorial.get("verdict")),
        ("摘要", editorial.get("summary")),
        ("阅读路径", editorial.get("reading_route")),
        ("研究定位", editorial.get("research_position")),
    ):
        if isinstance(value, str) and value.strip():
            lines.append(f"- {label}: {value}")
    for item in ensure_strings(editorial.get("why_read")):
        lines.append(f"- 为什么读: {item}")
    for item in ensure_strings(editorial.get("strengths")):
        lines.append(f"- Strength: {item}")
    for item in ensure_strings(editorial.get("cautions")):
        lines.append(f"- Caution: {item}")
    if editorial.get("graph_worthy") is True:
        lines.append("- 图谱价值: 值得长期保留")
    lines.append("")

    lines.extend(["## 对比线索", ""])
    for item in ensure_strings(evaluation.get("baselines")):
        lines.append(f"- 基线: {item}")
    aspects = comparison.get("aspects") if isinstance(comparison.get("aspects"), list) else []
    for item in aspects:
        if isinstance(item, dict) and item.get("aspect") and item.get("difference"):
            lines.append(f"- {item.get('aspect')}: {item.get('difference')}")
    next_read = ensure_strings(comparison.get("next_read"))
    if next_read:
        lines.append(f"- 下一篇: {' / '.join(next_read)}")
    lines.append("")

    lines.extend(render_neighbor_section("任务近邻", neighbors.get("task") if isinstance(neighbors.get("task"), list) else []))
    lines.extend(render_neighbor_section("方法近邻", neighbors.get("method") if isinstance(neighbors.get("method"), list) else []))
    lines.extend(render_neighbor_section("对比近邻", neighbors.get("comparison") if isinstance(neighbors.get("comparison"), list) else []))

    lines.extend(["## Materials", ""])
    link_lines = render_link_lines(bibliography)
    if link_lines:
        lines.extend(link_lines)
    if abstracts.get("zh"):
        lines.extend(["", "### 中文摘要", "", str(abstracts.get("zh")), ""])
    if abstracts.get("raw"):
        lines.extend(["### 原始摘要", "", str(abstracts.get("raw")), ""])
    if claims:
        lines.extend(["### Claims", ""])
        for claim in claims:
            if not isinstance(claim, dict):
                continue
            lines.append(f"- {claim.get('text') or ''}")
            support = ensure_strings(claim.get("support"))
            if support:
                lines.append(f"  support: {', '.join(support)}")
        lines.append("")
    for group_name, group_key in (("Figures", "figures"), ("Tables", "tables")):
        items = assets.get(group_key) if isinstance(assets.get(group_key), list) else []
        if items:
            lines.extend([f"### {group_name}", ""])
            for item in items:
                if not isinstance(item, dict):
                    continue
                lines.append(
                    f"- {item.get('label') or ''} | {item.get('role') or ''} | {item.get('importance') or ''}: {item.get('caption') or ''}"
                )
            lines.append("")
    if conclusion.get("author"):
        lines.extend(["### 作者结论", "", str(conclusion.get("author")), ""])
    limitations = ensure_strings(conclusion.get("limitations"))
    if limitations:
        lines.extend(["### 局限", ""])
        for item in limitations:
            lines.append(f"- {item}")
        lines.append("")
    if relations:
        lines.extend(["### Relations", ""])
        for item in relations:
            if not isinstance(item, dict):
                continue
            target_kind = str(item.get("target_kind") or "")
            label = str(item.get("label") or item.get("target_paper_id") or item.get("target_semantic_scholar_paper_id") or "")
            description = str(item.get("description") or "").strip()
            confidence = item.get("confidence")
            confidence_text = f" | confidence {confidence:.2f}" if isinstance(confidence, (int, float)) else ""
            if target_kind == "local" and item.get("target_paper_id"):
                target = f"[{label}](../index.html#/paper/{item.get('target_paper_id')})"
            elif target_kind == "external" and item.get("target_url"):
                target = f"[{label}]({item.get('target_url')})"
            else:
                target = label
            lines.append(
                f"- {item.get('type') or ''} [{target_kind or 'unknown'}]: {target}{confidence_text}"
                + (f" | {description}" if description else "")
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render Markdown pages and derived site payloads.")
    parser.add_argument("--papers-dir", required=True, help="Directory containing canonical paper JSON files.")
    parser.add_argument("--site-dir", required=True, help="Directory to write the site.")
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
    write_text(site_dir / "index.md", render_index(site_payload))

    for paper_id, detail_payload in detail_payloads.items():
        write_json(site_dir / "papers" / f"{paper_id}.json", detail_payload)
        write_text(site_dir / "papers" / f"{paper_id}.md", render_paper_page(detail_payload))

    print(f"Rendered Markdown site for {len(records)} papers into {site_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
