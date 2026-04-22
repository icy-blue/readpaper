import { App as AntApp, Button, Collapse, Empty, Flex, Input, Tabs, Tag, Typography } from "antd";
import { ArrowLeftOutlined, BookOutlined, CopyOutlined, LinkOutlined } from "@ant-design/icons";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  chipToneClass,
  cleanDisplayText,
  confidenceTone,
  displayClaimType,
  displayComparisonAspect,
  displayFigureRole,
  displayValueLabel,
  filterFigureTableItems,
  firstExternalLinks,
  formatYear,
  importanceTagClass,
  loadPaperDetail,
  markdownHref,
  paperRoute,
  recommendedRouteLabel,
  scoreLevelLabel,
  scoreLevelTagClass,
  sharedSignalPreview,
  verdictTagClass,
} from "../lib/paper";
import type { FigureTableIndexItem, NeighborItem, PaperCanonicalRecord, PaperDetailViewModel, SiteIndexPayload } from "../types";
import { TooltipTag, TooltipText } from "../components/OverflowTooltip";

const { Title, Paragraph, Text } = Typography;

async function copyText(value: string) {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(value);
    return;
  }
  const input = document.createElement("textarea");
  input.value = value;
  document.body.appendChild(input);
  input.select();
  document.execCommand("copy");
  document.body.removeChild(input);
}

function PaperSection({
  title,
  kicker,
  summary,
  children,
}: {
  title: string;
  kicker?: string;
  summary?: string | null;
  children: ReactNode;
}) {
  return (
    <section className="paper-section">
      <div className="paper-section-heading">
        {kicker ? <Text className="section-kicker">{kicker}</Text> : null}
        <Title level={2} className="paper-section-title">
          {title}
        </Title>
        {summary ? <Paragraph className="paper-section-summary">{summary}</Paragraph> : null}
      </div>
      <div className="paper-section-body">{children}</div>
    </section>
  );
}

function EmptyBlock({ description }: { description: string }) {
  return <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={description} />;
}

function BadgeGroup({ values, color }: { values: string[]; color?: string }) {
  if (!values.length) {
    return <Text type="secondary">暂无</Text>;
  }
  return (
    <Flex wrap="wrap" gap={8}>
      {values.map((value) => (
        <TooltipTag key={value} label={displayValueLabel(value)} className={chipToneClass(color)} />
      ))}
    </Flex>
  );
}

function MetaLine({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="meta-line">
      <Text className="meta-label">{label}</Text>
      <div className="meta-value">{value}</div>
    </div>
  );
}

function ContentGroup({
  title,
  children,
  className = "",
}: {
  title: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={`content-group ${className}`.trim()}>
      <Text className="content-group-title">{title}</Text>
      <div className="content-group-body">{children}</div>
    </div>
  );
}

function HighlightPanel({
  kicker,
  title,
  copy,
  children,
  className = "",
}: {
  kicker?: string;
  title: string;
  copy: string;
  children?: ReactNode;
  className?: string;
}) {
  return (
    <div className={`highlight-panel ${className}`.trim()}>
      {kicker ? <Text className="section-kicker">{kicker}</Text> : null}
      <Text className="highlight-title">{title}</Text>
      <Paragraph className="section-lead">{copy}</Paragraph>
      {children}
    </div>
  );
}

function TextList({
  items,
  emptyText,
  ordered = false,
  className = "",
}: {
  items: string[];
  emptyText: string;
  ordered?: boolean;
  className?: string;
}) {
  if (!items.length) {
    return (
      <Paragraph type="secondary" className="group-empty">
        {emptyText}
      </Paragraph>
    );
  }

  const ListTag = ordered ? "ol" : "ul";
  return (
    <ListTag className={`content-list${ordered ? " ordered" : ""} ${className}`.trim()}>
      {items.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ListTag>
  );
}

function StatTile({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="stat-tile">
      <Text className="stat-label">{label}</Text>
      <div className="stat-value">{value}</div>
    </div>
  );
}

function ExternalLinkButtons({ paper }: { paper: PaperCanonicalRecord }) {
  const navigate = useNavigate();
  const links = firstExternalLinks(paper.bibliography);
  const markdownLink = markdownHref(paper.source.paper_path);

  return (
    <Flex wrap="wrap" gap={10} className="hero-action-row">
      <Button icon={<ArrowLeftOutlined />} onClick={() => navigate("/")}>
        返回首页
      </Button>
      {markdownLink ? (
        <Button href={markdownLink} target="_blank" icon={<BookOutlined />}>
          Markdown
        </Button>
      ) : null}
      {links.map((item, index) => (
        <Button
          key={item.key}
          href={item.href}
          target="_blank"
          type={index === 0 && item.key === "pdf" ? "primary" : "default"}
          icon={<LinkOutlined />}
        >
          {item.label}
        </Button>
      ))}
    </Flex>
  );
}

function DecisionHero({ paper }: { paper: PaperCanonicalRecord }) {
  const tags = [...paper.taxonomy.tasks, ...paper.taxonomy.methods, ...paper.taxonomy.modalities, ...paper.taxonomy.novelty_types].slice(0, 8);
  const quickLines = [
    { label: "摘要判断", value: paper.editorial.summary },
    { label: "推荐路径", value: recommendedRouteLabel(paper.editorial.reading_route) },
    { label: "结果先看", value: paper.evaluation.headline },
  ].filter((item): item is { label: string; value: string } => Boolean(item.value));

  return (
    <section className="hero-surface detail-hero-shell">
      <div className="detail-hero-main">
        <Flex wrap="wrap" gap={8}>
          <Tag className="chip-tag chip-tag-venue">{paper.bibliography.venue || "未知来源"}</Tag>
          <Tag className="chip-tag chip-tag-year">{formatYear(paper.bibliography.year)}</Tag>
          {paper.bibliography.citation_count !== null ? <Tag className="chip-tag chip-tag-citation">引用 {paper.bibliography.citation_count}</Tag> : null}
          {paper.editorial.verdict ? <Tag className={verdictTagClass(paper.editorial.verdict)}>{paper.editorial.verdict}</Tag> : null}
          <Tag className={chipToneClass("processing")}>{recommendedRouteLabel(paper.editorial.reading_route)}</Tag>
        </Flex>

        <div>
          <Title className="detail-display-title">{paper.bibliography.title}</Title>
          <Paragraph className="author-line">
            {paper.bibliography.authors.length ? paper.bibliography.authors.join(" / ") : "作者信息暂缺"} · {paper.bibliography.venue || "未知来源"} ·{" "}
            {formatYear(paper.bibliography.year)}
          </Paragraph>
          <TooltipText
            text={paper.story.paper_one_liner || paper.editorial.summary || "暂无首屏阅读判断。"}
            as="paragraph"
            rows={4}
            className="hero-one-liner detail-one-liner"
          />
        </div>

        <div className="content-group hero-summary-group">
          <Text className="content-group-title">读前摘要</Text>
          {quickLines.length ? (
            <dl className="info-list hero-summary-list">
              {quickLines.map((item) => (
                <div key={item.label} className="info-list-row">
                  <dt>{item.label}</dt>
                  <dd>{item.value}</dd>
                </div>
              ))}
            </dl>
          ) : (
            <Paragraph type="secondary" className="group-empty">
              暂无结构化摘要。
            </Paragraph>
          )}
        </div>

        {tags.length ? (
          <div className="hero-tag-block">
            <Text className="hero-tag-label">定位标签</Text>
            <Flex wrap="wrap" gap={8} className="hero-tag-row">
              {tags.map((tag) => (
                <TooltipTag key={`${paper.id}-${tag}`} label={tag} className="chip-tag chip-tag-tone-blue" />
              ))}
            </Flex>
          </div>
        ) : null}
      </div>

      <aside className="detail-hero-aside">
        <div className="hero-action-panel">
          <Text className="section-kicker">Resources</Text>
          <ExternalLinkButtons paper={paper} />
        </div>

        <div className="facts-grid hero-facts-grid">
          <StatTile label="数据集" value={paper.evaluation.datasets.length || "暂无"} />
          <StatTile label="对比基线" value={paper.evaluation.baselines.length || "暂无"} />
          <StatTile label="Claims" value={paper.claims.length || "暂无"} />
        </div>
      </aside>
    </section>
  );
}

function ResearchSection({ paper }: { paper: PaperCanonicalRecord }) {
  const summary = paper.research_problem.summary || paper.story.problem || "暂无研究问题摘要。";

  return (
    <PaperSection title="研究问题" kicker="story / problem" summary={summary}>
      <div className="paper-two-column">
        <HighlightPanel kicker="问题与目标" title="研究动机" copy={summary} className="highlight-panel-warm">
          {paper.research_problem.goal ? (
            <div className="focus-note-card goal-note-card">
              <Text className="focus-note-label">研究目标</Text>
              <Paragraph className="focus-note-copy">{paper.research_problem.goal}</Paragraph>
            </div>
          ) : null}
        </HighlightPanel>

        <ContentGroup title="研究缺口">
          <TextList items={paper.research_problem.gaps} emptyText="暂无结构化研究缺口。" />
        </ContentGroup>
      </div>

      <ContentGroup title="核心贡献" className="content-group-muted">
        <TextList items={paper.core_contributions} emptyText="暂无核心贡献整理。" ordered />
      </ContentGroup>
    </PaperSection>
  );
}

function MethodSection({ paper }: { paper: PaperCanonicalRecord }) {
  return (
    <PaperSection title="方法设计" kicker="canonical method" summary={paper.method.summary || paper.story.method || "暂无方法概述。"}>
      <HighlightPanel kicker="方案摘要" title="核心思路" copy={paper.method.summary || paper.story.method || "暂无方法摘要。"} />

      <div className="paper-two-column">
        <ContentGroup title="方法流程">
          <TextList items={paper.method.pipeline_steps} emptyText="暂无明确流程拆解。" ordered className="step-list" />
        </ContentGroup>

        <ContentGroup title="主要创新" className="content-group-muted">
          <TextList items={paper.method.innovations} emptyText="暂无结构化创新点。" />
        </ContentGroup>
      </div>

      <div className="facts-grid">
        <ContentGroup title="关键组件" className="fact-group">
          <BadgeGroup values={paper.method.ingredients} />
        </ContentGroup>
        <ContentGroup title="输入" className="fact-group">
          <BadgeGroup values={paper.method.inputs} />
        </ContentGroup>
        <ContentGroup title="输出" className="fact-group">
          <BadgeGroup values={paper.method.outputs} />
        </ContentGroup>
        <ContentGroup title="表示形式" className="fact-group">
          <BadgeGroup values={paper.method.representations} />
        </ContentGroup>
      </div>
    </PaperSection>
  );
}

function EvaluationSection({ paper }: { paper: PaperCanonicalRecord }) {
  return (
    <PaperSection title="实验结果" kicker="evaluation" summary={paper.evaluation.headline || paper.story.result || "暂无实验结论。"}>
      <HighlightPanel kicker="结论先看" title="Headline" copy={paper.evaluation.headline || paper.story.result || "暂无前置结果判断。"} />

      {paper.evaluation.setup_summary ? (
        <ContentGroup title="实验设置摘要">
          <Paragraph className="long-copy">{paper.evaluation.setup_summary}</Paragraph>
        </ContentGroup>
      ) : null}

      <div className="facts-grid">
        <ContentGroup title="数据集" className="fact-group">
          <BadgeGroup values={paper.evaluation.datasets} />
        </ContentGroup>
        <ContentGroup title="指标" className="fact-group">
          <BadgeGroup values={paper.evaluation.metrics} />
        </ContentGroup>
        <ContentGroup title="对比方法" className="fact-group">
          <BadgeGroup values={paper.evaluation.baselines} />
        </ContentGroup>
      </div>

      <ContentGroup title="主要发现" className="content-group-muted">
        <TextList items={paper.evaluation.key_findings} emptyText="暂无结构化主要发现。" />
      </ContentGroup>
    </PaperSection>
  );
}

function EditorialSection({ paper }: { paper: PaperCanonicalRecord }) {
  const highlights = [...paper.editorial.why_read, ...paper.editorial.strengths];
  const cautions = paper.editorial.cautions.length ? paper.editorial.cautions : paper.conclusion.limitations;

  return (
    <PaperSection title="阅读判断" kicker="editorial" summary={paper.editorial.research_position || paper.editorial.summary || "帮助判断值不值得继续读。"}>
      <div className="paper-two-column editorial-top-grid">
        <div className="content-stack">
          <HighlightPanel
            kicker="总评"
            title={paper.editorial.verdict || "暂无明确总评"}
            copy={paper.editorial.summary || paper.editorial.research_position || "暂无编辑判断摘要。"}
            className="highlight-panel-cool"
          />
        </div>

        <div className="content-stack">
          <ContentGroup title="为什么读 / Strengths">
            <TextList items={highlights} emptyText="暂无明确亮点。" />
          </ContentGroup>
          <ContentGroup title="需注意" className="content-group-muted">
            <TextList items={cautions} emptyText="暂无明确风险提示。" />
          </ContentGroup>
        </div>
      </div>

      <div className="paper-two-column">
        <ContentGroup title="研究定位">
          <Paragraph className="long-copy">{paper.editorial.research_position || "暂无定位描述。"}</Paragraph>
        </ContentGroup>
        <ContentGroup title="下一篇建议" className="content-group-muted">
          <BadgeGroup values={paper.editorial.next_read} color="processing" />
        </ContentGroup>
      </div>
    </PaperSection>
  );
}

function ComparisonSection({ paper, neighbors }: { paper: PaperCanonicalRecord; neighbors: PaperDetailViewModel["neighbors"] }) {
  return (
    <PaperSection title="对比线索" kicker="comparison" summary={paper.comparison.next_read[0] || "拿谁来比，为什么值得比。"}>
      <div className="facts-grid comparison-facts-grid">
        <ContentGroup title="显式基线" className="fact-group">
          <BadgeGroup values={paper.evaluation.baselines} />
        </ContentGroup>
        <ContentGroup title="下一篇建议" className="fact-group">
          <BadgeGroup values={paper.comparison.next_read} color="processing" />
        </ContentGroup>
      </div>

      <ContentGroup title="对比维度">
        {paper.comparison.aspects.length ? (
          <dl className="info-list">
            {paper.comparison.aspects.map((item) => (
              <div key={`${item.aspect}-${item.difference}`} className="info-list-row">
                <dt>{displayComparisonAspect(item.aspect)}</dt>
                <dd>{cleanDisplayText(item.difference, 96)}</dd>
              </div>
            ))}
          </dl>
        ) : (
          <Paragraph type="secondary" className="group-empty">
            暂无结构化对比维度。
          </Paragraph>
        )}
      </ContentGroup>

      <div className="content-group tabs-group">
        <Tabs
          items={[
            { key: "task", label: "任务近邻", children: <NeighborList items={neighbors.task} /> },
            { key: "method", label: "方法近邻", children: <NeighborList items={neighbors.method} /> },
            { key: "comparison", label: "对比近邻", children: <NeighborList items={neighbors.comparison} /> },
          ]}
        />
      </div>
    </PaperSection>
  );
}

function ClaimsPanel({ paper }: { paper: PaperCanonicalRecord }) {
  if (!paper.claims.length) {
    return <EmptyBlock description="暂无结构化 claims。" />;
  }

  return (
    <div className="info-stack">
      {paper.claims.map((claim, index) => (
        <div key={`${paper.id}-claim-${index}`} className="info-item claim-item">
          <Flex justify="space-between" align="start" gap={12} wrap="wrap">
            <Paragraph className="claim-text">{claim.text}</Paragraph>
            <Tag className="chip-tag chip-tag-route-overview">{displayClaimType(claim.type)}</Tag>
          </Flex>
          <Flex wrap="wrap" gap={8}>
            {claim.support.map((item) => (
              <Tag key={`${paper.id}-${index}-${item}`} className="chip-tag chip-tag-tone-blue">
                {item}
              </Tag>
            ))}
            {claim.confidence ? <Tag className={chipToneClass(confidenceTone(claim.confidence))}>可信度 {claim.confidence}</Tag> : null}
          </Flex>
        </div>
      ))}
    </div>
  );
}

function FigureTablePanel({
  paper,
  activeKey,
  setActiveKey,
}: {
  paper: PaperCanonicalRecord;
  activeKey: "figures" | "tables";
  setActiveKey: (key: "figures" | "tables") => void;
}) {
  const [query, setQuery] = useState("");
  const figureItems = useMemo(() => filterFigureTableItems(paper.assets.figures, query), [paper.assets.figures, query]);
  const tableItems = useMemo(() => filterFigureTableItems(paper.assets.tables, query), [paper.assets.tables, query]);

  const renderItem = (item: FigureTableIndexItem) => (
    <div key={item.label} className="info-item figure-item-card">
      <Flex justify="space-between" align="start" gap={12} wrap="wrap">
        <Text strong>{item.label}</Text>
        <Flex wrap="wrap" gap={8}>
          <Tag className={importanceTagClass(item.importance)}>{item.importance}</Tag>
          <Tag className="chip-tag chip-tag-tone-cyan">{displayFigureRole(item.role)}</Tag>
        </Flex>
      </Flex>
      <Paragraph className="long-copy figure-caption">{item.caption}</Paragraph>
    </div>
  );

  if (!paper.assets.figures.length && !paper.assets.tables.length) {
    return <EmptyBlock description="暂无图表索引。" />;
  }

  return (
    <div className="materials-pane">
      <Input allowClear placeholder="搜索图表编号或说明" value={query} onChange={(event) => setQuery(event.target.value)} className="compact-search" />
      <Tabs
        activeKey={activeKey}
        onChange={(value) => setActiveKey(value as "figures" | "tables")}
        items={[
          {
            key: "figures",
            label: `图 (${figureItems.length})`,
            children: figureItems.length ? <div className="info-stack">{figureItems.map(renderItem)}</div> : <EmptyBlock description="没有命中图条目。" />,
          },
          {
            key: "tables",
            label: `表 (${tableItems.length})`,
            children: tableItems.length ? <div className="info-stack">{tableItems.map(renderItem)}</div> : <EmptyBlock description="没有命中表条目。" />,
          },
        ]}
      />
    </div>
  );
}

function NeighborList({ items }: { items: NeighborItem[] }) {
  if (!items.length) {
    return <EmptyBlock description="当前没有足够可靠的近邻。" />;
  }

  return (
    <div className="info-stack">
      {items.map((item) => (
        <div key={`${item.paper_id}-${item.match_source}`} className="neighbor-card">
          <Flex justify="space-between" align="start" gap={12} wrap="wrap">
            <div style={{ minWidth: 0, flex: 1 }}>
              <Link to={paperRoute(item.route_path, item.paper_id)} className="paper-link small">
                {item.title}
              </Link>
              <TooltipText text={item.reason_short || item.reason} as="paragraph" maxChars={50} className="neighbor-reason-short" />
              <Paragraph type="secondary" className="neighbor-reason-long">
                {item.reason}
              </Paragraph>
            </div>
            <Tag className={scoreLevelTagClass(item.score_level)}>{scoreLevelLabel(item.score_level)}</Tag>
          </Flex>
          <Flex wrap="wrap" gap={8} style={{ marginTop: 12 }}>
            {sharedSignalPreview(item.shared_signals).map((signal) => (
              <TooltipTag key={`${item.paper_id}-${signal}`} label={signal} maxChars={24} className="chip-tag chip-tag-tone-blue" />
            ))}
          </Flex>
        </div>
      ))}
    </div>
  );
}

function MaterialsSection({
  detail,
  debugMode,
  activeFigureTab,
  setActiveFigureTab,
}: {
  detail: PaperDetailViewModel;
  debugMode: boolean;
  activeFigureTab: "figures" | "tables";
  setActiveFigureTab: (key: "figures" | "tables") => void;
}) {
  const { message } = AntApp.useApp();
  const paper = detail.canonical;

  const handleCopy = async () => {
    try {
      await copyText(JSON.stringify(detail, null, 2));
      message.success("已复制结构化 JSON。");
    } catch {
      message.error("复制失败。");
    }
  };

  const items = [
    {
      key: "claims",
      label: "Claims",
      children: <ClaimsPanel paper={paper} />,
    },
    {
      key: "figures",
      label: "图表索引",
      children: <FigureTablePanel paper={paper} activeKey={activeFigureTab} setActiveKey={setActiveFigureTab} />,
    },
    {
      key: "abstracts",
      label: "摘要",
      children: (
        <Tabs
          defaultActiveKey={paper.abstracts.zh ? "zh" : "raw"}
          items={[
            {
              key: "zh",
              label: "中文摘要",
              children: paper.abstracts.zh ? <Paragraph className="long-copy">{paper.abstracts.zh}</Paragraph> : <EmptyBlock description="暂无中文摘要。" />,
            },
            {
              key: "raw",
              label: "原始摘要",
              children: paper.abstracts.raw ? <Paragraph className="long-copy">{paper.abstracts.raw}</Paragraph> : <EmptyBlock description="暂无原始摘要。" />,
            },
          ]}
        />
      ),
    },
    {
      key: "relations",
      label: "Relations",
      children: paper.relations.length ? (
        <div className="info-stack">
          {paper.relations.map((item) => (
            <div key={`${item.type}-${item.target_paper_id}`} className="info-item relation-item">
              <Text strong>{item.type}</Text>
              <Paragraph className="relation-title">{item.label || item.target_paper_id}</Paragraph>
              {item.description ? <Paragraph type="secondary" className="relation-description">{item.description}</Paragraph> : null}
            </div>
          ))}
        </div>
      ) : (
        <EmptyBlock description="暂无结构化 relations。" />
      ),
    },
  ];

  if (debugMode) {
    items.push({
      key: "debug",
      label: "JSON / 调试",
      children: (
        <div className="info-stack">
          <Button icon={<CopyOutlined />} onClick={handleCopy}>
            复制 JSON
          </Button>
          <pre className="debug-json-block">{JSON.stringify(detail, null, 2)}</pre>
        </div>
      ),
    });
  }

  return (
    <PaperSection title="附录资料" kicker="materials" summary="Claims、图表、摘要和 relations 收在后半段，避免正文信息流反复跳转。">
      <div className="content-group materials-group">
        <Collapse defaultActiveKey={[]} items={items} />
      </div>
    </PaperSection>
  );
}

function SidebarSnapshotCard({ paper }: { paper: PaperCanonicalRecord }) {
  return (
    <div className="sidebar-panel">
      <Text className="section-kicker">Paper Info</Text>
      <Title level={4} className="sidebar-title">
        Canonical Snapshot
      </Title>
      <MetaLine label="来源 / 年份" value={`${paper.bibliography.venue || "未知"} / ${formatYear(paper.bibliography.year)}`} />
      <MetaLine label="引用数" value={paper.bibliography.citation_count ?? "暂无"} />
      <MetaLine label="阅读判断" value={paper.editorial.verdict || "暂无"} />
      <MetaLine label="推荐路径" value={recommendedRouteLabel(paper.editorial.reading_route)} />
    </div>
  );
}

function SidebarQuickFactsCard({ paper }: { paper: PaperCanonicalRecord }) {
  return (
    <div className="sidebar-panel sidebar-panel-muted">
      <Text className="section-kicker">Quick Facts</Text>
      <MetaLine label="任务" value={<BadgeGroup values={paper.taxonomy.tasks} color="gold" />} />
      <MetaLine label="方法" value={<BadgeGroup values={paper.taxonomy.methods} color="green" />} />
      <MetaLine label="创新类型" value={<BadgeGroup values={paper.taxonomy.novelty_types} color="magenta" />} />
      <MetaLine label="模态" value={<BadgeGroup values={paper.taxonomy.modalities} color="processing" />} />
    </div>
  );
}

function SidebarActionsPanel({ paper, payload }: { paper: PaperCanonicalRecord; payload: SiteIndexPayload }) {
  const navigate = useNavigate();
  const links = firstExternalLinks(paper.bibliography);
  const markdownLink = markdownHref(paper.source.paper_path);

  return (
    <div className="sidebar-panel sidebar-panel-actions">
      <Text className="section-kicker">Actions</Text>
      <div className="sidebar-actions-block">
        <Text className="meta-label">外部资源</Text>
        <Flex wrap="wrap" gap={8}>
          {links.map((item) => (
            <Button key={item.key} size="small" href={item.href} target="_blank">
              {item.label}
            </Button>
          ))}
          {markdownLink ? (
            <Button size="small" href={markdownLink} target="_blank" icon={<BookOutlined />}>
              Markdown
            </Button>
          ) : null}
          {!links.length && !markdownLink ? <Text type="secondary">暂无外部资源</Text> : null}
        </Flex>
      </div>

      <div className="sidebar-actions-block">
        <Text className="meta-label">站内导航</Text>
        <div className="sidebar-action-stack">
          <Button block icon={<ArrowLeftOutlined />} onClick={() => navigate("/")}>
            返回首页
          </Button>
          <Button block icon={<LinkOutlined />} onClick={() => navigate(paperRoute(payload.navigation.home_route, paper.id))}>
            回到站点入口
          </Button>
        </div>
      </div>
    </div>
  );
}

export function PaperDetailPage({ payload, debugMode }: { payload: SiteIndexPayload; debugMode: boolean }) {
  const navigate = useNavigate();
  const params = useParams();
  const paperId = params.paperId ?? "";
  const [detail, setDetail] = useState<PaperDetailViewModel | null>(null);
  const [loadError, setLoadError] = useState("");
  const [activeFigureTab, setActiveFigureTab] = useState<"figures" | "tables">("figures");

  useEffect(() => {
    let cancelled = false;
    setDetail(null);
    setLoadError("");
    setActiveFigureTab("figures");

    if (!paperId) {
      setLoadError("缺少论文 ID。");
      return;
    }

    loadPaperDetail(paperId)
      .then((result) => {
        if (!cancelled) {
          setDetail(result);
        }
      })
      .catch((reason: unknown) => {
        if (!cancelled) {
          setLoadError(reason instanceof Error ? reason.message : "加载论文详情失败。");
        }
      });

    return () => {
      cancelled = true;
    };
  }, [paperId]);

  if (!paperId) {
    return (
      <div className="detail-state-panel">
        <Title level={4}>缺少论文 ID</Title>
        <Button onClick={() => navigate("/")}>返回首页</Button>
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="detail-state-panel">
        <Title level={4}>加载失败</Title>
        <Paragraph>{loadError}</Paragraph>
        <Button onClick={() => navigate("/")}>返回首页</Button>
      </div>
    );
  }

  if (!detail) {
    return (
      <div className="detail-state-panel">
        <Paragraph>正在加载论文详情…</Paragraph>
      </div>
    );
  }

  const paper = detail.canonical;

  return (
    <div className="page-stack detail-page-stack">
      <DecisionHero paper={paper} />

      <div className="detail-layout">
        <div className="detail-main">
          <ResearchSection paper={paper} />
          <MethodSection paper={paper} />
          <EvaluationSection paper={paper} />
          <EditorialSection paper={paper} />
          <ComparisonSection paper={paper} neighbors={detail.neighbors} />
          <MaterialsSection detail={detail} debugMode={debugMode} activeFigureTab={activeFigureTab} setActiveFigureTab={setActiveFigureTab} />
        </div>

        <aside className="detail-sidebar sticky-column">
          <SidebarSnapshotCard paper={paper} />
          <SidebarQuickFactsCard paper={paper} />
          <SidebarActionsPanel paper={paper} payload={payload} />
        </aside>
      </div>
    </div>
  );
}
