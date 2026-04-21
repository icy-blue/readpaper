#!/usr/bin/env python3
"""Update the local paper registry from normalized paper JSON records."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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


def normalize_text(value: str) -> str:
    text = unicodedata.normalize("NFKC", value or "")
    text = text.replace("∗", " ").replace("*", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_key(value: str) -> str:
    text = normalize_text(value).lower()
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def primary_key(title: str, year: str, venue: str) -> str:
    return f"{normalize_key(title)}::{normalize_key(year)}::{normalize_key(venue)}"


def fallback_key(title: str, year: str) -> str:
    return f"{normalize_key(title)}::{normalize_key(year)}"


def list_paper_files(papers_dir: Path) -> list[Path]:
    if not papers_dir.exists():
        return []
    return sorted(path for path in papers_dir.glob("*.json") if path.is_file())


def ensure_list_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            cleaned = item.strip()
            if cleaned not in result:
                result.append(cleaned)
    return result


def load_record(path: Path) -> dict[str, Any]:
    data = read_json(path, {})
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    title = data.get("title")
    year = data.get("year")
    venue = data.get("venue")
    paper_id = data.get("paper_id")
    if not isinstance(title, str) or not title.strip():
        raise ValueError(f"{path} is missing a valid 'title'.")
    if not isinstance(paper_id, str) or not paper_id.strip():
        raise ValueError(f"{path} is missing a valid 'paper_id'.")
    if not isinstance(venue, str) or not venue.strip():
        venue = "Unknown"
    if isinstance(year, int):
        year_text = str(year)
    elif isinstance(year, str) and year.strip():
        year_text = year.strip()
    else:
        year_text = "unknown"

    source_ids = ensure_list_strings(data.get("source_conversation_ids"))
    record = {
        "paper_id": paper_id.strip(),
        "title": normalize_text(title),
        "year": year_text,
        "venue": normalize_text(venue),
        "dedupe_key": primary_key(title, year_text, venue),
        "fallback_key": fallback_key(title, year_text),
        "source_conversation_ids": source_ids,
        "canonical_url": str(data.get("pdf_url") or ""),
        "record_path": str(path),
        "processed_at": str(data.get("processed_at") or "") or utc_now(),
    }
    return record


def merge_entry(target: dict[str, Any], incoming: dict[str, Any]) -> None:
    target["title"] = incoming["title"]
    target["year"] = incoming["year"]
    target["venue"] = incoming["venue"]
    target["dedupe_key"] = incoming["dedupe_key"]
    target["fallback_key"] = incoming["fallback_key"]
    target["paper_id"] = incoming["paper_id"]
    target["record_path"] = incoming["record_path"]
    target["last_processed"] = incoming["processed_at"]
    if not target.get("first_processed"):
        target["first_processed"] = incoming["processed_at"]
    source_ids = ensure_list_strings(target.get("source_conversation_ids"))
    for source_id in incoming["source_conversation_ids"]:
        if source_id not in source_ids:
            source_ids.append(source_id)
    target["source_conversation_ids"] = source_ids
    if incoming["canonical_url"]:
        target["canonical_url"] = incoming["canonical_url"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Build paper_registry.json from normalized paper records.")
    parser.add_argument("--papers-dir", required=True, help="Directory containing normalized paper JSON files.")
    parser.add_argument("--registry", required=True, help="Path to paper_registry.json.")
    args = parser.parse_args()

    papers_dir = Path(args.papers_dir)
    registry_path = Path(args.registry)
    registry = read_json(registry_path, {"source": "https://translate.icydev.cn", "updated_at": None, "items": []})
    items = registry.setdefault("items", [])
    if not isinstance(items, list):
        raise ValueError("Registry field 'items' must be a list.")

    index: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        for key_name in ("dedupe_key", "fallback_key", "paper_id"):
            value = item.get(key_name)
            if isinstance(value, str) and value.strip():
                index[f"{key_name}:{value.strip()}"] = item

    added = 0
    updated = 0
    for path in list_paper_files(papers_dir):
        record = load_record(path)
        entry = (
            index.get(f"dedupe_key:{record['dedupe_key']}")
            or index.get(f"fallback_key:{record['fallback_key']}")
            or index.get(f"paper_id:{record['paper_id']}")
        )
        if entry is None:
            entry = {
                "paper_id": record["paper_id"],
                "title": record["title"],
                "year": record["year"],
                "venue": record["venue"],
                "dedupe_key": record["dedupe_key"],
                "fallback_key": record["fallback_key"],
                "source_conversation_ids": record["source_conversation_ids"],
                "record_path": record["record_path"],
                "canonical_url": record["canonical_url"],
                "first_processed": record["processed_at"],
                "last_processed": record["processed_at"],
            }
            items.append(entry)
            added += 1
        else:
            updated += 1
        merge_entry(entry, record)
        for key_name in ("dedupe_key", "fallback_key", "paper_id"):
            value = entry.get(key_name)
            if isinstance(value, str) and value.strip():
                index[f"{key_name}:{value.strip()}"] = entry

    items.sort(key=lambda item: (str(item.get("year") or ""), str(item.get("title") or "")), reverse=True)
    registry["updated_at"] = utc_now()
    write_json(registry_path, registry)

    print(f"Loaded {len(list_paper_files(papers_dir))} paper records.")
    print(f"Added {added} registry entries.")
    print(f"Updated {updated} registry entries.")
    print(f"Registry written to {registry_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
