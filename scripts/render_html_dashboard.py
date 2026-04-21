#!/usr/bin/env python3
"""Publish the React single-page site into outputs/site/."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("site-index.json must contain a JSON object.")
    return data


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_dist_dir() -> Path:
    return repo_root() / "web" / "dist"


def ensure_dist(dist_dir: Path) -> None:
    index_path = dist_dir / "index.html"
    if not index_path.exists():
        raise FileNotFoundError(f"Frontend build output not found at {index_path}. Run `npm run build:web` first.")


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


def publish_site(dist_dir: Path, site_dir: Path) -> Path:
    ensure_dist(dist_dir)
    site_dir.mkdir(parents=True, exist_ok=True)
    clear_legacy_html(site_dir)
    copy_dist(dist_dir, site_dir)
    return site_dir / "index.html"


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish the React SPA to outputs/site.")
    parser.add_argument("--site-index-json", help="Path to outputs/site/site-index.json.")
    parser.add_argument("--neighbors-json", help="Backward-compatible alias for legacy workflows.")
    parser.add_argument("--output", required=True, help="Path to write the HTML dashboard entry page.")
    parser.add_argument("--dist-dir", help="Path to the built frontend dist directory.")
    args = parser.parse_args()

    input_path = args.site_index_json or args.neighbors_json
    if not input_path:
        raise SystemExit("One of --site-index-json or --neighbors-json is required.")

    payload = read_json(Path(input_path))
    output_path = Path(args.output)
    dist_dir = Path(args.dist_dir) if args.dist_dir else default_dist_dir()
    index_path = publish_site(dist_dir=dist_dir, site_dir=output_path.parent)

    print(f"Published SPA site to {output_path.parent}")
    print(f"Entry page: {index_path}")
    print(f"Paper count: {payload.get('paper_count') or 0}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
