#!/usr/bin/env python3
"""Assemble paper records from raw translate payloads and meta artifacts."""

from __future__ import annotations

import argparse
import json
import os
import re
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXTRACTOR_CONFIG = REPO_ROOT / "extractor-config.json"

SEMANTIC_SCHOLAR_BASE_URL = "https://api.semanticscholar.org/graph/v1"
SEMANTIC_SCHOLAR_FIELDS = [
    "title",
    "authors",
    "year",
    "venue",
    "citationCount",
    "abstract",
    "externalIds",
    "openAccessPdf",
    "url",
]
USER_AGENT = "translate-paper-forest/1.0"

URL_PATTERN = re.compile(r"https?://[^\s)>\]\"']+")
DOI_PATTERN = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)
GITHUB_PATTERN = re.compile(r"https?://(?:www\.)?github\.com/[^\s)>\]\"']+", re.IGNORECASE)
LABEL_SENTENCE_PREFIXES = (
    "我们",
    "本文",
    "该方法",
    "该工作",
    "适合",
    "通过",
    "实验",
    "结果",
    "为了",
)
LABEL_SENTENCE_PREFIXES_EN = (
    "we ",
    "our ",
    "this paper",
    "the paper",
    "it ",
)


@dataclass
class SemanticScholarPaper:
    title: str
    authors: list[str]
    year: int | None
    venue: str | None
    citation_count: int | None
    abstract_raw: str | None
    doi: str | None
    arxiv: str | None
    open_access_pdf: str | None


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
    return re.sub(r"\s+", " ", text).strip()


def normalize_title(value: str) -> str:
    text = normalize_text(value)
    return re.sub(r"\s*[†‡*]+$", "", text).strip()


def normalize_key(value: str) -> str:
    text = normalize_text(value).lower()
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def compact_markdown(text: str) -> str:
    content = text.replace("\r\n", "\n").strip()
    return re.sub(r"\n{3,}", "\n\n", content).strip()


def strip_heading(text: str) -> str:
    lines = compact_markdown(text).splitlines()
    while lines and lines[0].lstrip().startswith("#"):
        lines.pop(0)
        if lines and not lines[0].strip():
            lines.pop(0)
    return compact_markdown("\n".join(lines))


def ensure_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        if isinstance(item, str):
            cleaned = normalize_text(item)
            if cleaned and cleaned not in result:
                result.append(cleaned)
    return result


def semantic_scholar_headers() -> dict[str, str]:
    headers = {"User-Agent": USER_AGENT}
    api_key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY", "").strip()
    if api_key:
        headers["x-api-key"] = api_key
    return headers


def fetch_json(url: str, headers: dict[str, str] | None = None) -> Any:
    request = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(request, timeout=20) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        payload = response.read().decode(charset)
    return json.loads(payload)


def semantic_scholar_fields(include_external_ids: bool) -> str:
    if include_external_ids:
        return ",".join(SEMANTIC_SCHOLAR_FIELDS)
    return ",".join(field for field in SEMANTIC_SCHOLAR_FIELDS if field != "externalIds")


def build_semantic_scholar_url(route: str, params: dict[str, Any]) -> str:
    return f"{SEMANTIC_SCHOLAR_BASE_URL}{route}?{urllib.parse.urlencode(params, doseq=True)}"


def parse_external_ids(payload: dict[str, Any]) -> tuple[str | None, str | None]:
    external_ids = payload.get("externalIds")
    if not isinstance(external_ids, dict):
        return None, None
    doi = external_ids.get("DOI") or external_ids.get("doi")
    arxiv = external_ids.get("ArXiv") or external_ids.get("ARXIV") or external_ids.get("arXiv")
    doi_text = normalize_text(str(doi)) if isinstance(doi, str) and doi.strip() else None
    arxiv_text = normalize_text(str(arxiv)) if isinstance(arxiv, str) and arxiv.strip() else None
    return doi_text, arxiv_text


def parse_semantic_scholar_candidate(payload: dict[str, Any]) -> SemanticScholarPaper:
    authors = payload.get("authors")
    author_names: list[str] = []
    if isinstance(authors, list):
        for author in authors:
            if isinstance(author, dict) and isinstance(author.get("name"), str):
                cleaned = normalize_text(str(author["name"]))
                if cleaned and cleaned not in author_names:
                    author_names.append(cleaned)

    open_access_pdf = payload.get("openAccessPdf")
    pdf_url = None
    if isinstance(open_access_pdf, dict) and isinstance(open_access_pdf.get("url"), str) and str(open_access_pdf["url"]).strip():
        pdf_url = str(open_access_pdf["url"]).strip()

    citation_count = payload.get("citationCount")
    year = payload.get("year")
    venue = payload.get("venue")
    abstract_raw = payload.get("abstract")
    doi, arxiv = parse_external_ids(payload)
    return SemanticScholarPaper(
        title=normalize_title(str(payload.get("title") or "")),
        authors=author_names,
        year=year if isinstance(year, int) else None,
        venue=normalize_text(str(venue)) if isinstance(venue, str) and venue.strip() else None,
        citation_count=citation_count if isinstance(citation_count, int) else None,
        abstract_raw=normalize_text(str(abstract_raw)) if isinstance(abstract_raw, str) and abstract_raw.strip() else None,
        doi=doi,
        arxiv=arxiv,
        open_access_pdf=pdf_url,
    )


def semantic_scholar_title_match(title: str, year: int | None, *, fetcher: Any = fetch_json) -> SemanticScholarPaper | None:
    headers = semantic_scholar_headers()
    normalized_title = normalize_key(title)
    if not normalized_title:
        return None

    routes = [
        ("/paper/search/match", {"query": title}),
        ("/paper/search", {"query": title, "limit": 5}),
    ]
    for route, base_params in routes:
        payload: Any | None = None
        for include_external_ids in (True, False):
            params = dict(base_params)
            params["fields"] = semantic_scholar_fields(include_external_ids)
            url = build_semantic_scholar_url(route, params)
            try:
                payload = fetcher(url, headers)
                break
            except urllib.error.HTTPError as error:
                if error.code == 400 and include_external_ids:
                    continue
                payload = None
                break
            except Exception:
                payload = None
                break
        if payload is None:
            continue

        candidates: list[dict[str, Any]] = []
        if isinstance(payload, dict) and isinstance(payload.get("data"), list):
            candidates = [item for item in payload["data"] if isinstance(item, dict)]
        elif isinstance(payload, dict):
            candidates = [payload]

        for candidate in candidates:
            parsed = parse_semantic_scholar_candidate(candidate)
            if normalize_key(parsed.title) != normalized_title:
                continue
            if year is not None and parsed.year is not None and parsed.year != year:
                continue
            return parsed
    return None


def message_unit_id(message: dict[str, Any]) -> str:
    translation_status = message.get("translation_status")
    if isinstance(translation_status, dict) and isinstance(translation_status.get("current_unit_id"), str):
        return normalize_text(str(translation_status["current_unit_id"]))
    return ""


def visible_bot_messages(conversation: dict[str, Any]) -> list[dict[str, Any]]:
    messages = conversation.get("messages")
    if not isinstance(messages, list):
        return []

    result: list[dict[str, Any]] = []
    for message in messages:
        if not isinstance(message, dict):
            continue
        if message.get("message_kind") != "bot_reply":
            continue
        if message.get("visible_to_user") is False:
            continue
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            continue
        result.append(message)
    return result


def section_bucket(unit_id: str) -> str:
    lowered = unit_id.lower()
    if lowered == "abstract":
        return "abstract"
    if "introduction" in lowered or "引言" in lowered:
        return "introduction"
    if "method" in lowered or "approach" in lowered or "framework" in lowered:
        return "method"
    if "experiment" in lowered or "evaluation" in lowered or "result" in lowered:
        return "experiments"
    if "conclusion" in lowered or "discussion" in lowered:
        return "conclusion"
    if lowered.startswith("appendix") or re.match(r"^[a-z]\.", lowered):
        return "appendix"
    return "body"


def extract_sections(conversation: dict[str, Any]) -> dict[str, list[str]]:
    buckets: dict[str, list[str]] = {
        "abstract": [],
        "introduction": [],
        "method": [],
        "experiments": [],
        "conclusion": [],
        "appendix": [],
        "body": [],
    }
    for message in visible_bot_messages(conversation):
        bucket = section_bucket(message_unit_id(message))
        content = strip_heading(str(message.get("content") or ""))
        if content:
            buckets[bucket].append(content)
    return buckets


def extract_urls(conversation: dict[str, Any]) -> list[str]:
    urls: list[str] = []
    for message in visible_bot_messages(conversation):
        for value in URL_PATTERN.findall(str(message.get("content") or "")):
            cleaned = value.rstrip(".,;")
            if cleaned not in urls:
                urls.append(cleaned)
    return urls


def classify_links(urls: list[str], title: str, abstract_zh: str, semantic_paper: SemanticScholarPaper | None) -> dict[str, str | None]:
    links: dict[str, str | None] = {
        "pdf": None,
        "doi": semantic_paper.doi if semantic_paper else None,
        "arxiv": semantic_paper.arxiv if semantic_paper else None,
        "project": None,
        "code": None,
        "data": None,
    }

    for url in urls:
        lowered = url.lower()
        if not links["code"] and ("github.com" in lowered or "gitlab.com" in lowered):
            links["code"] = url
            continue
        if not links["data"] and any(token in lowered for token in ("dataset", "data", "huggingface.co/datasets", "kaggle")):
            links["data"] = url
            continue
        if not links["doi"]:
            match = DOI_PATTERN.search(url)
            if match:
                links["doi"] = match.group(0)
                continue
        if not links["arxiv"] and "arxiv.org" in lowered:
            links["arxiv"] = url
            continue
        if not links["project"] and not GITHUB_PATTERN.search(url):
            links["project"] = url

    abstract_and_title = f"{title}\n{abstract_zh}"
    if not links["code"]:
        match = GITHUB_PATTERN.search(abstract_and_title)
        if match:
            links["code"] = match.group(0)
    return links


def validate_figure_table_items(errors: list[str], path: str, value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        errors.append(f"{path} must be a list")
        return []
    result: list[dict[str, str]] = []
    for index, item in enumerate(value):
        record = validate_record(errors, f"{path}[{index}]", item)
        label = validate_string_field(errors, f"{path}[{index}].label", record.get("label"), required=True) or ""
        caption = validate_string_field(errors, f"{path}[{index}].caption", record.get("caption"), required=True) or ""
        role = validate_string_field(errors, f"{path}[{index}].role", record.get("role"), required=True) or ""
        importance = validate_string_field(errors, f"{path}[{index}].importance", record.get("importance"), required=True) or ""
        if role not in {"method_overview", "qualitative_result", "quantitative_result", "ablation", "failure_case"}:
            errors.append(f"{path}[{index}].role must be a supported reading role")
        if importance not in {"high", "medium", "low"}:
            errors.append(f"{path}[{index}].importance must be high, medium, or low")
        result.append({"label": label, "caption": caption, "role": role, "importance": importance})
    return result


def read_extractor_version(config_path: Path) -> str:
    payload = read_json(config_path, {})
    if not isinstance(payload, dict):
        raise ValueError(f"{config_path} must contain a JSON object.")
    version = payload.get("extractor_version")
    if not isinstance(version, str) or not version.strip():
        raise ValueError(f"{config_path} is missing extractor_version.")
    return normalize_text(version)


def meta_artifact_is_current(meta_path: Path, extractor_version: str) -> bool:
    payload = read_json(meta_path, {})
    if not isinstance(payload, dict):
        return False
    version = payload.get("extractor_version")
    return isinstance(version, str) and normalize_text(version) == normalize_text(extractor_version)


def looks_like_sentence_label(value: str) -> bool:
    text = normalize_text(value)
    lowered = text.lower()
    if text.startswith(LABEL_SENTENCE_PREFIXES):
        return True
    return lowered.startswith(LABEL_SENTENCE_PREFIXES_EN)


def build_validation_error(meta_path: Path, errors: list[str]) -> ValueError:
    preview = "; ".join(errors[:6])
    if len(errors) > 6:
        preview += f"; and {len(errors) - 6} more"
    return ValueError(f"Invalid meta artifact {meta_path}: {preview}")


def normalized_optional_string(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        cleaned = normalize_text(value)
        return cleaned or None
    return None


def validate_string_field(
    errors: list[str],
    path: str,
    value: Any,
    *,
    max_chars: int | None = None,
    required: bool = False,
) -> str | None:
    cleaned = normalized_optional_string(value)
    if cleaned is None:
        if required:
            errors.append(f"{path} must be a non-empty string")
        return None
    if max_chars is not None and len(cleaned) > max_chars:
        errors.append(f"{path} exceeds {max_chars} chars")
    return cleaned


def validate_bool_field(errors: list[str], path: str, value: Any) -> bool:
    if not isinstance(value, bool):
        errors.append(f"{path} must be a boolean")
        return False
    return value


def validate_string_list(
    errors: list[str],
    path: str,
    value: Any,
    *,
    max_chars: int,
    max_items: int,
    label_like: bool = False,
) -> list[str]:
    if not isinstance(value, list):
        errors.append(f"{path} must be a list")
        return []
    result: list[str] = []
    if len(value) > max_items:
        errors.append(f"{path} exceeds {max_items} items")
    for index, item in enumerate(value[:max_items]):
        cleaned = validate_string_field(errors, f"{path}[{index}]", item, max_chars=max_chars, required=True)
        if not cleaned:
            continue
        if label_like and looks_like_sentence_label(cleaned):
            errors.append(f"{path}[{index}] must be a short label, not a sentence")
        if cleaned not in result:
            result.append(cleaned)
    return result


def validate_string_array_without_limit(errors: list[str], path: str, value: Any) -> list[str]:
    if not isinstance(value, list):
        errors.append(f"{path} must be a list")
        return []
    result: list[str] = []
    for index, item in enumerate(value):
        cleaned = validate_string_field(errors, f"{path}[{index}]", item, required=True)
        if cleaned and cleaned not in result:
            result.append(cleaned)
    return result


def validate_record(errors: list[str], path: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{path} must be an object")
        return {}
    return value


def validate_choice_field(errors: list[str], path: str, value: Any, choices: set[str]) -> str:
    cleaned = validate_string_field(errors, path, value, required=True)
    if not cleaned:
        return next(iter(choices))
    if cleaned not in choices:
        errors.append(f"{path} must be one of {sorted(choices)}")
    return cleaned


def validate_summary_block(errors: list[str], value: Any) -> dict[str, Any]:
    block = validate_record(errors, "meta.summary", value)
    research_value = validate_record(errors, "meta.summary.research_value", block.get("research_value"))
    return {
        "one_liner": validate_string_field(errors, "meta.summary.one_liner", block.get("one_liner"), max_chars=110, required=True) or "",
        "abstract_summary": validate_string_field(errors, "meta.summary.abstract_summary", block.get("abstract_summary"), max_chars=150),
        "research_value": {
            "summary": validate_string_field(errors, "meta.summary.research_value.summary", research_value.get("summary"), max_chars=72),
            "points": validate_string_list(
                errors,
                "meta.summary.research_value.points",
                research_value.get("points"),
                max_chars=64,
                max_items=3,
            ),
        },
        "worth_long_term_graph": validate_bool_field(errors, "meta.summary.worth_long_term_graph", block.get("worth_long_term_graph")),
    }


def validate_reading_digest(errors: list[str], value: Any) -> dict[str, Any]:
    block = validate_record(errors, "meta.reading_digest", value)
    positioning = validate_record(errors, "meta.reading_digest.positioning", block.get("positioning"))
    narrative = validate_record(errors, "meta.reading_digest.narrative", block.get("narrative"))
    return {
        "value_statement": validate_string_field(errors, "meta.reading_digest.value_statement", block.get("value_statement"), max_chars=84),
        "best_for": validate_string_field(errors, "meta.reading_digest.best_for", block.get("best_for"), max_chars=72),
        "why_read": validate_string_list(
            errors,
            "meta.reading_digest.why_read",
            block.get("why_read"),
            max_chars=64,
            max_items=3,
        ),
        "recommended_route": validate_choice_field(
            errors,
            "meta.reading_digest.recommended_route",
            block.get("recommended_route"),
            {"method", "evaluation", "comparison", "overview"},
        ),
        "positioning": {
            "task": validate_string_list(errors, "meta.reading_digest.positioning.task", positioning.get("task"), max_chars=28, max_items=4, label_like=True),
            "modality": validate_string_list(
                errors,
                "meta.reading_digest.positioning.modality",
                positioning.get("modality"),
                max_chars=24,
                max_items=4,
                label_like=True,
            ),
            "method": validate_string_list(errors, "meta.reading_digest.positioning.method", positioning.get("method"), max_chars=28, max_items=4, label_like=True),
            "novelty": validate_string_list(errors, "meta.reading_digest.positioning.novelty", positioning.get("novelty"), max_chars=24, max_items=4, label_like=True),
        },
        "narrative": {
            "problem": validate_string_field(errors, "meta.reading_digest.narrative.problem", narrative.get("problem"), max_chars=90),
            "method": validate_string_field(errors, "meta.reading_digest.narrative.method", narrative.get("method"), max_chars=90),
            "result": validate_string_field(errors, "meta.reading_digest.narrative.result", narrative.get("result"), max_chars=90),
        },
        "result_headline": validate_string_field(errors, "meta.reading_digest.result_headline", block.get("result_headline"), max_chars=96),
    }


def validate_storyline(errors: list[str], value: Any) -> dict[str, Any]:
    block = validate_record(errors, "meta.storyline", value)
    return {
        "problem": validate_string_field(errors, "meta.storyline.problem", block.get("problem"), max_chars=84),
        "method": validate_string_field(errors, "meta.storyline.method", block.get("method"), max_chars=84),
        "outcome": validate_string_field(errors, "meta.storyline.outcome", block.get("outcome"), max_chars=84),
    }


def validate_research_problem(errors: list[str], value: Any) -> dict[str, Any]:
    block = validate_record(errors, "meta.research_problem", value)
    return {
        "summary": validate_string_field(errors, "meta.research_problem.summary", block.get("summary"), max_chars=100),
        "gaps": validate_string_list(errors, "meta.research_problem.gaps", block.get("gaps"), max_chars=84, max_items=4),
        "goal": validate_string_field(errors, "meta.research_problem.goal", block.get("goal"), max_chars=100),
    }


def validate_claim_items(errors: list[str], value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        errors.append("meta.key_claims must be a list")
        return []
    if len(value) > 5:
        errors.append("meta.key_claims exceeds 5 items")
    result: list[dict[str, Any]] = []
    for index, item in enumerate(value[:5]):
        record = validate_record(errors, f"meta.key_claims[{index}]", item)
        support = validate_string_array_without_limit(errors, f"meta.key_claims[{index}].support", record.get("support"))
        result.append(
            {
                "claim": validate_string_field(errors, f"meta.key_claims[{index}].claim", record.get("claim"), max_chars=120, required=True) or "",
                "type": validate_string_field(errors, f"meta.key_claims[{index}].type", record.get("type"), max_chars=24, required=True) or "method",
                "support": support,
                "confidence": validate_string_field(errors, f"meta.key_claims[{index}].confidence", record.get("confidence"), max_chars=16) or "medium",
            }
        )
        if not support:
            errors.append(f"meta.key_claims[{index}].support must contain grounded evidence")
    return result


def validate_method_core(errors: list[str], value: Any) -> dict[str, Any]:
    block = validate_record(errors, "meta.method_core", value)
    return {
        "approach_summary": validate_string_field(errors, "meta.method_core.approach_summary", block.get("approach_summary"), max_chars=110),
        "pipeline_steps": validate_string_list(errors, "meta.method_core.pipeline_steps", block.get("pipeline_steps"), max_chars=105, max_items=4),
        "innovations": validate_string_list(errors, "meta.method_core.innovations", block.get("innovations"), max_chars=90, max_items=4),
        "ingredients": validate_string_list(errors, "meta.method_core.ingredients", block.get("ingredients"), max_chars=32, max_items=6, label_like=True),
        "representation": validate_string_list(
            errors,
            "meta.method_core.representation",
            block.get("representation"),
            max_chars=32,
            max_items=6,
            label_like=True,
        ),
        "supervision": validate_string_list(errors, "meta.method_core.supervision", block.get("supervision"), max_chars=48, max_items=4),
        "differences": validate_string_list(errors, "meta.method_core.differences", block.get("differences"), max_chars=90, max_items=4),
    }


def validate_inputs_outputs(errors: list[str], value: Any) -> dict[str, Any]:
    block = validate_record(errors, "meta.inputs_outputs", value)
    return {
        "inputs": validate_string_list(errors, "meta.inputs_outputs.inputs", block.get("inputs"), max_chars=28, max_items=6, label_like=True),
        "outputs": validate_string_list(errors, "meta.inputs_outputs.outputs", block.get("outputs"), max_chars=28, max_items=6, label_like=True),
        "modalities": validate_string_list(errors, "meta.inputs_outputs.modalities", block.get("modalities"), max_chars=24, max_items=6, label_like=True),
    }


def validate_benchmarks(errors: list[str], value: Any) -> dict[str, Any]:
    block = validate_record(errors, "meta.benchmarks_or_eval", value)
    return {
        "datasets": validate_string_list(errors, "meta.benchmarks_or_eval.datasets", block.get("datasets"), max_chars=30, max_items=8, label_like=True),
        "metrics": validate_string_list(errors, "meta.benchmarks_or_eval.metrics", block.get("metrics"), max_chars=20, max_items=8, label_like=True),
        "baselines": validate_string_list(errors, "meta.benchmarks_or_eval.baselines", block.get("baselines"), max_chars=28, max_items=8, label_like=True),
        "findings": validate_string_list(errors, "meta.benchmarks_or_eval.findings", block.get("findings"), max_chars=90, max_items=4),
        "best_results": validate_string_list(errors, "meta.benchmarks_or_eval.best_results", block.get("best_results"), max_chars=90, max_items=4),
        "experiment_setup_summary": validate_string_field(
            errors,
            "meta.benchmarks_or_eval.experiment_setup_summary",
            block.get("experiment_setup_summary"),
            max_chars=140,
        ),
    }


def validate_editor_note(errors: list[str], value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    block = validate_record(errors, "meta.editor_note", value)
    return {
        "summary": validate_string_field(errors, "meta.editor_note.summary", block.get("summary"), max_chars=120),
        "points": validate_string_list(errors, "meta.editor_note.points", block.get("points"), max_chars=90, max_items=3),
    }


def validate_editorial_review(errors: list[str], value: Any) -> dict[str, Any]:
    block = validate_record(errors, "meta.editorial_review", value)
    verdict = validate_string_field(errors, "meta.editorial_review.verdict", block.get("verdict"), max_chars=16)
    if verdict and verdict not in {"值得精读", "值得浏览", "只记结论"}:
        errors.append("meta.editorial_review.verdict must be 值得精读, 值得浏览, 只记结论, or null")
    return {
        "verdict": verdict,
        "strengths": validate_string_list(errors, "meta.editorial_review.strengths", block.get("strengths"), max_chars=80, max_items=4),
        "cautions": validate_string_list(errors, "meta.editorial_review.cautions", block.get("cautions"), max_chars=80, max_items=4),
        "research_position": validate_string_field(errors, "meta.editorial_review.research_position", block.get("research_position"), max_chars=84),
        "next_read_hint": validate_string_field(errors, "meta.editorial_review.next_read_hint", block.get("next_read_hint"), max_chars=60),
    }


def validate_research_tags(errors: list[str], value: Any) -> dict[str, Any]:
    block = validate_record(errors, "meta.research_tags", value)
    return {
        "themes": validate_string_list(errors, "meta.research_tags.themes", block.get("themes"), max_chars=28, max_items=8, label_like=True),
        "tasks": validate_string_list(errors, "meta.research_tags.tasks", block.get("tasks"), max_chars=28, max_items=8, label_like=True),
        "methods": validate_string_list(errors, "meta.research_tags.methods", block.get("methods"), max_chars=28, max_items=8, label_like=True),
        "modalities": validate_string_list(errors, "meta.research_tags.modalities", block.get("modalities"), max_chars=24, max_items=6, label_like=True),
        "representations": validate_string_list(
            errors,
            "meta.research_tags.representations",
            block.get("representations"),
            max_chars=28,
            max_items=6,
            label_like=True,
        ),
    }


def validate_topics(errors: list[str], value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        errors.append("meta.topics must be a list")
        return []
    result: list[dict[str, str]] = []
    for index, item in enumerate(value):
        record = validate_record(errors, f"meta.topics[{index}]", item)
        slug = validate_string_field(errors, f"meta.topics[{index}].slug", record.get("slug"), required=True) or ""
        name = validate_string_field(errors, f"meta.topics[{index}].name", record.get("name"), required=True) or ""
        role = validate_string_field(errors, f"meta.topics[{index}].role", record.get("role"), required=True) or ""
        result.append({"slug": slug, "name": name, "role": role})
    return result


def validate_retrieval_profile(errors: list[str], value: Any) -> dict[str, Any]:
    block = validate_record(errors, "meta.retrieval_profile", value)
    return {
        "problem_spaces": validate_string_array_without_limit(errors, "meta.retrieval_profile.problem_spaces", block.get("problem_spaces")),
        "task_axes": validate_string_array_without_limit(errors, "meta.retrieval_profile.task_axes", block.get("task_axes")),
        "approach_axes": validate_string_array_without_limit(errors, "meta.retrieval_profile.approach_axes", block.get("approach_axes")),
        "input_axes": validate_string_array_without_limit(errors, "meta.retrieval_profile.input_axes", block.get("input_axes")),
        "output_axes": validate_string_array_without_limit(errors, "meta.retrieval_profile.output_axes", block.get("output_axes")),
        "modality_axes": validate_string_array_without_limit(errors, "meta.retrieval_profile.modality_axes", block.get("modality_axes")),
        "comparison_axes": validate_string_array_without_limit(errors, "meta.retrieval_profile.comparison_axes", block.get("comparison_axes")),
    }


def validate_comparison_context(errors: list[str], value: Any) -> dict[str, Any]:
    block = validate_record(errors, "meta.comparison_context", value)
    aspects_value = block.get("comparison_aspects")
    aspects: list[dict[str, str]] = []
    if not isinstance(aspects_value, list):
        errors.append("meta.comparison_context.comparison_aspects must be a list")
    else:
        for index, item in enumerate(aspects_value[:8]):
            record = validate_record(errors, f"meta.comparison_context.comparison_aspects[{index}]", item)
            aspects.append(
                {
                    "aspect": validate_string_field(
                        errors,
                        f"meta.comparison_context.comparison_aspects[{index}].aspect",
                        record.get("aspect"),
                        max_chars=28,
                        required=True,
                    )
                    or "",
                    "difference": validate_string_field(
                        errors,
                        f"meta.comparison_context.comparison_aspects[{index}].difference",
                        record.get("difference"),
                        max_chars=96,
                        required=True,
                    )
                    or "",
                }
            )
    return {
        "explicit_baselines": validate_string_list(
            errors,
            "meta.comparison_context.explicit_baselines",
            block.get("explicit_baselines"),
            max_chars=28,
            max_items=8,
            label_like=True,
        ),
        "contrast_methods": validate_string_list(
            errors,
            "meta.comparison_context.contrast_methods",
            block.get("contrast_methods"),
            max_chars=28,
            max_items=8,
            label_like=True,
        ),
        "comparison_aspects": aspects,
        "recommended_next_read": validate_string_field(
            errors,
            "meta.comparison_context.recommended_next_read",
            block.get("recommended_next_read"),
            max_chars=36,
        ),
    }


def validate_paper_relations(errors: list[str], value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        errors.append("meta.paper_relations must be a list")
        return []
    result: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        record = validate_record(errors, f"meta.paper_relations[{index}]", item)
        confidence = record.get("confidence")
        if confidence is not None and not isinstance(confidence, (int, float)):
            errors.append(f"meta.paper_relations[{index}].confidence must be a number or null")
        result.append(
            {
                "target_paper_id": validate_string_field(errors, f"meta.paper_relations[{index}].target_paper_id", record.get("target_paper_id"), required=True) or "",
                "relation_type": validate_string_field(errors, f"meta.paper_relations[{index}].relation_type", record.get("relation_type"), required=True) or "",
                "description": validate_string_field(errors, f"meta.paper_relations[{index}].description", record.get("description"), required=True) or "",
                "confidence": float(confidence) if isinstance(confidence, (int, float)) else None,
            }
        )
    return result


def validate_figure_table_index(errors: list[str], value: Any) -> dict[str, Any]:
    block = validate_record(errors, "meta.figure_table_index", value)
    return {
        "figures": validate_figure_table_items(errors, "meta.figure_table_index.figures", block.get("figures")),
        "tables": validate_figure_table_items(errors, "meta.figure_table_index.tables", block.get("tables")),
    }


def validate_meta_payload(meta_path: Path, payload: Any, paper_id: str, extractor_version: str) -> dict[str, Any]:
    errors: list[str] = []
    artifact = validate_record(errors, "artifact", payload)

    artifact_paper_id = validate_string_field(errors, "artifact.paper_id", artifact.get("paper_id"), required=True)
    artifact_version = validate_string_field(errors, "artifact.extractor_version", artifact.get("extractor_version"), required=True)
    source_conversation_id = validate_string_field(errors, "artifact.source_conversation_id", artifact.get("source_conversation_id"), required=True)
    source_semantic_updated_at = validate_string_field(errors, "artifact.source_semantic_updated_at", artifact.get("source_semantic_updated_at"))
    extracted_at = validate_string_field(errors, "artifact.extracted_at", artifact.get("extracted_at"), required=True)
    meta = validate_record(errors, "artifact.meta", artifact.get("meta"))

    if artifact_paper_id and artifact_paper_id != paper_id:
        errors.append("artifact.paper_id does not match the raw payload paper_id")
    if artifact_version and normalize_text(artifact_version) != normalize_text(extractor_version):
        errors.append("artifact.extractor_version does not match extractor-config.json")

    validated_meta = {
        "summary": validate_summary_block(errors, meta.get("summary")),
        "reading_digest": validate_reading_digest(errors, meta.get("reading_digest")),
        "storyline": validate_storyline(errors, meta.get("storyline")),
        "research_problem": validate_research_problem(errors, meta.get("research_problem")),
        "core_contributions": validate_string_list(errors, "meta.core_contributions", meta.get("core_contributions"), max_chars=90, max_items=4),
        "key_claims": validate_claim_items(errors, meta.get("key_claims")),
        "method_core": validate_method_core(errors, meta.get("method_core")),
        "inputs_outputs": validate_inputs_outputs(errors, meta.get("inputs_outputs")),
        "benchmarks_or_eval": validate_benchmarks(errors, meta.get("benchmarks_or_eval")),
        "author_conclusion": validate_string_field(errors, "meta.author_conclusion", meta.get("author_conclusion"), max_chars=180),
        "editor_note": validate_editor_note(errors, meta.get("editor_note")),
        "editorial_review": validate_editorial_review(errors, meta.get("editorial_review")),
        "limitations": validate_string_list(errors, "meta.limitations", meta.get("limitations"), max_chars=90, max_items=4),
        "novelty_type": validate_string_list(errors, "meta.novelty_type", meta.get("novelty_type"), max_chars=24, max_items=4, label_like=True),
        "research_tags": validate_research_tags(errors, meta.get("research_tags")),
        "topics": validate_topics(errors, meta.get("topics")),
        "retrieval_profile": validate_retrieval_profile(errors, meta.get("retrieval_profile")),
        "comparison_context": validate_comparison_context(errors, meta.get("comparison_context")),
        "paper_relations": validate_paper_relations(errors, meta.get("paper_relations")),
        "figure_table_index": validate_figure_table_index(errors, meta.get("figure_table_index")),
    }

    if errors:
        raise build_validation_error(meta_path, errors)

    return {
        "paper_id": artifact_paper_id,
        "extractor_version": artifact_version,
        "source_conversation_id": source_conversation_id,
        "source_semantic_updated_at": source_semantic_updated_at,
        "extracted_at": extracted_at,
        "meta": validated_meta,
    }


def paper_neighbor_defaults() -> dict[str, list[dict[str, Any]]]:
    return {"task": [], "method": [], "comparison": []}


def normalize_record(raw_payload: dict[str, Any], semantic_paper: SemanticScholarPaper | None, meta_artifact: dict[str, Any]) -> dict[str, Any]:
    conversation = raw_payload.get("conversation")
    if not isinstance(conversation, dict):
        raise ValueError("Raw payload must include a conversation object.")

    paper_id = normalize_text(str(raw_payload.get("paper_id") or ""))
    if not paper_id:
        raise ValueError("Raw payload must include paper_id.")

    title = normalize_title(str(conversation.get("title") or paper_id))
    source_conversation_ids = ensure_strings(raw_payload.get("source_conversation_ids"))
    if not source_conversation_ids:
        conversation_id = conversation.get("id")
        if isinstance(conversation_id, str) and conversation_id.strip():
            source_conversation_ids = [conversation_id.strip()]

    sections = extract_sections(conversation)
    abstract_zh = sections["abstract"][0] if sections["abstract"] else None
    meta = meta_artifact["meta"]

    links = classify_links(extract_urls(conversation), title, abstract_zh or "", semantic_paper)
    pdf_url = conversation.get("pdf_url")
    if isinstance(pdf_url, str) and pdf_url.strip():
        links["pdf"] = pdf_url.strip()
    elif semantic_paper and semantic_paper.open_access_pdf:
        links["pdf"] = semantic_paper.open_access_pdf

    year = conversation.get("year")
    if not isinstance(year, int):
        year = semantic_paper.year if semantic_paper else None
    venue = conversation.get("venue_abbr") or conversation.get("venue")
    venue_text = normalize_text(str(venue)) if isinstance(venue, str) and venue else None
    if not venue_text and semantic_paper and semantic_paper.venue:
        venue_text = semantic_paper.venue

    citation_count = conversation.get("citation_count")
    if not isinstance(citation_count, int):
        citation_count = semantic_paper.citation_count if semantic_paper else None

    return {
        "paper_id": paper_id,
        "source_conversation_ids": source_conversation_ids,
        "title": title,
        "authors": semantic_paper.authors if semantic_paper else [],
        "year": year,
        "venue": venue_text or "Unknown",
        "citation_count": citation_count,
        "links": links,
        "abstract_raw": semantic_paper.abstract_raw if semantic_paper else None,
        "abstract_zh": abstract_zh,
        "summary": meta["summary"],
        "reading_digest": meta["reading_digest"],
        "storyline": meta["storyline"],
        "research_problem": meta["research_problem"],
        "core_contributions": meta["core_contributions"],
        "key_claims": meta["key_claims"],
        "method_core": meta["method_core"],
        "inputs_outputs": meta["inputs_outputs"],
        "benchmarks_or_eval": meta["benchmarks_or_eval"],
        "author_conclusion": meta["author_conclusion"],
        "editor_note": meta["editor_note"],
        "editorial_review": meta["editorial_review"],
        "limitations": meta["limitations"],
        "novelty_type": meta["novelty_type"],
        "research_tags": meta["research_tags"],
        "topics": meta["topics"],
        "retrieval_profile": meta["retrieval_profile"],
        "comparison_context": meta["comparison_context"],
        "paper_neighbors": paper_neighbor_defaults(),
        "paper_relations": meta["paper_relations"],
        "figure_table_index": meta["figure_table_index"],
    }


def merge_existing_enrichment(record: dict[str, Any], existing_record: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(existing_record, dict):
        return record

    merged = dict(record)
    existing_authors = ensure_strings(existing_record.get("authors"))
    if not ensure_strings(merged.get("authors")) and existing_authors:
        merged["authors"] = existing_authors

    existing_abstract_raw = normalize_text(str(existing_record.get("abstract_raw") or ""))
    if not merged.get("abstract_raw") and existing_abstract_raw:
        merged["abstract_raw"] = existing_abstract_raw

    existing_citation_count = existing_record.get("citation_count")
    if merged.get("citation_count") is None and isinstance(existing_citation_count, int):
        merged["citation_count"] = existing_citation_count

    existing_links = existing_record.get("links")
    current_links = merged.get("links")
    if isinstance(existing_links, dict) and isinstance(current_links, dict):
        merged_links = dict(current_links)
        for key in ("doi", "arxiv", "project", "code", "data"):
            if not merged_links.get(key) and isinstance(existing_links.get(key), str) and str(existing_links.get(key)).strip():
                merged_links[key] = str(existing_links.get(key)).strip()
        merged["links"] = merged_links
    return merged


def normalize_raw_file(
    raw_path: Path,
    *,
    meta_path: Path,
    extractor_version: str,
    fetcher: Any = fetch_json,
    existing_record: dict[str, Any] | None = None,
) -> dict[str, Any]:
    raw_payload = read_json(raw_path, {})
    if not isinstance(raw_payload, dict):
        raise ValueError(f"{raw_path} must contain a JSON object.")
    conversation = raw_payload.get("conversation")
    if not isinstance(conversation, dict):
        raise ValueError(f"{raw_path} is missing conversation data.")

    paper_id = normalize_text(str(raw_payload.get("paper_id") or ""))
    if not paper_id:
        raise ValueError(f"{raw_path} is missing paper_id.")
    if not meta_path.exists():
        raise ValueError(f"Missing meta artifact for {paper_id}: {meta_path}")

    meta_artifact = validate_meta_payload(meta_path, read_json(meta_path, {}), paper_id, extractor_version)

    title = normalize_title(str(conversation.get("title") or paper_id))
    year = conversation.get("year")
    semantic_paper = None
    try:
        semantic_paper = semantic_scholar_title_match(title, year if isinstance(year, int) else None, fetcher=fetcher)
    except Exception:
        semantic_paper = None

    record = normalize_record(raw_payload, semantic_paper, meta_artifact)
    return merge_existing_enrichment(record, existing_record)


def iter_raw_files(raw_dir: Path) -> list[Path]:
    if not raw_dir.exists():
        return []
    return sorted(path for path in raw_dir.glob("*.json") if path.is_file())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Assemble paper records from raw translate payloads and meta artifacts.")
    parser.add_argument("--raw-dir", required=True, help="Directory containing raw JSON payloads.")
    parser.add_argument("--meta-dir", required=True, help="Directory containing per-paper meta artifacts.")
    parser.add_argument("--papers-dir", required=True, help="Directory to write normalized paper JSON files.")
    parser.add_argument(
        "--extractor-config",
        default=str(DEFAULT_EXTRACTOR_CONFIG),
        help="Path to extractor-config.json.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    raw_dir = Path(args.raw_dir)
    meta_dir = Path(args.meta_dir)
    papers_dir = Path(args.papers_dir)
    extractor_version = read_extractor_version(Path(args.extractor_config))

    papers_dir.mkdir(parents=True, exist_ok=True)
    written = 0
    for raw_path in iter_raw_files(raw_dir):
        raw_payload = read_json(raw_path, {})
        raw_paper_id = normalize_text(str(raw_payload.get("paper_id") or ""))
        if not raw_paper_id:
            continue
        existing_record = read_json(papers_dir / f"{raw_paper_id}.json", {})
        record = normalize_raw_file(
            raw_path,
            meta_path=meta_dir / f"{raw_paper_id}.json",
            extractor_version=extractor_version,
            existing_record=existing_record,
        )
        paper_id = normalize_text(str(record.get("paper_id") or raw_paper_id))
        if not paper_id:
            continue
        write_json(papers_dir / f"{paper_id}.json", record)
        written += 1

    print(f"Assembled {written} papers from {raw_dir} using meta artifacts from {meta_dir} into {papers_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
