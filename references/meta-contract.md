# Meta Contract

Use this contract for `extract-paper-meta`.

## Purpose

Extract a single paper's research-facing meta artifact from one raw translate payload.

The artifact is an intermediate product written to `outputs/meta/<paper-id>.json`.
It is not the final paper record.

## Input Source

Ground extraction only in:

- `conversation.title`
- `conversation.year`
- `conversation.venue` / `conversation.venue_abbr`
- `conversation.tags`
- `conversation.figures`
- `conversation.tables`
- visible bot messages and their `translation_status.current_unit_id`

Do not infer claims from absent sections. Prefer missing over invented.

## Artifact Shape

```json
{
  "paper_id": "demo-paper",
  "extractor_version": "meta-v1",
  "source_conversation_id": "conv-1",
  "source_semantic_updated_at": "2026-04-21T00:00:00+08:00",
  "extracted_at": "2026-04-21T00:00:00+08:00",
  "meta": {
    "summary": {},
    "reading_digest": {},
    "storyline": {},
    "research_problem": {},
    "core_contributions": [],
    "key_claims": [],
    "method_core": {},
    "inputs_outputs": {},
    "benchmarks_or_eval": {},
    "author_conclusion": null,
    "editor_note": null,
    "editorial_review": {},
    "limitations": [],
    "novelty_type": [],
    "research_tags": {},
    "topics": [],
    "retrieval_profile": {},
    "comparison_context": {},
    "paper_relations": []
  }
}
```

## Output Rules

- Keep the final `meta` payload schema-compatible with `references/paper-schema.md`.
- Use Chinese for human-facing summaries and judgments.
- Keep paper titles, venue names, method names, dataset names, and URLs in their original form.
- Missing scalars must be `null`.
- Missing arrays must be `[]`.
- Missing objects must still be present with valid empty members.

## Length Limits

Treat these as hard limits, not suggestions.

- `summary.one_liner`: 110
- `summary.abstract_summary`: 150
- `summary.research_value.summary`: 72
- `summary.research_value.points[]`: 64, max 3
- `reading_digest.value_statement`: 84
- `reading_digest.best_for`: 72
- `reading_digest.why_read[]`: 64, max 3
- `reading_digest.positioning.task[]`: 28, max 4
- `reading_digest.positioning.method[]`: 28, max 4
- `reading_digest.positioning.modality[]`: 24, max 4
- `reading_digest.positioning.novelty[]`: 24, max 4
- `reading_digest.narrative.problem|method|result`: 90
- `reading_digest.result_headline`: 96
- `storyline.problem|method|outcome`: 84
- `research_problem.summary`: 100
- `research_problem.goal`: 100
- `research_problem.gaps[]`: 84, max 4
- `core_contributions[]`: 90, max 4
- `key_claims[].claim`: 120, max 5
- `key_claims[].type`: 24
- `key_claims[].confidence`: 16
- `method_core.approach_summary`: 110
- `method_core.pipeline_steps[]`: 105, max 4
- `method_core.innovations[]`: 90, max 4
- `method_core.ingredients[]`: 32, max 6
- `method_core.representation[]`: 32, max 6
- `method_core.supervision[]`: 48, max 4
- `method_core.differences[]`: 90, max 4
- `inputs_outputs.inputs[]`: 28, max 6
- `inputs_outputs.outputs[]`: 28, max 6
- `inputs_outputs.modalities[]`: 24, max 6
- `benchmarks_or_eval.datasets[]`: 30, max 8
- `benchmarks_or_eval.metrics[]`: 20, max 8
- `benchmarks_or_eval.baselines[]`: 28, max 8
- `benchmarks_or_eval.findings[]`: 90, max 4
- `benchmarks_or_eval.best_results[]`: 90, max 4
- `benchmarks_or_eval.experiment_setup_summary`: 140
- `author_conclusion`: 180
- `editorial_review.verdict`: 16
- `editorial_review.strengths[]`: 80, max 4
- `editorial_review.cautions[]`: 80, max 4
- `editorial_review.research_position`: 84
- `editorial_review.next_read_hint`: 60
- `limitations[]`: 90, max 4
- `novelty_type[]`: 24, max 4
- `comparison_context.explicit_baselines[]`: 28, max 8
- `comparison_context.contrast_methods[]`: 28, max 8
- `comparison_context.comparison_aspects[].aspect`: 28
- `comparison_context.comparison_aspects[].difference`: 96
- `comparison_context.recommended_next_read`: 36

## Writing Style

- Write short judgment-heavy lines, not mini abstracts.
- `value_statement`, `result_headline`, and `research_position` must be judgments, not content recap.
- `best_for` must describe reader profile and purpose.
- `why_read[]`, `strengths[]`, `cautions[]`, and `limitations[]` must keep one point per item.
- `core_contributions[]`, `innovations[]`, and `findings[]` must be concrete.
- `positioning.*`, `ingredients`, `representation`, `datasets`, and `metrics` must be tag-like phrases, not sentences.
- Do not emit filler such as “很有启发”, “值得关注”, or “有重要意义” unless followed by a concrete reason in the same short line.

## Evidence Rules

- `key_claims[].claim` must be falsifiable or comparable.
- `key_claims[].support` must cite grounded evidence such as `section:4. Experiments`, `figure:Figure 2`, or `table:Table 1`.
- Use `limitations` only for paper-side limitations, not extraction caveats.

## Versioning

- Read `extractor-config.json` before extraction.
- Copy `extractor_version` from config into the artifact.
- When the prompt, contract, extraction policy, or field-writing policy changes, bump `extractor_version` in config and regenerate affected meta artifacts.
