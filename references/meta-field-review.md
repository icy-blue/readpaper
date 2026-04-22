# Meta 字段瘦身决议

## 背景与前提

这份决议面向当前 `translate-paper-forest` 的使用场景，而不是抽象通用 schema 设计。

本次判断固定基于以下前提：

- 用户画像：研究生，核心任务是 `方法复现 + 文献建图`
- 信息原则：优先保留 `少而硬的证据`，弱化大段主观 editorial
- 产品方向：关系发现是核心能力，不走纯摘要化路线
- 现实约束：当前前端已经消费了相当多的 canonical 字段，但并不是每个字段都值得继续让 skill 维护

本轮只沉淀结论文档，不直接改代码。  
后续如果采纳本决议，需要同步更新：

- `references/meta-contract.md`
- `references/paper-schema.md`
- `references/analysis-rubric.md`
- 前端展示与校验逻辑

## 当前前端真实消费情况

基于当前实现，前端的真实依赖大致如下：

- 首页主要依赖：`bibliography + story.paper_one_liner + editorial.research_position + taxonomy`
- 详情页 Summary/Method/Related 基本依赖：
  - `research_problem.*`
  - `core_contributions[]`
  - `method.*`
  - `evaluation.headline`
  - `evaluation.key_findings[]`
  - `evaluation.setup_summary`
  - `claims[]`
  - `comparison.*`
  - `relations[]`
  - `editorial.research_position`
- 当前前端没有真正展示正文内容或独立价值较弱的字段：
  - `assets.figures[] / assets.tables[]` 只显示数量，不显示内容
  - `evaluation.datasets[] / metrics[] / baselines[]` 已校验但前端未显式展示
  - `editorial.next_read[]` 未展示
  - `conclusion.author` 未展示
  - `taxonomy.representations[]` 未展示
  - `abstracts.*` 目前不是主要阅读入口

这意味着后续字段取舍不能只看 schema 完整性，还要看“是否真的服务复现和建图”。

## 关联发现是否需要新增字段

结论：`需要`。

原因不是当前系统完全没有关联能力，而是现有链路主要依赖下面几类信息混合推断：

- `taxonomy`
- `comparison.next_read[]`
- `evaluation.baselines[]`
- `relation_candidates[]`

这套组合已经能支撑基础的关联发现，但对研究生真正关心的三类关联仍然不够稳定：

- `问题线`：同问题、同目标、同缺口的论文
- `方法谱系`：同方法家族、extends、uses_method、关键机制相近的论文
- `实验对照`：共享 benchmark line、baseline family、evaluation protocol 的论文

当前最大缺口不是“没有关系边”，而是“没有统一、结构化、可复用的关联轴”。  
因此建议新增一个最小 canonical 字段 `meta.discovery_axes`，专门给关联发现和派生层使用。

## 字段决议

### 删除

以下字段建议在下一版 contract 中删除。

| JSON Path | 决议 | 原因 |
| --- | --- | --- |
| `meta.assets.*` | 删除 | 当前前端只显示计数，不展示 `caption/role/importance` 正文；维护成本高，且 contract 还要求 skill 明确产出，性价比偏低。 |
| `meta.story.problem` | 删除 | 与 `research_problem.summary/gaps/goal` 高度重复，当前更多作为 fallback 使用，不值得单独维护。 |
| `meta.story.method` | 删除 | 与 `method.summary/pipeline_steps/innovations` 重复，信息密度明显更低。 |
| `meta.story.result` | 删除 | 与 `evaluation.headline/key_findings` 重复，属于摘要层再压缩。 |
| `meta.editorial.summary` | 删除 | 主观性较高，且与 `story.paper_one_liner`、`evaluation.headline`、`research_position` 形成重复。 |
| `meta.editorial.why_read[]` | 删除 | 偏编辑式引导语，不属于“少而硬的证据”。 |
| `meta.editorial.strengths[]` | 删除 | 价值与 `core_contributions[]`、`claims[]`、`evaluation.key_findings[]` 重叠。 |
| `meta.editorial.cautions[]` | 删除 | 应收敛到更明确的新风险字段，而不是保留一个宽泛主观列表。 |
| `meta.editorial.next_read[]` | 删除 | 当前前端不消费，且与 `comparison.next_read[]` 职责重复。 |
| `meta.taxonomy.representations[]` | 删除 | 与 `method.representations[]` 重复；当前前端只展示后者。 |
| `meta.conclusion.author` | 删除 | 当前前端不展示，且属于作者结论的二次摘录，复现和建图价值弱。 |

### 保留

以下字段建议继续保留，作为“研究生复现 + 建图”的核心结构。

| JSON Path | 决议 | 原因 |
| --- | --- | --- |
| `meta.story.paper_one_liner` | 保留 | 适合首页和读前快速判断，是 `story` 中唯一明显高性价比字段。 |
| `meta.research_problem.*` | 保留 | 对判断论文想解决什么问题、补什么缺口非常关键。 |
| `meta.core_contributions[]` | 保留 | 是快速建立论文认知和做综述整理的核心字段。 |
| `meta.method.summary` | 保留 | 是方法复现入口，不可缺。 |
| `meta.method.pipeline_steps[]` | 保留 | 对复现、讲解和做 route 拆解都很有用。 |
| `meta.method.innovations[]` | 保留 | 帮助理解相对已有路线到底新在哪里。 |
| `meta.method.ingredients[]` | 保留 | 支持复现导向阅读。 |
| `meta.method.inputs[]` | 保留 | 是 canonical task I/O 基础信息。 |
| `meta.method.outputs[]` | 保留 | 是 canonical task I/O 基础信息。 |
| `meta.method.representations[]` | 保留 | 对方法理解和路线路由都重要，且与 `taxonomy.representations` 相比更贴近正文。 |
| `meta.evaluation.headline` | 保留 | 是实验读前入口，比纯 editorial 更接近证据。 |
| `meta.evaluation.datasets[]` | 保留 | 直接服务复现和实验对比。 |
| `meta.evaluation.metrics[]` | 保留 | 直接服务复现和实验对比。 |
| `meta.evaluation.baselines[]` | 保留 | 是方法定位和对比阅读的关键线索。 |
| `meta.evaluation.key_findings[]` | 保留 | 是实验部分最值得保留的结构化结论。 |
| `meta.evaluation.setup_summary` | 保留 | 能帮助快速理解实验边界和比较设置。 |
| `meta.claims[]` | 保留 | 是最符合“少而硬的证据”的结构块，应该继续作为核心证据入口。 |
| `meta.editorial.research_position` | 保留 | 对研究生做 route map 和 related work 定位有实际帮助。 |
| `meta.comparison.*` | 保留 | 继续承担人工可读的“对比钩子”和“下一篇线索”。 |
| `meta.relation_candidates[]` | 保留 | 继续承担图谱发现和关系生成的上游输入。 |

### 新增

以下字段建议在下一版 contract 中新增，用来增强“研究生做文章关联发现”的稳定性和可解释性。

| JSON Path | 决议 | 原因 |
| --- | --- | --- |
| `meta.discovery_axes.problem[]` | 新增 | 为“同问题空间 / 同研究目标 / 同缺口”的关联发现提供统一锚点，避免只靠 `taxonomy.tasks` 粗粒度碰撞。 |
| `meta.discovery_axes.method[]` | 新增 | 为方法家族、路线谱系、关键机制相近的论文建立统一锚点，补足 `taxonomy.methods` 过粗和 `relation_candidates` 过边式的问题。 |
| `meta.discovery_axes.evaluation[]` | 新增 | 为 benchmark line、baseline family、evaluation protocol 等实验对照语境提供稳定锚点，减少只靠 `datasets/metrics/baselines` 零散匹配的波动。 |
| `meta.discovery_axes.risk[]` | 新增 | 作为次级关联轴，用于连接共享局限、失败模式或研究风险相近的论文，但不作为主排序轴。 |

建议把 `meta.discovery_axes` 定位为：

- `paper` 级 discovery anchor
- 不是 relation edge
- 不是 UI-only 派生物
- 不直接存边、不直接存排序分数、不直接存近邻列表
- 由 skill 产出少量稳定的标准化标签，不写长句

推荐 shape：

- `meta.discovery_axes.problem[]`
- `meta.discovery_axes.method[]`
- `meta.discovery_axes.evaluation[]`
- `meta.discovery_axes.risk[]`

值约束：

- 使用短标签列表，不写句子
- 默认使用英文 canonical labels
- 必要时允许保留方法名、数据集名、benchmark 名等原文
- `risk[]` 只作为次级关联轴，不能盖过 `problem / method / evaluation`

### 调整

以下字段不建议简单保留原样，而应在下一版 contract 中重定义。

| 当前 JSON Path | 建议变更 | 新语义 |
| --- | --- | --- |
| `meta.conclusion.limitations[]` | 改为 `meta.research_risks[]` | 由 skill 基于全文综合判断的研究风险/限制，不要求只复述作者原文；服务复现、批判性阅读和路线判断。 |
| `meta.editorial.graph_worthy` | 保留但重定义 | 作为 `知识图谱锚点信号` 使用，是内部 curation 信号，不属于读者摘要，不应与 `值得精读` 混用。 |

对这两个调整项，建议补充更明确的 policy：

- `research_risks[]`
  - 关注“这篇论文真正需要警惕的限制或不确定性”
  - 可以来自作者限制、实验覆盖不足、泛化边界、对比不充分、依赖特殊前提等
  - 目标是帮助研究生快速判断复现难点和研究风险
- `graph_worthy`
  - 不再理解成“好论文”标记
  - 也不应与首页读前判断绑定
  - 它只回答一个问题：这篇论文是否值得作为长期知识图谱里的锚点保留

## 关联字段边界

为了避免新增字段后与现有链路冲突，建议把职责拆清如下：

- `discovery_axes`
  - 只提供统一的结构化关联锚点
  - 服务 `neighbors`、关联排序、结构化解释
  - 不直接存图谱边
- `comparison.*`
  - 继续负责人工可读的对比钩子与 next-read
  - 更偏“给人看的比较入口”
- `relation_candidates[]`
  - 继续负责显式 typed relation 的上游输入
  - 更偏“边为什么成立”
- `relations[]`
  - 继续负责最终 canonical 图谱边
- `neighbors`
  - 继续是派生结果
  - 后续优先消费 `discovery_axes`，再结合现有字段做排序与解释

## 推荐的新 contract 方向

如果采纳本决议，下一版 schema 建议朝下面收缩：

- `story` 收缩为仅保留 `paper_one_liner`
- `editorial` 收缩为：
  - `research_position`
  - `graph_worthy`
- 删除 `taxonomy.representations`
- 新增 `research_risks[]`
- 新增 `discovery_axes`
- 删除 `assets`

这是一条推荐的 contract 方向，不是本次已经实施的代码现实。

## 前端含义

如果后续按本决议推进，前端展示层建议对应调整为：

- 首页继续依赖：
  - `paper_one_liner`
  - `research_position`
  - `taxonomy`
- 详情页补展示：
  - `evaluation.datasets[]`
  - `evaluation.metrics[]`
  - `evaluation.baselines[]`
- “风险与限制”区块后续改读：
  - `research_risks[]`
- `neighbors` 的结构化解释后续优先读取：
  - `discovery_axes`
- `assets` 计数卡移除，不再为只显示数量维护高成本结构
- `comparison` 继续保留为人工可读的对比钩子
- `relations/neighbors` 继续承担图谱和发现功能
- 相关论文解释后续从纯自然语言 `reason` 升级为“结构化关联轴 + 一句话解释”
- 不要求首页直接展示 `discovery_axes`，先服务详情页 Related 区和派生逻辑

需要注意：

- 上面的“前端含义”已经被下文“用户前端结构修改决议”进一步收紧
- 尤其是 `verdict / reading_route`，不再视为首页或详情页的长期展示字段

## 用户前端结构修改决议

这部分不是抽象产品说明，而是面向实现前端改造的结构文档。  
目标是让研究生用户的主入口更稳定地服务三件事：

- `问题理解`
- `方法复现`
- `关联发现`

前端信息架构建议从当前的 `Summary / Method / Metadata / Related` 重组为：

- `Overview`
- `Method`
- `Graph`

### 首页结构决议

首页卡片不再以“读前判断”作为主入口，而改成“研究入口”。

建议首页卡片主依赖收敛为：

- `story.paper_one_liner`
- `editorial.research_position`
- 少量 `taxonomy.tasks / taxonomy.methods / taxonomy.themes`

对应地：

- `editorial.verdict`
- `editorial.reading_route`

不再作为首页卡片的长期主入口字段。

这里需要明确一条前端 override：

- 这不只是“前端暂时不显示”
- 而是前端结构决议明确认为这两个字段不应继续作为长期字段存在
- 后续 schema 应同步收缩，不再受前文“轻判断字段保留”的旧结论约束

### 详情页结构决议

详情页主结构建议重组为 `Overview / Method / Graph` 三段，而不是继续保留独立 `Metadata` tab。

推荐实现落点：

- `web/src/pages/HomePage.tsx`
- `web/src/components/PaperDetailWorkspace.tsx`
- `web/src/types.ts`

文档按行为分组描述，不按文件逐条改动罗列。

#### Overview

`Overview` 负责论文入口理解，不再承担编辑式读前判断。

建议放入：

- `story.paper_one_liner`
- `research_problem.summary`
- `research_problem.gaps[]`
- `research_problem.goal`
- `core_contributions[]`
- `research_risks[]`
- `editorial.research_position`
- 必要的 `taxonomy` 阅读相关信息

这里的重点是：

- 从“值不值得读”转向“这篇论文在解决什么问题、贡献了什么、风险在哪里”
- 基础元信息中的阅读相关部分放在这里，而不是单开 `Metadata`

#### Method

`Method` 负责方法和证据，不再依赖旧的 story fallback。

建议放入：

- `method.summary`
- `method.pipeline_steps[]`
- `method.innovations[]`
- `method.ingredients[]`
- `method.inputs[]`
- `method.outputs[]`
- `method.representations[]`
- `evaluation.headline`
- `evaluation.datasets[]`
- `evaluation.metrics[]`
- `evaluation.baselines[]`
- `evaluation.key_findings[]`
- `evaluation.setup_summary`
- `claims[]`

这里需要明确：

- `claims[]` 如果保留，默认视作 `Method` 下的证据块
- 不再继续挂在旧 `Metadata` 结构下
- `evaluation.datasets / metrics / baselines` 从“未显式展示的事实字段”升级为 `Method` 中的核心区块

#### Graph

`Graph` 负责关联发现与路线探索，是旧 `Related` 的升级版。

建议展示顺序：

1. `discovery_axes.*`
2. `neighbors`
3. `comparison.*`
4. `relations[]`

对应职责：

- `discovery_axes.*`：先告诉用户“为什么相关”
- `neighbors`：给出派生出来的候选相关论文
- `comparison.*`：保留人工可读的对比钩子
- `relations[]`：保留最终结构化图谱边

这里的目标不是把所有关系混在一起，而是让研究生先看懂关联轴，再看具体论文和正式关系。

### Metadata 的去向

独立 `Metadata` tab 建议取消。

其内容拆分如下：

- 作者、venue、年份、外部链接：迁移到页头
- taxonomy 中与阅读相关的部分：迁移到 `Overview`
- `claims[]`：迁移到 `Method`
- `assets` 计数卡：直接删除

因此前端实现不再需要继续维护“元信息 tab 兼任 claims 容器”的结构。

### 前端字段去向映射

为了让实现者不用自己判断旧字段去哪里，建议直接按下面收口：

| 旧字段/结构 | 新去向 |
| --- | --- |
| `story.problem` | 删除，不再做前端 fallback |
| `story.method` | 删除，不再做前端 fallback |
| `story.result` | 删除，不再做前端 fallback |
| `editorial.summary` | 删除，不再进入前端 |
| `editorial.why_read[]` | 删除，不再进入前端 |
| `editorial.strengths[]` | 删除，不再进入前端 |
| `editorial.cautions[]` | 删除，不再进入前端 |
| `editorial.next_read[]` | 删除，不再进入前端 |
| `conclusion.limitations[]` | 迁移语义后改为 `research_risks[]`，进入 `Overview` |
| `evaluation.datasets[] / metrics[] / baselines[]` | 进入 `Method`，作为核心实验区块 |
| `claims[]` | 进入 `Method`，作为证据块 |
| `discovery_axes.*` | 只在 `Graph` 直接展示 |
| `comparison.* + neighbors + relations[]` | 在 `Graph` 分层展示，职责拆清 |
| `assets.*` | 直接删除，不再保留前端计数卡 |

### 新的前端依赖方向

首页卡片主依赖：

- `paper_one_liner`
- `research_position`
- `taxonomy`

详情页主依赖：

- `research_problem.*`
- `core_contributions[]`
- `method.*`
- `evaluation.*`
- `claims[]`
- `research_risks[]`
- `discovery_axes.*`
- `comparison.*`
- `neighbors`
- `relations[]`

这里也需要再次明确：

- `editorial.verdict`
- `editorial.reading_route`

在这份前端结构修改决议中不再保留为长期字段，后续 schema 应同步收缩。

## 当前展示字段 vs 建议保留字段

下表用于确认前端不会因为字段瘦身而失去核心能力。

| 使用场景 | 当前主要字段 | 建议保留字段 |
| --- | --- | --- |
| 首页快速筛选 | `story.paper_one_liner`、`editorial.verdict`、`editorial.reading_route`、`taxonomy` | 收敛为 `paper_one_liner + research_position + taxonomy`，并下线 `verdict / reading_route` |
| 研究问题判断 | `research_problem.*`、`story.problem` fallback | 保留 `research_problem.*`，删除 `story.problem` |
| 方法理解 | `method.*`、`story.method` fallback | 保留 `method.*`，删除 `story.method` |
| 实验判断 | `evaluation.headline`、`evaluation.key_findings[]`、`evaluation.setup_summary`、`story.result` fallback | 保留 `evaluation.*`，删除 `story.result`，并补展示 `datasets/metrics/baselines` |
| 证据阅读 | `claims[]` | 保持 `claims[]` 作为核心证据块 |
| 风险判断 | `editorial.cautions[]` 或 `conclusion.limitations[]` fallback | 收敛为新的 `research_risks[]` |
| 路线对比 | `comparison.*` | 保持不变 |
| 关联发现 | `taxonomy + comparison.next_read + evaluation.baselines + relation_candidates -> relations/neighbors` | 收敛为 `discovery_axes + comparison + relations/neighbors` 的分工 |
| 图谱发现 | `relation_candidates -> relations -> neighbors` | 保持主链路不变，但优先引入 `discovery_axes` 作为统一锚点来源 |
| 图表导航 | `assets.*` 仅计数 | 删除整组，不再单独维护 |

## 结论

从当前前端展示和研究生用户目标出发，最值得砍掉的是：

- 重复性的短摘要字段
- 主观 editorial 扩写字段
- 当前前端不消费或只展示计数的高维护成本字段

最应该保住的是：

- 研究问题
- 方法结构
- 实验三件套与关键发现
- claims 证据块
- comparison / relation 这两层建图结构

为了让研究生更稳定地发现“同问题 / 同方法谱系 / 同实验对照”的论文，还值得新增：

- `discovery_axes.problem[]`
- `discovery_axes.method[]`
- `discovery_axes.evaluation[]`
- `discovery_axes.risk[]`

最值得重定义的是：

- `research_risks[]`
- `graph_worthy`

这两处一旦定义清楚，后续 contract、rubric、前端展示就会明显更一致。
