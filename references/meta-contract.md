# Meta Contract v2

Use this contract for `extract-paper-meta`.

The artifact written to `outputs/meta/<paper-id>.json` is the analysis-layer input for canonical paper assembly.

It should align with canonical paper analysis and taxonomy fields, while leaving bibliography, source, abstracts, and link enrichment to `normalize_papers.py`.

## Input Source

Ground extraction only in:

- `conversation.title`
- `conversation.year`
- `conversation.venue` / `conversation.venue_abbr`
- `conversation.tags`
- `conversation.figures`
- `conversation.tables`
- visible translated bot messages and their `translation_status.current_unit_id`

Prefer missing over guessed. Do not infer unsupported claims from absent sections.

## Artifact Shape

```json
{
  "paper_id": "demo-paper",
  "extractor_version": "meta-v7",
  "source_conversation_id": "conv-1",
  "source_semantic_updated_at": "2026-04-21T00:00:00+08:00",
  "extracted_at": "2026-04-21T00:00:00+08:00",
  "meta": {
    "story": {
      "paper_one_liner": null
    },
    "research_problem": {
      "summary": null,
      "gaps": [],
      "goal": null
    },
    "core_contributions": [],
    "method": {
      "summary": null,
      "pipeline_steps": [],
      "innovations": [],
      "ingredients": [],
      "inputs": [],
      "outputs": [],
      "representations": []
    },
    "evaluation": {
      "headline": null,
      "datasets": [],
      "metrics": [],
      "baselines": [],
      "key_findings": [],
      "setup_summary": null
    },
    "claims": [],
    "research_risks": [],
    "editorial": {
      "research_position": null,
      "graph_worthy": false
    },
    "taxonomy": {
      "themes": [],
      "tasks": [],
      "methods": [],
      "modalities": [],
      "novelty_types": []
    },
    "comparison": {
      "aspects": [],
      "next_read": []
    },
    "discovery_axes": {
      "problem": [],
      "method": [],
      "evaluation": [],
      "risk": []
    },
    "relation_candidates": []
  }
}
```

## Output Rules

- Use Chinese for human-facing summaries and judgments.
- For Chinese reader-facing text, prefer full-width punctuation such as `，。：；（）！？` in sentence flow.
- Keep natural spacing between Chinese and embedded English words, abbreviations, or number phrases such as `3D`, `Open-World`, and `Point Cloud`.
- Keep paper titles, method names, dataset names, venues, and URLs in original form.
- Do not collapse Chinese punctuation into half-width ASCII punctuation in reader-facing fields.
- Do not remove natural spaces between Chinese and embedded English or number phrases.
- Use English canonical labels for `taxonomy.*`.
- Missing scalar fields must be `null`.
- Missing arrays must be `[]`.
- Every object listed above must still be present.

## Length Limits

- `story.paper_one_liner`: 110
- `research_problem.summary|goal`: 100
- `research_problem.gaps[]`: 84, max 4
- `core_contributions[]`: 90, max 4
- `method.summary`: 110
- `method.pipeline_steps[]`: 105, max 4
- `method.innovations[]`: 90, max 4
- `method.ingredients[]`: 40, max 6
- `method.inputs[]|outputs[]`: 32, max 6
- `method.representations[]`: 40, max 6
- `evaluation.headline`: 96
- `evaluation.datasets[]`: 36, max 8
- `evaluation.metrics[]`: 20, max 8
- `evaluation.baselines[]`: 36, max 8
- `evaluation.key_findings[]`: 90, max 4
- `evaluation.setup_summary`: 140
- `claims[].text`: 120, max 5
- `claims[].type`: 24
- `claims[].confidence`: 16
- `research_risks[]`: 90, max 4
- `editorial.research_position`: 84
- `taxonomy.*[]`: tag-like labels only
- `comparison.aspects[].aspect`: 28
- `comparison.aspects[].difference`: 96
- `discovery_axes.problem[]|method[]|evaluation[]`: 40, max 8
- `discovery_axes.risk[]`: 40, max 6
- `relation_candidates[].type`: 24
- `relation_candidates[].target_name`: 120
- `relation_candidates[].description`: 120
- `relation_candidates[].confidence_hint`: `low`, `medium`, or `high`
- `relation_candidates[].evidence_mode`: `explicit` or `heuristic`

## Grounding Rules

- Build evidence buckets first: `problem`, `method`, `evaluation`, `conclusion`.
- `story.paper_one_liner` should be the highest-value reader-facing summary sentence for quick scanning.
- `method.*` must come from method sections or method figures first.
- `evaluation.headline` and `evaluation.key_findings` must come from experiment or conclusion evidence.
- `research_problem.goal` must be the paper's objective, not a background citation or motivation anecdote.
- `core_contributions` must list what the paper adds, not generic SOTA lines.
- `method.summary` must describe the paper-specific mechanism first, not a reused baseline backbone.
- `evaluation.datasets`, `metrics`, and `baselines` must be explicit names from experiment text or captions.
- `research_risks` should capture the real reproduction or comparison risks that matter, not only copied author-limitations language.
- `taxonomy` should be conservative and canonical. Do not mix Chinese and English labels.
- `comparison.next_read` should contain short target names, not sentences.
- `discovery_axes` should use short canonical labels, not sentences, and should not duplicate final graph edges.
- `editorial.graph_worthy` means worth keeping as a long-term anchor in the local knowledge forest, not simply "good paper" or "worth reading".
- Set `editorial.graph_worthy` to `true` only when at least 2 of these are grounded: the paper is a representative route anchor, a clear comparison anchor, a reusable mechanism reference, or a durable evidence anchor.
- Keep `editorial.graph_worthy` `false` when the evidence is incomplete, the contribution is mostly incremental, the paper is too narrow for future comparison, or the same anchor role is already covered more clearly by another local paper.
- `relation_candidates` are analysis-layer inputs only; do not emit final canonical relation ids here.
- `relation_candidates` should prefer explicit typed evidence such as `compares_to` or `uses_method`.
- Heuristic `relation_candidates` are limited to `compares_to`.
- `relation_candidates[].confidence_hint` is an extraction-layer hint, not the final numeric `relations[].confidence`.
- Current canonical assembly derives final `relations[].confidence` from `target_kind` and `evidence_mode`:
  - `local + explicit` -> `0.90`
  - `external + explicit` -> `0.82`
  - `local + heuristic` -> `0.68`
  - `external + heuristic` -> `0.60`
- Therefore, many explicit external links may share the same final score even when the extraction-layer confidence differs.
- Use `confidence_hint=high` only when the target and relation are directly grounded in the translated text, figure caption, or table caption.
- Use `confidence_hint=medium` when the target is named explicitly but the exact relation wording still requires small interpretation.
- Use `confidence_hint=low` only for weak but still admissible candidates; if the evidence is too weak, prefer omitting the candidate instead of emitting a low-confidence placeholder.
- If a `relation_candidate` does not resolve to a local paper id, canonical assembly may keep it as an `external` relation and let the render layer generate a Semantic Scholar search link from `target_name`.

## Evidence Rules

- Each `claims[].text` must be falsifiable or comparable.
- Each `claims[].support` must cite grounded evidence such as `section:4. Experiments`, `figure:Figure 2`, or `table:Table 1`.

## Versioning

- Read `extractor-config.json` before extraction.
- Copy `extractor_version` from config into the artifact.
- When the contract, prompt, or writing policy changes, bump `extractor_version` and regenerate affected meta artifacts.
