# Output Template

Use these outputs exactly.

## Markdown site

Write these files under `outputs/site/`:

- `index.md`
- `paper-neighbors.json`
- `index.html`
- `papers/<paper-id>.json`
- `papers/<paper-id>.md`
- `assets/*`

## `index.md`

Include:

- title
- generation time
- total paper count
- SPA-first navigation
- current reading strategy note
- recent papers
- theme/task/method quick filter sections

## Per-paper Markdown

Each `papers/<paper-id>.md` should include:

- title and metadata
- a decision layer with `reading_digest` and `editorial_review`
- a understanding layer with research problem, method core, evaluation, and comparison context
- a materials layer folded toward the end for claims, figure / table index, abstracts, neighbors, retrieval profile, and debug-style structured data when needed

The Markdown page should feel like a reading flow, not a flat archive dump.

## `paper-neighbors.json`

Each paper payload should retain only homepage / discovery fields:

- `title`
- `authors`
- `year`
- `venue`
- `reading_digest`
- `editorial_review`
- `links`
- `summary`
- `research_tags`
- `paper_neighbors`

At the top level, include:

- `site_meta`
- `navigation`
- `filters`

## `papers/<paper-id>.json`

Each per-paper detail JSON should retain the full reading payload used by the SPA detail page, including:

- `research_problem`
- `core_contributions`
- `method_core`
- `benchmarks_or_eval`
- `retrieval_profile`
- `comparison_context`
- `paper_neighbors`
- `topics`
- `paper_relations`
- `figure_table_index`
- abstracts, claims, editorial notes, and supporting metadata

## HTML site

Generate a React single-page site from structured data and publish the build artifacts with Python.

The site should include:

- summary cards sourced from `reading_digest`
- a decision / understanding / materials reading flow
- SPA local navigation
- search and filter controls
- links between SPA detail routes and Markdown counterparts
- single-paper detail routes with reading-focused layout and per-paper JSON fetch
- author / link metadata
- editorial verdicts, reading routes, abstract / problem / contribution / comparison / evaluation sections, and folded materials panels
