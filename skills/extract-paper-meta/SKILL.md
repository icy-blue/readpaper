---
name: extract-paper-meta
description: Extract a single paper meta artifact from one translate raw payload using the executing agent's native reasoning, following the repository v2 meta contract.
---

# Extract Paper Meta

Use this skill when the user wants agent-native paper meta extraction for this repository.

This skill reads one raw payload and writes one structured meta artifact to `outputs/meta/<paper-id>.json`.
It does not write the final canonical paper record.

## Read First

1. [../../references/paper-schema.md](../../references/paper-schema.md)
2. [../../references/analysis-rubric.md](../../references/analysis-rubric.md)
3. [../../references/meta-contract.md](../../references/meta-contract.md)
4. [../../extractor-config.json](../../extractor-config.json)

## Workflow

1. Read `outputs/raw/<paper-id>.json`.
2. Read `extractor_version` from `extractor-config.json`.
3. Build grounded evidence buckets first:
   - `problem`
   - `method`
   - `evaluation`
   - `conclusion`
4. Extract `relation_candidates` from explicit evidence first, then add conservative heuristic candidates only when the contract allows them.
5. Write one v2 meta artifact matching `references/meta-contract.md`.
6. Save it to `outputs/meta/<paper-id>.json`.

## Output Rules

- Ground everything in translated visible content, figure captions, and table captions from the raw payload.
- Prefer missing over guessed.
- Keep human-facing summaries in Chinese.
- Keep Chinese reader-facing text typographically natural: use full-width punctuation such as `，。：；（）！？` and preserve natural spacing between Chinese and embedded English or number phrases.
- Keep paper titles, method names, dataset names, URLs, and formula-like tokens in their original form.
- Keep taxonomy labels canonical and English.
- Do not emit old schema blocks such as `summary`, `reading_digest`, `storyline`, `method_core`, `benchmarks_or_eval`, `editorial_review`, or `retrieval_profile`.
- Do not copy long paragraphs verbatim into short fields.
- Do not emit `...` or hard-truncated half-sentences.
- Do not let baseline descriptions overwrite the paper's own method summary.
- Do not collapse Chinese punctuation into half-width ASCII punctuation in reader-facing fields.
- Only emit `relation_candidates`, never final canonical `relations`.
- Prefer explicit `compares_to` / `extends` / `uses_method` over heuristic candidates.
- Heuristic candidates are limited to `compares_to` and `same_problem`.

## Validation Checklist

Before writing the JSON, verify:

- `meta.story` contains only paper-facing story fields
- `meta.method.inputs` and `meta.method.outputs` are the only canonical task I/O fields
- `meta.evaluation.baselines` contains only explicit baselines named in the paper
- `meta.editorial.reading_route` is one of `method`, `evaluation`, `comparison`, or `overview`
- `meta.taxonomy` uses English canonical labels only
- `meta.comparison.next_read` and `meta.editorial.next_read` are short target names, not sentences
- `meta.assets` contains figure/table items with grounded `role` and `importance`
- `meta.relation_candidates` only contains `type`, `target_name`, `description`, `confidence_hint`, and `evidence_mode`
- `meta.relation_candidates[].evidence_mode` is `explicit` or `heuristic`
