# Analysis Rubric

Extract knowledge for future retrieval, comparison, and idea generation.

## Priority order

1. What problem the paper solves
2. What the paper claims is new
3. What evidence in the translated payload supports those claims
4. What makes this paper similar to or different from neighboring papers
5. Whether the paper deserves a durable place in the long-term graph

## Claim extraction rules

- Prefer concrete claims over generic praise.
- Write 2 to 5 claims.
- Each claim should be falsifiable or comparable.
- When possible, attach evidence from:
  - translated section ids
  - figure captions
  - table captions
  - summary text already present in the payload

## Method analysis rules

- Separate `approach` from `innovation`.
- `approach` explains the pipeline.
- `innovation` explains what changed relative to familiar baselines or nearby work.
- `differences` should emphasize the most decision-relevant differences, not every detail.

## Similarity and difference rules

When writing single-paper neighbor context, prioritize three reading dimensions:

- task neighbors: same or very close `research_tags.tasks`
- method neighbors: same method family or representation family
- comparison neighbors: explicit baselines first, then methods called out in `differences` or `innovation`

Use `comparison_context` to store the machine-readable comparison cues:

- `explicit_baselines`
- `contrast_methods`
- `contrast_notes`

Use `paper_neighbors` to store the actual per-paper results:

- `task`
- `method`
- `comparison`

Each neighbor should explain:

- why it matched
- which signals were shared
- whether the match came from task overlap, method overlap, baseline match, contrast-method match, or fallback contrast

## Partial-translation handling

If the payload does not cover the full paper:

- still extract useful structure
- prefer visible evidence
- mention uncertainty through `limitations`
- mark `translate_status.is_partial` as `true`

## Tone rules

- Write for your future self as a research engineer.
- Favor short, information-dense phrasing.
- Avoid marketing language.
- Avoid repeating the abstract unless it truly captures the novelty.
