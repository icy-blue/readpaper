# Analysis Rubric v2

Extract knowledge for:

- durable paper understanding
- comparison and next-read decisions
- canonical taxonomy
- site-derived discovery views

## Priority Order

1. The core research problem
2. The paper-specific method mechanism
3. The strongest evaluation signals
4. Canonical taxonomy and comparison hooks
5. A concise editorial reading judgment

## Field Guidance

- `story.paper_one_liner`: one finished judgment sentence for quick scanning; do not splice fragments or emit `...`.
- `story.problem`: describe the task difficulty or missing variable.
- `story.method`: describe the paper's own mechanism or route.
- `story.result`: describe the strongest grounded result or observed gain.
- `research_problem.summary`: short problem definition, not conclusion text.
- `research_problem.goal`: intended objective in plain language.
- `core_contributions`: 2 to 4 concrete additions.
- `method.summary`: concise paper-specific mechanism summary.
- `method.pipeline_steps`: 2 to 4 short action steps, not copied paragraph fragments.
- `method.innovations`: short innovation statements, not section headings.
- `evaluation.headline`: one result-first judgment line for readers.
- `evaluation.key_findings`: concrete experiment takeaways.
- `claims`: 2 to 5 falsifiable or comparable claims with grounded support.
- `editorial.summary`: one editorial reading judgment.
- `editorial.why_read`: 2 to 3 reasons to keep reading.
- `editorial.reading_route`: `method`, `evaluation`, `comparison`, or `overview`.
- `editorial.graph_worthy`: a conservative boolean for long-term graph value, not a synonym for `值得精读`.
- `taxonomy`: canonical English labels only.
- `comparison.aspects`: short reading-facing comparison hooks.

## Graph-Worthy Rubric

Treat `editorial.graph_worthy` as a stable curation signal for the local knowledge forest.

Set it to `true` only when the paper satisfies at least 2 of the following:

- `route anchor`: it is a representative sample for a theme, task, or method route you are likely to revisit.
- `comparison anchor`: it creates a clear baseline, contrast, or next-read bridge for other papers in the repo.
- `reusable mechanism`: its problem framing or method mechanism is likely to be reused in future summaries or comparisons.
- `durable evidence`: its strongest evaluation signal or claims are clear enough to support future recall without re-reading the whole paper.

Keep it `false` when any of the following dominates the reading judgment:

- the evidence is partial, ambiguous, or too weak to support durable comparison
- the contribution is mostly an incremental benchmark gain or narrow engineering tweak
- the paper is too narrow, short-lived, or redundant to serve as a long-term anchor
- an existing local paper already covers the same anchor role more clearly and this paper adds little new comparison value

`editorial.graph_worthy` is independent from `editorial.verdict`: not every `值得精读` paper is graph-worthy, and a `值得浏览` paper may still be graph-worthy if it is the right comparison anchor.

## Similarity And Relation Rules

Canonical records should only retain stable relation hooks:

- `comparison.aspects`
- `comparison.next_read`
- `relations`

Neighbors, retrieval indexes, ranking signals, and filter buckets are derived artifacts and must be generated in the site build step.

## Failure Patterns To Avoid

- Do not let baseline recaps overwrite the paper's own method summary.
- Do not copy subsection headers like `数据与监督（外部）` into reader-facing fields.
- Do not emit hard-truncated strings with `...`.
- Do not invent stock metrics, novelty labels, or representation tags.
- Do not store both Chinese and English variants of the same canonical taxonomy item.
- Do not keep UI-only fallback text in canonical records.

## Source Priority

- Prefer translated conversation units for Chinese summaries.
- Prefer source-grounded local payloads first; if bibliography enrichment is missing, keep the canonical record partial rather than querying external services at assembly time.
- Never override `conversation.pdf_url` with an external PDF when the conversation already has one.
