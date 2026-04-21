---
name: translate-paper-forest
description: Build a local research knowledge forest from papers stored on translate.icydev.cn. Use when Codex needs to fetch translated paper metadata and sections from the translate platform, avoid reprocessing already-analyzed papers with a local registry, extract structured knowledge records for each paper, compare papers across themes and methods, and render Markdown plus static HTML visualizations for personal research use.
---

# Translate Paper Forest

## Overview

Use this skill to turn `translate.icydev.cn` into a local, durable, research-facing paper memory.

The skill treats the translate platform as a read-only source. It fetches paper conversations, skips already-processed items with a file-backed registry, writes one normalized knowledge record per paper, rebuilds a multi-view knowledge forest, and renders both Markdown and static HTML outputs.

## Built-in Resources

Read these references before writing or updating paper records:

1. [references/paper-schema.md](references/paper-schema.md)
2. [references/analysis-rubric.md](references/analysis-rubric.md)
3. [references/forest-schema.md](references/forest-schema.md)
4. [references/output-template.md](references/output-template.md)

Use these scripts directly instead of inventing ad hoc workflows:

- [scripts/fetch_translate_papers.py](scripts/fetch_translate_papers.py)
- [scripts/normalize_papers.py](scripts/normalize_papers.py)
- [scripts/build_registry.py](scripts/build_registry.py)
- [scripts/backfill_paper_neighbors.py](scripts/backfill_paper_neighbors.py)
- [scripts/render_markdown_site.py](scripts/render_markdown_site.py)
- [scripts/render_html_dashboard.py](scripts/render_html_dashboard.py)

Registry and outputs live here:

- [state/paper_registry.json](state/paper_registry.json)
- `outputs/fetch/`
- `outputs/raw/`
- `outputs/papers/`
- `outputs/site/`

## Default Workflow

### 1. Fetch candidate papers from translate

Run:

```bash
python scripts/fetch_translate_papers.py \
  --registry state/paper_registry.json \
  --manifest outputs/fetch/latest-fetch.json \
  --raw-dir outputs/raw \
  --limit 20
```

This fetches `translate.icydev.cn` conversations through the existing read-only endpoints, collapses duplicates by title/year/venue, and writes raw JSON payloads only for papers that are new relative to the registry.

If the user wants a larger refresh, increase `--limit`.  
If the user wants a full pass without registry skipping, add `--include-known`.

### 2. Read the fetch manifest and raw paper payloads

Open `outputs/fetch/latest-fetch.json`.

If `new_paper_count` is `0`, do not fabricate work. Rebuild the site from existing paper records unless the user asked for a refresh.

For each new paper, read the corresponding raw JSON file in `outputs/raw/`.

### 3. Normalize raw payloads into paper records

Run:

```bash
python scripts/normalize_papers.py \
  --raw-dir outputs/raw \
  --papers-dir outputs/papers
```

This is the only supported paper-record generation entrypoint.

Important rules:

- Follow [references/paper-schema.md](references/paper-schema.md) exactly.
- Prefer `translate.icydev.cn` for translated content, section state, and `links.pdf`.
- Use Semantic Scholar as the preferred enrichment source for `authors`, `abstract_raw`, and `citation_count`.
- Do not override `conversation.pdf_url` with an external PDF.
- Leave `topics`, `paper_relations`, and `editor_note` empty unless there is grounded signal.

### 4. Update the dedupe registry

After writing or updating paper records, run:

```bash
python scripts/build_registry.py \
  --papers-dir outputs/papers \
  --registry state/paper_registry.json
```

This registry is the persistent memory that prevents repeated AI extraction for already-processed papers.

### 5. Backfill per-paper comparison context and neighbors

Run:

```bash
python scripts/backfill_paper_neighbors.py \
  --papers-dir outputs/papers
```

This upgrades existing paper JSON records to the current schema:

- remove legacy `related_papers`
- add `comparison_context`
- add `paper_neighbors`

### 6. Rebuild the reading site

Run:

```bash
python scripts/render_markdown_site.py \
  --papers-dir outputs/papers \
  --site-dir outputs/site
```

This generates:

- `outputs/site/index.md`
- `outputs/site/paper-neighbors.json`
- `outputs/site/papers/<paper-id>.md`

The main reading flow should expose:

- `首页目录`
- `单篇论文页`
- `任务近邻`
- `方法近邻`
- `对比方法近邻`

Compatibility placeholders may still be written for the old global view pages, but they are no longer first-class outputs.

### 7. Render the static HTML dashboard

Run:

```bash
python scripts/render_html_dashboard.py \
  --neighbors-json outputs/site/paper-neighbors.json \
  --output outputs/site/index.html
```

Generate HTML from structured data, not from free-form Codex-authored markup. The HTML should remain lightweight and local-first.

## Decision Rules

- Default ingest mode is new papers only.
- Use the registry as the source of truth for “already processed”.
- If two conversations refer to the same paper, collapse them into one canonical paper id and keep all source conversation ids.
- If the payload is incomplete, still write a paper record when enough signal exists, but mark it as partial.
- If no paper records exist yet, render an empty but valid site and dashboard.

## Output Rules

- Default to Chinese for all human-facing summaries and section labels.
- Keep paper titles, venue names, method names, dataset names, and URLs in original form.
- Keep JSON records machine-readable and stable.
- Keep Markdown concise and scannable.
- Keep Mermaid graphs readable for small-to-medium libraries; prefer signal over density.

## Updating The Skill

Update the reference files instead of bloating this file:

- use `references/paper-schema.md` for normalized record changes
- use `references/analysis-rubric.md` for extraction heuristics
- use `references/forest-schema.md` for view and clustering logic
- use `references/output-template.md` for rendered artifact structure
