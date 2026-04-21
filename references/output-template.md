# Output Template

Use these outputs exactly.

## Markdown site

Write these files under `outputs/site/`:

- `index.md`
- `paper-neighbors.json`
- `index.html`
- `papers/<paper-id>.md`
- `papers/<paper-id>.html`
- `theme-map.md`
- `method-map.md`
- `timeline.md`
- `relationship-graph.md`
- `theme-map.html`
- `method-map.html`
- `timeline.html`
- `relationship-graph.html`

## `index.md`

Include:

- title
- generation time
- total paper count
- HTML-first navigation
- current reading strategy note
- recent papers
- theme/task/method quick filter sections

## Compatibility pages

`theme-map.md`, `method-map.md`, `timeline.md`, and `relationship-graph.md` should remain as short compatibility pages that point readers back to single-paper pages.

## Per-paper Markdown

Each `papers/<paper-id>.md` should include:

- title and metadata
- link back to HTML detail page
- one-line conclusion
- key claims with support
- method core
- inputs/outputs when available
- evaluation snapshot
- limitations
- research tags
- comparison context
- task neighbors
- method neighbors
- comparison neighbors
- figure/table index

## HTML site

Generate the HTML pages from structured data with Python, not by hand.

The site should include:

- summary cards
- local navigation
- recent paper list
- filter sections by theme, task, and method
- links between HTML and Markdown counterparts
- per-paper HTML detail pages with reading-focused layout
- compatibility placeholder pages for old global views
