#!/usr/bin/env python3
"""Publish the React single-page site into outputs/site/."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any


INLINE_TOKEN = "__PAPER_NEIGHBORS_DATA__"


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("paper-neighbors.json must contain a JSON object.")
    return data


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_dist_dir() -> Path:
    return repo_root() / "web" / "dist"


def ensure_dist(dist_dir: Path) -> None:
    index_path = dist_dir / "index.html"
    if not index_path.exists():
        raise FileNotFoundError(
            f"Frontend build output not found at {index_path}. Run `npm run build:web` first."
        )


def replace_inline_data(index_html: str, payload: dict[str, Any]) -> str:
    serialized = json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c")
    if INLINE_TOKEN in index_html:
        return index_html.replace(INLINE_TOKEN, serialized)
    script_tag = f'<script id="paper-neighbors-data" type="application/json">{serialized}</script>'
    return index_html.replace("</body>", f"  {script_tag}\n</body>")


def clear_legacy_html(site_dir: Path) -> None:
    for path in site_dir.glob("*.html"):
        if path.name != "index.html":
            path.unlink()

    paper_dir = site_dir / "papers"
    if paper_dir.exists():
        for path in paper_dir.glob("*.html"):
            path.unlink()


def copy_dist(dist_dir: Path, site_dir: Path) -> None:
    for item in dist_dir.iterdir():
        destination = site_dir / item.name
        if destination.exists():
            if destination.is_dir():
                shutil.rmtree(destination)
            else:
                destination.unlink()
        if item.is_dir():
            shutil.copytree(item, destination)
        else:
            shutil.copy2(item, destination)


def publish_site(
    payload: dict[str, Any],
    *,
    dist_dir: Path,
    site_dir: Path,
) -> Path:
    ensure_dist(dist_dir)
    site_dir.mkdir(parents=True, exist_ok=True)
    clear_legacy_html(site_dir)
    copy_dist(dist_dir, site_dir)

    index_path = site_dir / "index.html"
    index_html = index_path.read_text(encoding="utf-8")
    index_path.write_text(replace_inline_data(index_html, payload), encoding="utf-8")
    return index_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish the React SPA to outputs/site.")
    parser.add_argument("--neighbors-json", help="Path to outputs/site/paper-neighbors.json.")
    parser.add_argument("--forest-json", help="Backward-compatible alias for --neighbors-json.")
    parser.add_argument("--output", required=True, help="Path to write the HTML dashboard entry page.")
    parser.add_argument("--dist-dir", help="Path to the built frontend dist directory.")
    args = parser.parse_args()

    input_path = args.neighbors_json or args.forest_json
    if not input_path:
        raise SystemExit("One of --neighbors-json or --forest-json is required.")

    payload = read_json(Path(input_path))
    output_path = Path(args.output)
    dist_dir = Path(args.dist_dir) if args.dist_dir else default_dist_dir()
    index_path = publish_site(payload, dist_dir=dist_dir, site_dir=output_path.parent)

    print(f"Published SPA site to {output_path.parent}")
    print(f"Entry page: {index_path}")
    print(f"Paper count: {payload.get('paper_count') or 0}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
