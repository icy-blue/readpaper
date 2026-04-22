#!/usr/bin/env python3
"""Assemble canonical paper records from raw translate payloads and meta artifacts."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

from display_text import normalize_display_optional_string, normalize_display_text


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXTRACTOR_CONFIG = REPO_ROOT / "extractor-config.json"
DEFAULT_REGISTRY_PATH = REPO_ROOT / "state" / "paper_registry.json"

URL_PATTERN = re.compile(r"https?://[^\s)>\]\"']+")
DOI_PATTERN = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)
GITHUB_PATTERN = re.compile(r"https?://(?:www\.)?github\.com/[^\s)>\]\"']+", re.IGNORECASE)

ASSET_ROLES = {"method_overview", "qualitative_result", "quantitative_result", "ablation", "failure_case"}
ASSET_IMPORTANCE = {"high", "medium", "low"}
EDITORIAL_VERDICTS = {"值得精读", "值得浏览", "只记结论"}
READING_ROUTES = {"method", "evaluation", "comparison", "overview"}
RELATION_TYPES = {
    "compares_to",
    "extends",
    "uses_dataset",
    "uses_method",
    "inspired_by",
    "same_problem",
}
RELATION_TARGET_KINDS = {"local", "external"}
RELATION_CANDIDATE_CONFIDENCE_HINTS = {"low", "medium", "high"}
RELATION_CANDIDATE_EVIDENCE_MODES = {"explicit", "heuristic"}
EXPLICIT_RELATION_TYPES = {"compares_to", "extends", "uses_method"}
HEURISTIC_RELATION_TYPES = {"compares_to", "same_problem"}


def progress(message: str) -> None:
    print(f"[normalize] {message}", flush=True)


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


def normalize_optional_string(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    cleaned = normalize_text(value)
    return cleaned or None


def normalize_display_string(value: Any) -> str | None:
    return normalize_display_optional_string(value)


def message_unit_id(message: dict[str, Any]) -> str:
    translation_status = message.get("translation_status")
    if isinstance(translation_status, dict) and isinstance(translation_status.get("current_unit_id"), str):
        return normalize_text(str(translation_status["current_unit_id"]))
    return ""


def message_section_key(message: dict[str, Any]) -> str:
    unit_id = message_unit_id(message)
    if unit_id:
        return unit_id

    section_category = message.get("section_category")
    if isinstance(section_category, str):
        normalized = normalize_text(section_category)
        if normalized and normalized not in {"body"}:
            return normalized

    content = message.get("content")
    if isinstance(content, str):
        first_line = content.splitlines()[0] if content.splitlines() else ""
        normalized = normalize_text(first_line.lstrip("#").strip())
        if normalized:
            return normalized
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
    if lowered == "abstract" or "摘要" in lowered:
        return "abstract"
    if "introduction" in lowered or "引言" in lowered:
        return "introduction"
    if "method" in lowered or "approach" in lowered or "framework" in lowered or "方法" in lowered:
        return "method"
    if "experiment" in lowered or "evaluation" in lowered or "result" in lowered or "实验" in lowered or "结果" in lowered:
        return "experiments"
    if "conclusion" in lowered or "discussion" in lowered or "结论" in lowered or "讨论" in lowered:
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
        bucket = section_bucket(message_section_key(message))
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


def classify_links(urls: list[str], title: str, abstract_zh: str) -> dict[str, str | None]:
    links: dict[str, str | None] = {
        "pdf": None,
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
        if not links["project"] and not GITHUB_PATTERN.search(url):
            links["project"] = url

    abstract_and_title = f"{title}\n{abstract_zh}"
    if not links["code"]:
        match = GITHUB_PATTERN.search(abstract_and_title)
        if match:
            links["code"] = match.group(0)

    return links


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


def validate_record(errors: list[str], path: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{path} must be an object")
        return {}
    return value


def validate_string_field(errors: list[str], path: str, value: Any, *, required: bool = False, max_chars: int | None = None) -> str | None:
    cleaned = normalize_display_string(value)
    if cleaned is None:
        if required:
            errors.append(f"{path} must be a non-empty string")
        return None
    if max_chars is not None and len(cleaned) > max_chars:
        errors.append(f"{path} exceeds {max_chars} chars")
    return cleaned


def validate_machine_string_field(
    errors: list[str],
    path: str,
    value: Any,
    *,
    required: bool = False,
    max_chars: int | None = None,
) -> str | None:
    cleaned = normalize_optional_string(value)
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
    display_safe: bool = True,
) -> list[str]:
    if not isinstance(value, list):
        errors.append(f"{path} must be a list")
        return []
    if len(value) > max_items:
        errors.append(f"{path} exceeds {max_items} items")
    result: list[str] = []
    for index, item in enumerate(value[:max_items]):
        cleaned = (
            validate_string_field(errors, f"{path}[{index}]", item, required=True, max_chars=max_chars)
            if display_safe
            else validate_machine_string_field(errors, f"{path}[{index}]", item, required=True, max_chars=max_chars)
        )
        if cleaned and cleaned not in result:
            result.append(cleaned)
    return result


def validate_support_list(errors: list[str], path: str, value: Any) -> list[str]:
    items = validate_string_list(errors, path, value, max_chars=64, max_items=8, display_safe=False)
    for item in items:
        if ":" not in item:
            errors.append(f"{path} items must be grounded support references")
    return items


def validate_choice(errors: list[str], path: str, value: Any, choices: set[str], *, required: bool = False) -> str | None:
    cleaned = validate_machine_string_field(errors, path, value, required=required)
    if cleaned is None:
        return None
    if cleaned not in choices:
        errors.append(f"{path} must be one of {sorted(choices)}")
    return cleaned


def validate_story(errors: list[str], value: Any) -> dict[str, Any]:
    record = validate_record(errors, "meta.story", value)
    return {
        "paper_one_liner": validate_string_field(errors, "meta.story.paper_one_liner", record.get("paper_one_liner"), max_chars=110),
        "problem": validate_string_field(errors, "meta.story.problem", record.get("problem"), max_chars=88),
        "method": validate_string_field(errors, "meta.story.method", record.get("method"), max_chars=88),
        "result": validate_string_field(errors, "meta.story.result", record.get("result"), max_chars=88),
    }


def validate_research_problem(errors: list[str], value: Any) -> dict[str, Any]:
    record = validate_record(errors, "meta.research_problem", value)
    return {
        "summary": validate_string_field(errors, "meta.research_problem.summary", record.get("summary"), max_chars=100),
        "gaps": validate_string_list(errors, "meta.research_problem.gaps", record.get("gaps"), max_chars=84, max_items=4),
        "goal": validate_string_field(errors, "meta.research_problem.goal", record.get("goal"), max_chars=100),
    }


def validate_method(errors: list[str], value: Any) -> dict[str, Any]:
    record = validate_record(errors, "meta.method", value)
    return {
        "summary": validate_string_field(errors, "meta.method.summary", record.get("summary"), max_chars=110),
        "pipeline_steps": validate_string_list(errors, "meta.method.pipeline_steps", record.get("pipeline_steps"), max_chars=105, max_items=4),
        "innovations": validate_string_list(errors, "meta.method.innovations", record.get("innovations"), max_chars=90, max_items=4),
        "ingredients": validate_string_list(errors, "meta.method.ingredients", record.get("ingredients"), max_chars=40, max_items=6, display_safe=False),
        "inputs": validate_string_list(errors, "meta.method.inputs", record.get("inputs"), max_chars=32, max_items=6, display_safe=False),
        "outputs": validate_string_list(errors, "meta.method.outputs", record.get("outputs"), max_chars=32, max_items=6, display_safe=False),
        "representations": validate_string_list(
            errors, "meta.method.representations", record.get("representations"), max_chars=40, max_items=6, display_safe=False
        ),
    }


def validate_evaluation(errors: list[str], value: Any) -> dict[str, Any]:
    record = validate_record(errors, "meta.evaluation", value)
    return {
        "headline": validate_string_field(errors, "meta.evaluation.headline", record.get("headline"), max_chars=96),
        "datasets": validate_string_list(errors, "meta.evaluation.datasets", record.get("datasets"), max_chars=36, max_items=8, display_safe=False),
        "metrics": validate_string_list(errors, "meta.evaluation.metrics", record.get("metrics"), max_chars=20, max_items=8, display_safe=False),
        "baselines": validate_string_list(errors, "meta.evaluation.baselines", record.get("baselines"), max_chars=36, max_items=8, display_safe=False),
        "key_findings": validate_string_list(errors, "meta.evaluation.key_findings", record.get("key_findings"), max_chars=90, max_items=4),
        "setup_summary": validate_string_field(errors, "meta.evaluation.setup_summary", record.get("setup_summary"), max_chars=140),
    }


def validate_claims(errors: list[str], value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        errors.append("meta.claims must be a list")
        return []
    if len(value) > 5:
        errors.append("meta.claims exceeds 5 items")
    result: list[dict[str, Any]] = []
    for index, item in enumerate(value[:5]):
        record = validate_record(errors, f"meta.claims[{index}]", item)
        result.append(
            {
                "text": validate_string_field(errors, f"meta.claims[{index}].text", record.get("text"), required=True, max_chars=120) or "",
                "type": validate_machine_string_field(errors, f"meta.claims[{index}].type", record.get("type"), required=True, max_chars=24) or "method",
                "support": validate_support_list(errors, f"meta.claims[{index}].support", record.get("support")),
                "confidence": validate_machine_string_field(errors, f"meta.claims[{index}].confidence", record.get("confidence"), max_chars=16) or "medium",
            }
        )
    return result


def validate_conclusion(errors: list[str], value: Any) -> dict[str, Any]:
    record = validate_record(errors, "meta.conclusion", value)
    return {
        "author": validate_string_field(errors, "meta.conclusion.author", record.get("author"), max_chars=180),
        "limitations": validate_string_list(errors, "meta.conclusion.limitations", record.get("limitations"), max_chars=90, max_items=4),
    }


def validate_editorial(errors: list[str], value: Any) -> dict[str, Any]:
    record = validate_record(errors, "meta.editorial", value)
    verdict = validate_choice(errors, "meta.editorial.verdict", record.get("verdict"), EDITORIAL_VERDICTS)
    reading_route = validate_choice(errors, "meta.editorial.reading_route", record.get("reading_route"), READING_ROUTES, required=True) or "overview"
    return {
        "verdict": verdict,
        "summary": validate_string_field(errors, "meta.editorial.summary", record.get("summary"), max_chars=84),
        "why_read": validate_string_list(errors, "meta.editorial.why_read", record.get("why_read"), max_chars=64, max_items=3),
        "strengths": validate_string_list(errors, "meta.editorial.strengths", record.get("strengths"), max_chars=80, max_items=4),
        "cautions": validate_string_list(errors, "meta.editorial.cautions", record.get("cautions"), max_chars=80, max_items=4),
        "reading_route": reading_route,
        "research_position": validate_string_field(errors, "meta.editorial.research_position", record.get("research_position"), max_chars=84),
        "graph_worthy": validate_bool_field(errors, "meta.editorial.graph_worthy", record.get("graph_worthy")),
        "next_read": validate_string_list(errors, "meta.editorial.next_read", record.get("next_read"), max_chars=36, max_items=4, display_safe=False),
    }


def validate_taxonomy(errors: list[str], value: Any) -> dict[str, Any]:
    record = validate_record(errors, "meta.taxonomy", value)
    return {
        "themes": validate_string_list(errors, "meta.taxonomy.themes", record.get("themes"), max_chars=40, max_items=8, display_safe=False),
        "tasks": validate_string_list(errors, "meta.taxonomy.tasks", record.get("tasks"), max_chars=40, max_items=8, display_safe=False),
        "methods": validate_string_list(errors, "meta.taxonomy.methods", record.get("methods"), max_chars=40, max_items=8, display_safe=False),
        "modalities": validate_string_list(errors, "meta.taxonomy.modalities", record.get("modalities"), max_chars=24, max_items=6, display_safe=False),
        "representations": validate_string_list(
            errors, "meta.taxonomy.representations", record.get("representations"), max_chars=40, max_items=8, display_safe=False
        ),
        "novelty_types": validate_string_list(errors, "meta.taxonomy.novelty_types", record.get("novelty_types"), max_chars=40, max_items=6, display_safe=False),
    }


def validate_comparison(errors: list[str], value: Any) -> dict[str, Any]:
    record = validate_record(errors, "meta.comparison", value)
    aspects_value = record.get("aspects")
    aspects: list[dict[str, str]] = []
    if not isinstance(aspects_value, list):
        errors.append("meta.comparison.aspects must be a list")
    else:
        for index, item in enumerate(aspects_value[:8]):
            aspect_record = validate_record(errors, f"meta.comparison.aspects[{index}]", item)
            aspects.append(
                {
                    "aspect": validate_string_field(errors, f"meta.comparison.aspects[{index}].aspect", aspect_record.get("aspect"), required=True, max_chars=28) or "",
                    "difference": validate_string_field(
                        errors,
                        f"meta.comparison.aspects[{index}].difference",
                        aspect_record.get("difference"),
                        required=True,
                        max_chars=96,
                    )
                    or "",
                }
            )
    return {
        "aspects": aspects,
        "next_read": validate_string_list(errors, "meta.comparison.next_read", record.get("next_read"), max_chars=36, max_items=4, display_safe=False),
    }


def validate_asset_items(errors: list[str], path: str, value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        errors.append(f"{path} must be a list")
        return []
    result: list[dict[str, str]] = []
    for index, item in enumerate(value):
        record = validate_record(errors, f"{path}[{index}]", item)
        role = validate_machine_string_field(errors, f"{path}[{index}].role", record.get("role"), required=True, max_chars=32) or ""
        importance = validate_machine_string_field(errors, f"{path}[{index}].importance", record.get("importance"), required=True, max_chars=8) or ""
        if role not in ASSET_ROLES:
            errors.append(f"{path}[{index}].role must be one of {sorted(ASSET_ROLES)}")
        if importance not in ASSET_IMPORTANCE:
            errors.append(f"{path}[{index}].importance must be one of {sorted(ASSET_IMPORTANCE)}")
        result.append(
            {
                "label": validate_machine_string_field(errors, f"{path}[{index}].label", record.get("label"), required=True, max_chars=24) or "",
                "caption": validate_string_field(errors, f"{path}[{index}].caption", record.get("caption"), required=True, max_chars=220) or "",
                "role": role,
                "importance": importance,
            }
        )
    return result


def validate_assets(errors: list[str], value: Any) -> dict[str, Any]:
    record = validate_record(errors, "meta.assets", value)
    return {
        "figures": validate_asset_items(errors, "meta.assets.figures", record.get("figures")),
        "tables": validate_asset_items(errors, "meta.assets.tables", record.get("tables")),
    }


def validate_relation_candidates(errors: list[str], value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        errors.append("meta.relation_candidates must be a list")
        return []
    result: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        record = validate_record(errors, f"meta.relation_candidates[{index}]", item)
        relation_type = validate_machine_string_field(
            errors, f"meta.relation_candidates[{index}].type", record.get("type"), required=True, max_chars=24
        ) or ""
        evidence_mode = (
            validate_choice(
                errors,
                f"meta.relation_candidates[{index}].evidence_mode",
                record.get("evidence_mode"),
                RELATION_CANDIDATE_EVIDENCE_MODES,
                required=True,
            )
            or "explicit"
        )
        if evidence_mode == "explicit" and relation_type not in EXPLICIT_RELATION_TYPES:
            errors.append(f"meta.relation_candidates[{index}].type must be one of {sorted(EXPLICIT_RELATION_TYPES)} for explicit evidence")
        if evidence_mode == "heuristic" and relation_type not in HEURISTIC_RELATION_TYPES:
            errors.append(f"meta.relation_candidates[{index}].type must be one of {sorted(HEURISTIC_RELATION_TYPES)} for heuristic evidence")
        result.append(
            {
                "type": relation_type,
                "target_name": validate_string_field(
                    errors,
                    f"meta.relation_candidates[{index}].target_name",
                    record.get("target_name"),
                    required=True,
                    max_chars=120,
                )
                or "",
                "description": validate_string_field(errors, f"meta.relation_candidates[{index}].description", record.get("description"), max_chars=120),
                "confidence_hint": (
                    validate_choice(
                        errors,
                        f"meta.relation_candidates[{index}].confidence_hint",
                        record.get("confidence_hint"),
                        RELATION_CANDIDATE_CONFIDENCE_HINTS,
                        required=True,
                    )
                    or "medium"
                ),
                "evidence_mode": evidence_mode,
            }
        )
    return result


def build_validation_error(meta_path: Path, errors: list[str]) -> ValueError:
    preview = "; ".join(errors[:6])
    if len(errors) > 6:
        preview += f"; and {len(errors) - 6} more"
    return ValueError(f"Invalid meta artifact {meta_path}: {preview}")


def validate_meta_payload(meta_path: Path, payload: Any, paper_id: str, extractor_version: str) -> dict[str, Any]:
    errors: list[str] = []
    artifact = validate_record(errors, "artifact", payload)

    artifact_paper_id = validate_machine_string_field(errors, "artifact.paper_id", artifact.get("paper_id"), required=True)
    artifact_version = validate_machine_string_field(errors, "artifact.extractor_version", artifact.get("extractor_version"), required=True)
    source_conversation_id = validate_machine_string_field(errors, "artifact.source_conversation_id", artifact.get("source_conversation_id"), required=True)
    source_semantic_updated_at = validate_machine_string_field(errors, "artifact.source_semantic_updated_at", artifact.get("source_semantic_updated_at"))
    extracted_at = validate_machine_string_field(errors, "artifact.extracted_at", artifact.get("extracted_at"), required=True)
    meta = validate_record(errors, "artifact.meta", artifact.get("meta"))

    if artifact_paper_id and artifact_paper_id != paper_id:
        errors.append("artifact.paper_id does not match the raw payload paper_id")
    if artifact_version and normalize_text(artifact_version) != normalize_text(extractor_version):
        errors.append("artifact.extractor_version does not match extractor-config.json")

    validated_meta = {
        "story": validate_story(errors, meta.get("story")),
        "research_problem": validate_research_problem(errors, meta.get("research_problem")),
        "core_contributions": validate_string_list(errors, "meta.core_contributions", meta.get("core_contributions"), max_chars=90, max_items=4),
        "method": validate_method(errors, meta.get("method")),
        "evaluation": validate_evaluation(errors, meta.get("evaluation")),
        "claims": validate_claims(errors, meta.get("claims")),
        "conclusion": validate_conclusion(errors, meta.get("conclusion")),
        "editorial": validate_editorial(errors, meta.get("editorial")),
        "taxonomy": validate_taxonomy(errors, meta.get("taxonomy")),
        "comparison": validate_comparison(errors, meta.get("comparison")),
        "assets": validate_assets(errors, meta.get("assets")),
        "relation_candidates": validate_relation_candidates(errors, meta.get("relation_candidates")),
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


def load_registry_items(registry_path: Path) -> list[dict[str, Any]]:
    payload = read_json(registry_path, {})
    if not isinstance(payload, dict):
        return []
    items = payload.get("items")
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict)]


def match_registry_entry(registry_items: list[dict[str, Any]], target_name: str) -> dict[str, Any] | None:
    normalized_target = normalize_key(target_name)
    if not normalized_target:
        return None
    allow_fuzzy = len(normalized_target) >= 12 and " " in normalized_target

    exact_matches: list[dict[str, Any]] = []
    fuzzy_matches: list[dict[str, Any]] = []
    for item in registry_items:
        exact_keys = {
            normalize_key(str(item.get("paper_id") or "")),
            normalize_key(str(item.get("title") or "")),
            normalize_key(str(item.get("dedupe_key") or "")),
            normalize_key(str(item.get("fallback_key") or "")),
        }
        exact_keys.discard("")
        if normalized_target in exact_keys:
            exact_matches.append(item)
            continue
        title_key = normalize_key(str(item.get("title") or ""))
        if allow_fuzzy and title_key and (normalized_target in title_key or title_key in normalized_target):
            fuzzy_matches.append(item)

    if len(exact_matches) == 1:
        return exact_matches[0]
    if not exact_matches and len(fuzzy_matches) == 1:
        return fuzzy_matches[0]
    return None


def relation_cache_key(item: dict[str, Any]) -> str:
    target_key = str(item.get("target_paper_id") or item.get("label") or "")
    return f"{item.get('type') or ''}::{item.get('target_kind') or ''}::{target_key}"


def relation_confidence(target_kind: str, evidence_mode: str) -> float:
    if evidence_mode == "explicit":
        return 0.9 if target_kind == "local" else 0.82
    return 0.68 if target_kind == "local" else 0.6


def build_local_relation(entry: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    paper_id = normalize_text(str(entry.get("paper_id") or "")) or None
    title = normalize_text(str(entry.get("title") or "")) or paper_id
    return {
        "type": candidate["type"],
        "target_kind": "local",
        "target_paper_id": paper_id,
        "label": title,
        "description": candidate.get("description"),
        "confidence": relation_confidence("local", str(candidate.get("evidence_mode") or "explicit")),
    }


def build_external_relation(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": candidate["type"],
        "target_kind": "external",
        "target_paper_id": None,
        "label": normalize_text(str(candidate.get("target_name") or "")) or None,
        "description": candidate.get("description"),
        "confidence": relation_confidence("external", str(candidate.get("evidence_mode") or "explicit")),
    }


def merge_relation_candidates(meta_candidates: list[dict[str, Any]], derived_candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[tuple[str, str, str], dict[str, Any]] = {}
    for candidate in derived_candidates + meta_candidates:
        key = (
            str(candidate.get("type") or ""),
            normalize_key(str(candidate.get("target_name") or "")),
            str(candidate.get("evidence_mode") or "explicit"),
        )
        existing = merged.get(key)
        if existing is None:
            merged[key] = candidate
            continue
        if not existing.get("description") and candidate.get("description"):
            existing["description"] = candidate["description"]
        if existing.get("evidence_mode") == "heuristic" and candidate.get("evidence_mode") == "explicit":
            merged[key] = candidate
    return list(merged.values())


def resolve_relation_candidate(
    current_record: dict[str, Any],
    candidate: dict[str, Any],
    *,
    registry_items: list[dict[str, Any]],
) -> dict[str, Any] | None:
    relation_type = str(candidate.get("type") or "")
    target_name = str(candidate.get("target_name") or "")
    current_paper_id = normalize_text(str(current_record.get("id") or ""))
    current_title = normalize_key(str(((current_record.get("bibliography") or {}) if isinstance(current_record.get("bibliography"), dict) else {}).get("title") or ""))
    local_entry = match_registry_entry(registry_items, target_name)
    if local_entry is not None:
        local_paper_id = normalize_text(str(local_entry.get("paper_id") or ""))
        local_title = normalize_key(str(local_entry.get("title") or ""))
        if local_paper_id == current_paper_id or (local_title and local_title == current_title):
            local_entry = None

    if local_entry is not None:
        progress(f"[{current_paper_id}] relation 命中本地论文: {relation_type} -> {target_name}")
        return build_local_relation(local_entry, candidate)

    normalized_target = normalize_key(target_name)
    if not normalized_target or normalized_target == current_title or normalized_target == normalize_key(current_paper_id):
        progress(f"[{current_paper_id}] relation 解析到自身，已跳过: {relation_type} -> {target_name}")
        return None
    progress(f"[{current_paper_id}] relation 命中站外搜索目标: {relation_type} -> {target_name}")
    return build_external_relation(candidate)


def resolve_relations(
    current_record: dict[str, Any],
    meta: dict[str, Any],
    *,
    registry_items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    meta_candidates = meta.get("relation_candidates") if isinstance(meta.get("relation_candidates"), list) else []
    candidates = merge_relation_candidates(meta_candidates, [])
    paper_id = normalize_text(str(current_record.get("id") or ""))
    progress(f"[{paper_id}] 开始解析 {len(candidates)} 条 relation candidates")
    relations: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        relation = resolve_relation_candidate(
            current_record,
            candidate,
            registry_items=registry_items,
        )
        if relation is None:
            continue
        key = relation_cache_key(relation)
        existing = relations.get(key)
        if existing is None or float(relation.get("confidence") or 0) > float(existing.get("confidence") or 0):
            relations[key] = relation
        elif existing is not None and not existing.get("description") and relation.get("description"):
            existing["description"] = relation["description"]
    sorted_relations = sorted(relations.values(), key=lambda item: (-float(item.get("confidence") or 0), str(item.get("label") or "")))
    progress(f"[{paper_id}] relation 解析完成，保留 {len(sorted_relations)} 条")
    return sorted_relations


def paper_paths(paper_id: str) -> dict[str, str]:
    return {
        "paper_path": f"papers/{paper_id}.md",
        "route_path": f"#/?paper={paper_id}&detail=1",
    }


def normalize_record(
    raw_payload: dict[str, Any],
    meta_artifact: dict[str, Any],
    *,
    registry_items: list[dict[str, Any]],
) -> dict[str, Any]:
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
    abstract_zh = normalize_display_text(sections["abstract"][0]) if sections["abstract"] else None
    meta = meta_artifact["meta"]

    links = classify_links(extract_urls(conversation), title, abstract_zh or "")
    pdf_url = conversation.get("pdf_url")
    if isinstance(pdf_url, str) and pdf_url.strip():
        links["pdf"] = pdf_url.strip()

    year = conversation.get("year")
    if not isinstance(year, int):
        year = None
    venue = conversation.get("venue_abbr") or conversation.get("venue")
    venue_text = normalize_text(str(venue)) if isinstance(venue, str) and venue else None

    citation_count = conversation.get("citation_count")
    if not isinstance(citation_count, int):
        citation_count = None

    identifiers = {
        "doi": None,
        "arxiv": None,
    }

    record = {
        "id": paper_id,
        "source": {
            "conversation_ids": source_conversation_ids,
            **paper_paths(paper_id),
        },
        "bibliography": {
            "title": title,
            "authors": [],
            "year": year,
            "venue": venue_text or "Unknown",
            "citation_count": citation_count,
            "identifiers": identifiers,
            "links": links,
        },
        "abstracts": {
            "raw": None,
            "zh": abstract_zh,
        },
        "story": meta["story"],
        "research_problem": meta["research_problem"],
        "core_contributions": meta["core_contributions"],
        "method": meta["method"],
        "evaluation": meta["evaluation"],
        "claims": meta["claims"],
        "conclusion": meta["conclusion"],
        "editorial": meta["editorial"],
        "taxonomy": meta["taxonomy"],
        "comparison": meta["comparison"],
        "assets": meta["assets"],
        "relations": [],
    }
    record["relations"] = resolve_relations(
        record,
        meta,
        registry_items=registry_items,
    )
    return record


def merge_existing_enrichment(record: dict[str, Any], existing_record: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(existing_record, dict):
        return record

    merged = json.loads(json.dumps(record, ensure_ascii=False))
    bibliography = merged.get("bibliography") if isinstance(merged.get("bibliography"), dict) else {}
    existing_bibliography = existing_record.get("bibliography") if isinstance(existing_record.get("bibliography"), dict) else {}

    current_authors = ensure_strings(bibliography.get("authors"))
    existing_authors = ensure_strings(existing_bibliography.get("authors") if existing_bibliography else existing_record.get("authors"))
    if not current_authors and existing_authors:
        bibliography["authors"] = existing_authors

    current_citation_count = bibliography.get("citation_count")
    existing_citation_count = existing_bibliography.get("citation_count") if existing_bibliography else existing_record.get("citation_count")
    if current_citation_count is None and isinstance(existing_citation_count, int):
        bibliography["citation_count"] = existing_citation_count

    identifiers = bibliography.get("identifiers") if isinstance(bibliography.get("identifiers"), dict) else {}
    existing_identifiers = existing_bibliography.get("identifiers") if isinstance(existing_bibliography.get("identifiers"), dict) else {}
    if not identifiers.get("doi"):
        old_doi = existing_identifiers.get("doi") or existing_record.get("links", {}).get("doi") if isinstance(existing_record.get("links"), dict) else None
        if isinstance(old_doi, str) and old_doi.strip():
            identifiers["doi"] = old_doi.strip()
    if not identifiers.get("arxiv"):
        old_arxiv = existing_identifiers.get("arxiv") or existing_record.get("links", {}).get("arxiv") if isinstance(existing_record.get("links"), dict) else None
        if isinstance(old_arxiv, str) and old_arxiv.strip():
            identifiers["arxiv"] = old_arxiv.strip()
    bibliography["identifiers"] = identifiers

    links = bibliography.get("links") if isinstance(bibliography.get("links"), dict) else {}
    existing_links = existing_bibliography.get("links") if isinstance(existing_bibliography.get("links"), dict) else existing_record.get("links")
    if isinstance(existing_links, dict):
        for key in ("project", "code", "data"):
            if not links.get(key) and isinstance(existing_links.get(key), str) and str(existing_links.get(key)).strip():
                links[key] = str(existing_links.get(key)).strip()
    bibliography["links"] = links
    merged["bibliography"] = bibliography

    abstracts = merged.get("abstracts") if isinstance(merged.get("abstracts"), dict) else {}
    existing_abstracts = existing_record.get("abstracts") if isinstance(existing_record.get("abstracts"), dict) else {}
    if not abstracts.get("raw"):
        old_raw = existing_abstracts.get("raw") or existing_record.get("abstract_raw")
        if isinstance(old_raw, str) and old_raw.strip():
            abstracts["raw"] = normalize_text(old_raw)
    merged["abstracts"] = abstracts
    return merged


def normalize_raw_file(
    raw_path: Path,
    *,
    meta_path: Path,
    extractor_version: str,
    registry_items: list[dict[str, Any]] | None = None,
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
    progress(f"[{paper_id}] 读取 raw/meta artifact")
    if not meta_path.exists():
        raise ValueError(f"Missing meta artifact for {paper_id}: {meta_path}")

    meta_artifact = validate_meta_payload(meta_path, read_json(meta_path, {}), paper_id, extractor_version)

    record = normalize_record(
        raw_payload,
        meta_artifact,
        registry_items=registry_items or [],
    )
    return merge_existing_enrichment(record, existing_record)


def iter_raw_files(raw_dir: Path) -> list[Path]:
    if not raw_dir.exists():
        return []
    return sorted(path for path in raw_dir.glob("*.json") if path.is_file())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Assemble canonical paper records from raw translate payloads and meta artifacts.")
    parser.add_argument("--raw-dir", required=True, help="Directory containing raw JSON payloads.")
    parser.add_argument("--meta-dir", required=True, help="Directory containing per-paper meta artifacts.")
    parser.add_argument("--papers-dir", required=True, help="Directory to write canonical paper JSON files.")
    parser.add_argument(
        "--extractor-config",
        default=str(DEFAULT_EXTRACTOR_CONFIG),
        help="Path to extractor-config.json.",
    )
    parser.add_argument(
        "--registry",
        default=str(DEFAULT_REGISTRY_PATH),
        help="Path to paper_registry.json used for local relation resolution.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    raw_dir = Path(args.raw_dir)
    meta_dir = Path(args.meta_dir)
    papers_dir = Path(args.papers_dir)
    extractor_version = read_extractor_version(Path(args.extractor_config))
    registry_items = load_registry_items(Path(args.registry))
    papers_dir.mkdir(parents=True, exist_ok=True)
    raw_files = iter_raw_files(raw_dir)
    progress(
        f"开始装配 canonical papers: raw={len(raw_files)} meta_dir={meta_dir} papers_dir={papers_dir} registry_items={len(registry_items)}"
    )
    written = 0
    for index, raw_path in enumerate(raw_files, start=1):
        raw_payload = read_json(raw_path, {})
        raw_paper_id = normalize_text(str(raw_payload.get("paper_id") or ""))
        if not raw_paper_id:
            continue
        progress(f"[{index}/{len(raw_files)}] 开始处理 {raw_paper_id}")
        existing_record = read_json(papers_dir / f"{raw_paper_id}.json", {})
        record = normalize_raw_file(
            raw_path,
            meta_path=meta_dir / f"{raw_paper_id}.json",
            extractor_version=extractor_version,
            registry_items=registry_items,
            existing_record=existing_record,
        )
        paper_id = normalize_text(str(record.get("id") or raw_paper_id))
        if not paper_id:
            continue
        write_json(papers_dir / f"{paper_id}.json", record)
        progress(f"[{index}/{len(raw_files)}] 写入完成 {paper_id}，relations={len(record.get('relations') or [])}")
        written += 1

    print(f"Assembled {written} canonical papers from {raw_dir} using meta artifacts from {meta_dir} into {papers_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
