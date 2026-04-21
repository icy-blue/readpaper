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
- `research_problem`: write the shortest grounded formulation of the problem. Prefer missing over wrong-field content.
- `storyline`: compress the paper into `problem`, `method`, and `outcome` for first-screen scanning.
- `storyline.problem`: must describe the research gap or task difficulty, not method or result.
- `storyline.method`: must describe the core method action or mechanism, not evaluation.
- `storyline.outcome`: must describe the result or observed gain, not problem framing.
- `summary.one_liner`: write one finished judgment sentence; do not splice `problem + method` fragments with semicolons and do not emit `...`.
- `reading_digest.value_statement`: write a reading-value judgment, not a content recap.
- `reading_digest.best_for`: write a reader profile sentence, not a task/method tag dump.
- `reading_digest.why_read`: write 2 to 3 reading reasons; do not emit `任务:` / `方法:` label strings.
- `research_problem.goal`: write the intended research objective in plain language, not background evidence or literature motivation.
- `method_core.innovations`: keep short innovation sentences only; do not copy long method paragraphs or section headings.
- `method_core.approach_summary`: summarize the paper-specific mechanism first; avoid reducing the paper to a generic baseline pipeline.
- `method_core.pipeline_steps`: rewrite into 2 to 4 short action steps instead of copying paragraph fragments.
- `core_contributions`: keep 2 to 4 concrete items.
- `core_contributions`: do not use a plain SOTA sentence as one contribution unless the paper itself frames the system contribution that way.
- `key_claims`: keep 2 to 5 falsifiable or comparable claims.
- `key_claims[].type`: classify each claim as `method`, `experiment`, `capability`, or `limitation` when possible.
- `benchmarks_or_eval.datasets` / `metrics` / `baselines`: prefer explicit names from experiments and tables; leave missing rather than guessing.
- `novelty_type`: stay conservative and grounded; omit stock labels unrelated to the paper.
- `author_conclusion`: prefer conclusion-section wording over editor paraphrase.
- `editor_note`: reserve for your own grounded reading note; keep it as `summary + points`, or leave it empty when unavailable.
- `experiment_setup_summary`: summarize datasets / settings / evaluation setup, not the whole result section.
- `figure_table_index`: add `role` and `importance` so the front end can prioritize what to read first.

## Failure Patterns To Avoid

- Do not let baseline descriptions overwrite the paper's own method summary.
- Do not copy subsection headers like `数据与监督（外部）` into summary bullets.
- Do not leave front-end strings clipped with `...`; rewrite shorter instead.
- Do not invent extra metrics, novelty tags, or representations from prior papers.
- Do not leave `retrieval_profile` empty when the paper clearly exposes tasks, methods, inputs, and outputs.

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
