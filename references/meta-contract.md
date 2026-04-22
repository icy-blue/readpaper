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
  "extractor_version": "meta-v3",
  "source_conversation_id": "conv-1",
  "source_semantic_updated_at": "2026-04-21T00:00:00+08:00",
  "extracted_at": "2026-04-21T00:00:00+08:00",
  "meta": {
    "story": {
      "paper_one_liner": null,
      "problem": null,
      "method": null,
      "result": null
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
    "conclusion": {
      "author": null,
      "limitations": []
    },
    "editorial": {
      "verdict": null,
      "summary": null,
      "why_read": [],
      "strengths": [],
      "cautions": [],
      "reading_route": "overview",
      "research_position": null,
      "graph_worthy": false,
      "next_read": []
    },
    "taxonomy": {
      "themes": [],
      "tasks": [],
      "methods": [],
      "modalities": [],
      "representations": [],
      "novelty_types": []
    },
    "comparison": {
      "aspects": [],
      "next_read": []
    },
    "assets": {
      "figures": [],
      "tables": []
    },
    "relation_candidates": []
  }
}
```

## Output Rules

- Use Chinese for human-facing summaries and judgments.
- Keep paper titles, method names, dataset names, venues, and URLs in original form.
- Use English canonical labels for `taxonomy.*`.
- Missing scalar fields must be `null`.
- Missing arrays must be `[]`.
- Every object listed above must still be present.

## Length Limits

- `story.paper_one_liner`: 110
- `story.problem|method|result`: 88
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
- `conclusion.author`: 180
- `conclusion.limitations[]`: 90, max 4
- `editorial.verdict`: 16
- `editorial.summary`: 84
- `editorial.why_read[]`: 64, max 3
- `editorial.strengths[]|cautions[]`: 80, max 4
- `editorial.research_position`: 84
- `editorial.reading_route`: one of `method`, `evaluation`, `comparison`, `overview`
- `editorial.next_read[]`: 36, max 4
- `taxonomy.*[]`: tag-like labels only
- `comparison.aspects[].aspect`: 28
- `comparison.aspects[].difference`: 96
- `assets.*[].label`: 24
- `assets.*[].caption`: 220
- `assets.*[].role`: 32
- `assets.*[].importance`: `high`, `medium`, or `low`
- `relation_candidates[].type`: 24
- `relation_candidates[].target_name`: 120
- `relation_candidates[].description`: 120
- `relation_candidates[].confidence_hint`: `low`, `medium`, or `high`
- `relation_candidates[].evidence_mode`: `explicit` or `heuristic`

## Grounding Rules

- Build evidence buckets first: `problem`, `method`, `evaluation`, `conclusion`.
- `story.problem` must come from gap/problem evidence.
- `story.method` and `method.*` must come from method sections or method figures first.
- `story.result`, `evaluation.headline`, and `evaluation.key_findings` must come from experiment or conclusion evidence.
- `research_problem.goal` must be the paper's objective, not a background citation or motivation anecdote.
- `core_contributions` must list what the paper adds, not generic SOTA lines.
- `method.summary` must describe the paper-specific mechanism first, not a reused baseline backbone.
- `evaluation.datasets`, `metrics`, and `baselines` must be explicit names from experiment text or captions.
- `taxonomy` should be conservative and canonical. Do not mix Chinese and English labels.
- `comparison.next_read` and `editorial.next_read` should contain short target names, not sentences.
- `relation_candidates` are analysis-layer inputs only; do not emit final canonical relation ids here.
- `relation_candidates` should prefer explicit typed evidence such as `compares_to`, `extends`, or `uses_method`.
- Heuristic `relation_candidates` are limited to `compares_to` and `same_problem`.

## Evidence Rules

- Each `claims[].text` must be falsifiable or comparable.
- Each `claims[].support` must cite grounded evidence such as `section:4. Experiments`, `figure:Figure 2`, or `table:Table 1`.
- `assets` must be produced by the skill; downstream scripts must not infer them from keyword heuristics alone.

## Versioning

- Read `extractor-config.json` before extraction.
- Copy `extractor_version` from config into the artifact.
- When the contract, prompt, or writing policy changes, bump `extractor_version` and regenerate affected meta artifacts.
