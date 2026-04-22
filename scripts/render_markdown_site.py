#!/usr/bin/env python3
"""Render homepage Markdown plus derived site payloads from canonical papers."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from build_site_derivatives import build_site_payload, load_papers, write_json


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def clear_legacy_paper_markdown(site_dir: Path) -> None:
    paper_dir = site_dir / "papers"
    if not paper_dir.exists():
        return
    for path in paper_dir.glob("*.md"):
        try:
            path.unlink()
        except FileNotFoundError:
            continue


def render_index(payload: dict[str, Any]) -> str:
    papers = payload.get("papers", []) if isinstance(payload.get("papers"), list) else []
    filters = payload.get("filters", {}) if isinstance(payload.get("filters"), dict) else {}
    lines = [
        "# Translate Paper Forest",
        "",
        f"- 生成时间: {payload.get('generated_at') or ''}",
        f"- 论文总数: {payload.get('paper_count') or 0}",
        "- 当前结构: canonical paper records + derived site payloads。",
        "- 阅读策略: 只保留主页，在首页完成检索、筛选与论文详情阅读。",
        "",
        "## 最近论文",
        "",
    ]
    if papers:
        for paper in papers[:10]:
            bibliography = paper.get("bibliography") if isinstance(paper.get("bibliography"), dict) else {}
            lines.append(f"- {bibliography.get('title') or paper.get('id') or ''} | {bibliography.get('venue') or ''} {bibliography.get('year') or ''}")
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
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render homepage Markdown and derived site payloads.")
    parser.add_argument("--papers-dir", required=True, help="Directory containing canonical paper JSON files.")
    parser.add_argument("--site-dir", required=True, help="Directory to write the site.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    papers_dir = Path(args.papers_dir)
    site_dir = Path(args.site_dir)
    site_dir.mkdir(parents=True, exist_ok=True)
    (site_dir / "papers").mkdir(parents=True, exist_ok=True)
    clear_legacy_paper_markdown(site_dir)

    records = load_papers(papers_dir)
    site_payload, detail_payloads = build_site_payload(records)
    write_json(site_dir / "site-index.json", site_payload)
    write_text(site_dir / "index.md", render_index(site_payload))

    for paper_id, detail_payload in detail_payloads.items():
        write_json(site_dir / "papers" / f"{paper_id}.json", detail_payload)

    print(f"Rendered Markdown site for {len(records)} papers into {site_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
