# Paper Schema

Write one JSON file per canonical paper at `outputs/papers/<paper-id>.json`.

## Required shape

```json
{
  "paper_id": "structured-3d-latents-cvpr-2024-a1b2c3d4",
  "source_conversation_ids": ["399facf1f854"],
  "title": "Structured 3D Latents for Scalable and Versatile 3D Generation",
  "authors": ["Author A", "Author B"],
  "year": 2024,
  "venue": "CVPR",
  "citation_count": 564,
  "links": {
    "pdf": "https://...",
    "doi": null,
    "arxiv": null,
    "project": null,
    "code": null,
    "data": null
  },
  "translate_created_at": "2026-04-15T14:41:27.094309+08:00",
  "translate_status": {
    "state": "BODY_DONE",
    "completed_unit_count": 7,
    "total_unit_count": 11,
    "is_partial": true,
    "active_scope": "appendix",
    "coverage_notes": ["当前记录主要依据摘要，正文细节仍需完整核对。"]
  },
  "abstract_raw": "Original abstract text...",
  "abstract_zh": "中文摘要……",
  "summary": {
    "one_liner": "一句话结论",
    "abstract_summary": "面向自己复盘的短摘要",
    "research_value": "为什么值得放进长期知识图谱",
    "worth_long_term_graph": true
  },
  "research_problem": "这篇论文要解决的核心研究问题",
  "core_contributions": ["贡献 1", "贡献 2"],
  "key_claims": [
    {
      "claim": "具体 claim",
      "support": ["section:4. Experiments", "figure:Figure 2"],
      "confidence": "high"
    }
  ],
  "method_core": {
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
    "findings": ["最重要实验结论"],
    "experiment_setup_summary": "实验设置摘要"
  },
  "author_conclusion": "作者在论文中最终想传达的结论",
  "editor_note": "你的编者按/阅读备注",
  "limitations": ["局限 1", "局限 2"],
  "novelty_type": ["representation", "decoder flexibility"],
  "research_tags": {
    "themes": ["3D Generation"],
    "tasks": ["Text-to-3D", "Image-to-3D"],
    "methods": ["Rectified Flow Transformer"],
    "modalities": ["text", "image", "3D"],
    "representations": ["SLAT", "Radiance Fields", "3D Gaussians", "Mesh"]
  },
  "topics": [],
  "retrieval_profile": {
    "problem_spaces": ["3D Generation", "Image-to-3D", "mesh"],
    "task_axes": ["Text-to-3D", "Image-to-3D"],
    "approach_axes": ["Rectified Flow Transformer", "Structured Latents", "Mesh"],
    "input_axes": ["text prompt", "image prompt"],
    "output_axes": ["mesh", "3D Gaussian"],
    "modality_axes": ["text", "image", "3D"],
    "comparison_axes": ["baseline a", "method phrase a"]
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
        "paper_path": "papers/neighbor-paper.md",
        "route_path": "#/paper/neighbor-paper",
        "shared_signals": {
          "task_axes": ["Text-to-3D"]
        },
        "reason": "同属 Text-to-3D，且输出与模态接近。",
        "relation_hint": "同任务代表方法"
      }
    ],
    "method": [],
    "comparison": []
  },
  "paper_relations": [],
  "figure_table_index": {
    "figures": [{"label": "Figure 1", "caption": "图注"}],
    "tables": [{"label": "Table 1", "caption": "表注"}]
  }
}
```

## Field rules

- `links.pdf`: always prefer `conversation.pdf_url`; only fall back to Semantic Scholar `openAccessPdf.url` when the conversation payload is missing a PDF link.
- `authors`, `abstract_raw`, `citation_count`: Semantic Scholar is the preferred enrichment source when available.
- `links.doi` / `links.arxiv`: try Semantic Scholar `externalIds`; otherwise keep `null`.
- `research_problem`: top-level field; do not write `method_core.problem`.
- `benchmarks_or_eval.experiment_setup_summary`: keep it concise and focused on setup, not results.
- `editor_note`, `topics`, `paper_relations`: optional, research-facing fields; leave empty when no grounded signal exists.
- Missing scalar/link values should be `null`; missing arrays should be `[]`.

## Do not do

- Do not write legacy `pdf_url`.
- Do not write legacy `method_core.problem`.
- Do not infer `authors`, `doi`, `arxiv`, or `abstract_raw` without a grounded source.
- Do not fabricate `topics` or `paper_relations` just to fill the schema.
