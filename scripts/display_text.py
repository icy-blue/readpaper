#!/usr/bin/env python3
"""Helpers for human-facing display text normalization."""

from __future__ import annotations

import re
import unicodedata


CJK_CHARS = "\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff"
CJK_RE = re.compile(rf"[{CJK_CHARS}]")
WHITESPACE_RE = re.compile(r"\s+")


def collapse_whitespace(value: str) -> str:
    return WHITESPACE_RE.sub(" ", value).strip()


def contains_cjk(value: str) -> bool:
    return bool(CJK_RE.search(value))


def convert_halfwidth_punctuation(value: str) -> str:
    text = value
    replacements = {
        ",": "，",
        ":": "：",
        ";": "；",
        "!": "！",
        "?": "？",
    }
    for halfwidth, fullwidth in replacements.items():
        text = re.sub(rf"(?<=[{CJK_CHARS}]){re.escape(halfwidth)}(?=\S)", fullwidth, text)
        text = re.sub(rf"(?<=\S){re.escape(halfwidth)}(?=[{CJK_CHARS}])", fullwidth, text)
        text = re.sub(rf"(?<=[{CJK_CHARS}）]){re.escape(halfwidth)}(?=$|\s|[”’\"'])", fullwidth, text)

    text = re.sub(rf"(?<=[{CJK_CHARS}])\((?=\S)", "（", text)
    text = re.sub(rf"(?<=\S)\)(?=[{CJK_CHARS}])", "）", text)
    text = re.sub(rf"(?<=\S)\)(?=$|\s|[，。：；！？、”’\"'])", "）", text)
    return text


def insert_cjk_latin_spacing(value: str) -> str:
    text = value
    text = re.sub(rf"([{CJK_CHARS}])([A-Za-z0-9])", r"\1 \2", text)
    text = re.sub(rf"([A-Za-z0-9])([{CJK_CHARS}])", r"\1 \2", text)
    return text


def tighten_cjk_punctuation_spacing(value: str) -> str:
    text = value
    text = re.sub(r"\s*([，。：；！？、])\s*", r"\1", text)
    text = re.sub(r"\s*（\s*", "（", text)
    text = re.sub(r"\s*）\s*", "）", text)
    return text


def normalize_display_text(value: str) -> str:
    text = unicodedata.normalize("NFC", value or "")
    text = text.replace("∗", " ").replace("*", " ")
    text = collapse_whitespace(text)
    if not text or not contains_cjk(text):
        return text
    text = convert_halfwidth_punctuation(text)
    text = insert_cjk_latin_spacing(text)
    text = tighten_cjk_punctuation_spacing(text)
    return collapse_whitespace(text)


def normalize_display_optional_string(value: object) -> str | None:
    if value is None or not isinstance(value, str):
        return None
    cleaned = normalize_display_text(value)
    return cleaned or None
