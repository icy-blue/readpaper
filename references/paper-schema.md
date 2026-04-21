# Paper Schema

Write one JSON file per canonical paper at `outputs/papers/<paper-id>.json`.

## Required shape

```json
{
  "paper_id": "structured-3d-latents-cvpr-2024-a1b2c3d4",
  "source_conversation_ids": ["399facf1f854"],
  "title": "Structured 3D Latents for Scalable and Versatile 3D Generation",
  "year": 2024,
  "venue": "CVPR",
  "citation_count": 564,
  "pdf_url": "https://...",
  "translate_created_at": "2026-04-15T14:41:27.094309+08:00",
  "translate_status": {
    "state": "BODY_DONE",
    "completed_unit_count": 7,
    "total_unit_count": 11,
    "is_partial": true,
    "active_scope": "appendix"
  },
  "summary": {
    "one_liner": "一句话结论",
    "abstract_summary": "面向自己复盘的短摘要",
    "research_value": "为什么值得放进长期知识图谱",
    "worth_long_term_graph": true
  },
  "key_claims": [
    {
      "claim": "具体 claim",
      "support": ["section:4. Experiments", "figure:Figure 2"],
      "confidence": "high"
    }
  ],
  "method_core": {
    "problem": "解决什么问题",
    "approach": "核心做法",
    "innovation": "方法创新",
    "ingredients": ["ingredient a", "ingredient b"],
    "representation": ["representation a"],
    "supervision": ["监督或约束"],
    "differences": ["相对相近论文最重要差异"]
  },
  "inputs_outputs": {
    "inputs": ["text prompt", "image prompt"],
    "outputs": ["mesh", "3D Gaussian"],
    "modalities": ["text", "image", "3D"]
  },
  "benchmarks_or_eval": {
    "datasets": ["dataset a"],
    "metrics": ["metric a"],
    "baselines": ["baseline a"],
    "findings": ["最重要实验结论"]
  },
  "limitations": ["局限 1", "局限 2"],
  "novelty_type": ["representation", "decoder flexibility"],
  "research_tags": {
    "themes": ["3D Generation"],
    "tasks": ["Text-to-3D", "Image-to-3D"],
    "methods": ["Rectified Flow Transformer"],
    "modalities": ["text", "image", "3D"],
    "representations": ["SLAT", "Radiance Fields", "3D Gaussians", "Mesh"]
  },
  "comparison_context": {
    "explicit_baselines": ["baseline a"],
    "contrast_methods": ["method phrase a"],
    "contrast_notes": ["与某条路线相比的关键差异"]
  },
  "paper_neighbors": {
    "task": [
      {
        "paper_id": "neighbor-paper",
        "title": "Neighbor Paper",
        "score": 11,
        "match_source": "task_overlap",
        "shared_signals": {
          "tasks": ["Text-to-3D"],
          "themes": ["3D Generation"],
          "modalities": ["text", "3D"]
        },
        "reason": "同属 Text-to-3D，且输入模态一致。"
      }
    ],
    "method": [],
    "comparison": []
  },
  "figure_table_index": {
    "figures": [
      {"label": "Figure 1", "caption": "图注"}
    ],
    "tables": [
      {"label": "Table 1", "caption": "表注"}
    ]
  }
}
```

## Field rules

- `paper_id`: use the fetch manifest value exactly.
- `source_conversation_ids`: preserve all source conversation ids tied to the canonical paper.
- `venue`: prefer `venue_abbr`; fall back to `venue`; use `"Unknown"` only when neither exists.
- `translate_status.is_partial`: set to `true` unless the payload clearly indicates the entire paper is translated.
- `summary.one_liner`: one sentence only.
- `key_claims`: keep 2 to 5 items.
- `key_claims.support`: prefer `section:<unit id>`, `figure:<label>`, `table:<label>`.
- `research_tags`: keep tags high-signal and reusable across the forest.
- `comparison_context.explicit_baselines`: copy from `benchmarks_or_eval.baselines` when available.
- `comparison_context.contrast_methods`: extract reusable method phrases from `method_core.differences` and `innovation`; do not dump whole sentences here.
- `comparison_context.contrast_notes`: keep short and comparison-oriented; prefer 1 to 3 items.
- `paper_neighbors`: keep at most 3 neighbors per dimension and do not fabricate filler results when signal is weak.

## Do not do

- Do not write prose outside the JSON file.
- Do not copy large translated sections into the record.
- Do not infer hidden details not supported by the payload.
- Do not omit `limitations` just because the paper sounds strong; include real uncertainty or coverage gaps.
- Do not write `related_papers`; use `paper_neighbors` instead.
