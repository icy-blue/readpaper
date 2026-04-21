# Analysis Rubric

Extract knowledge for future retrieval, comparison, and idea generation.

## Priority order

1. The core research problem
2. The paper's concrete contributions
3. The strongest claims and their support
4. The method route and comparison hooks
5. Whether the paper deserves a durable place in the long-term graph

## Extraction guidance

- `abstract_zh`: prefer the translated abstract unit from the conversation.
- `abstract_raw`: prefer Semantic Scholar abstract; otherwise keep `null`.
- `research_problem`: write the shortest grounded formulation of the problem.
- `storyline`: compress the paper into `problem`, `method`, and `outcome` for first-screen scanning.
- `core_contributions`: keep 2 to 4 concrete items.
- `key_claims`: keep 2 to 5 falsifiable or comparable claims.
- `key_claims[].type`: classify each claim as `method`, `experiment`, `capability`, or `limitation` when possible.
- `author_conclusion`: prefer conclusion-section wording over editor paraphrase.
- `editor_note`: reserve for your own grounded reading note; keep it as `summary + points`, or leave it empty when unavailable.
- `experiment_setup_summary`: summarize datasets / settings / evaluation setup, not the whole result section.
- `figure_table_index`: add `role` and `importance` so the front end can prioritize what to read first.

## Similarity and difference rules

Before matching papers, compress each paper into a retrieval-facing profile:

- `problem_spaces`
- `task_axes`
- `approach_axes`
- `input_axes`
- `output_axes`
- `modality_axes`
- `comparison_axes`

Use `comparison_context` for machine-readable comparison cues and `paper_neighbors` for the actual retrieved neighbor list.

Each neighbor should include:

- `match_source`
- `reason`
- `reason_short`
- `score_level`
- `shared_signals`
- `relation_hint`

## Partial translation handling

- Prefer visible evidence from translated sections, figures, and tables.
- If translation is incomplete, keep the record partial rather than inventing missing details.
- Use `limitations` only for paper-side limitations, not extraction caveats.

## Source priority

- Prefer `translate.icydev.cn` for translated content, section state, and PDF link.
- Prefer Semantic Scholar for `authors`, `abstract_raw`, `citation_count`, and metadata enrichment.
- Never override `conversation.pdf_url` with an external PDF when a conversation PDF is already present.
