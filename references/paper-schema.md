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
  "abstract_raw": "Original abstract text...",
  "abstract_zh": "中文摘要……",
  "summary": {
    "one_liner": "一句话结论",
    "abstract_summary": "面向自己复盘的短摘要",
    "research_value": {
      "summary": "为什么值得继续读",
      "points": ["可作为长期知识图谱节点", "适合作为某条技术路线的对比入口"]
    },
    "worth_long_term_graph": true
  },
  "storyline": {
    "problem": "现有开放词汇 3D part segmentation 缺少规范空间建模",
    "method": "通过 LLM-guided canonical spatial modeling 建模规范空间",
    "outcome": "提升开放世界 promptable segmentation 的稳定性"
  },
  "research_problem": {
    "summary": "这篇论文要解决的核心研究问题",
    "gaps": ["已有方法仍在输入坐标系里做语义推断", "跨姿态和跨类别的一致性不足"],
    "goal": "建立面向开放世界 3D 语义部件理解的规范空间建模"
  },
  "core_contributions": ["贡献 1", "贡献 2"],
  "key_claims": [
    {
      "claim": "具体 claim",
      "type": "experiment",
      "support": ["section:4. Experiments", "figure:Figure 2"],
      "confidence": "high"
    }
  ],
  "method_core": {
    "approach_summary": "核心做法",
    "pipeline_steps": ["步骤 1", "步骤 2"],
    "innovations": ["方法创新 1", "方法创新 2"],
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
    "best_results": ["最值得高亮的一条结果"],
    "experiment_setup_summary": "实验设置摘要"
  },
  "author_conclusion": "作者在论文中最终想传达的结论",
  "editor_note": {
    "summary": "你的编者按/阅读备注",
    "points": ["为什么值得看", "接下来最适合拿谁做对比"]
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
    "comparison_aspects": [
      {
        "aspect": "canonical space modeling",
        "difference": "把规范空间直接引入开放世界 3D part segmentation"
      }
    ],
    "recommended_next_read": "Find3D"
  },
  "paper_neighbors": {
    "task": [
      {
        "paper_id": "neighbor-paper",
        "title": "Neighbor Paper",
        "score": 11,
        "score_level": "high",
        "match_source": "task_overlap",
        "paper_path": "papers/neighbor-paper.md",
        "route_path": "#/paper/neighbor-paper",
        "shared_signals": {
          "task_axes": ["Text-to-3D"]
        },
        "reason": "同属 Text-to-3D，且输出与模态接近。",
        "reason_short": "同任务且输出对象接近。",
        "relation_hint": "same-task"
      }
    ],
    "method": [],
    "comparison": []
  },
  "paper_relations": [],
  "figure_table_index": {
    "figures": [
      {
        "label": "Figure 1",
        "caption": "图注",
        "role": "method_overview",
        "importance": "high"
      }
    ],
    "tables": [
      {
        "label": "Table 1",
        "caption": "表注",
        "role": "quantitative_result",
        "importance": "medium"
      }
    ]
  }
}
```

## Field rules

- `links.pdf`: always prefer `conversation.pdf_url`; only fall back to Semantic Scholar `openAccessPdf.url` when the conversation payload is missing a PDF link.
- `authors`, `abstract_raw`, `citation_count`: Semantic Scholar is the preferred enrichment source when available.
- `links.doi` / `links.arxiv`: try Semantic Scholar `externalIds`; otherwise keep `null`.
- `summary.one_liner`: keep it under 120 Chinese characters when possible.
- `storyline.problem` / `storyline.method` / `storyline.outcome`: keep each item short enough for a two-line first-screen strip.
- `research_problem.summary`: keep it under 100 Chinese characters when possible.
- `method_core.approach_summary`: keep it under 100 Chinese characters when possible.
- `benchmarks_or_eval.findings`: prefer short bullet-like results; each item should stay under 80 Chinese characters when possible.
- `editor_note.summary`: keep it under 120 Chinese characters when possible.
- `paper_neighbors.*[].reason_short`: keep it under 50 Chinese characters when possible.
- `benchmarks_or_eval.experiment_setup_summary`: keep it concise and focused on setup, not results.
- `key_claims[].type`: use `method`, `experiment`, `capability`, or `limitation` when grounded; otherwise keep a stable custom string or omit the claim.
- `figure_table_index.*[].role`: use lightweight reading-oriented categories such as `method_overview`, `qualitative_result`, `quantitative_result`, `ablation`, or `failure_case`.
- `figure_table_index.*[].importance`: use `high`, `medium`, or `low`.
- `editor_note`, `topics`, `paper_relations`: optional, research-facing fields; leave empty when no grounded signal exists.
- Missing scalar/link values should be `null`; missing arrays should be `[]`.

## Do not do

- Do not write legacy `pdf_url`.
- Do not write legacy `method_core.problem`.
- Do not keep `research_problem`, `summary.research_value`, or `editor_note` as plain strings.
- Do not infer `authors`, `doi`, `arxiv`, or `abstract_raw` without a grounded source.
- Do not fabricate `topics` or `paper_relations` just to fill the schema.
