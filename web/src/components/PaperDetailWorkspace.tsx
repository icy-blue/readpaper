import { Alert, Button, Empty, Flex, Spin, Tabs, Tag, Typography } from "antd";
import { BookOutlined, LinkOutlined } from "@ant-design/icons";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import {
  chipToneClass,
  cleanDisplayText,
  confidenceTone,
  displayClaimType,
  displayComparisonAspect,
  displayRelationType,
  displayValueLabel,
  firstExternalLinks,
  formatYear,
  loadPaperDetailCached,
  paperRoute,
  relationConfidenceLabel,
  relationTargetLabel,
  scoreLevelLabel,
  scoreLevelTagClass,
  semanticScholarSearchUrl,
  sharedSignalPreview,
  translateConversationHref,
} from "../lib/paper";
import { OverflowCount, TooltipTag, TooltipText } from "./OverflowTooltip";
import type { NeighborItem, PaperCanonicalRecord, PaperDetailViewModel, RelationItem, SiteIndexPayload } from "../types";

const { Title, Paragraph, Text } = Typography;
type WorkspaceLayoutMode = "default" | "home-compact";
type SurfaceVariant = "card" | "plain";

const RESOURCE_LABELS: Record<string, string> = {
  pdf: "查看 PDF",
  arxiv: "查看 arXiv",
  doi: "查看 DOI",
  code: "查看 Code",
  project: "查看 Project",
  data: "查看 Data",
  translate: "查看翻译",
};
const RESOURCE_ORDER = ["pdf", "arxiv", "doi", "code", "project", "data"] as const;

function EmptyState({ description }: { description: string }) {
  return <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={description} />;
}

function SectionCard({
  title,
  kicker,
  children,
  muted = false,
  variant = "card",
}: {
  title: string;
  kicker?: string;
  children: ReactNode;
  muted?: boolean;
  variant?: SurfaceVariant;
}) {
  const displayKicker = variant === "card" ? kicker : undefined;

  return (
    <section className={`workspace-section-card${muted ? " is-muted" : ""}${variant === "plain" ? " is-plain" : ""}`}>
      {displayKicker ? <Text className="section-kicker">{displayKicker}</Text> : null}
      <Text className="workspace-section-title">{title}</Text>
      <div className="workspace-section-body">{children}</div>
    </section>
  );
}

function KeyValueGrid({ items }: { items: Array<{ label: string; value: ReactNode }> }) {
  return (
    <dl className="workspace-key-value-grid">
      {items.map((item) => (
        <div key={item.label} className="workspace-key-value-item">
          <dt>{item.label}</dt>
          <dd>{item.value}</dd>
        </div>
      ))}
    </dl>
  );
}

function TextList({ items, emptyText, ordered = false }: { items: string[]; emptyText: string; ordered?: boolean }) {
  if (!items.length) {
    return <Paragraph className="workspace-empty-copy">{emptyText}</Paragraph>;
  }
  const ListTag = ordered ? "ol" : "ul";
  return (
    <ListTag className={`workspace-list${ordered ? " is-ordered" : ""}`}>
      {items.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ListTag>
  );
}

function metadataTagLabel(value: string): string {
  return cleanDisplayText(value) ?? value;
}

function claimSourceLabel(value: string): string {
  const content = cleanDisplayText(value) ?? value;
  if (content.toLowerCase().startsWith("section:")) {
    return `来源：${content.slice("section:".length)}`;
  }
  return `来源：${content}`;
}

function claimConfidenceLabel(value: string | null | undefined): string | null {
  if (!value) {
    return null;
  }
  if (value === "high") {
    return "可信度高";
  }
  if (value === "medium") {
    return "可信度中";
  }
  if (value === "low") {
    return "可信度低";
  }
  return `可信度 ${value}`;
}

function BadgeGroup({
  values,
  tone,
  getLabel = displayValueLabel,
}: {
  values: string[];
  tone?: string | null;
  getLabel?: (value: string) => string;
}) {
  if (!values.length) {
    return <Text type="secondary">暂无</Text>;
  }
  return (
    <Flex wrap="wrap" gap={8}>
      {values.map((value) => (
        <TooltipTag key={value} label={getLabel(value)} className={chipToneClass(tone)} maxChars={24} />
      ))}
    </Flex>
  );
}

function orderedResourceLinks(paper: PaperCanonicalRecord): Array<{ key: string; label: string; href: string }> {
  const orderMap = new Map<string, number>(RESOURCE_ORDER.map((key, index) => [key, index]));
  return [...firstExternalLinks(paper.bibliography)]
    .sort((left, right) => (orderMap.get(left.key) ?? 99) - (orderMap.get(right.key) ?? 99))
    .map((item) => ({ ...item, label: RESOURCE_LABELS[item.key] || `查看 ${item.label}` }));
}

function CompactMetaLine({ paper }: { paper: PaperCanonicalRecord }) {
  const authors = paper.bibliography.authors.filter((author) => author.trim());
  const visibleAuthors = authors.slice(0, 5);
  const hiddenAuthors = authors.slice(5);
  const authorLabel = visibleAuthors.length ? visibleAuthors.join(" / ") : "作者信息暂缺";
  const venueLabel = paper.bibliography.venue || "未知 venue";

  return (
    <div className="workspace-meta-line workspace-meta-line-compact">
      <span className="workspace-meta-group workspace-meta-authors" title={authorLabel}>
        <Text className="workspace-meta-primary-text">{authorLabel}</Text>
        <OverflowCount items={hiddenAuthors} className="workspace-meta-overflow-count" />
      </span>
      <span className="workspace-meta-separator">·</span>
      <span className="workspace-meta-group workspace-meta-venue" title={venueLabel}>
        <Text className="workspace-meta-venue-text">{venueLabel}</Text>
      </span>
      <span className="workspace-meta-separator">·</span>
      <span className="workspace-meta-year">{formatYear(paper.bibliography.year)}</span>
    </div>
  );
}

function OverviewLeadPanel({ paper }: { paper: PaperCanonicalRecord }) {
  return (
    <section className="workspace-research-position">
      <Text className="workspace-section-title">研究入口</Text>
      <Paragraph className="workspace-lead">{paper.story.paper_one_liner || "暂无一句话入口。"}</Paragraph>
      {paper.editorial.research_position ? <Paragraph className="workspace-support-copy">{paper.editorial.research_position}</Paragraph> : null}
    </section>
  );
}

function ClaimList({ paper, variant = "card" }: { paper: PaperCanonicalRecord; variant?: SurfaceVariant }) {
  if (!paper.claims.length) {
    return <EmptyState description="暂无结构化论断。" />;
  }
  return (
    <div className={`workspace-claim-list${variant === "plain" ? " is-plain" : ""}`}>
      {paper.claims.map((claim, index) => (
        <div key={`${paper.id}-claim-${index}`} className={`workspace-claim-entry${variant === "plain" ? " is-plain" : ""}`}>
          <Flex wrap="wrap" gap={8} className="workspace-claim-chip-row">
            <Tag className="chip-tag chip-tag-route-overview">{displayClaimType(claim.type)}</Tag>
            {claim.confidence ? (
              <Tag className={chipToneClass(confidenceTone(claim.confidence))}>{claimConfidenceLabel(claim.confidence)}</Tag>
            ) : null}
            {claim.support.map((item) => (
              <Tag key={`${paper.id}-${index}-${item}`} className="chip-tag chip-tag-tone-blue">
                {claimSourceLabel(item)}
              </Tag>
            ))}
          </Flex>

          <Paragraph className="workspace-body-copy workspace-claim-text">{claim.text}</Paragraph>

          {index < paper.claims.length - 1 ? <div className="workspace-claim-divider" aria-hidden="true" /> : null}
        </div>
      ))}
    </div>
  );
}

function RelationsList({ items, variant = "card" }: { items: RelationItem[]; variant?: SurfaceVariant }) {
  if (!items.length) {
    return <EmptyState description="暂无结构化关联关系。" />;
  }
  return (
    <div className="workspace-stack">
      {items.map((item) => {
        const externalHref = item.target_kind === "external" ? semanticScholarSearchUrl(item.label) : null;
        const targetLabel = relationTargetLabel(item);
        return (
          <div
            key={`${item.type}-${item.target_paper_id || item.label || "relation"}`}
            className={`workspace-note-card${variant === "plain" ? " is-plain" : ""}`}
          >
            <Flex justify="space-between" align="start" gap={12} wrap="wrap">
              <Text strong>{displayRelationType(item.type)}</Text>
              <Flex wrap="wrap" gap={8}>
                <Tag className="chip-tag chip-tag-tone-blue">{item.target_kind === "external" ? "外部论文" : "本地论文"}</Tag>
                {relationConfidenceLabel(item.confidence) ? (
                  <Tag className="chip-tag chip-tag-tone-green">{relationConfidenceLabel(item.confidence)}</Tag>
                ) : null}
              </Flex>
            </Flex>
            {externalHref ? (
              <a href={externalHref} target="_blank" rel="noreferrer" className="paper-link small workspace-inline-link">
                {targetLabel}
              </a>
            ) : item.target_paper_id ? (
              <Link to={paperRoute(undefined, item.target_paper_id)} className="paper-link small workspace-inline-link">
                {targetLabel}
              </Link>
            ) : (
              <Paragraph className="workspace-body-copy">{targetLabel}</Paragraph>
            )}
            {item.description ? <Paragraph className="workspace-support-copy">{item.description}</Paragraph> : null}
          </div>
        );
      })}
    </div>
  );
}

function NeighborList({ items, variant = "card" }: { items: NeighborItem[]; variant?: SurfaceVariant }) {
  if (!items.length) {
    return <EmptyState description="当前没有足够可靠的近邻。" />;
  }
  return (
    <div className="workspace-stack">
      {items.map((item) => (
        <div
          key={`${item.paper_id}-${item.match_source}`}
          className={`workspace-note-card workspace-neighbor-card${variant === "plain" ? " is-plain" : ""}`}
        >
          <div className="workspace-neighbor-header">
            <div className="workspace-note-main workspace-neighbor-main">
              <Link to={paperRoute(item.route_path, item.paper_id)} className="paper-link small">
                {item.title}
              </Link>
              <TooltipText text={item.reason_short || item.reason} as="paragraph" rows={2} className="workspace-body-copy" />
              <Paragraph className="workspace-support-copy">{item.reason}</Paragraph>
            </div>
            <Tag className={`workspace-neighbor-score ${scoreLevelTagClass(item.score_level)}`}>{scoreLevelLabel(item.score_level)}</Tag>
          </div>
          <Flex wrap="wrap" gap={8}>
            {sharedSignalPreview(item.shared_signals).map((signal) => (
              <TooltipTag key={`${item.paper_id}-${signal}`} label={signal} maxChars={24} className="chip-tag chip-tag-tone-blue" />
            ))}
          </Flex>
        </div>
      ))}
    </div>
  );
}

function OverviewTab({ paper, variant = "card" }: { paper: PaperCanonicalRecord; variant?: SurfaceVariant }) {
  const taxonomyRows = [
    { label: "主题", value: <BadgeGroup values={paper.taxonomy.themes} getLabel={metadataTagLabel} /> },
    { label: "任务", value: <BadgeGroup values={paper.taxonomy.tasks} tone="gold" getLabel={metadataTagLabel} /> },
    { label: "方法", value: <BadgeGroup values={paper.taxonomy.methods} tone="green" getLabel={metadataTagLabel} /> },
    { label: "模态", value: <BadgeGroup values={paper.taxonomy.modalities} tone="processing" getLabel={metadataTagLabel} /> },
    { label: "创新类型", value: <BadgeGroup values={paper.taxonomy.novelty_types} tone="magenta" getLabel={metadataTagLabel} /> },
  ];

  return (
    <div className={`workspace-tab-stack${variant === "plain" ? " is-plain" : ""}`}>
      <SectionCard title="论文入口" kicker="Overview" variant={variant}>
        <Paragraph className="workspace-body-copy">{paper.story.paper_one_liner || "暂无一句话入口。"}</Paragraph>
        {paper.editorial.research_position ? <Paragraph className="workspace-support-copy">{paper.editorial.research_position}</Paragraph> : null}
      </SectionCard>
      <SectionCard title="研究问题" muted variant={variant}>
        <Paragraph className="workspace-body-copy">{paper.research_problem.summary || "暂无研究问题摘要。"}</Paragraph>
        {paper.research_problem.goal ? <Paragraph className="workspace-support-copy">目标：{paper.research_problem.goal}</Paragraph> : null}
        <TextList items={paper.research_problem.gaps} emptyText="暂无结构化研究缺口。" />
      </SectionCard>
      <SectionCard title="核心贡献" variant={variant}>
        <TextList items={paper.core_contributions} emptyText="暂无核心贡献整理。" ordered />
      </SectionCard>
      <SectionCard title="风险与限制" muted variant={variant}>
        <TextList items={paper.research_risks} emptyText="暂无明确风险提示。" />
      </SectionCard>
      <SectionCard title="阅读标签" variant={variant}>
        <KeyValueGrid items={taxonomyRows} />
      </SectionCard>
    </div>
  );
}

function MethodTab({ paper, variant = "card" }: { paper: PaperCanonicalRecord; variant?: SurfaceVariant }) {
  return (
    <div className={`workspace-tab-stack${variant === "plain" ? " is-plain" : ""}`}>
      <SectionCard title="方法摘要" kicker="Method" variant={variant}>
        <Paragraph className="workspace-body-copy">{paper.method.summary || "暂无方法概述。"}</Paragraph>
      </SectionCard>
      <SectionCard title="方法流程" variant={variant}>
        <TextList items={paper.method.pipeline_steps} emptyText="暂无明确流程拆解。" ordered />
      </SectionCard>
      <SectionCard title="关键创新" muted variant={variant}>
        <TextList items={paper.method.innovations} emptyText="暂无结构化创新点。" />
      </SectionCard>
      <SectionCard title="组件与表示" variant={variant}>
        <KeyValueGrid
          items={[
            { label: "组件", value: <BadgeGroup values={paper.method.ingredients} tone="gold" /> },
            { label: "输入", value: <BadgeGroup values={paper.method.inputs} tone="processing" /> },
            { label: "输出", value: <BadgeGroup values={paper.method.outputs} tone="green" /> },
            { label: "表示", value: <BadgeGroup values={paper.method.representations} tone="magenta" /> },
          ]}
        />
      </SectionCard>
      <SectionCard title="实验上下文" muted variant={variant}>
        <KeyValueGrid
          items={[
            { label: "数据集", value: <BadgeGroup values={paper.evaluation.datasets} tone="processing" /> },
            { label: "指标", value: <BadgeGroup values={paper.evaluation.metrics} tone="gold" /> },
            { label: "基线", value: <BadgeGroup values={paper.evaluation.baselines} tone="green" /> },
          ]}
        />
      </SectionCard>
      <SectionCard title="实验结论" variant={variant}>
        <Paragraph className="workspace-body-copy">{paper.evaluation.headline || "暂无实验结论。"}</Paragraph>
        {paper.evaluation.setup_summary ? <Paragraph className="workspace-support-copy">{paper.evaluation.setup_summary}</Paragraph> : null}
        <TextList items={paper.evaluation.key_findings} emptyText="暂无结构化主要发现。" />
      </SectionCard>
      <SectionCard title="证据论断" muted variant={variant}>
        <ClaimList paper={paper} variant={variant} />
      </SectionCard>
    </div>
  );
}

function GraphTab({
  detail,
  payload,
  variant = "card",
}: {
  detail: PaperDetailViewModel;
  payload: SiteIndexPayload;
  variant?: SurfaceVariant;
}) {
  const paper = detail.canonical;
  const discoveryRows = [
    { label: "问题线", value: <BadgeGroup values={paper.discovery_axes.problem} getLabel={metadataTagLabel} /> },
    { label: "方法谱系", value: <BadgeGroup values={paper.discovery_axes.method} tone="green" getLabel={metadataTagLabel} /> },
    { label: "实验对照", value: <BadgeGroup values={paper.discovery_axes.evaluation} tone="gold" getLabel={metadataTagLabel} /> },
    { label: "风险轴", value: <BadgeGroup values={paper.discovery_axes.risk} tone="magenta" getLabel={metadataTagLabel} /> },
  ];

  return (
    <div className={`workspace-tab-stack${variant === "plain" ? " is-plain" : ""}`}>
      <SectionCard title="关联轴" kicker="Graph" variant={variant}>
        <KeyValueGrid items={discoveryRows} />
      </SectionCard>
      <SectionCard title="相关论文近邻" muted variant={variant}>
        <Tabs
          items={payload.navigation.neighbor_tabs.map((tab) => ({
            key: tab.key,
            label: tab.label,
            children: <NeighborList items={detail.neighbors[tab.key]} variant={variant} />,
          }))}
        />
      </SectionCard>
      <SectionCard title="对比钩子" variant={variant}>
        <BadgeGroup values={paper.comparison.next_read} tone="processing" />
        {paper.comparison.aspects.length ? (
          <div className="workspace-stack">
            {paper.comparison.aspects.map((item) => (
              <div key={`${item.aspect}-${item.difference}`} className={`workspace-note-card${variant === "plain" ? " is-plain" : ""}`}>
                <Text strong>{displayComparisonAspect(item.aspect)}</Text>
                <Paragraph className="workspace-support-copy">{cleanDisplayText(item.difference, 160)}</Paragraph>
              </div>
            ))}
          </div>
        ) : null}
      </SectionCard>
      <SectionCard title="关联关系" muted variant={variant}>
        <RelationsList items={paper.relations} variant={variant} />
      </SectionCard>
    </div>
  );
}

export function PaperDetailWorkspace({
  paperId,
  payload,
  headerActions,
  debugMode = false,
  layoutMode = "default",
  className = "",
}: {
  paperId: string;
  payload: SiteIndexPayload;
  headerActions?: ReactNode;
  debugMode?: boolean;
  layoutMode?: WorkspaceLayoutMode;
  className?: string;
}) {
  const [detail, setDetail] = useState<PaperDetailViewModel | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    if (!paperId) {
      setDetail(null);
      setLoading(false);
      setError("");
      return;
    }

    setLoading(true);
    setError("");

    loadPaperDetailCached(paperId)
      .then((result) => {
        if (cancelled) {
          return;
        }
        setDetail(result);
        setLoading(false);
      })
      .catch((reason: unknown) => {
        if (cancelled) {
          return;
        }
        setError(reason instanceof Error ? reason.message : "加载论文详情失败。");
        setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [paperId]);

  const tabItems = useMemo(() => {
    if (!detail) {
      return [];
    }
    const variant: SurfaceVariant = layoutMode === "home-compact" ? "plain" : "card";
    const items = [
      { key: "overview", label: layoutMode === "home-compact" ? "概览" : "Overview", children: <OverviewTab paper={detail.canonical} variant={variant} /> },
      { key: "method", label: layoutMode === "home-compact" ? "方法" : "Method", children: <MethodTab paper={detail.canonical} variant={variant} /> },
      { key: "graph", label: layoutMode === "home-compact" ? "图谱" : "Graph", children: <GraphTab detail={detail} payload={payload} variant={variant} /> },
    ];
    if (debugMode) {
      items.push({
        key: "debug",
        label: "Debug",
        children: <pre className="debug-json-block">{JSON.stringify(detail, null, 2)}</pre>,
      });
    }
    return items;
  }, [debugMode, detail, layoutMode, payload]);

  if (!paperId) {
    return (
      <div className={`workspace-shell ${className}`.trim()}>
        <div className="workspace-empty-state">
          <EmptyState description="先从左侧选择一篇论文。" />
        </div>
      </div>
    );
  }

  if (loading && !detail) {
    return (
      <div className={`workspace-shell ${className}`.trim()}>
        <div className="workspace-loading-state">
          <Spin size="large" />
          <Text type="secondary">正在加载论文详情…</Text>
        </div>
      </div>
    );
  }

  if (error && !detail) {
    return (
      <div className={`workspace-shell ${className}`.trim()}>
        <Alert type="error" showIcon message="详情加载失败" description={<span style={{ whiteSpace: "pre-wrap" }}>{error}</span>} />
      </div>
    );
  }

  if (!detail) {
    return null;
  }

  const paper = detail.canonical;
  const translateLinkHref = translateConversationHref(paper.source.conversation_ids);
  const links = orderedResourceLinks(paper).slice(0, layoutMode === "home-compact" ? 2 : 4);
  const headlineTags = [...new Set([...paper.taxonomy.tasks, ...paper.taxonomy.methods, ...paper.taxonomy.themes])].slice(0, 4);

  return (
    <div className={`workspace-shell${layoutMode === "home-compact" ? " is-home-compact" : ""} ${className}`.trim()}>
      <div className="workspace-header">
        <div className="workspace-header-main">
          {layoutMode !== "home-compact" ? (
            <Flex wrap="wrap" gap={8}>
              <Tag className="chip-tag chip-tag-tone-blue">{paper.bibliography.venue || "未知来源"}</Tag>
              <Tag className="chip-tag chip-tag-tone-blue">{formatYear(paper.bibliography.year)}</Tag>
              {paper.bibliography.citation_count !== null ? (
                <Tag className="chip-tag chip-tag-citation">{`引用 ${paper.bibliography.citation_count}`}</Tag>
              ) : null}
              {paper.editorial.graph_worthy ? <Tag className="chip-tag chip-tag-worth">图谱锚点</Tag> : null}
            </Flex>
          ) : null}
          <div className="workspace-title-block">
            <Title level={2} className="workspace-title">
              {paper.bibliography.title}
            </Title>
            {layoutMode === "home-compact" ? <CompactMetaLine paper={paper} /> : (
              <Paragraph className="workspace-meta-line">
                {paper.bibliography.authors.length ? paper.bibliography.authors.join(" / ") : "作者信息暂缺"} · {paper.bibliography.venue || "未知 venue"} ·{" "}
                {formatYear(paper.bibliography.year)}
              </Paragraph>
            )}
          </div>
          <div className="workspace-header-actions">
            <Flex wrap="wrap" gap={10}>
              {headerActions}
              {translateLinkHref ? (
                <Button href={translateLinkHref} target="_blank" icon={<BookOutlined />}>
                  {RESOURCE_LABELS.translate}
                </Button>
              ) : null}
              {links.map((item) => (
                <Button key={item.key} href={item.href} target="_blank" icon={<LinkOutlined />}>
                  {item.label}
                </Button>
              ))}
            </Flex>
          </div>
          {headlineTags.length ? (
            <Flex wrap="wrap" gap={8} className="workspace-headline-tags">
              {headlineTags.map((tag) => (
                <TooltipTag key={`${paper.id}-${tag}`} label={displayValueLabel(tag)} maxChars={24} className="chip-tag chip-tag-route-overview" />
              ))}
            </Flex>
          ) : null}
        </div>
      </div>

      <OverviewLeadPanel paper={paper} />

      {error ? <Alert type="warning" showIcon message="已显示缓存内容，刷新详情时出现问题" description={error} /> : null}

      <Tabs items={tabItems} className="workspace-tabs" />
    </div>
  );
}
