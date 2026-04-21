---
name: translate-paper-forest
description: Build a local research knowledge forest from papers stored on translate.icydev.cn using canonical paper records plus fully derived site payloads.
---

# Translate Paper Forest

## Overview

Use this skill to turn `translate.icydev.cn` into a local, durable, research-facing paper memory.

The repo now uses:

- canonical paper records in `outputs/papers/`
- analysis-layer meta artifacts in `outputs/meta/`
- fully derived site payloads in `outputs/site/`

## Read First

1. [references/paper-schema.md](references/paper-schema.md)
2. [references/analysis-rubric.md](references/analysis-rubric.md)
3. [references/meta-contract.md](references/meta-contract.md)
4. [references/forest-schema.md](references/forest-schema.md)
5. [references/output-template.md](references/output-template.md)

## Main Scripts

- [scripts/fetch_translate_papers.py](scripts/fetch_translate_papers.py)
- [scripts/normalize_papers.py](scripts/normalize_papers.py)
- [scripts/build_registry.py](scripts/build_registry.py)
- [scripts/build_site_derivatives.py](scripts/build_site_derivatives.py)
- [scripts/render_markdown_site.py](scripts/render_markdown_site.py)
- [scripts/render_html_dashboard.py](scripts/render_html_dashboard.py)

Single-paper extraction uses:

- [skills/extract-paper-meta/SKILL.md](skills/extract-paper-meta/SKILL.md)

## Default Workflow

1. Fetch new raw payloads.
2. Extract per-paper meta artifacts with the repo-local `extract-paper-meta` skill.
3. Assemble canonical paper records:

```bash
python3 scripts/normalize_papers.py \
  --raw-dir outputs/raw \
  --meta-dir outputs/meta \
  --papers-dir outputs/papers
```

4. Rebuild the dedupe registry:

```bash
python3 scripts/build_registry.py \
  --papers-dir outputs/papers \
  --registry state/paper_registry.json
```

5. Build site-derived JSON payloads:

```bash
python3 scripts/build_site_derivatives.py \
  --papers-dir outputs/papers \
  --site-dir outputs/site
```

6. Render Markdown:

```bash
python3 scripts/render_markdown_site.py \
  --papers-dir outputs/papers \
  --site-dir outputs/site
```

7. Build the frontend and publish the SPA:

```bash
npm run build:web

python3 scripts/render_html_dashboard.py \
  --site-index-json outputs/site/site-index.json \
  --output outputs/site/index.html
```

## Core Rules

- Treat `translate.icydev.cn` as read-only.
- `outputs/papers/` stores canonical paper records only.
- Do not write site-derived neighbors, retrieval indexes, or UI fallbacks back into canonical paper records.
- Keep taxonomy canonical in English.
- Keep human-facing summaries in Chinese.
