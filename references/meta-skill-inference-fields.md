# Meta 字段里需要 skill 推断的字段清单

这份清单用于回答一个具体问题：

- `outputs/meta/<paper-id>.json` 里，哪些字段必须由 `extract-paper-meta` skill 负责？
- 哪些字段只是 artifact 级别的包裹信息？
- 哪些字段其实是 `normalize_papers.py` 在 canonical assembly 阶段补出来的？

结论先说：

- 按当前 `meta-v7` contract，`meta.*` 下的字段都属于 `extract-paper-meta` skill 负责产出的分析层字段。
- 其中一部分是强依赖阅读理解的“归纳 / 判断 / 结构化解释”字段。
- 另一部分虽然更接近抽取，但仍然需要 skill 做 grounding、去重、规范化和裁剪。
- `paper_id`、`extractor_version`、`source_conversation_id`、`source_semantic_updated_at`、`extracted_at` 不属于 `meta` 本体分析字段，不应和 skill-owned 的 `meta.*` 混在一起。

## 1. 强依赖 skill 推断的字段

这些字段不是简单拷贝原文就能得到，必须靠 skill 基于上下文做归纳、压缩、判断、取舍或分类。

### Story

- `meta.story.paper_one_liner`

### Research Problem

- `meta.research_problem.summary`
- `meta.research_problem.gaps[]`
- `meta.research_problem.goal`

### Contributions

- `meta.core_contributions[]`

### Method Understanding

- `meta.method.summary`
- `meta.method.pipeline_steps[]`
- `meta.method.innovations[]`

### Evaluation Understanding

- `meta.evaluation.headline`
- `meta.evaluation.key_findings[]`
- `meta.evaluation.setup_summary`

### Claims

- `meta.claims[].text`
- `meta.claims[].type`
- `meta.claims[].support`
- `meta.claims[].confidence`

### Research Risks

- `meta.research_risks[]`

### Editorial Judgment

- `meta.editorial.research_position`
- `meta.editorial.graph_worthy`

### Canonical Taxonomy

- `meta.taxonomy.themes[]`
- `meta.taxonomy.tasks[]`
- `meta.taxonomy.methods[]`
- `meta.taxonomy.modalities[]`
- `meta.taxonomy.novelty_types[]`

### Comparison Hooks

- `meta.comparison.aspects[].aspect`
- `meta.comparison.aspects[].difference`
- `meta.comparison.next_read[]`

### Discovery Axes

- `meta.discovery_axes.problem[]`
- `meta.discovery_axes.method[]`
- `meta.discovery_axes.evaluation[]`
- `meta.discovery_axes.risk[]`

### Relation Candidates

- `meta.relation_candidates[].type`
- `meta.relation_candidates[].target_name`
- `meta.relation_candidates[].description`
- `meta.relation_candidates[].confidence_hint`
- `meta.relation_candidates[].evidence_mode`

## 2. 由 skill 负责抽取和归一化，但“推断强度”相对较低的字段

这些字段通常在论文翻译内容、图表标题、实验段落里能直接找到候选值，但仍然应该由 skill 产出，而不是在下游脚本里用启发式乱猜。

### Method Facts

- `meta.method.ingredients[]`
- `meta.method.inputs[]`
- `meta.method.outputs[]`
- `meta.method.representations[]`

### Evaluation Facts

- `meta.evaluation.datasets[]`
- `meta.evaluation.metrics[]`
- `meta.evaluation.baselines[]`

## 3. 不应算进“需要 skill 推断的 meta 字段”的 artifact 包裹字段

这些字段位于 meta artifact 顶层，但它们不是论文分析内容本身。

- `paper_id`
- `extractor_version`
- `source_conversation_id`
- `source_semantic_updated_at`
- `extracted_at`

建议分工：

- `paper_id`：来自 raw payload
- `extractor_version`：来自 `extractor-config.json`
- `source_conversation_id`：来自源 conversation
- `source_semantic_updated_at`：来自源 payload 的语义更新时间
- `extracted_at`：meta artifact 写出时间

## 4. 不属于 meta skill 负责范围、而由 normalize 阶段补齐的字段

下面这些不在 `outputs/meta/<paper-id>.json` 的 `meta.*` 里，属于 canonical paper record 组装阶段的职责：

- `source.*`
- `bibliography.title`
- `bibliography.year`
- `bibliography.venue`
- `bibliography.citation_count`
- `bibliography.identifiers.*`
- `bibliography.links.*`
- `abstracts.raw`
- `abstracts.zh`
- 最终 `relations[]`

其中：

- `abstracts.zh` 是 `normalize_papers.py` 从 translated abstract section 提取出来的。
- `bibliography.links.*` 主要由 `normalize_papers.py` 从 payload 和 URL 中归类。
- 最终 `relations[]` 由 `meta.relation_candidates[]` 结合本地 registry 解析得到。

## 5. 如果你只想记一条最短规则

可以直接按下面这条记：

- 除了 artifact 顶层的来源/版本/时间字段以外，`meta.*` 全部都应该视为 skill-owned。
- 其中 `story`、`research_problem`、`core_contributions`、`method.summary/pipeline_steps/innovations`、`evaluation.headline/key_findings/setup_summary`、`claims`、`research_risks`、`editorial`、`taxonomy`、`comparison`、`discovery_axes`、`relation_candidates` 是最典型的“必须靠 skill 推断”的部分。
- `datasets / metrics / baselines / method ingredients / method representations` 虽然更接近抽取，但也仍应由 skill 负责 grounding 和规范化，不应交给下游脚本猜。
