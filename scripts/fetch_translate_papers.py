#!/usr/bin/env python3
"""Fetch paper conversations from translate.icydev.cn and stage new raw payloads."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
import urllib.parse
import urllib.request
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_BASE_URL = "https://translate.icydev.cn"
DEFAULT_LIMIT = 20
DEFAULT_PAGE_SIZE = 20
USER_AGENT = "translate-paper-forest/1.0"


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


def fetch_json(base_url: str, route: str, params: dict[str, Any] | None = None) -> Any:
    url = base_url.rstrip("/") + route
    if params:
        query = urllib.parse.urlencode(params, doseq=True)
        url = f"{url}?{query}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        payload = response.read().decode(charset)
    return json.loads(payload)


def normalize_text(value: str) -> str:
    text = unicodedata.normalize("NFKC", value or "")
    text = text.replace("∗", " ").replace("*", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_key(value: str) -> str:
    text = normalize_text(value).lower()
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def slugify(value: str, max_length: int = 80) -> str:
    text = unicodedata.normalize("NFKD", value)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    text = re.sub(r"-{2,}", "-", text)
    if not text:
        text = "paper"
    return text[:max_length].rstrip("-")


def venue_for_record(item: dict[str, Any]) -> str:
    for key in ("venue_abbr", "venue"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return normalize_text(value)
    return "Unknown"


def year_for_record(item: dict[str, Any]) -> str:
    year = item.get("year")
    if isinstance(year, int):
        return str(year)
    if isinstance(year, str) and year.strip():
        return year.strip()
    return "unknown"


def primary_key(title: str, year: str, venue: str) -> str:
    return f"{normalize_key(title)}::{normalize_key(year)}::{normalize_key(venue)}"


def fallback_key(title: str, year: str) -> str:
    return f"{normalize_key(title)}::{normalize_key(year)}"


def stable_paper_id(title: str, year: str, venue: str) -> str:
    slug = slugify(f"{title}-{venue}-{year}", max_length=56)
    digest = hashlib.sha1(primary_key(title, year, venue).encode("utf-8")).hexdigest()[:8]
    return f"{slug}-{digest}"


@dataclass
class Candidate:
    title: str
    year: str
    venue: str
    primary: str
    fallback: str
    paper_id: str
    representative: dict[str, Any]
    conversation_ids: list[str]


def group_candidates(conversations: list[dict[str, Any]]) -> list[Candidate]:
    groups: list[Candidate] = []
    for item in conversations:
        title = normalize_text(str(item.get("title") or "Untitled Paper"))
        year = year_for_record(item)
        venue = venue_for_record(item)
        convo_id = str(item.get("id") or "").strip()
        current_primary = primary_key(title, year, venue)
        current_fallback = fallback_key(title, year)

        match: Candidate | None = None
        for candidate in groups:
            if candidate.primary == current_primary or candidate.fallback == current_fallback:
                match = candidate
                break

        if match is None:
            groups.append(
                Candidate(
                    title=title,
                    year=year,
                    venue=venue,
                    primary=current_primary,
                    fallback=current_fallback,
                    paper_id=stable_paper_id(title, year, venue),
                    representative=item,
                    conversation_ids=[convo_id] if convo_id else [],
                )
            )
            continue

        if convo_id and convo_id not in match.conversation_ids:
            match.conversation_ids.append(convo_id)
        current_created = str(item.get("created_at") or "")
        match_created = str(match.representative.get("created_at") or "")
        if current_created > match_created:
            match.representative = item

    return groups


def load_registry_keys(registry_path: Path) -> tuple[set[str], set[str]]:
    registry = read_json(registry_path, {"items": []})
    items = registry.get("items", [])
    primary_keys: set[str] = set()
    fallback_keys: set[str] = set()
    if not isinstance(items, list):
        return primary_keys, fallback_keys
    for item in items:
        if not isinstance(item, dict):
            continue
        primary = item.get("dedupe_key")
        fallback = item.get("fallback_key")
        if isinstance(primary, str) and primary.strip():
            primary_keys.add(primary.strip())
        if isinstance(fallback, str) and fallback.strip():
            fallback_keys.add(fallback.strip())
    return primary_keys, fallback_keys


def fetch_conversation_page(base_url: str, limit: int, offset: int) -> dict[str, Any]:
    data = fetch_json(base_url, "/conversations", {"limit": limit, "offset": offset})
    if not isinstance(data, dict):
        raise ValueError("Conversation list response must be a JSON object.")
    return data


def fetch_all_conversations(base_url: str, total_limit: int, page_size: int) -> list[dict[str, Any]]:
    offset = 0
    fetched: list[dict[str, Any]] = []
    while len(fetched) < total_limit:
        current_limit = min(page_size, total_limit - len(fetched))
        page = fetch_conversation_page(base_url, current_limit, offset)
        items = page.get("conversations", [])
        if not isinstance(items, list):
            raise ValueError("Conversation list response field 'conversations' must be a list.")
        typed_items = [item for item in items if isinstance(item, dict)]
        fetched.extend(typed_items)
        if not page.get("has_more") or not typed_items:
            break
        offset += len(typed_items)
    return fetched[:total_limit]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch new translate.icydev.cn paper payloads.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Translate platform base URL.")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help="Maximum conversations to inspect.")
    parser.add_argument("--page-size", type=int, default=DEFAULT_PAGE_SIZE, help="Conversation page size.")
    parser.add_argument("--registry", required=True, help="Path to paper_registry.json.")
    parser.add_argument("--manifest", required=True, help="Path to write the fetch manifest JSON.")
    parser.add_argument("--raw-dir", required=True, help="Directory to store raw paper JSON payloads.")
    parser.add_argument("--detail-id", help="Fetch only one specific conversation id.")
    parser.add_argument(
        "--include-known",
        action="store_true",
        help="Include already-known papers instead of restricting to new papers only.",
    )
    return parser.parse_args()


def detail_payload(
    base_url: str,
    paper_id: str,
    primary: str,
    fallback: str,
    conversation_ids: list[str],
    representative: dict[str, Any],
) -> dict[str, Any]:
    selected_id = str(representative.get("id") or "").strip()
    detail = fetch_json(base_url, f"/conversations/{selected_id}")
    if not isinstance(detail, dict):
        raise ValueError(f"Conversation detail for '{selected_id}' must be a JSON object.")
    return {
        "paper_id": paper_id,
        "dedupe_key": primary,
        "fallback_key": fallback,
        "selected_conversation_id": selected_id,
        "source_conversation_ids": conversation_ids,
        "fetched_at": utc_now(),
        "conversation": detail,
    }


def run_detail_mode(args: argparse.Namespace) -> int:
    detail = fetch_json(args.base_url, f"/conversations/{args.detail_id}")
    if not isinstance(detail, dict):
        raise ValueError("Conversation detail response must be a JSON object.")
    payload = {
        "paper_id": stable_paper_id(
            normalize_text(str(detail.get("title") or "Untitled Paper")),
            year_for_record(detail),
            venue_for_record(detail),
        ),
        "dedupe_key": primary_key(
            normalize_text(str(detail.get("title") or "Untitled Paper")),
            year_for_record(detail),
            venue_for_record(detail),
        ),
        "fallback_key": fallback_key(
            normalize_text(str(detail.get("title") or "Untitled Paper")),
            year_for_record(detail),
        ),
        "selected_conversation_id": str(detail.get("id") or ""),
        "source_conversation_ids": [str(detail.get("id") or "")],
        "fetched_at": utc_now(),
        "conversation": detail,
    }
    write_json(Path(args.manifest), payload)
    raw_path = Path(args.raw_dir) / f"{payload['paper_id']}.json"
    write_json(raw_path, payload)
    print(f"Wrote detail payload to {raw_path}")
    return 0


def main() -> int:
    args = parse_args()
    if args.limit <= 0 or args.page_size <= 0:
        raise ValueError("--limit and --page-size must be positive integers.")

    registry_path = Path(args.registry)
    manifest_path = Path(args.manifest)
    raw_dir = Path(args.raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)

    if args.detail_id:
        return run_detail_mode(args)

    config = fetch_json(args.base_url, "/config")
    conversations = fetch_all_conversations(args.base_url, args.limit, args.page_size)
    grouped = group_candidates(conversations)
    known_primary, known_fallback = load_registry_keys(registry_path)

    selected: list[Candidate] = []
    known_count = 0
    for candidate in grouped:
        is_known = candidate.primary in known_primary or candidate.fallback in known_fallback
        if is_known and not args.include_known:
            known_count += 1
            continue
        selected.append(candidate)

    manifest_papers: list[dict[str, Any]] = []
    for candidate in selected:
        payload = detail_payload(
            args.base_url,
            candidate.paper_id,
            candidate.primary,
            candidate.fallback,
            candidate.conversation_ids,
            candidate.representative,
        )
        raw_path = raw_dir / f"{candidate.paper_id}.json"
        write_json(raw_path, payload)
        manifest_papers.append(
            {
                "paper_id": candidate.paper_id,
                "title": candidate.title,
                "year": candidate.year,
                "venue": candidate.venue,
                "dedupe_key": candidate.primary,
                "fallback_key": candidate.fallback,
                "selected_conversation_id": payload["selected_conversation_id"],
                "source_conversation_ids": candidate.conversation_ids,
                "raw_path": str(raw_path),
            }
        )

    manifest = OrderedDict(
        [
            ("generated_at", utc_now()),
            ("base_url", args.base_url.rstrip("/")),
            ("config", config),
            (
                "stats",
                {
                    "conversation_count": len(conversations),
                    "grouped_paper_count": len(grouped),
                    "known_paper_count": known_count,
                    "new_paper_count": len(manifest_papers),
                },
            ),
            ("papers", manifest_papers),
        ]
    )
    write_json(manifest_path, manifest)

    print(f"Fetched {len(conversations)} conversations.")
    print(f"Collapsed to {len(grouped)} canonical papers.")
    print(f"Selected {len(manifest_papers)} papers for processing.")
    print(f"Manifest written to {manifest_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        raise SystemExit(130)
