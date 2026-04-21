# Paper Neighbor Site Schema

The primary derived payload is built from normalized paper JSON records and keeps single-paper reading as the main interaction.

## Expected derived payload

`outputs/site/paper-neighbors.json` should expose at least:

```json
{
  "generated_at": "2026-04-15T00:00:00Z",
  "paper_count": 12,
  "papers": [
    {
      "paper_id": "example-paper",
      "paper_path": "papers/example-paper.md",
      "html_path": "papers/example-paper.html",
      "comparison_context": {
        "explicit_baselines": ["baseline a"],
        "contrast_methods": ["method phrase a"],
        "contrast_notes": ["与 baseline 的关键差异"]
      },
      "paper_neighbors": {
        "task": [],
        "method": [],
        "comparison": []
      }
    }
  ],
  "tag_filters": {
    "themes": [
      {
        "label": "3D Generation",
        "count": 4,
        "paper_ids": ["example-paper"]
      }
    ],
    "tasks": [],
    "methods": []
  },
  "recent_titles": ["Example Paper"]
}
```

## Neighbor selection rules

- `task`: requires at least one shared `research_tags.tasks`
- `method`: requires at least one shared `research_tags.methods` or `research_tags.representations`
- `comparison`: baseline match first, contrast-method match second, same-task-but-different-method fallback last
- Keep at most 3 neighbors per dimension
- Allow the same paper to appear in multiple dimensions when the signals justify it

## HTML site outputs

The site should support a full HTML reading flow generated from structured data:

- `outputs/site/index.html`
- `outputs/site/papers/<paper-id>.html`

Compatibility placeholders may still be written for:

- `outputs/site/theme-map.html`
- `outputs/site/method-map.html`
- `outputs/site/timeline.html`
- `outputs/site/relationship-graph.html`

## Empty state

If there are no papers yet:

- still write valid Markdown files
- still write a valid `paper-neighbors.json`
- still write a valid HTML site
- explain that no processed papers exist yet
