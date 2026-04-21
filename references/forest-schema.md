# Paper Neighbor Site Schema

The primary derived payload is built from normalized paper JSON records and powers a React single-page reading site.

## Expected derived payload

`outputs/site/paper-neighbors.json` should expose a site index payload at least:

```json
{
  "generated_at": "2026-04-15T00:00:00Z",
  "paper_count": 12,
  "site_meta": {
    "title": "Translate Paper Forest",
    "generated_at": "2026-04-15T00:00:00Z",
    "paper_count": 12
  },
  "navigation": {
    "home_route": "#/",
    "detail_route_template": "#/paper/{paper_id}",
    "neighbor_tabs": [
      {"key": "task", "label": "任务近邻"},
      {"key": "method", "label": "方法近邻"},
      {"key": "comparison", "label": "对比近邻"}
    ],
    "filter_groups": [
      {"key": "themes", "label": "主题"},
      {"key": "tasks", "label": "任务"},
      {"key": "methods", "label": "方法"}
    ]
  },
  "papers": [
    {
      "paper_id": "example-paper",
      "paper_path": "papers/example-paper.md",
      "route_path": "#/paper/example-paper",
      "summary": {
        "one_liner": "一句话结论"
      },
      "reading_digest": {
        "recommended_route": "method"
      },
      "editorial_review": {
        "verdict": "值得精读"
      },
      "research_tags": {
        "themes": ["3D Generation"],
        "tasks": ["Image-to-3D"],
        "methods": ["Diffusion Model"]
      },
      "paper_neighbors": {
        "task": [],
        "method": [],
        "comparison": []
      }
    }
  ],
  "filters": {
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

- `task`: requires at least one shared `retrieval_profile.task_axes`; rank by problem-space, input, output, and modality overlap
- `method`: requires shared `task_axes` or `problem_spaces`, then shared `approach_axes`
- `comparison`: baseline match first, contrast-method match second, same-task-or-problem-space fallback last
- `comparison` matching may only read candidate `retrieval_profile.comparison_axes` and `retrieval_profile.approach_axes`; it must not scan paper titles
- `comparison` and `fallback contrast` both require a gate of shared `task_axes` or `problem_spaces`, plus at least one shared `input_axes`, `output_axes`, or `modality_axes`
- `fallback contrast` should only fire when the two papers have clearly different `approach_axes`
- Keep at most 3 neighbors per dimension
- Allow the same paper to appear in multiple dimensions when the signals justify it
- Each neighbor should retain `reason` for verbose display, plus `reason_short` and `score_level` for compact cards

## HTML site outputs

The site should support a single-page HTML reading flow generated from structured data:

- `outputs/site/index.html`
- `outputs/site/assets/*`
- `outputs/site/paper-neighbors.json`
- `outputs/site/papers/<paper-id>.json`

The React app should use hash routes such as `#/paper/<paper-id>` for detail pages.
The homepage should load only `paper-neighbors.json`, while each detail page should fetch `papers/<paper-id>.json` on demand.

## Empty state

If there are no papers yet:

- still write valid Markdown files
- still write a valid `paper-neighbors.json`
- still write an empty-but-valid `papers/` detail directory when publishing the SPA
- still publish a valid single-page HTML site
- explain that no processed papers exist yet
