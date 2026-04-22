# Paper Schema v2

Write one canonical paper record per file at `outputs/papers/<paper-id>.json`.

This schema is the long-lived source of truth for paper content. It stores:

- paper facts
- grounded analysis
- canonical taxonomy
- typed relations

It does **not** store UI-only fallback text, search indexes, neighbor lists, or other site-derived artifacts.

## Required Shape

```json
{
  "id": "cosmo3d-open-world-promptable-3d-semantic-part-segmentat-8764ad09",
  "source": {
    "conversation_ids": ["1bec2cbb63a7"],
    "paper_path": "papers/cosmo3d-open-world-promptable-3d-semantic-part-segmentat-8764ad09.md",
    "route_path": "#/paper/cosmo3d-open-world-promptable-3d-semantic-part-segmentat-8764ad09"
  },
  "bibliography": {
    "title": "CoSMo3D: Open-World Promptable 3D Semantic Part Segmentation through LLM-Guided Canonical Spatial Modeling",
    "authors": ["Li Jin", "Weikai Chen"],
    "year": 2026,
    "venue": "arXiv.org",
    "citation_count": 0,
    "identifiers": {
      "doi": "10.48550/arXiv.2603.01205",
      "arxiv": "2603.01205"
    },
    "links": {
      "pdf": "https://...",
      "project": null,
      "code": "https://github.com/JinLi998/CoSMo3D/tree/main",
      "data": null
    }
  },
  "abstracts": {
    "raw": "Original abstract text...",
    "zh": "中文摘要……"
  },
  "story": {
    "paper_one_liner": "把规范空间直接引入开放世界 3D part segmentation 的代表工作。",
    "problem": "现有开放世界 3D part segmentation 缺少稳定的规范空间建模。",
    "method": "通过 canonical spatial modeling 与双分支训练目标学习可迁移的规范空间。",
    "result": "在多组 promptable segmentation 设定下结果更稳且更强。"
  },
  "research_problem": {
    "summary": "开放世界 promptable 3D segmentation 在任意姿态和跨类别场景下仍不稳定。",
    "gaps": ["现有方法主要依赖几何-文本匹配。", "缺少跨姿态与跨类别共享的规范空间语义。"],
    "goal": "为开放世界 3D part understanding 建立可学习的 canonical-space reasoning。"
  },
  "core_contributions": [
    "提出面向开放世界 promptable 3D segmentation 的 canonical spatial modeling 框架。",
    "构建 LLM-guided 的跨类别 canonicalized dataset。",
    "通过 canonical map anchoring 与 box calibration 强化规范空间一致性。"
  ],
  "method": {
    "summary": "以双分支框架把几何-语言对齐和 canonical-space regularization 结合起来。",
    "pipeline_steps": [
      "编码点云与文本提示并建立跨模态对齐。",
      "引入训练期 canonical embedding branch 预测 canonical map 与 semantic boxes。",
      "用 canonical-space losses 压缩姿态变化并稳定部件语义。"
    ],
    "innovations": [
      "把开放世界 3D part segmentation 重写为 canonical-space reasoning 问题。",
      "引入跨类别 canonicalized supervision 与双分支 regularization。"
    ],
    "ingredients": ["Large Language Model", "Point Transformer", "SigLIP"],
    "inputs": ["Point Cloud", "Text Prompt"],
    "outputs": ["Segmentation Mask"],
    "representations": ["Point Cloud", "Canonical Map", "Bounding Box", "Normals"]
  },
  "evaluation": {
    "headline": "在多组 promptable segmentation 设定下都优于 Find3D 等基线。",
    "datasets": ["3Dcompat-Coarse", "3Dcompat-Fine", "ShapeNet-Part", "PartNet-E"],
    "metrics": ["mIoU"],
    "baselines": ["Find3D", "PartSLIP++", "PointCLIPV2"],
    "key_findings": [
      "在 canonical 与 rotated 两类姿态设定下都保持稳定提升。",
      "相对 2D rendering baselines 推理更快且分割更稳。"
    ],
    "setup_summary": "在多组 prompt 和姿态设置下，对 3Dcompat、ShapeNet-Part 与 PartNet-E 做统一比较。"
  },
  "claims": [
    {
      "text": "canonical-space modeling 能显著提升开放世界 promptable 3D segmentation 的稳定性与精度。",
      "type": "method",
      "support": ["section:3. Method", "figure:Figure 2"],
      "confidence": "high"
    }
  ],
  "conclusion": {
    "author": "作者认为 canonical space 是开放世界 3D understanding 的关键缺失变量。",
    "limitations": []
  },
  "editorial": {
    "verdict": "值得精读",
    "summary": "适合作为 canonical-space 3D understanding 路线的代表样本。",
    "why_read": ["方法动机和机制都很明确。", "和 Find3D 的对比线清楚。"],
    "strengths": ["canonical-space 变量引入得自然。", "实验设置覆盖姿态与 prompt 变化。"],
    "cautions": ["主要仍聚焦于 segmentation 任务。"],
    "reading_route": "method",
    "research_position": "可作为开放世界 3D part reasoning 的关键对照样本。",
    "graph_worthy": true,
    "next_read": ["Find3D"]
  },
  "taxonomy": {
    "themes": ["3D Understanding"],
    "tasks": ["Semantic Segmentation", "Open-Vocabulary Segmentation"],
    "methods": ["Large Language Model", "Point Transformer", "Canonical Spatial Modeling"],
    "modalities": ["3D", "Text"],
    "representations": ["Point Cloud", "Canonical Map", "Bounding Box", "Normals"],
    "novelty_types": ["Representation Modeling", "Architecture Design", "Data Curation"]
  },
  "comparison": {
    "aspects": [
      {
        "aspect": "method",
        "difference": "相对只做 geometry-text matching 的路线，显式引入 canonical-space regularization。"
      },
      {
        "aspect": "result",
        "difference": "在任意姿态与跨类别设定下保持更稳的 part localization。"
      }
    ],
    "next_read": ["Find3D"]
  },
  "assets": {
    "figures": [
      {
        "label": "Figure 1",
        "caption": "Method overview.",
        "role": "method_overview",
        "importance": "high"
      }
    ],
    "tables": [
      {
        "label": "Table 1",
        "caption": "Quantitative comparison on promptable segmentation benchmarks.",
        "role": "quantitative_result",
        "importance": "high"
      }
    ]
  },
  "relations": [
    {
      "type": "compares_to",
      "target_kind": "local",
      "target_paper_id": "find3d-open-world-3d-part-segmentation-xxxx",
      "label": "Find3D",
      "description": "最直接的几何-文本匹配对照路线。",
      "confidence": 0.9
    },
    {
      "type": "extends",
      "target_kind": "external",
      "target_paper_id": null,
      "label": "Example External Paper",
      "description": "在已有视觉-几何生成路线基础上做扩展。",
      "confidence": 0.82
    }
  ]
}
```

## Field Rules

- `id`: canonical paper id, unique within the repo.
- `source.conversation_ids`: all contributing source conversations for the canonical paper.
- `source.paper_path` / `source.route_path`: stable local routing info used by site generators.
- `bibliography.identifiers`: only persistent scholarly IDs such as DOI / arXiv.
- `bibliography.links`: only reader-facing URLs such as PDF / project / code / data.
- `abstracts.raw`: original-language abstract when locally available from prior enrichment; keep it `null` rather than querying external services during assembly.
- `abstracts.zh`: translated abstract from the translate conversation.
- `story`: short reading-facing summary of the paper itself.
- `research_problem`: grounded formulation of the problem, gaps, and goal.
- `method.inputs` / `method.outputs`: canonical task I/O facts; do not repeat elsewhere.
- `evaluation.baselines`: explicit comparison methods named in the paper.
- `claims`: falsifiable or comparable claims with grounded support references.
- `editorial`: editor-facing reading judgment for humans.
- `editorial.graph_worthy`: conservative long-term curation flag for graph anchors; set it only when the paper has durable route or comparison value beyond a one-off strong read.
- `taxonomy`: canonical English labels only. Translate only in view/render layers.
- `comparison.aspects`: short comparison hooks for reading and relation building.
- `assets`: figure/table reading index with stable role and importance labels.
- `relations`: normalized typed graph edges only; do not store generic neighbors, unresolved names, or retrieval artifacts here.
- `relations.target_kind`: `local` or `external`.
- `relations.target_paper_id`: required when `target_kind` is `local`.
- `relations.label`: required when `target_kind` is `external`; the Semantic Scholar search URL is derived in the render layer and must not be stored in canonical records.

## Do Not Store In Canonical Records

- UI fallbacks or display-specific duplicated text
- search text, embeddings, retrieval axes, or ranking features
- homepage cards, filters, featured-paper lists, or reading-route chips
- derived neighbor lists
- empty future placeholders such as `topics`, `paper_neighbors`, or `retrieval_profile`

Those belong in `outputs/site/` or other derived artifacts.
