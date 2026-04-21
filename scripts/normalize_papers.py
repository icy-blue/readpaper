#!/usr/bin/env python3
"""Normalize translate raw payloads into paper records."""

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
SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[。！？!?])\s+|\n+")
DOI_PATTERN = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)
GITHUB_PATTERN = re.compile(r"https?://(?:www\.)?github\.com/[^\s)>\]\"']+", re.IGNORECASE)

TASK_KEYWORDS = [
    (re.compile(r"text[- ]to[- ]3d|text to 3d", re.IGNORECASE), "Text-to-3D"),
    (re.compile(r"image[- ]to[- ]3d|one image to", re.IGNORECASE), "Image-to-3D"),
    (re.compile(r"scene generation", re.IGNORECASE), "3D Scene Generation"),
    (re.compile(r"novel view synthesis|view synthesis", re.IGNORECASE), "Novel View Synthesis"),
    (re.compile(r"semantic segmentation", re.IGNORECASE), "Semantic Segmentation"),
    (re.compile(r"open[- ]world|open[- ]vocabulary segmentation", re.IGNORECASE), "Open-Vocabulary Segmentation"),
    (re.compile(r"object detection|目标检测", re.IGNORECASE), "Object Detection"),
    (re.compile(r"keypoint", re.IGNORECASE), "Keypoint Detection"),
    (re.compile(r"ocr", re.IGNORECASE), "OCR"),
    (re.compile(r"registration|relocalization|matching|alignment", re.IGNORECASE), "Registration and Alignment"),
    (re.compile(r"normal estimation", re.IGNORECASE), "Point Cloud Normal Estimation"),
    (re.compile(r"surface reconstruction", re.IGNORECASE), "Surface Reconstruction"),
    (re.compile(r"3d generation|3d asset", re.IGNORECASE), "3D Generation"),
    (re.compile(r"3d reconstruction", re.IGNORECASE), "3D Reconstruction"),
]

METHOD_KEYWORDS = [
    (re.compile(r"transformer", re.IGNORECASE), "Transformer"),
    (re.compile(r"diffusion", re.IGNORECASE), "Diffusion Model"),
    (re.compile(r"rectified flow", re.IGNORECASE), "Rectified Flow"),
    (re.compile(r"graph neural network|gnn", re.IGNORECASE), "Graph Neural Network"),
    (re.compile(r"convolution|cnn", re.IGNORECASE), "Convolutional Network"),
    (re.compile(r"large multimodal model|mllm", re.IGNORECASE), "Large Multimodal Model"),
    (re.compile(r"large language model|llm", re.IGNORECASE), "Large Language Model"),
    (re.compile(r"implicit neural representation", re.IGNORECASE), "Implicit Neural Representation"),
    (re.compile(r"poisson", re.IGNORECASE), "Poisson Solver"),
]

REPRESENTATION_KEYWORDS = [
    (re.compile(r"\bmesh\b|网格", re.IGNORECASE), "Mesh"),
    (re.compile(r"point cloud|点云", re.IGNORECASE), "Point Cloud"),
    (re.compile(r"3d gaussian|高斯", re.IGNORECASE), "3D Gaussians"),
    (re.compile(r"radiance field|辐射场|nerf", re.IGNORECASE), "Radiance Fields"),
    (re.compile(r"voxel|体素", re.IGNORECASE), "Voxel"),
    (re.compile(r"latent|潜变量", re.IGNORECASE), "Latent Representation"),
    (re.compile(r"bounding box|框", re.IGNORECASE), "Bounding Box"),
    (re.compile(r"normal|法向", re.IGNORECASE), "Normals"),
]

METRIC_KEYWORDS = [
    "PSNR",
    "SSIM",
    "LPIPS",
    "IoU",
    "mIoU",
    "mAP",
    "F1",
    "MAE",
    "RTE",
    "RRE",
    "Chamfer Distance",
]

NOVELTY_KEYWORDS = [
    (re.compile(r"latent|表征|representation", re.IGNORECASE), "representation"),
    (re.compile(r"transformer|architecture|框架", re.IGNORECASE), "architecture"),
    (re.compile(r"training|数据引擎|训练流程|reinforcement", re.IGNORECASE), "training recipe"),
    (re.compile(r"physics|物理", re.IGNORECASE), "physics prior"),
    (re.compile(r"decoder|解码", re.IGNORECASE), "decoder flexibility"),
]

RELATION_HINTS = {
    "task_overlap": "同任务代表方法",
    "method_overlap": "同路线近邻",
    "baseline_match": "显式对比对象",
    "contrast_method_match": "路线对比对象",
    "fallback_contrast": "同任务差异路线",
}


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
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_title(value: str) -> str:
    text = normalize_text(value)
    return re.sub(r"\s*[†‡*]+$", "", text).strip()


def normalize_key(value: str) -> str:
    text = normalize_text(value).lower()
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


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


def unique(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        cleaned = normalize_text(value)
        if cleaned and cleaned not in result:
            result.append(cleaned)
    return result


def compact_markdown(text: str) -> str:
    content = text.replace("\r\n", "\n").strip()
    content = re.sub(r"\n{3,}", "\n\n", content)
    return content.strip()


def strip_heading(text: str) -> str:
    content = compact_markdown(text)
    lines = content.splitlines()
    while lines and lines[0].lstrip().startswith("#"):
        lines.pop(0)
        if lines and not lines[0].strip():
            lines.pop(0)
    return compact_markdown("\n".join(lines))


def split_sentences(text: str) -> list[str]:
    flattened = compact_markdown(text).replace("\n", " ")
    parts = [normalize_text(part) for part in SENTENCE_SPLIT_PATTERN.split(flattened)]
    return [part for part in parts if len(part) >= 8]


def first_sentence(text: str) -> str | None:
    sentences = split_sentences(text)
    return sentences[0] if sentences else None


def paragraph_blocks(text: str) -> list[str]:
    return [normalize_text(part) for part in compact_markdown(text).split("\n\n") if normalize_text(part)]


def match_any(patterns: list[tuple[re.Pattern[str], str]], text: str) -> list[str]:
    result: list[str] = []
    for pattern, label in patterns:
        if pattern.search(text) and label not in result:
            result.append(label)
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
    query = urllib.parse.urlencode(params, doseq=True)
    return f"{SEMANTIC_SCHOLAR_BASE_URL}{route}?{query}"


def parse_external_ids(payload: dict[str, Any]) -> tuple[str | None, str | None]:
    external_ids = payload.get("externalIds")
    if not isinstance(external_ids, dict):
        return None, None
    doi = external_ids.get("DOI") or external_ids.get("doi")
    arxiv = external_ids.get("ArXiv") or external_ids.get("ARXIV") or external_ids.get("arXiv")
    return normalize_text(str(doi)) if isinstance(doi, str) and doi.strip() else None, normalize_text(str(arxiv)) if isinstance(arxiv, str) and arxiv.strip() else None


def parse_semantic_scholar_candidate(payload: dict[str, Any]) -> SemanticScholarPaper:
    authors = payload.get("authors")
    author_names: list[str] = []
    if isinstance(authors, list):
        for author in authors:
            if isinstance(author, dict):
                name = author.get("name")
                if isinstance(name, str):
                    cleaned = normalize_text(name)
                    if cleaned and cleaned not in author_names:
                        author_names.append(cleaned)

    open_access_pdf = payload.get("openAccessPdf")
    pdf_url = None
    if isinstance(open_access_pdf, dict):
        candidate_url = open_access_pdf.get("url")
        if isinstance(candidate_url, str) and candidate_url.strip():
            pdf_url = candidate_url.strip()

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


def semantic_scholar_title_match(
    title: str,
    year: int | None,
    *,
    fetcher: Any = fetch_json,
) -> SemanticScholarPaper | None:
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
    if isinstance(translation_status, dict):
        current_unit_id = translation_status.get("current_unit_id")
        if isinstance(current_unit_id, str):
            return normalize_text(current_unit_id)
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
        unit_id = message_unit_id(message)
        content = strip_heading(str(message.get("content") or ""))
        if not content:
            continue
        bucket = section_bucket(unit_id)
        buckets.setdefault(bucket, []).append(content)
    return buckets


def latest_translation_status(conversation: dict[str, Any]) -> dict[str, Any]:
    latest: dict[str, Any] = {}
    for message in visible_bot_messages(conversation):
        translation_status = message.get("translation_status")
        if isinstance(translation_status, dict):
            latest = translation_status
    return latest


def translate_status_payload(conversation: dict[str, Any]) -> dict[str, Any]:
    latest = latest_translation_status(conversation)
    state = normalize_text(str(latest.get("state") or "UNKNOWN"))
    completed_count = latest.get("completed_unit_count")
    total_count = latest.get("total_unit_count")
    completed = completed_count if isinstance(completed_count, int) else 0
    total = total_count if isinstance(total_count, int) else completed
    is_all_done = bool(latest.get("is_all_done"))
    active_scope = normalize_text(str(latest.get("active_scope") or "body")) or "body"
    coverage_notes: list[str] = []
    if not is_all_done:
        coverage_notes.append("当前记录主要依据已完成翻译单元，未完成部分暂未纳入。")
    if state == "BODY_DONE" and active_scope == "body":
        coverage_notes.append("正文已完成，但附录或补充材料可能仍未完全覆盖。")
    return {
        "state": state or "UNKNOWN",
        "completed_unit_count": completed,
        "total_unit_count": total,
        "is_partial": not is_all_done,
        "active_scope": active_scope,
        "coverage_notes": coverage_notes,
    }


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


def title_and_abstract_blob(title: str, abstract_zh: str, sections: dict[str, list[str]]) -> str:
    return "\n".join([title, abstract_zh, *sections.get("introduction", []), *sections.get("method", []), *sections.get("experiments", []), *sections.get("conclusion", [])])


def infer_tasks(text: str, raw_tags: list[dict[str, Any]]) -> list[str]:
    tasks = []
    for item in raw_tags:
        if not isinstance(item, dict):
            continue
        if item.get("category_code") == "T":
            label = item.get("tag_label_en") or item.get("tag_label")
            if isinstance(label, str) and normalize_text(label) not in tasks:
                tasks.append(normalize_text(label))
    return unique(tasks + match_any(TASK_KEYWORDS, text))


def infer_methods(text: str, raw_tags: list[dict[str, Any]]) -> list[str]:
    methods = []
    for item in raw_tags:
        if not isinstance(item, dict):
            continue
        if item.get("category_code") == "S":
            label = item.get("tag_label_en") or item.get("tag_label")
            if isinstance(label, str):
                methods.append(normalize_text(label))
    return unique(methods + match_any(METHOD_KEYWORDS, text))


def infer_modalities(text: str, raw_tags: list[dict[str, Any]]) -> list[str]:
    result: list[str] = []
    for item in raw_tags:
        if not isinstance(item, dict):
            continue
        if item.get("category_code") != "M":
            continue
        label = normalize_text(str(item.get("tag_label_en") or item.get("tag_label") or ""))
        lowered = label.lower()
        if "image" in lowered and "image" not in result:
            result.append("image")
        elif "point cloud" in lowered and "point cloud" not in result:
            result.append("point cloud")
        elif "multimodal" in lowered and "multimodal" not in result:
            result.append("multimodal")

    lowered_text = text.lower()
    if "text-to-3d" in lowered_text or "text prompt" in lowered_text:
        result.append("text")
    if any(token in lowered_text for token in ("3d", "mesh", "gaussian", "point cloud", "point clouds")):
        result.append("3D")
    if "image" in lowered_text:
        result.append("image")
    return unique(result)


def infer_representations(text: str) -> list[str]:
    return match_any(REPRESENTATION_KEYWORDS, text)


def infer_themes(tasks: list[str], title: str) -> list[str]:
    lowered_title = title.lower()
    themes: list[str] = []
    if any("generation" in task.lower() or "text-to-3d" in task.lower() or "image-to-3d" in task.lower() for task in tasks):
        themes.append("3D Generation")
    if any("segmentation" in task.lower() or "3d understanding" in task.lower() for task in tasks):
        themes.append("3D Understanding")
    if any("detection" in task.lower() or "ocr" in task.lower() or "keypoint" in task.lower() for task in tasks):
        themes.append("Open-World Perception")
    if any("registration" in task.lower() or "alignment" in task.lower() for task in tasks):
        themes.append("3D Registration")
    if any("reconstruction" in task.lower() or "normal estimation" in task.lower() for task in tasks):
        themes.append("3D Reconstruction")
    if not themes and "3d generation" in lowered_title:
        themes.append("3D Generation")
    if not themes and "registration" in lowered_title:
        themes.append("3D Registration")
    if not themes and "normal estimation" in lowered_title:
        themes.append("3D Reconstruction")
    if not themes:
        themes.append("Computer Vision")
    return unique(themes)


def infer_inputs_outputs(title: str, tasks: list[str], modalities: list[str], representations: list[str], text: str) -> tuple[list[str], list[str], list[str]]:
    lowered = text.lower()
    inputs: list[str] = []
    outputs: list[str] = []

    if any(task in {"Text-to-3D", "3D Scene Generation"} for task in tasks):
        inputs.append("text prompt")
    if any(task in {"Image-to-3D", "Object Detection", "OCR", "Keypoint Detection", "Novel View Synthesis"} for task in tasks) or "one image" in lowered:
        inputs.append("image")
    if "Semantic Segmentation" in tasks or "Open-Vocabulary Segmentation" in tasks:
        inputs.append("point cloud")
    if "Open-Vocabulary Segmentation" in tasks:
        inputs.append("text prompt")
    if "Registration and Alignment" in tasks:
        if "image" in modalities:
            inputs.append("image")
        if "point cloud" in modalities or "3D" in modalities:
            inputs.append("point cloud")
    if "Point Cloud Normal Estimation" in tasks or "Surface Reconstruction" in tasks:
        inputs.append("point cloud")

    if "Object Detection" in tasks:
        outputs.append("bounding boxes")
    if "Keypoint Detection" in tasks:
        outputs.append("keypoints")
    if "OCR" in tasks:
        outputs.append("recognized text")
    if any(task in {"Text-to-3D", "Image-to-3D", "3D Generation", "3D Scene Generation"} for task in tasks):
        if "Mesh" in representations:
            outputs.append("mesh")
        elif "3D Gaussians" in representations:
            outputs.append("3D Gaussian")
        else:
            outputs.append("3D asset")
    if "Novel View Synthesis" in tasks:
        outputs.append("novel views")
    if "Semantic Segmentation" in tasks or "Open-Vocabulary Segmentation" in tasks:
        outputs.append("segmentation masks")
    if "Registration and Alignment" in tasks:
        outputs.append("camera pose")
    if "Point Cloud Normal Estimation" in tasks:
        outputs.append("oriented normals")
    if "Surface Reconstruction" in tasks:
        outputs.append("surface reconstruction")

    derived_modalities = list(modalities)
    if any(value in inputs for value in ("text prompt",)):
        derived_modalities.append("text")
    if any(value in inputs for value in ("image",)):
        derived_modalities.append("image")
    if any(value in inputs for value in ("point cloud",)) or any(
        value in outputs for value in ("mesh", "3D Gaussian", "3D asset", "oriented normals", "surface reconstruction")
    ):
        derived_modalities.append("3D")
    return unique(inputs), unique(outputs), unique(derived_modalities)


def extract_bullet_like_sentences(texts: list[str], limit: int, *, support: str) -> list[dict[str, Any]]:
    candidates: list[str] = []
    for text in texts:
        for sentence in split_sentences(text):
            if any(token in sentence for token in ("我们提出", "本文提出", "我们展示", "结果表明", "实验表明", "显著优于", "达到")):
                candidates.append(sentence)
    if not candidates:
        for text in texts:
            candidates.extend(split_sentences(text)[:2])

    claims: list[dict[str, Any]] = []
    for sentence in unique(candidates):
        claims.append({"claim": sentence, "support": [support], "confidence": "medium"})
        if len(claims) >= limit:
            break
    return claims


def extract_core_contributions(abstract_zh: str, conclusion: str) -> list[str]:
    sentences = []
    for source in (abstract_zh, conclusion):
        for sentence in split_sentences(source):
            if any(token in sentence for token in ("我们提出", "本文提出", "我们展示", "我们采用", "结果表明", "实验表明")):
                sentences.append(sentence)
    if not sentences:
        sentences = split_sentences(abstract_zh)[:3]
    return unique(sentences)[:4]


def extract_research_problem(introduction: str, abstract_zh: str) -> str | None:
    for source in (introduction, abstract_zh):
        for sentence in split_sentences(source):
            if any(token in sentence for token in ("目标", "问题", "挑战", "困难", "task", "problem")):
                return sentence
    return first_sentence(introduction or abstract_zh)


def extract_experiment_setup(experiments: str) -> str | None:
    for paragraph in paragraph_blocks(experiments):
        if any(token in paragraph for token in ("dataset", "数据集", "benchmark", "baseline", "实验", "评估")):
            return paragraph
    return first_sentence(experiments)


def extract_author_conclusion(conclusion: str) -> str | None:
    if not conclusion:
        return None
    sentences = split_sentences(conclusion)
    if not sentences:
        return None
    return " ".join(sentences[:2])


def extract_limitations(conclusion: str) -> list[str]:
    limitations: list[str] = []
    for sentence in split_sentences(conclusion):
        if any(token in sentence for token in ("局限", "限制", "未来工作", "仍然", "尚未")):
            limitations.append(sentence)
    return unique(limitations)


def extract_metrics(text: str) -> list[str]:
    metrics: list[str] = []
    upper_text = text.upper()
    for metric in METRIC_KEYWORDS:
        if metric.upper() in upper_text and metric not in metrics:
            metrics.append(metric)
    return metrics


def extract_baselines(text: str) -> list[str]:
    baselines: list[str] = []
    for sentence in split_sentences(text):
        if not any(token in sentence for token in ("相比", "优于", "baseline", "compared", "against")):
            continue
        for candidate in re.findall(r"\b[A-Z][A-Za-z0-9+._-]{2,}\b", sentence):
            if candidate not in baselines:
                baselines.append(candidate)
    return baselines[:8]


def extract_findings(abstract_zh: str, conclusion: str) -> list[str]:
    findings: list[str] = []
    for source in (abstract_zh, conclusion):
        for sentence in split_sentences(source):
            if any(token in sentence for token in ("优于", "显著", "达到", "提升", "improve", "state-of-the-art")):
                findings.append(sentence)
    return unique(findings)[:4]


def infer_novelty_types(text: str) -> list[str]:
    return unique(match_any(NOVELTY_KEYWORDS, text))[:4]


def relation_hint(match_source: str) -> str | None:
    return RELATION_HINTS.get(normalize_text(match_source))


def paper_neighbor_defaults() -> dict[str, list[dict[str, Any]]]:
    return {"task": [], "method": [], "comparison": []}


def normalize_record(raw_payload: dict[str, Any], semantic_paper: SemanticScholarPaper | None) -> dict[str, Any]:
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
    introduction = "\n\n".join(sections["introduction"])
    method_text = "\n\n".join(sections["method"])
    experiments_text = "\n\n".join(sections["experiments"])
    conclusion_text = "\n\n".join(sections["conclusion"])
    combined_text = title_and_abstract_blob(title, abstract_zh or "", sections)

    raw_tags = conversation.get("tags") if isinstance(conversation.get("tags"), list) else []
    tasks = infer_tasks(combined_text, raw_tags)
    methods = infer_methods(combined_text, raw_tags)
    representations = infer_representations(combined_text)
    modalities = infer_modalities(combined_text, raw_tags)
    inputs, outputs, modalities = infer_inputs_outputs(title, tasks, modalities, representations, combined_text)
    themes = infer_themes(tasks, title)

    summary_one_liner = first_sentence(abstract_zh or "") or first_sentence(conclusion_text or "") or title
    research_problem = extract_research_problem(introduction, abstract_zh or "")
    contributions = extract_core_contributions(abstract_zh or "", conclusion_text)
    claims = extract_bullet_like_sentences([abstract_zh or "", conclusion_text], 3, support="section:Abstract")
    experiment_setup_summary = extract_experiment_setup(experiments_text)
    author_conclusion = extract_author_conclusion(conclusion_text)
    limitations = extract_limitations(conclusion_text)
    findings = extract_findings(abstract_zh or "", conclusion_text)
    novelty_type = infer_novelty_types(combined_text)

    figures = conversation.get("figures") if isinstance(conversation.get("figures"), list) else []
    tables = conversation.get("tables") if isinstance(conversation.get("tables"), list) else []
    figure_table_index = {
        "figures": [
            {"label": normalize_text(str(item.get("figure_label") or "")), "caption": normalize_text(str(item.get("caption") or ""))}
            for item in figures
            if isinstance(item, dict)
        ],
        "tables": [
            {"label": normalize_text(str(item.get("table_label") or "")), "caption": normalize_text(str(item.get("caption") or ""))}
            for item in tables
            if isinstance(item, dict)
        ],
    }

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

    comparison_context = {
        "explicit_baselines": extract_baselines("\n".join([abstract_zh or "", experiments_text])),
        "contrast_methods": [],
        "contrast_notes": unique((contributions + findings)[:3]),
    }

    return {
        "paper_id": paper_id,
        "source_conversation_ids": source_conversation_ids,
        "title": title,
        "authors": semantic_paper.authors if semantic_paper else [],
        "year": year,
        "venue": venue_text or "Unknown",
        "citation_count": citation_count,
        "links": links,
        "translate_created_at": normalize_text(str(conversation.get("created_at") or raw_payload.get("fetched_at") or "")),
        "translate_status": translate_status_payload(conversation),
        "abstract_raw": semantic_paper.abstract_raw if semantic_paper else None,
        "abstract_zh": abstract_zh,
        "summary": {
            "one_liner": summary_one_liner,
            "abstract_summary": abstract_zh,
            "research_value": f"适合作为 {themes[0]} 方向的检索节点。" if themes else None,
            "worth_long_term_graph": bool(tasks or methods or citation_count),
        },
        "research_problem": research_problem,
        "core_contributions": contributions,
        "key_claims": claims,
        "method_core": {
            "approach": first_sentence(method_text) or first_sentence(abstract_zh or ""),
            "innovation": contributions[0] if contributions else None,
            "ingredients": methods,
            "representation": representations,
            "supervision": [],
            "differences": findings[:2],
        },
        "inputs_outputs": {
            "inputs": inputs,
            "outputs": outputs,
            "modalities": modalities,
        },
        "benchmarks_or_eval": {
            "datasets": [],
            "metrics": extract_metrics("\n".join([experiments_text, *[item["caption"] for item in figure_table_index["tables"] if isinstance(item, dict)]])),
            "baselines": comparison_context["explicit_baselines"],
            "findings": findings,
            "experiment_setup_summary": experiment_setup_summary,
        },
        "author_conclusion": author_conclusion,
        "editor_note": None,
        "limitations": limitations,
        "novelty_type": novelty_type,
        "research_tags": {
            "themes": themes,
            "tasks": tasks,
            "methods": methods,
            "modalities": modalities,
            "representations": representations,
        },
        "topics": [],
        "retrieval_profile": {
            "problem_spaces": [],
            "task_axes": [],
            "approach_axes": [],
            "input_axes": [],
            "output_axes": [],
            "modality_axes": [],
            "comparison_axes": [],
        },
        "comparison_context": comparison_context,
        "paper_neighbors": paper_neighbor_defaults(),
        "paper_relations": [],
        "figure_table_index": figure_table_index,
    }


def normalize_raw_file(
    raw_path: Path,
    *,
    fetcher: Any = fetch_json,
) -> dict[str, Any]:
    raw_payload = read_json(raw_path, {})
    if not isinstance(raw_payload, dict):
        raise ValueError(f"{raw_path} must contain a JSON object.")
    conversation = raw_payload.get("conversation")
    if not isinstance(conversation, dict):
        raise ValueError(f"{raw_path} is missing conversation data.")

    title = normalize_title(str(conversation.get("title") or raw_payload.get("paper_id") or ""))
    year = conversation.get("year")
    semantic_paper = None
    try:
        semantic_paper = semantic_scholar_title_match(title, year if isinstance(year, int) else None, fetcher=fetcher)
    except Exception:
        semantic_paper = None
    return normalize_record(raw_payload, semantic_paper)


def iter_raw_files(raw_dir: Path) -> list[Path]:
    if not raw_dir.exists():
        return []
    return sorted(path for path in raw_dir.glob("*.json") if path.is_file())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize translate raw payloads into paper records.")
    parser.add_argument("--raw-dir", required=True, help="Directory containing raw JSON payloads.")
    parser.add_argument("--papers-dir", required=True, help="Directory to write normalized paper JSON files.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    raw_dir = Path(args.raw_dir)
    papers_dir = Path(args.papers_dir)
    papers_dir.mkdir(parents=True, exist_ok=True)

    written = 0
    for raw_path in iter_raw_files(raw_dir):
        record = normalize_raw_file(raw_path)
        paper_id = normalize_text(str(record.get("paper_id") or ""))
        if not paper_id:
            continue
        write_json(papers_dir / f"{paper_id}.json", record)
        written += 1

    print(f"Normalized {written} papers from {raw_dir} into {papers_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
