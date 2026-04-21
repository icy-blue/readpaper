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
SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[。！？!?])\s*|\n+")
DOI_PATTERN = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)
GITHUB_PATTERN = re.compile(r"https?://(?:www\.)?github\.com/[^\s)>\]\"']+", re.IGNORECASE)
LEADING_SECTION_PATTERN = re.compile(r"^(?:#+\s*|\d+(?:\.\d+)*[.)]?\s+)")

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

RESULT_KEYWORDS = ("优于", "显著", "达到", "提升", "state-of-the-art", "improve", "outperform", "sota")
METHOD_KEYWORDS_ZH = ("提出", "构建", "设计", "通过", "采用", "引入", "建立", "框架", "方法")
PROBLEM_KEYWORDS_ZH = ("问题", "挑战", "困难", "缺口", "不足", "受限", "仍然", "缺乏", "脆弱")
GOAL_KEYWORDS_ZH = ("目标", "旨在", "希望", "要解决", "为了解决", "为此", "以实现", "需要")
DISPLAY_SENTENCE_MARKERS = (
    "我们提出",
    "本文提出",
    "我们设计",
    "我们构建",
    "我们引入",
    "我们采用",
    "我们的方法",
    "我们认为",
    "该方法",
    "该框架",
    "CoSMo3D",
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


def strip_inline_urls(text: str) -> str:
    return normalize_text(URL_PATTERN.sub("", text or "")).strip()


def normalize_sentence_candidate(text: str) -> str:
    cleaned = strip_inline_urls(text)
    cleaned = LEADING_SECTION_PATTERN.sub("", cleaned)
    cleaned = re.sub(r"^[-*•]+\s*", "", cleaned)
    cleaned = re.sub(r"\[[0-9,\s]+\]", "", cleaned)
    cleaned = re.sub(r"^(?:如图\s*\d+[a-zA-Z()（）]*所示[,:：，]?\s*)", "", cleaned)
    cleaned = re.sub(r"^(?:整体框架如图\s*\d+\s*所示[。,:：，]?\s*)", "", cleaned)
    if any(token in cleaned for token in ("###", "第 3.", "第3.", "3.2.", "3.3.", "4.1.")):
        for marker in DISPLAY_SENTENCE_MARKERS:
            marker_index = cleaned.find(marker)
            if marker_index <= 0:
                continue
            prefix = cleaned[:marker_index]
            if "###" in prefix or "第" in prefix or "节" in prefix or re.search(r"\d", prefix) or ":" in prefix or "：" in prefix:
                cleaned = cleaned[marker_index:]
                break
    cleaned = re.sub(r"^(?:在此框架下,|为此,|具体而言,|此外,|其中,)\s*", "", cleaned)
    if cleaned.startswith("给定一个 ") and "我们的方法" in cleaned:
        cleaned = cleaned[cleaned.find("我们的方法") :]
    return normalize_text(cleaned)


def sentence_fragment_score(text: str) -> int:
    score = 0
    if any(token in text for token in ("…", "...")):
        score += 2
    if text.startswith(("其中", "此外", "同时", "首先", "然后", "最后")):
        score += 1
    if "##" in text:
        score += 3
    if text.count("，") + text.count(",") >= 3:
        score += 2
    if any(token in text for token in ("损失定义", "形式上", "更多", "参见补充材料", "\\(", "\\[", "λ_", "L_")):
        score += 2
    if len(text) < 14:
        score += 1
    if len(text) > 88:
        score += 1
    return score


def sentence_has_any(text: str, keywords: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in keywords)


def is_result_sentence(text: str) -> bool:
    return sentence_has_any(text, RESULT_KEYWORDS)


def is_method_sentence(text: str) -> bool:
    return sentence_has_any(text, METHOD_KEYWORDS_ZH + ("framework", "pipeline", "align", "encode", "train"))


def is_problem_sentence(text: str) -> bool:
    return sentence_has_any(text, PROBLEM_KEYWORDS_ZH + ("problem", "challenge", "limited", "brittle"))


def is_goal_sentence(text: str) -> bool:
    return sentence_has_any(text, GOAL_KEYWORDS_ZH + ("to address", "to solve", "aim to", "need to"))


def looks_like_section_heading(text: str) -> bool:
    if not text:
        return True
    if text.startswith("#"):
        return True
    if re.match(r"^\d+(?:\.\d+)*[.)]?\s*$", text):
        return True
    if len(text.split()) <= 6 and not re.search(r"[。！？!?，,:;]", text) and all(
        token[:1].isupper() for token in text.split() if token and token[0].isalpha()
    ):
        return True
    return False


def clean_sentence_candidates(texts: list[str]) -> list[str]:
    cleaned: list[str] = []
    for text in texts:
        candidate = normalize_sentence_candidate(text)
        if not candidate or looks_like_section_heading(candidate):
            continue
        if candidate not in cleaned:
            cleaned.append(candidate)
    return cleaned


def shorten_text(text: str | None, max_chars: int) -> str | None:
    if not text:
        return None
    cleaned = normalize_sentence_candidate(text)
    if not cleaned:
        return None
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[: max_chars - 1].rstrip("，,；;：: ") + "…"


def merge_unique_texts(*groups: list[str]) -> list[str]:
    merged: list[str] = []
    for group in groups:
        for item in group:
            cleaned = normalize_text(item)
            if cleaned and cleaned not in merged:
                merged.append(cleaned)
    return merged


def summarize_tag_mix(task: str | None, method: str | None, theme: str | None) -> str | None:
    if task and method:
        return shorten_text(f"把 {task} 放到 {method} 语境里看的一篇代表工作。", 60)
    if task and theme:
        return shorten_text(f"一篇围绕 {theme} 中 {task} 展开的代表性工作。", 60)
    if task:
        return shorten_text(f"一篇围绕 {task} 展开的代表性工作。", 60)
    if method and theme:
        return shorten_text(f"适合用来理解 {theme} 中 {method} 这条路线。", 60)
    if method:
        return shorten_text(f"适合用来快速把握 {method} 这条方法路线。", 60)
    if theme:
        return shorten_text(f"适合作为 {theme} 方向的快速入口。", 60)
    return None


def infer_recommended_route(
    *,
    pipeline_steps: list[str],
    innovations: list[str],
    best_results: list[str],
    findings: list[str],
    comparison_context: dict[str, Any],
) -> str:
    if len(pipeline_steps) >= 2 and innovations:
        return "method"
    if best_results or len(findings) >= 2:
        return "evaluation"
    if (
        ensure_strings(comparison_context.get("explicit_baselines"))
        or ensure_strings(comparison_context.get("contrast_methods"))
        or comparison_context.get("comparison_aspects")
    ):
        return "comparison"
    return "overview"


def build_reading_digest(
    *,
    themes: list[str],
    tasks: list[str],
    methods: list[str],
    modalities: list[str],
    novelty_type: list[str],
    storyline: dict[str, str | None],
    research_problem: dict[str, Any],
    method_core: dict[str, Any],
    findings: list[str],
    best_results: list[str],
    comparison_context: dict[str, Any],
    research_value: dict[str, Any],
    editor_note: dict[str, Any] | None,
) -> dict[str, Any]:
    task = tasks[0] if tasks else None
    method = methods[0] if methods else None
    theme = themes[0] if themes else None
    best_for_parts: list[str] = []
    if tasks:
        best_for_parts.append("想看 " + " / ".join(tasks[:2]))
    elif themes:
        best_for_parts.append("想看 " + themes[0])
    if methods:
        best_for_parts.append("并关注 " + " / ".join(methods[:2]))
    elif novelty_type:
        best_for_parts.append("并关注 " + " / ".join(novelty_type[:2]))
    best_for = shorten_text("适合" + "，".join(best_for_parts) + "的读者。", 70) if best_for_parts else None

    why_read_candidates = merge_unique_texts(
        ensure_strings(editor_note.get("points")) if isinstance(editor_note, dict) else [],
        ensure_strings(research_value.get("points")) if isinstance(research_value, dict) else [],
        best_results,
        findings,
    )
    why_read = [
        item
        for item in (shorten_text(candidate, 72) for candidate in why_read_candidates)
        if item and not item.startswith(("任务：", "任务:", "方法：", "方法:"))
    ][:3]

    storyline_problem = shorten_text(storyline.get("problem"), 70) if storyline.get("problem") and not is_result_sentence(storyline.get("problem") or "") else None
    storyline_method = shorten_text(storyline.get("method"), 70) if storyline.get("method") and is_method_sentence(storyline.get("method") or "") and not is_result_sentence(storyline.get("method") or "") else None
    storyline_outcome = shorten_text(storyline.get("outcome"), 70) if storyline.get("outcome") and is_result_sentence(storyline.get("outcome") or "") else None
    research_problem_summary = shorten_text(research_problem.get("summary"), 70) if research_problem.get("summary") and not is_result_sentence(research_problem.get("summary") or "") and not is_method_sentence(research_problem.get("summary") or "") else None
    approach_summary = shorten_text(method_core.get("approach_summary"), 70) if method_core.get("approach_summary") and is_method_sentence(method_core.get("approach_summary") or "") and not is_result_sentence(method_core.get("approach_summary") or "") else None
    best_result = next((shorten_text(item, 70) for item in best_results if is_result_sentence(item)), None)
    finding_result = next((shorten_text(item, 70) for item in findings if is_result_sentence(item)), None)
    result_headline = next((shorten_text(item, 88) for item in [*best_results, *findings] if is_result_sentence(item)), None)

    return {
        "value_statement": (
            shorten_text((editor_note or {}).get("summary"), 80)
            or shorten_text(research_value.get("summary"), 80)
            or summarize_tag_mix(task, method, theme)
        ),
        "best_for": best_for,
        "why_read": why_read,
        "recommended_route": infer_recommended_route(
            pipeline_steps=ensure_strings(method_core.get("pipeline_steps")),
            innovations=ensure_strings(method_core.get("innovations")),
            best_results=best_results,
            findings=findings,
            comparison_context=comparison_context,
        ),
        "positioning": {
            "task": tasks[:2],
            "modality": modalities[:3],
            "method": methods[:2],
            "novelty": novelty_type[:2],
        },
        "narrative": {
            "problem": storyline_problem or research_problem_summary,
            "method": storyline_method or approach_summary,
            "result": storyline_outcome or best_result or finding_result,
        },
        "result_headline": result_headline,
    }


def infer_editorial_verdict(
    *,
    pipeline_steps: list[str],
    innovations: list[str],
    best_results: list[str],
    findings: list[str],
    comparison_context: dict[str, Any],
) -> str | None:
    has_method_signal = len(pipeline_steps) >= 2 and bool(innovations)
    has_eval_signal = bool(best_results or findings)
    has_comparison_signal = bool(
        ensure_strings(comparison_context.get("explicit_baselines"))
        or ensure_strings(comparison_context.get("contrast_methods"))
        or comparison_context.get("comparison_aspects")
    )
    if has_method_signal and has_eval_signal:
        return "值得精读"
    if has_method_signal or has_eval_signal or has_comparison_signal:
        return "值得浏览"
    if findings:
        return "只记结论"
    return None


def build_editorial_review(
    *,
    themes: list[str],
    tasks: list[str],
    methods: list[str],
    novelty_type: list[str],
    method_core: dict[str, Any],
    findings: list[str],
    best_results: list[str],
    limitations: list[str],
    comparison_context: dict[str, Any],
    editor_note: dict[str, Any] | None,
) -> dict[str, Any]:
    strengths = merge_unique_texts(
        ensure_strings(method_core.get("innovations")),
        best_results,
        findings,
        ensure_strings((editor_note or {}).get("points")) if isinstance(editor_note, dict) else [],
    )
    cautions = [
        item
        for item in (shorten_text(candidate, 72) for candidate in limitations[:3])
        if item
    ][:3]
    position_parts: list[str] = []
    if themes:
        position_parts.append(themes[0])
    if tasks:
        position_parts.append(tasks[0])
    if methods:
        position_parts.append(methods[0])
    elif novelty_type:
        position_parts.append(novelty_type[0])
    research_position = None
    if position_parts:
        research_position = shorten_text("可作为 " + " / ".join(position_parts) + " 的阅读入口或对比样本。", 80)
    next_read_target = (
        str(comparison_context.get("recommended_next_read") or "").strip()
        or (ensure_strings(comparison_context.get("explicit_baselines"))[:1] or [None])[0]
    )
    return {
        "verdict": infer_editorial_verdict(
            pipeline_steps=ensure_strings(method_core.get("pipeline_steps")),
            innovations=ensure_strings(method_core.get("innovations")),
            best_results=best_results,
            findings=findings,
            comparison_context=comparison_context,
        ),
        "strengths": [item for item in (shorten_text(candidate, 72) for candidate in strengths) if item][:3],
        "cautions": cautions,
        "research_position": research_position,
        "next_read_hint": shorten_text(f"可继续对比 {next_read_target}。", 72) if next_read_target else None,
    }


def collect_sentences(
    texts: list[str],
    *,
    keywords: tuple[str, ...] = (),
    max_items: int = 4,
    max_chars: int | None = None,
) -> list[str]:
    values: list[str] = []
    for text in texts:
        for sentence in split_sentences(text):
            cleaned = strip_inline_urls(sentence)
            if not cleaned:
                continue
            if keywords and not any(token in cleaned for token in keywords):
                continue
            if max_chars is not None:
                shortened = shorten_text(cleaned, max_chars)
                if not shortened:
                    continue
                cleaned = shortened
            if cleaned not in values:
                values.append(cleaned)
            if len(values) >= max_items:
                return values
    return values


def pick_sentence(
    texts: list[str],
    *,
    keywords: tuple[str, ...] = (),
    fallback: bool = True,
    max_chars: int = 120,
) -> str | None:
    matches = collect_sentences(texts, keywords=keywords, max_items=1, max_chars=max_chars)
    if matches:
        return matches[0]
    if not fallback:
        return None
    fallback_matches = collect_sentences(texts, max_items=1, max_chars=max_chars)
    return fallback_matches[0] if fallback_matches else None


def select_semantic_sentences(
    texts: list[str],
    *,
    prefer_keywords: tuple[str, ...] = (),
    allow: Any = None,
    deny: Any = None,
    max_items: int = 4,
    max_chars: int = 90,
) -> list[str]:
    ranked: list[tuple[tuple[int, int, int, int], str]] = []
    seen: set[str] = set()
    for source_index, text in enumerate(texts):
        for sentence_index, sentence in enumerate(split_sentences(text)):
            cleaned = normalize_sentence_candidate(sentence)
            if not cleaned or looks_like_section_heading(cleaned):
                continue
            if allow and not allow(cleaned):
                continue
            if deny and deny(cleaned):
                continue
            shortened = shorten_text(cleaned, max_chars)
            if not shortened or shortened in seen:
                continue
            score = (
                0 if prefer_keywords and sentence_has_any(cleaned, prefer_keywords) else 1,
                sentence_fragment_score(cleaned),
                len(shortened),
                source_index,
                sentence_index,
            )
            ranked.append((score, shortened))
            seen.add(shortened)
    ranked.sort(key=lambda item: item[0])
    return [sentence for _, sentence in ranked[:max_items]]


def select_semantic_sentence(
    texts: list[str],
    *,
    prefer_keywords: tuple[str, ...] = (),
    allow: Any = None,
    deny: Any = None,
    max_chars: int = 90,
) -> str | None:
    candidates = select_semantic_sentences(
        texts,
        prefer_keywords=prefer_keywords,
        allow=allow,
        deny=deny,
        max_items=1,
        max_chars=max_chars,
    )
    return candidates[0] if candidates else None


def classify_claim_type(text: str) -> str:
    lowered = text.lower()
    if any(token in text for token in ("局限", "限制", "future work", "仍然存在")):
        return "limitation"
    if any(token in lowered for token in ("ablation", "experiment", "benchmark", "miou", "iou")) or any(
        token in text for token in ("实验", "结果", "优于", "提升", "达到", "显著")
    ):
        return "experiment"
    if any(token in lowered for token in ("can", "generalize", "robust")) or any(
        token in text for token in ("支持", "能够", "泛化", "鲁棒")
    ):
        return "capability"
    return "method"


def extract_bullet_like_sentences(texts: list[str], limit: int, *, support: str) -> list[dict[str, Any]]:
    candidates = collect_sentences(
        texts,
        keywords=("我们提出", "本文提出", "我们展示", "结果表明", "实验表明", "显著优于", "达到", "提升"),
        max_items=limit,
        max_chars=110,
    )
    if not candidates:
        candidates = collect_sentences(texts, max_items=limit, max_chars=110)

    return [
        {
            "claim": sentence,
            "type": classify_claim_type(sentence),
            "support": [support],
            "confidence": "medium",
        }
        for sentence in candidates
    ]


def extract_core_contributions(abstract_zh: str, conclusion: str) -> list[str]:
    sentences = collect_sentences(
        [abstract_zh, conclusion],
        keywords=("我们提出", "本文提出", "我们展示", "我们采用", "结果表明", "实验表明", "设计了", "引入了"),
        max_items=4,
        max_chars=100,
    )
    if not sentences:
        sentences = collect_sentences([abstract_zh], max_items=3, max_chars=100)
    return sentences


def extract_storyline(abstract_zh: str, introduction: str, method_text: str, conclusion: str) -> dict[str, str | None]:
    problem = select_semantic_sentence(
        [introduction, abstract_zh],
        prefer_keywords=PROBLEM_KEYWORDS_ZH + ("problem", "challenge", "task", "brittle"),
        allow=lambda text: (is_problem_sentence(text) or "任务" in text or "开放世界" in text) and not is_result_sentence(text) and not text.startswith(("我们提出", "本文提出")),
        deny=lambda text: is_result_sentence(text),
        max_chars=70,
    )
    method = select_semantic_sentence(
        [abstract_zh, method_text],
        prefer_keywords=("我们提出", "本文提出", "设计", "构建", "双分支", "规范空间", "框架", "pipeline", "framework"),
        allow=lambda text: is_method_sentence(text) and not is_result_sentence(text),
        deny=lambda text: is_result_sentence(text) or text.startswith("给定一个 "),
        max_chars=70,
    )
    outcome = select_semantic_sentence(
        [conclusion, abstract_zh],
        prefer_keywords=RESULT_KEYWORDS,
        allow=is_result_sentence,
        max_chars=70,
    )
    return {"problem": problem, "method": method, "outcome": outcome}


def extract_research_problem(introduction: str, abstract_zh: str) -> dict[str, Any]:
    summary = select_semantic_sentence(
        [introduction, abstract_zh],
        prefer_keywords=PROBLEM_KEYWORDS_ZH + ("problem", "challenge", "task"),
        allow=lambda text: (is_problem_sentence(text) or "任务" in text or "场景" in text) and not is_result_sentence(text) and not text.startswith(("我们提出", "本文提出")),
        deny=lambda text: is_result_sentence(text) or is_method_sentence(text),
        max_chars=100,
    )
    gaps = select_semantic_sentences(
        [introduction, abstract_zh],
        prefer_keywords=("现有", "已有", "仍然", "难以", "不足", "缺乏", "受限", "brittle", "limited", "challenge"),
        allow=lambda text: sentence_has_any(text, ("现有", "已有", "仍然", "难以", "不足", "缺乏", "受限", "brittle", "limited", "challenge")) and not is_result_sentence(text),
        deny=lambda text: is_result_sentence(text) or text.startswith(("我们提出", "本文提出")),
        max_items=4,
        max_chars=90,
    )
    goal = select_semantic_sentence(
        [introduction, abstract_zh],
        prefer_keywords=GOAL_KEYWORDS_ZH + ("实现", "建立", "to address", "to solve", "aim to"),
        allow=lambda text: is_goal_sentence(text) and "我们提出" not in text and "本文提出" not in text and not is_result_sentence(text) and not is_method_sentence(text),
        deny=lambda text: is_result_sentence(text) or text.startswith(("心理物理学研究", "心理物理学证据")),
        max_chars=100,
    )
    return {
        "summary": summary,
        "gaps": [item for item in gaps if item != summary and item != goal][:4],
        "goal": goal,
    }


def extract_experiment_setup(experiments: str) -> str | None:
    for paragraph in paragraph_blocks(experiments):
        if any(token in paragraph for token in ("dataset", "数据集", "benchmark", "baseline", "实验", "评估")):
            return shorten_text(paragraph, 180)
    return shorten_text(first_sentence(experiments), 180)


def extract_author_conclusion(conclusion: str) -> str | None:
    if not conclusion:
        return None
    sentences = split_sentences(conclusion)
    if not sentences:
        return None
    return shorten_text(" ".join(sentences[:2]), 180)


def extract_limitations(conclusion: str) -> list[str]:
    return collect_sentences(
        [conclusion],
        keywords=("局限", "限制", "未来工作", "仍然", "尚未", "future work", "limitation"),
        max_items=4,
        max_chars=100,
    )


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
    findings = collect_sentences(
        [abstract_zh, conclusion],
        keywords=("优于", "显著", "达到", "提升", "improve", "state-of-the-art", "outperform"),
        max_items=4,
        max_chars=80,
    )
    if findings:
        return findings
    return collect_sentences([conclusion], max_items=2, max_chars=80)


def extract_pipeline_steps(method_text: str, abstract_zh: str) -> list[str]:
    steps = select_semantic_sentences(
        paragraph_blocks(method_text),
        prefer_keywords=("首先", "然后", "最后", "通过", "使用", "采用", "encode", "align", "train"),
        allow=lambda text: is_method_sentence(text) and not is_result_sentence(text),
        deny=lambda text: is_result_sentence(text),
        max_items=4,
        max_chars=90,
    )
    if steps:
        return steps
    return select_semantic_sentences(
        [method_text, abstract_zh],
        prefer_keywords=("通过", "采用", "构建", "设计", "encode", "align", "train"),
        allow=lambda text: is_method_sentence(text) and not is_result_sentence(text),
        deny=lambda text: is_result_sentence(text),
        max_items=4,
        max_chars=90,
    )


def extract_method_core(method_text: str, abstract_zh: str, contributions: list[str], findings: list[str]) -> dict[str, Any]:
    approach_summary = select_semantic_sentence(
        [abstract_zh, method_text],
        prefer_keywords=("我们提出", "本文提出", "设计", "构建", "双分支", "规范空间", "框架", "pipeline", "framework"),
        allow=lambda text: is_method_sentence(text) and not is_result_sentence(text),
        deny=lambda text: is_result_sentence(text) or text.startswith("给定一个 "),
        max_chars=88,
    )
    innovations = select_semantic_sentences(
        [abstract_zh, "\n".join(contributions), *paragraph_blocks(method_text)[:12]],
        prefer_keywords=("创新", "提出", "引入", "设计", "构建", "数据集", "双分支", "canonical", "对齐", "校准"),
        allow=lambda text: (sentence_has_any(text, ("提出", "引入", "设计", "构建", "创建", "双分支", "数据集", "对齐", "校准")) or is_method_sentence(text)) and not is_result_sentence(text),
        deny=lambda text: is_result_sentence(text) or sentence_has_any(text, ("损失定义", "形式上", "更多数据集细节", "补充材料")),
        max_items=4,
        max_chars=78,
    )
    if not innovations:
        innovations = select_semantic_sentences(
            ["\n".join(contributions)],
            prefer_keywords=("提出", "引入", "设计", "构建"),
            allow=lambda text: is_method_sentence(text) and not is_result_sentence(text),
            deny=lambda text: is_result_sentence(text),
            max_items=3,
            max_chars=90,
        )
    differences = collect_sentences(
        ["\n".join(findings), "\n".join(innovations)],
        keywords=("优于", "提升", "不同", "区别", "相比", "contrast"),
        max_items=3,
        max_chars=90,
    )
    return {
        "approach_summary": approach_summary,
        "pipeline_steps": extract_pipeline_steps(method_text, abstract_zh),
        "innovations": innovations[:4],
        "differences": differences[:3],
    }


def build_research_value(themes: list[str], tasks: list[str], methods: list[str], findings: list[str]) -> dict[str, Any]:
    theme_label = themes[0] if themes else "相关方向"
    summary = shorten_text(f"适合作为 {theme_label} 方向的持续阅读入口。", 60)
    points: list[str] = []
    if tasks:
        points.append(f"适合放到 {' / '.join(tasks[:2])} 的问题线上对比阅读。")
    if methods:
        points.append(f"可用于理解 {' / '.join(methods[:2])} 这条方法路线。")
    if findings:
        points.append(findings[0])
    return {
        "summary": summary,
        "points": [item for item in (shorten_text(point, 80) for point in points) if item][:3],
    }


def build_editor_note(themes: list[str], comparison_baselines: list[str], findings: list[str]) -> dict[str, Any] | None:
    if not themes and not comparison_baselines and not findings:
        return None
    summary = None
    if themes:
        summary = shorten_text(f"可作为 {themes[0]} 方向的代表样本。", 120)
    elif comparison_baselines:
        summary = shorten_text(f"适合与 {comparison_baselines[0]} 做对比阅读。", 120)
    elif findings:
        summary = shorten_text("结果信号明确，值得继续读。", 120)
    points: list[str] = []
    if comparison_baselines:
        points.append(f"可优先与 {comparison_baselines[0]} 对比阅读。")
    if findings:
        points.append(findings[0])
    return {
        "summary": summary,
        "points": [item for item in (shorten_text(point, 90) for point in points) if item][:3],
    }


def extract_comparison_aspects(innovations: list[str], findings: list[str]) -> list[dict[str, str]]:
    aspects: list[dict[str, str]] = []
    if innovations:
        aspects.append(
            {
                "aspect": "method",
                "difference": innovations[0],
            }
        )
    if findings:
        aspects.append(
            {
                "aspect": "result",
                "difference": findings[0],
            }
        )
    return aspects[:3]


def infer_figure_role(label: str, caption: str, *, is_table: bool) -> str:
    lowered = f"{label} {caption}".lower()
    if "ablation" in lowered:
        return "ablation"
    if "failure" in lowered:
        return "failure_case"
    if any(token in lowered for token in ("framework", "overview", "pipeline", "architecture")):
        return "method_overview"
    if any(token in lowered for token in ("qualitative", "visual", "comparison")) and not is_table:
        return "qualitative_result"
    if is_table or any(token in lowered for token in ("quantitative", "evaluation", "result", "miou", "iou")):
        return "quantitative_result"
    return "method_overview" if not is_table and label.endswith("1") else "qualitative_result"


def infer_item_importance(label: str, role: str) -> str:
    if label.endswith("1") or role in {"method_overview", "quantitative_result"}:
        return "high"
    if role in {"ablation", "qualitative_result"}:
        return "medium"
    return "low"


def normalize_figure_table_items(items: list[dict[str, Any]], *, label_key: str, is_table: bool) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        label = normalize_text(str(item.get(label_key) or ""))
        caption = normalize_text(str(item.get("caption") or ""))
        if not label and not caption:
            continue
        role = infer_figure_role(label, caption, is_table=is_table)
        normalized.append(
            {
                "label": label,
                "caption": caption,
                "role": role,
                "importance": infer_item_importance(label, role),
            }
        )
    return normalized


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

    research_problem = extract_research_problem(introduction, abstract_zh or "")
    contributions = extract_core_contributions(abstract_zh or "", conclusion_text)
    findings = extract_findings(abstract_zh or "", conclusion_text)
    method_core_summary = extract_method_core(method_text, abstract_zh or "", contributions, findings)
    storyline = extract_storyline(abstract_zh or "", introduction, method_text, conclusion_text)
    summary_one_liner = shorten_text(
        "；".join(
            [
                item
                for item in (
                    storyline.get("problem"),
                    storyline.get("method"),
                    storyline.get("outcome"),
                )
                if item
            ]
        )
        or first_sentence(abstract_zh or "")
        or first_sentence(conclusion_text or "")
        or title,
        120,
    ) or title
    claims = extract_bullet_like_sentences([abstract_zh or "", conclusion_text], 3, support="section:Abstract")
    experiment_setup_summary = extract_experiment_setup(experiments_text)
    author_conclusion = extract_author_conclusion(conclusion_text)
    limitations = extract_limitations(conclusion_text)
    novelty_type = infer_novelty_types(combined_text)

    figures = conversation.get("figures") if isinstance(conversation.get("figures"), list) else []
    tables = conversation.get("tables") if isinstance(conversation.get("tables"), list) else []
    figure_table_index = {
        "figures": normalize_figure_table_items(figures, label_key="figure_label", is_table=False),
        "tables": normalize_figure_table_items(tables, label_key="table_label", is_table=True),
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
        "comparison_aspects": extract_comparison_aspects(method_core_summary["innovations"], findings),
        "recommended_next_read": None,
    }
    if comparison_context["explicit_baselines"]:
        comparison_context["recommended_next_read"] = comparison_context["explicit_baselines"][0]
    research_value = build_research_value(themes, tasks, methods, findings)
    editor_note = build_editor_note(themes, comparison_context["explicit_baselines"], findings)
    method_core_payload = {
        "approach_summary": method_core_summary["approach_summary"],
        "pipeline_steps": method_core_summary["pipeline_steps"],
        "innovations": method_core_summary["innovations"],
        "ingredients": methods,
        "representation": representations,
        "supervision": [],
        "differences": method_core_summary["differences"],
    }
    benchmarks_payload = {
        "datasets": [],
        "metrics": extract_metrics("\n".join([experiments_text, *[item["caption"] for item in figure_table_index["tables"] if isinstance(item, dict)]])),
        "baselines": comparison_context["explicit_baselines"],
        "findings": findings,
        "best_results": findings[:1],
        "experiment_setup_summary": experiment_setup_summary,
    }
    reading_digest = build_reading_digest(
        themes=themes,
        tasks=tasks,
        methods=methods,
        modalities=modalities,
        novelty_type=novelty_type,
        storyline=storyline,
        research_problem=research_problem,
        method_core=method_core_payload,
        findings=findings,
        best_results=benchmarks_payload["best_results"],
        comparison_context=comparison_context,
        research_value=research_value,
        editor_note=editor_note,
    )
    editorial_review = build_editorial_review(
        themes=themes,
        tasks=tasks,
        methods=methods,
        novelty_type=novelty_type,
        method_core=method_core_payload,
        findings=findings,
        best_results=benchmarks_payload["best_results"],
        limitations=limitations,
        comparison_context=comparison_context,
        editor_note=editor_note,
    )

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
        "summary": {
            "one_liner": summary_one_liner,
            "abstract_summary": shorten_text(abstract_zh, 220),
            "research_value": research_value,
            "worth_long_term_graph": bool(tasks or methods or citation_count),
        },
        "reading_digest": reading_digest,
        "storyline": storyline,
        "research_problem": research_problem,
        "core_contributions": contributions,
        "key_claims": claims,
        "method_core": method_core_payload,
        "inputs_outputs": {
            "inputs": inputs,
            "outputs": outputs,
            "modalities": modalities,
        },
        "benchmarks_or_eval": benchmarks_payload,
        "author_conclusion": author_conclusion,
        "editor_note": editor_note,
        "editorial_review": editorial_review,
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
    fetcher: Any = fetch_json,
    existing_record: dict[str, Any] | None = None,
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
    return merge_existing_enrichment(normalize_record(raw_payload, semantic_paper), existing_record)


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
        raw_payload = read_json(raw_path, {})
        raw_paper_id = normalize_text(str(raw_payload.get("paper_id") or ""))
        existing_record = read_json(papers_dir / f"{raw_paper_id}.json", {}) if raw_paper_id else None
        record = normalize_raw_file(raw_path, existing_record=existing_record)
        paper_id = normalize_text(str(record.get("paper_id") or raw_paper_id))
        if not paper_id:
            continue
        write_json(papers_dir / f"{paper_id}.json", record)
        written += 1

    print(f"Normalized {written} papers from {raw_dir} into {papers_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
