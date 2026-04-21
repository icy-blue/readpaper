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
4. Produce a single JSON artifact that matches the meta contract exactly.
5. Write it to `outputs/meta/<paper-id>.json`.

## Output Rules

- Keep every field short enough for the current front-end reading cards.
- Prefer missing over guessed.
- Do not copy long paragraphs into structured fields.
- Infer `figure_table_index` with native reasoning from the paper context instead of keyword rules in the assembler.
- Do not write the final paper record schema here; only write the intermediate meta artifact schema.
