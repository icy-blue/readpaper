# Forest Schema v2

The site is built from canonical paper records plus derived site payloads under `outputs/site/`.

## Derived Outputs

- `outputs/site/site-index.json`
- `outputs/site/papers/<paper-id>.json`
- `outputs/site/index.md`
- `outputs/site/index.html`
- `outputs/site/assets/*`

## `site-index.json`

`site-index.json` powers homepage discovery only.

Expected top-level fields:

- `generated_at`
- `paper_count`
- `site_meta`
- `navigation`
- `filters`
- `featured`
- `papers`
- `recent_titles`

Each homepage paper card should keep only discovery-facing fields:

- title / authors / venue / year
- links
- `story.paper_one_liner`
- `editorial.research_position`
- `editorial.graph_worthy`
- `taxonomy.themes|tasks|methods|modalities|novelty_types`
- compatibility `source` fields if the generators still need them, but the published site no longer exposes standalone paper pages

## Detail View Model

Each `outputs/site/papers/<paper-id>.json` should expose homepage detail data only:

- `canonical`: the full canonical paper record
- `neighbors`: derived `problem` / `method` / `evaluation` neighbor groups

No canonical paper file should be mutated to store those neighbors.

## Neighbor Rules

- `problem` neighbors prefer shared `discovery_axes.problem`, and may fall back to `taxonomy.tasks`
- `method` neighbors prefer shared `discovery_axes.method`, then `taxonomy.methods` or `method.representations`
- `evaluation` neighbors prefer explicit `comparison.next_read`, then shared `discovery_axes.evaluation`, then explicit baseline / dataset / metric matches
- keep at most 3 neighbors per dimension
- each neighbor must include `reason`, `reason_short`, `score_level`, and `shared_signals`

## Filters

Build homepage filters only from canonical taxonomy:

- `themes`
- `tasks`
- `methods`

Do not derive homepage filters from UI-only fields.
