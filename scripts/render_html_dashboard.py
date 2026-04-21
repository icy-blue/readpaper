#!/usr/bin/env python3
"""Render a static HTML reading site from paper-neighbors.json."""

from __future__ import annotations

import argparse
import json
from html import escape
from pathlib import Path
from typing import Any

from paper_neighbors import (
    confidence_label,
    display_label,
    ensure_strings,
    format_support_labels,
    match_source_label,
    short_title,
)


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("paper-neighbors.json must contain a JSON object.")
    return data


def ensure_dicts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def render_bullet_list(values: list[str], empty_text: str = "暂无") -> str:
    if not values:
        return f"<p class='empty'>{escape(empty_text)}</p>"
    return "<ul class='bullet-list'>" + "".join(f"<li>{escape(value)}</li>" for value in values) + "</ul>"


def render_chips(values: list[str], extra_class: str = "") -> str:
    if not values:
        return "<span class='empty'>暂无</span>"
    class_name = "chip"
    if extra_class:
        class_name += f" {extra_class}"
    return "".join(f"<span class='{class_name}'>{escape(value)}</span>" for value in values)


def render_kv_rows(rows: list[tuple[str, str]]) -> str:
    return "<dl class='kv-grid'>" + "".join(
        "<div>"
        f"<dt>{escape(label)}</dt>"
        f"<dd>{escape(value)}</dd>"
        "</div>"
        for label, value in rows
        if value
    ) + "</dl>"


def render_stat_cards(payload: dict[str, Any]) -> str:
    tag_filters = payload.get("tag_filters", {}) if isinstance(payload.get("tag_filters"), dict) else {}
    cards = [
        ("论文数", str(payload.get("paper_count") or 0)),
        ("主题标签", str(len(ensure_dicts(tag_filters.get("themes"))))),
        ("任务标签", str(len(ensure_dicts(tag_filters.get("tasks"))))),
        ("方法标签", str(len(ensure_dicts(tag_filters.get("methods"))))),
    ]
    return "".join(
        "<div class='card'>"
        f"<div class='card-label'>{escape(label)}</div>"
        f"<div class='card-value'>{escape(value)}</div>"
        "</div>"
        for label, value in cards
    )


def render_paper_card(paper: dict[str, Any]) -> str:
    summary = paper.get("summary", {}) if isinstance(paper.get("summary"), dict) else {}
    one_liner = str(summary.get("one_liner") or "")
    return (
        "<article class='paper-card'>"
        f"<h3><a href='{escape(str(paper.get('html_path') or ''))}'>{escape(str(paper.get('title') or paper.get('paper_id') or 'Untitled'))}</a></h3>"
        f"<div class='meta'>{escape(str(paper.get('venue') or ''))} {escape(str(paper.get('year') or ''))}</div>"
        f"<p>{escape(one_liner or '暂无一句话结论。')}</p>"
        "<div class='paper-actions'>"
        f"<a href='{escape(str(paper.get('html_path') or ''))}'>HTML</a>"
        f"<a href='{escape(str(paper.get('paper_path') or ''))}'>Markdown</a>"
        "</div>"
        "</article>"
    )


def render_recent_papers(papers: list[dict[str, Any]], limit: int = 12) -> str:
    if not papers:
        return "<section class='panel'><h2>最近论文</h2><p class='empty'>暂无已处理论文。</p></section>"
    html = ["<section class='panel'><h2>最近论文</h2><div class='paper-grid'>"]
    for paper in papers[:limit]:
        html.append(render_paper_card(paper))
    html.append("</div></section>")
    return "".join(html)


def render_filter_section(title: str, items: list[dict[str, Any]], paper_lookup: dict[str, dict[str, Any]]) -> str:
    if not items:
        return f"<section class='panel'><h2>{escape(title)}</h2><p class='empty'>暂无可筛选标签。</p></section>"
    rows = [f"<section class='panel'><h2>{escape(title)}</h2><div class='stack'>"]
    for item in items:
        rows.append("<article class='cluster-card'>")
        rows.append(
            "<div class='cluster-head'>"
            f"<h3>{escape(str(item.get('label') or ''))}</h3>"
            f"<span class='cluster-count'>{escape(str(item.get('count') or 0))} 篇</span>"
            "</div>"
        )
        rows.append("<div class='paper-link-grid'>")
        for paper_id in ensure_strings(item.get("paper_ids")):
            paper = paper_lookup.get(paper_id, {})
            rows.append(
                f"<a class='paper-pill' href='{escape(str(paper.get('html_path') or f'papers/{paper_id}.html'))}'>{escape(str(paper.get('title') or paper_id))}</a>"
            )
        rows.append("</div></article>")
    rows.append("</div></section>")
    return "".join(rows)


def render_claims(claims: list[dict[str, Any]]) -> str:
    if not claims:
        return "<p class='empty'>暂无核心论断。</p>"
    rows = ["<div class='stack'>"]
    for item in claims:
        rows.append("<article class='claim-card'>")
        rows.append(f"<p>{escape(str(item.get('claim') or ''))}</p>")
        support = format_support_labels(ensure_strings(item.get("support")))
        if support:
            rows.append(f"<div class='chip-row'>{render_chips(support, 'chip-soft')}</div>")
        confidence = str(item.get("confidence") or "")
        if confidence:
            rows.append(f"<div class='meta'>置信度：{escape(confidence_label(confidence))}</div>")
        rows.append("</article>")
    rows.append("</div>")
    return "".join(rows)


def render_method_core(method_core: dict[str, Any]) -> str:
    if not method_core:
        return "<p class='empty'>暂无方法核心。</p>"
    rows: list[tuple[str, str]] = []
    for key in ("problem", "approach", "innovation"):
        value = str(method_core.get(key) or "").strip()
        if value:
            rows.append((display_label(key), value))
    html = render_kv_rows(rows) if rows else "<p class='empty'>暂无研究问题、核心思路或主要创新。</p>"
    for key in ("ingredients", "representation", "supervision", "differences"):
        values = ensure_strings(method_core.get(key))
        if values:
            html += f"<h3>{escape(display_label(key))}</h3>{render_bullet_list(values)}"
    return html


def render_io_block(io_block: dict[str, Any]) -> str:
    if not io_block:
        return "<p class='empty'>暂无输入输出。</p>"
    html = ""
    for key in ("inputs", "outputs", "modalities"):
        values = ensure_strings(io_block.get(key))
        if values:
            html += f"<h3>{escape(display_label(key))}</h3>{render_bullet_list(values)}"
    return html or "<p class='empty'>暂无输入输出。</p>"


def render_eval_block(eval_block: dict[str, Any]) -> str:
    if not eval_block:
        return "<p class='empty'>暂无评估快照。</p>"
    html = ""
    for key in ("datasets", "metrics", "baselines", "findings"):
        values = ensure_strings(eval_block.get(key))
        if values:
            html += f"<h3>{escape(display_label(key))}</h3>{render_bullet_list(values)}"
    return html or "<p class='empty'>暂无评估快照。</p>"


def render_tag_groups(tags: dict[str, Any]) -> str:
    if not tags:
        return "<p class='empty'>暂无研究标签。</p>"
    rows = []
    for key in ("themes", "tasks", "methods", "modalities", "representations"):
        values = ensure_strings(tags.get(key))
        if values:
            rows.append(
                "<div class='tag-group'>"
                f"<h3>{escape(display_label(key))}</h3>"
                f"<div class='chip-row'>{render_chips(values)}</div>"
                "</div>"
            )
    return "".join(rows) if rows else "<p class='empty'>暂无研究标签。</p>"


def render_comparison_context(context: dict[str, Any]) -> str:
    baselines = ensure_strings(context.get("explicit_baselines"))
    contrast_methods = ensure_strings(context.get("contrast_methods"))
    contrast_notes = ensure_strings(context.get("contrast_notes"))
    rows = ["<div class='stack'>"]
    if baselines:
        rows.append(f"<article class='edge-card'><h3>{escape(display_label('explicit_baselines'))}</h3>")
        rows.append(f"<div class='chip-row'>{render_chips(baselines)}</div></article>")
    if contrast_methods:
        rows.append(f"<article class='edge-card'><h3>{escape(display_label('contrast_methods'))}</h3>")
        rows.append(f"<div class='chip-row'>{render_chips(contrast_methods)}</div></article>")
    if contrast_notes:
        rows.append(f"<article class='edge-card'><h3>{escape(display_label('contrast_notes'))}</h3>")
        rows.append(render_bullet_list(contrast_notes))
        rows.append("</article>")
    if not baselines and not contrast_methods and not contrast_notes:
        rows.append("<p class='empty'>暂无可计算的对比上下文。</p>")
    rows.append("</div>")
    return "".join(rows)


def render_neighbor_cards(title: str, items: list[dict[str, Any]]) -> str:
    if not items:
        return f"<section class='panel reading-panel'><h2>{escape(title)}</h2><p class='empty'>信号不足，当前库中没有足够可靠的近邻。</p></section>"
    rows = [f"<section class='panel reading-panel'><h2>{escape(title)}</h2><div class='stack'>"]
    for item in items:
        rows.append("<article class='edge-card'>")
        rows.append(
            f"<h3><a href='{escape(Path(str(item.get('html_path') or '')).name)}'>{escape(str(item.get('title') or ''))}</a></h3>"
        )
        rows.append(
            f"<div class='meta'>{escape(display_label('score'))} {escape(str(item.get('score') or 0))} · {escape(match_source_label(str(item.get('match_source') or 'neighbor')))}</div>"
        )
        rows.append(f"<p>{escape(str(item.get('reason') or ''))}</p>")
        shared_signals = item.get("shared_signals") if isinstance(item.get("shared_signals"), dict) else {}
        for key, values in shared_signals.items():
            cleaned = ensure_strings(values)
            if cleaned:
                rows.append(
                    f"<div class='bridge-meta'><strong>{escape(display_label(str(key)))}</strong><div class='chip-row'>{render_chips(cleaned, 'chip-soft')}</div></div>"
                )
        rows.append("</article>")
    rows.append("</div></section>")
    return "".join(rows)


def render_figure_table_index(payload: dict[str, Any]) -> str:
    figures = payload.get("figures")
    tables = payload.get("tables")
    html = ""
    if isinstance(figures, list) and figures:
        html += "<h3>Figures</h3><ul class='bullet-list'>" + "".join(
            f"<li><strong>图：{escape(str(item.get('label') or 'Figure'))}</strong>: {escape(str(item.get('caption') or ''))}</li>"
            for item in figures[:12]
            if isinstance(item, dict)
        ) + "</ul>"
    if isinstance(tables, list) and tables:
        html += "<h3>Tables</h3><ul class='bullet-list'>" + "".join(
            f"<li><strong>表：{escape(str(item.get('label') or 'Table'))}</strong>: {escape(str(item.get('caption') or ''))}</li>"
            for item in tables[:12]
            if isinstance(item, dict)
        ) + "</ul>"
    return html or "<p class='empty'>暂无图表索引。</p>"


def render_paper_navigation(papers: list[dict[str, Any]], current_index: int) -> str:
    prev_paper = papers[current_index - 1] if current_index > 0 else None
    next_paper = papers[current_index + 1] if current_index + 1 < len(papers) else None
    rows = ["<section class='panel'><h2>导航</h2><div class='paper-actions'>"]
    rows.append("<a href='../index.html'>返回首页</a>")
    if prev_paper:
        rows.append(f"<a href='{escape(str(prev_paper.get('paper_id') or ''))}.html'>上一篇</a>")
    if next_paper:
        rows.append(f"<a href='{escape(str(next_paper.get('paper_id') or ''))}.html'>下一篇</a>")
    rows.append("</div></section>")
    return "".join(rows)


def render_home_page_content(payload: dict[str, Any], paper_lookup: dict[str, dict[str, Any]]) -> str:
    papers = ensure_dicts(payload.get("papers"))
    tag_filters = payload.get("tag_filters", {}) if isinstance(payload.get("tag_filters"), dict) else {}
    return (
        "<section class='panel'>"
        "<h2>阅读重心</h2>"
        "<p>当前首页只承担入口职责：先找到论文，再进入单篇页面，沿任务、技术方法、对比方法三个维度查看近邻。</p>"
        f"<div class='cards'>{render_stat_cards(payload)}</div>"
        "</section>"
        + render_recent_papers(papers)
        + render_filter_section("按主题筛选", ensure_dicts(tag_filters.get("themes")), paper_lookup)
        + render_filter_section("按任务筛选", ensure_dicts(tag_filters.get("tasks")), paper_lookup)
        + render_filter_section("按方法筛选", ensure_dicts(tag_filters.get("methods")), paper_lookup)
    )


def render_compat_page_content(title: str) -> str:
    return (
        "<section class='panel reading-panel'>"
        f"<h2>{escape(title)}</h2>"
        "<p>该页面已降级为兼容占位页，不再承载主阅读流程。</p>"
        "<p>请从首页进入单篇论文详情页，再沿任务、技术方法、对比方法三个维度查看近邻。</p>"
        "</section>"
    )


def render_paper_page_content(paper: dict[str, Any], papers: list[dict[str, Any]], current_index: int) -> str:
    summary = paper.get("summary", {}) if isinstance(paper.get("summary"), dict) else {}
    metadata = [
        (display_label("paper_id"), str(paper.get("paper_id") or "")),
        (display_label("venue"), str(paper.get("venue") or "")),
        (display_label("year"), str(paper.get("year") or "")),
        (display_label("citation_count"), str(paper.get("citation_count") or 0)),
        (display_label("translate_created_at"), str(paper.get("translate_created_at") or "")),
    ]
    if str(paper.get("pdf_url") or ""):
        metadata.append((display_label("pdf_url"), str(paper.get("pdf_url") or "")))

    abstract_summary = str(summary.get("abstract_summary") or "")
    research_value = str(summary.get("research_value") or "")
    novelty_type = ensure_strings(paper.get("novelty_type"))
    neighbors = paper.get("paper_neighbors") if isinstance(paper.get("paper_neighbors"), dict) else {}

    blocks = [
        render_paper_navigation(papers, current_index),
        "<section class='panel reading-panel'>"
        "<div class='section-head'>"
        f"<h2>{escape(str(summary.get('one_liner') or '一句话结论'))}</h2>"
        "<p>单篇页现在是主入口，优先服务于近邻阅读和后续建森林前的局部比较。</p>"
        "</div>"
        f"{render_kv_rows(metadata)}"
        "<div class='paper-actions'>"
        f"<a href='{escape(Path(str(paper.get('paper_path') or '')).name)}'>查看 Markdown</a>"
        + (
            f"<a href='{escape(str(paper.get('pdf_url') or ''))}'>打开 PDF</a>"
            if str(paper.get("pdf_url") or "")
            else ""
        )
        + "</div>"
        "</section>",
        "<section class='panel reading-panel'><h2>一句话结论</h2>"
        f"<p class='lead'>{escape(str(summary.get('one_liner') or '暂无'))}</p>"
        "</section>",
        "<section class='panel reading-panel'><h2>核心论断</h2>"
        f"{render_claims(ensure_dicts(paper.get('key_claims')))}"
        "</section>",
    ]

    if abstract_summary:
        blocks.append(
            "<section class='panel reading-panel'><h2>摘要概览</h2>"
            f"<p>{escape(abstract_summary)}</p></section>"
        )
    if research_value:
        blocks.append(
            "<section class='panel reading-panel'><h2>长期价值</h2>"
            f"<p>{escape(research_value)}</p></section>"
        )

    blocks.extend(
        [
            "<section class='panel reading-panel'><h2>方法核心</h2>"
            f"{render_method_core(paper.get('method_core') if isinstance(paper.get('method_core'), dict) else {})}"
            "</section>",
            "<section class='panel reading-panel'><h2>输入输出</h2>"
            f"{render_io_block(paper.get('inputs_outputs') if isinstance(paper.get('inputs_outputs'), dict) else {})}"
            "</section>",
            "<section class='panel reading-panel'><h2>评估快照</h2>"
            f"{render_eval_block(paper.get('benchmarks_or_eval') if isinstance(paper.get('benchmarks_or_eval'), dict) else {})}"
            "</section>",
            "<section class='grid-two'>"
            "<section class='panel reading-panel'><h2>局限</h2>"
            f"{render_bullet_list(ensure_strings(paper.get('limitations')), '暂无局限记录。')}"
            "</section>"
            "<section class='panel reading-panel'><h2>研究标签</h2>"
            f"{render_tag_groups(paper.get('research_tags') if isinstance(paper.get('research_tags'), dict) else {})}"
            + (
                f"<h3>创新类型</h3><div class='chip-row'>{render_chips(novelty_type)}</div>"
                if novelty_type
                else ""
            )
            + "</section>"
            "</section>",
            "<section class='grid-two'>"
            "<section class='panel reading-panel'><h2>对比上下文</h2>"
            f"{render_comparison_context(paper.get('comparison_context') if isinstance(paper.get('comparison_context'), dict) else {})}"
            "</section>"
            "<section class='panel reading-panel'><h2>图表索引</h2>"
            f"{render_figure_table_index(paper.get('figure_table_index') if isinstance(paper.get('figure_table_index'), dict) else {})}"
            "</section>"
            "</section>",
            render_neighbor_cards("相似论文：任务维度", ensure_dicts(neighbors.get("task"))),
            render_neighbor_cards("相似论文：技术方法维度", ensure_dicts(neighbors.get("method"))),
            render_neighbor_cards("相似论文：对比方法维度", ensure_dicts(neighbors.get("comparison"))),
        ]
    )
    return "".join(blocks)


def nav_html(current: str, depth: int) -> str:
    prefix = "../" * depth
    class_name = "nav-link is-active" if current == "index" else "nav-link"
    return (
        "<nav class='top-nav'>"
        f"<a class='{class_name}' href='{escape(prefix + 'index.html')}'>首页</a>"
        "</nav>"
    )


def page_template(
    title: str,
    description: str,
    body_html: str,
    *,
    current: str,
    markdown_href: str,
    generated_at: str,
    depth: int = 0,
) -> str:
    prefix = "../" * depth
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)} · Translate Paper Forest</title>
  <style>
    :root {{
      --bg: #f4efe4;
      --panel: rgba(255, 251, 243, 0.88);
      --panel-strong: #fffaf1;
      --text: #1d2f2b;
      --muted: #6d776d;
      --accent: #204d46;
      --accent-2: #8a5a2b;
      --line: rgba(32, 77, 70, 0.12);
      --chip: rgba(32, 77, 70, 0.08);
      --accent-soft: rgba(138, 90, 43, 0.1);
      --shadow: 0 24px 60px rgba(29, 47, 43, 0.08);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", serif;
      background:
        radial-gradient(circle at top left, rgba(138, 90, 43, 0.14), transparent 32%),
        linear-gradient(180deg, #f8f2e8 0%, var(--bg) 100%);
      color: var(--text);
    }}
    a {{ color: var(--accent); }}
    .shell {{
      max-width: 1220px;
      margin: 0 auto;
      padding: 28px 18px 54px;
    }}
    .hero {{
      background: linear-gradient(135deg, rgba(255, 250, 241, 0.95), rgba(245, 236, 221, 0.9));
      border: 1px solid rgba(138, 90, 43, 0.14);
      border-radius: 28px;
      padding: 28px;
      box-shadow: var(--shadow);
    }}
    .eyebrow {{
      font-size: 12px;
      letter-spacing: 0.16em;
      text-transform: uppercase;
      color: var(--accent-2);
      margin-bottom: 10px;
    }}
    h1, h2, h3 {{
      margin: 0;
      font-weight: 600;
      line-height: 1.15;
    }}
    h1 {{ font-size: clamp(34px, 5vw, 56px); max-width: 12ch; }}
    h2 {{ font-size: 28px; }}
    h3 {{ font-size: 18px; }}
    p {{
      margin: 0;
      line-height: 1.75;
      color: var(--text);
    }}
    .hero-copy {{
      margin-top: 14px;
      max-width: 68ch;
      font-size: 17px;
      color: var(--muted);
    }}
    .meta-line {{
      margin-top: 16px;
      color: var(--muted);
      font-size: 14px;
    }}
    .top-nav {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 18px;
    }}
    .nav-link {{
      display: inline-flex;
      align-items: center;
      padding: 8px 12px;
      border-radius: 999px;
      background: rgba(32, 77, 70, 0.08);
      text-decoration: none;
    }}
    .nav-link.is-active {{
      background: var(--accent);
      color: #fffaf1;
    }}
    .content {{
      display: grid;
      gap: 18px;
      margin-top: 20px;
    }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 24px;
      padding: 22px;
      box-shadow: var(--shadow);
    }}
    .reading-panel {{
      max-width: 980px;
    }}
    .cards {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 12px;
      margin-top: 16px;
    }}
    .card {{
      padding: 16px;
      border-radius: 18px;
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.66);
    }}
    .card-label {{
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
    }}
    .card-value {{
      margin-top: 10px;
      font-size: 30px;
      color: var(--accent);
    }}
    .paper-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 14px;
      margin-top: 14px;
    }}
    .paper-card, .cluster-card, .edge-card, .claim-card {{
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 16px;
      background: rgba(255, 255, 255, 0.7);
    }}
    .paper-card p, .edge-card p {{
      margin-top: 10px;
    }}
    .paper-actions {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 14px;
    }}
    .paper-actions a {{
      padding: 8px 12px;
      border-radius: 999px;
      background: rgba(32, 77, 70, 0.08);
      text-decoration: none;
    }}
    .meta {{
      margin-top: 8px;
      font-size: 14px;
      color: var(--muted);
    }}
    .cluster-head {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 12px;
    }}
    .cluster-count {{
      font-size: 13px;
      color: var(--accent-2);
      white-space: nowrap;
    }}
    .paper-link-grid, .chip-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 12px;
    }}
    .chip, .paper-pill {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 7px 11px;
      border-radius: 999px;
      background: var(--chip);
      color: var(--text);
      text-decoration: none;
      font-size: 14px;
      border: 1px solid rgba(120, 103, 72, 0.08);
    }}
    .chip-soft {{
      background: var(--accent-soft);
    }}
    .stack {{
      display: grid;
      gap: 12px;
    }}
    .bridge-meta {{
      display: grid;
      gap: 10px;
      margin-top: 12px;
    }}
    .bridge-meta strong {{
      font-size: 13px;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    .section-head {{
      margin-bottom: 14px;
    }}
    .kv-grid {{
      display: grid;
      gap: 14px;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      margin: 0;
    }}
    .kv-grid div {{
      padding: 12px 14px;
      border-radius: 16px;
      background: rgba(255,255,255,0.68);
      border: 1px solid var(--line);
    }}
    .kv-grid dt {{
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--muted);
    }}
    .kv-grid dd {{
      margin: 8px 0 0;
      line-height: 1.55;
      word-break: break-word;
    }}
    .grid-two {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 18px;
    }}
    .lead {{
      font-size: 20px;
    }}
    .tag-group + .tag-group {{
      margin-top: 16px;
    }}
    .tag-group h3, .reading-panel h3 {{
      margin-bottom: 10px;
      font-size: 15px;
      color: var(--accent-2);
      letter-spacing: 0.03em;
      text-transform: uppercase;
    }}
    .bullet-list {{
      margin: 0;
      padding-left: 20px;
      line-height: 1.8;
    }}
    .empty {{
      color: var(--muted);
    }}
    @media (max-width: 900px) {{
      .grid-two {{
        grid-template-columns: 1fr;
      }}
      .shell {{
        padding: 18px 14px 42px;
      }}
      .hero {{
        padding: 22px;
      }}
      .card-value {{
        font-size: 26px;
      }}
    }}
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <div class="eyebrow">Translate Paper Forest</div>
      <h1>{escape(title)}</h1>
      <p class="hero-copy">{escape(description)}</p>
      <div class="meta-line">生成时间：{escape(generated_at)} · 主入口：<a href="{escape(prefix + 'index.html')}">HTML</a> / <a href="{escape(markdown_href)}">Markdown</a></div>
      {nav_html(current, depth)}
    </section>
    <section class="content">
      {body_html}
    </section>
  </main>
</body>
</html>
"""


def write_page(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a static HTML site from paper-neighbors.json.")
    parser.add_argument("--neighbors-json", help="Path to outputs/site/paper-neighbors.json.")
    parser.add_argument("--forest-json", help="Backward-compatible alias for --neighbors-json.")
    parser.add_argument("--output", required=True, help="Path to write the HTML dashboard entry page.")
    args = parser.parse_args()

    input_path = args.neighbors_json or args.forest_json
    if not input_path:
        raise SystemExit("One of --neighbors-json or --forest-json is required.")

    payload = read_json(Path(input_path))
    output_path = Path(args.output)
    site_dir = output_path.parent
    site_dir.mkdir(parents=True, exist_ok=True)

    papers = ensure_dicts(payload.get("papers"))
    paper_lookup = {
        str(item.get("paper_id") or ""): item
        for item in papers
        if str(item.get("paper_id") or "")
    }
    generated_at = str(payload.get("generated_at") or "")

    write_page(
        site_dir / "index.html",
        page_template(
            "Translate Paper Forest",
            "首页只负责找论文，真正的阅读与比较都在单篇页面里完成。",
            render_home_page_content(payload, paper_lookup),
            current="index",
            markdown_href="index.md",
            generated_at=generated_at,
        ),
    )

    for name, title in (
        ("theme-map.html", "主题视图"),
        ("method-map.html", "方法视图"),
        ("timeline.html", "时间视图"),
        ("relationship-graph.html", "关系视图"),
    ):
        current = name.replace(".html", "").split("-")[0]
        write_page(
            site_dir / name,
            page_template(
                title,
                "该页面保留为兼容入口，真正的阅读流程已经回到单篇论文页。",
                render_compat_page_content(title),
                current=current,
                markdown_href=name.replace(".html", ".md"),
                generated_at=generated_at,
            ),
        )

    paper_site_dir = site_dir / "papers"
    paper_site_dir.mkdir(parents=True, exist_ok=True)
    for index, paper in enumerate(papers):
        paper_id = str(paper.get("paper_id") or "")
        if not paper_id:
            continue
        write_page(
            paper_site_dir / f"{paper_id}.html",
            page_template(
                short_title(str(paper.get("title") or paper_id), 54),
                "单篇页优先呈现摘要、方法、评估和多维近邻，方便后续再回到全局森林。",
                render_paper_page_content(paper, papers, index),
                current="paper",
                markdown_href=f"{paper_id}.md",
                generated_at=generated_at,
                depth=1,
            ),
        )

    print(f"Rendered HTML site to {site_dir}")
    print(f"Paper count: {len(papers)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
