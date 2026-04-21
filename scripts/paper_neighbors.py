#!/usr/bin/env python3
"""Compatibility exports for the old paper_neighbors module name."""

from __future__ import annotations

from build_site_derivatives import build_site_payload, ensure_strings, load_papers, write_json

__all__ = ["build_site_payload", "ensure_strings", "load_papers", "write_json"]
