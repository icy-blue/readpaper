#!/usr/bin/env python3
"""Compatibility wrapper for the old neighbor backfill command."""

from __future__ import annotations

import argparse
from pathlib import Path

from build_site_derivatives import main as build_site_derivatives_main


def main() -> int:
    parser = argparse.ArgumentParser(description="Compatibility wrapper for build_site_derivatives.py.")
    parser.add_argument("--papers-dir", required=True, help="Directory containing canonical paper JSON files.")
    parser.add_argument("--site-dir", help="Directory to write derived site payloads.")
    args = parser.parse_args()

    papers_dir = Path(args.papers_dir)
    site_dir = Path(args.site_dir) if args.site_dir else papers_dir.parent / "site"

    print("`backfill_paper_neighbors.py` is deprecated. Building site-derived payloads instead.")
    import sys

    argv = sys.argv
    try:
        sys.argv = [
            "build_site_derivatives.py",
            "--papers-dir",
            str(papers_dir),
            "--site-dir",
            str(site_dir),
        ]
        return build_site_derivatives_main()
    finally:
        sys.argv = argv


if __name__ == "__main__":
    raise SystemExit(main())
