# Output Template

Use these outputs exactly.

## Markdown site

Write these files under `outputs/site/`:

- `index.md`
- `paper-neighbors.json`
- `index.html`
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
- links block
- one-line conclusion
- English / Chinese abstract when available
- research problem
- core contributions
- key claims with support
- method core
- inputs / outputs when available
- evaluation snapshot
- author conclusion / editor note when available
- limitations
- research tags
- topics / paper relations when available
- comparison context
- task / method / comparison neighbors
- figure / table index

Do not add a dedicated `retrieval_profile` section to the reading pages.

## `paper-neighbors.json`

Each paper payload should retain:

- `links`
- `research_problem`
- `core_contributions`
- `retrieval_profile`
- `comparison_context`
- `paper_neighbors`
- `topics`
- `paper_relations`

At the top level, include:

- `site_meta`
- `navigation`
- `filters`

## HTML site

Generate a React single-page site from structured data and publish the build artifacts with Python.

The site should include:

- summary cards
- SPA local navigation
- search and filter controls
- links between SPA detail routes and Markdown counterparts
- single-paper detail routes with reading-focused layout
- author / link metadata
- abstract, problem, contribution, evaluation, relation, and neighbor sections
