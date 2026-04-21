# Output Template v2

Use these outputs exactly.

## Markdown Site

Write these files under `outputs/site/`:

- `index.md`
- `site-index.json`
- `index.html`
- `papers/<paper-id>.json`
- `papers/<paper-id>.md`
- `assets/*`

## `index.md`

Include:

- title
- generation time
- total paper count
- current discovery flow note
- recent papers
- theme / task / method quick filter sections
- a short description of the homepage-first reading strategy

## Per-paper Markdown

Each `papers/<paper-id>.md` should include:

- title and metadata
- story / research problem
- method
- evaluation
- editorial judgment
- comparison and next-read hints
- claims / figures / tables / abstracts / relations near the end

The Markdown page should feel like a reading flow, not a flat field dump.

## `site-index.json`

Keep only homepage / discovery fields.

Do not duplicate the full canonical record here.

## `papers/<paper-id>.json`

Each detail JSON should keep:

- `canonical`
- `neighbors`

The frontend detail page may derive its own local display state from this payload.

## HTML Site

Generate a React single-page site from structured data and publish the build artifacts with Python.

The site should include:

- homepage search and filters
- featured reading cards
- detail pages focused on story / method / evaluation / editorial / comparison
- on-demand loading of `papers/<paper-id>.json`
- links between SPA routes and Markdown counterparts
