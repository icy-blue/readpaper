---
name: extract-paper-meta
description: Extract a single paper meta artifact from one translate raw payload using the executing agent's native reasoning, following the repository meta contract and display-length limits.
---

# Extract Paper Meta

Use this skill when the user wants agent-native paper meta extraction for this repository.

This skill reads one raw payload and writes one structured meta artifact to `outputs/meta/<paper-id>.json`.
It does not write the final paper record.

## Read First

1. [../../references/paper-schema.md](../../references/paper-schema.md)
2. [../../references/analysis-rubric.md](../../references/analysis-rubric.md)
3. [../../references/meta-contract.md](../../references/meta-contract.md)
4. [../../extractor-config.json](../../extractor-config.json)

## Workflow

1. Read the raw payload for one paper from `outputs/raw/<paper-id>.json`.
2. Read the current `extractor_version` from `extractor-config.json`.
3. Ground extraction only in the raw payload content defined in `references/meta-contract.md`.
4. Build a short evidence pack before writing fields:
   - `abstract`: translated abstract and raw abstract when present
   - `problem`: introduction sentences that describe the gap or failure mode
   - `method`: method-section sentences and method figures that describe the paper-specific mechanism
   - `evaluation`: experiment-section sentences plus table captions for datasets, metrics, baselines, and strongest results
   - `conclusion`: conclusion-section wording for `author_conclusion`
5. Produce a single JSON artifact that matches the meta contract exactly.
6. Write it to `outputs/meta/<paper-id>.json`.

## Output Rules

- Keep every field short enough for the current front-end reading cards.
- Prefer missing over guessed.
- Do not copy long paragraphs into structured fields.
- Rewrite to fit limits; never clip with `...` or leave a sentence half-finished.
- Do not paste section headings, subsection labels, figure labels, or lead-ins such as `第 3.2 节` into reader-facing fields unless the field is an evidence citation.
- Keep `problem`, `method`, and `result` separated by role. Do not reuse a baseline recap as the paper's own method summary.
- `method_core.approach_summary` must describe the paper-specific mechanism first. If the paper reuses a baseline backbone, mention it only after the unique idea.
- `core_contributions` must list contributions, not pure result sentences.
- `benchmarks_or_eval.datasets`, `metrics`, and `baselines` must come from explicit experiment evidence, not stock defaults.
- `novelty_type` must stay grounded and conservative. Leave it empty instead of emitting generic tags such as `physics prior` or `decoder flexibility` when the paper does not center them.
- If enough grounded task/method/input/output signals exist elsewhere in the artifact, fill `retrieval_profile` instead of leaving it empty.
- Infer `figure_table_index` with native reasoning from the paper context instead of keyword rules in the assembler.
- Do not write the final paper record schema here; only write the intermediate meta artifact schema.

## Validation Checklist

Before writing the final JSON, verify:

- no field contains `...`
- no display field is a raw section excerpt pasted with minimal editing
- `storyline.problem` is a gap, `storyline.method` is an action/mechanism, `storyline.outcome` is a result
- `research_problem.goal` is the target objective, not a motivation citation or psychophysics observation
- `method_core.pipeline_steps` are short action steps, not paragraph fragments
- `method_core.innovations` are concrete innovations, not section headings
- `benchmarks_or_eval.datasets` is non-empty when experiment text explicitly names datasets
- `benchmarks_or_eval.metrics` contains only metrics named in the paper
- each non-empty `key_claims[].support` points to a grounded section / figure / table
