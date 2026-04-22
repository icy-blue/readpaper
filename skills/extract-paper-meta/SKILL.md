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
   - `risk / limitation`
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
- Do not emit removed v6 fields such as `story.problem`, `story.method`, `story.result`, `editorial.verdict`, `editorial.reading_route`, `editorial.next_read`, `conclusion`, `taxonomy.representations`, or `assets`.
- Do not copy long paragraphs verbatim into short fields.
- Do not emit `...` or hard-truncated half-sentences.
- Do not let baseline descriptions overwrite the paper's own method summary.
- Do not collapse Chinese punctuation into half-width ASCII punctuation in reader-facing fields.
- Only emit `relation_candidates`, never final canonical `relations`.
- Prefer explicit `compares_to` / `uses_method` over heuristic candidates.
- Heuristic candidates are limited to `compares_to`.
- Treat `confidence_hint` as an extraction-layer hint only; do not assume it directly controls the final numeric `relations[].confidence`.
- Current downstream assembly maps many explicit external relations to the same numeric score, so your job is to make the hint semantically honest, not to spread scores artificially.
- Use `confidence_hint=high` only when the target paper or method is explicitly named and the relation is directly supported by text, figure captions, or table captions.
- Use `confidence_hint=medium` when the target is explicitly named but the exact relation still needs a small amount of interpretation.
- Use `confidence_hint=low` sparingly; if the evidence is genuinely weak, prefer omitting the candidate.
- Keep `meta.discovery_axes` as short canonical labels grouped into `problem / method / evaluation / risk`, not sentences and not final graph edges.
- Treat `meta.editorial.graph_worthy` as a conservative graph-anchor flag, not a generic quality score.
- Set `meta.editorial.graph_worthy` to `true` only when at least 2 grounded signals are present: representative route anchor, clear comparison anchor, reusable mechanism reference, or durable evidence anchor.
- Keep `meta.editorial.graph_worthy` `false` for incremental-only papers, incomplete evidence, overly narrow papers, or papers already fully covered by a stronger local anchor.

## Validation Checklist

Before writing the JSON, verify:

- `meta.story` 只保留 `paper_one_liner`
- `meta.method.inputs` and `meta.method.outputs` are the only canonical task I/O fields
- `meta.evaluation.baselines` contains only explicit baselines named in the paper
- `meta.research_risks` captures concrete reproduction / comparison risks, not generic filler
- `meta.editorial` 只保留 `research_position` 和 `graph_worthy`
- `meta.editorial.graph_worthy` follows the graph-worthy rubric and is not inferred from a generic read-worthiness judgment
- `meta.taxonomy` uses English canonical labels only
- `meta.comparison.next_read` contains short target names, not sentences
- `meta.discovery_axes.*` are short canonical labels with clear grouping
- `meta.relation_candidates` only contains `type`, `target_name`, `description`, `confidence_hint`, and `evidence_mode`
- `meta.relation_candidates[].evidence_mode` is `explicit` or `heuristic`
- `meta.relation_candidates[].confidence_hint` is justified by evidence strength, not by a desire to diversify downstream numeric scores
