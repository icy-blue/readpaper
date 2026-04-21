#!/usr/bin/env python3
"""Backfill comparison_context and paper_neighbors into normalized paper JSON files."""

from __future__ import annotations

import argparse
from pathlib import Path

from paper_neighbors import backfill_records, load_papers, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill paper_neighbors into outputs/papers/*.json.")
    parser.add_argument("--papers-dir", required=True, help="Directory containing normalized paper JSON files.")
    args = parser.parse_args()

    papers_dir = Path(args.papers_dir)
    records = load_papers(papers_dir)
    backfilled = backfill_records(records, include_site_paths=False)

    for record in backfilled:
        paper_id = str(record.get("paper_id") or "")
        if not paper_id:
            continue
        write_json(papers_dir / f"{paper_id}.json", record)

    print(f"Backfilled paper neighbors for {len(backfilled)} papers in {papers_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
