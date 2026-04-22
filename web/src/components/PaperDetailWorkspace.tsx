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
  markdownHref,
  paperRoute,
  recommendedRouteLabel,
  relationConfidenceLabel,
  relationTargetLabel,
  scoreLevelLabel,
  scoreLevelTagClass,
  semanticScholarSearchUrl,
  sharedSignalPreview,
  translateConversationHref,
  verdictTagClass,
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
  markdown: "查看 Markdown",
  translate: "查看 Translate 对话",
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

function BadgeGroup({ values, tone }: { values: string[]; tone?: string | null }) {
  if (!values.length) {
    return <Text type="secondary">暂无</Text>;
  }
  return (
    <Flex wrap="wrap" gap={8}>
      {values.map((value) => (
        <TooltipTag key={value} label={displayValueLabel(value)} className={chipToneClass(tone)} maxChars={24} />
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

function QuickLookPanel({ paper }: { paper: PaperCanonicalRecord }) {
  const leadingSignal =
    paper.editorial.why_read[0] ||
    paper.editorial.summary ||
    paper.story.paper_one_liner ||
    "暂无明确读前判断。";
  return (
    <section className="workspace-quicklook-card">
      <div className="workspace-quicklook-head">
        <Text className="section-kicker">Quick Look</Text>
        <Text className="workspace-section-title">快速判断</Text>
      </div>
      <Paragraph className="workspace-quicklook-lead">{leadingSignal}</Paragraph>
      <KeyValueGrid
        items={[
          { label: "Verdict", value: paper.editorial.verdict || "暂无" },
          { label: "阅读路径", value: recommendedRouteLabel(paper.editorial.reading_route) },
          { label: "研究定位", value: paper.editorial.research_position || "暂无" },
        ]}
      />
    </section>
  );
}

function ResearchPositionPanel({ paper }: { paper: PaperCanonicalRecord }) {
  return (
    <section className="workspace-research-position">
      <Text className="workspace-section-title">研究定位</Text>
      <Paragraph className="workspace-lead">{paper.editorial.research_position || "暂无研究定位。"}</Paragraph>
    </section>
  );
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

function ClaimList({ paper, variant = "card" }: { paper: PaperCanonicalRecord; variant?: SurfaceVariant }) {
  if (!paper.claims.length) {
    return <EmptyState description="暂无结构化论断。" />;
  }
  return (
    <div className="workspace-stack">
      {paper.claims.map((claim, index) => (
        <div key={`${paper.id}-claim-${index}`} className={`workspace-note-card${variant === "plain" ? " is-plain" : ""}`}>
          <Flex justify="space-between" align="start" gap={12} wrap="wrap">
            <Paragraph className="workspace-body-copy claim-copy">{claim.text}</Paragraph>
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
              <Link to={paperRoute(`#/paper/${item.target_paper_id}`, item.target_paper_id)} className="paper-link small workspace-inline-link">
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
        <div key={`${item.paper_id}-${item.match_source}`} className={`workspace-note-card${variant === "plain" ? " is-plain" : ""}`}>
          <Flex justify="space-between" align="start" gap={12} wrap="wrap">
            <div className="workspace-note-main">
              <Link to={paperRoute(item.route_path, item.paper_id)} className="paper-link small">
                {item.title}
              </Link>
              <TooltipText text={item.reason_short || item.reason} as="paragraph" rows={2} className="workspace-body-copy" />
              <Paragraph className="workspace-support-copy">{item.reason}</Paragraph>
            </div>
            <Tag className={scoreLevelTagClass(item.score_level)}>{scoreLevelLabel(item.score_level)}</Tag>
          </Flex>
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

function SummaryTab({ paper, variant = "card" }: { paper: PaperCanonicalRecord; variant?: SurfaceVariant }) {
  const summaryItems = [paper.story.paper_one_liner, paper.editorial.summary, paper.evaluation.headline].filter(Boolean) as string[];
  const highlights = [...paper.editorial.why_read, ...paper.editorial.strengths];
  const cautions = paper.editorial.cautions.length ? paper.editorial.cautions : paper.conclusion.limitations;

  return (
    <div className={`workspace-tab-stack${variant === "plain" ? " is-plain" : ""}`}>
      <SectionCard title="读前摘要" kicker="Summary" variant={variant}>
        {summaryItems.length ? (
          summaryItems.map((item) => (
            <Paragraph key={item} className="workspace-body-copy">
              {item}
            </Paragraph>
          ))
        ) : (
          <Paragraph className="workspace-empty-copy">暂无结构化摘要。</Paragraph>
        )}
      </SectionCard>
      <SectionCard title="研究问题" muted variant={variant}>
        <Paragraph className="workspace-body-copy">{paper.research_problem.summary || paper.story.problem || "暂无研究问题摘要。"}</Paragraph>
        {paper.research_problem.goal ? <Paragraph className="workspace-support-copy">目标：{paper.research_problem.goal}</Paragraph> : null}
        <TextList items={paper.research_problem.gaps} emptyText="暂无结构化研究缺口。" />
      </SectionCard>
      <SectionCard title="核心贡献" variant={variant}>
        <TextList items={paper.core_contributions} emptyText="暂无核心贡献整理。" ordered />
      </SectionCard>
      <SectionCard title="为什么值得读" variant={variant}>
        <TextList items={highlights} emptyText="暂无明确亮点。" />
      </SectionCard>
      <SectionCard title="风险与限制" muted variant={variant}>
        <TextList items={cautions} emptyText="暂无明确风险提示。" />
      </SectionCard>
    </div>
  );
}

function MethodTab({ paper, variant = "card" }: { paper: PaperCanonicalRecord; variant?: SurfaceVariant }) {
  return (
    <div className={`workspace-tab-stack${variant === "plain" ? " is-plain" : ""}`}>
      <SectionCard title="方法摘要" kicker="Method" variant={variant}>
        <Paragraph className="workspace-body-copy">{paper.method.summary || paper.story.method || "暂无方法概述。"}</Paragraph>
      </SectionCard>
      <SectionCard title="实验结论" muted variant={variant}>
        <Paragraph className="workspace-body-copy">{paper.evaluation.headline || paper.story.result || "暂无实验结论。"}</Paragraph>
        {paper.evaluation.setup_summary ? <Paragraph className="workspace-support-copy">{paper.evaluation.setup_summary}</Paragraph> : null}
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
      <SectionCard title="主要发现" muted variant={variant}>
        <TextList items={paper.evaluation.key_findings} emptyText="暂无结构化主要发现。" />
      </SectionCard>
    </div>
  );
}

function MetadataTab({ paper, variant = "card" }: { paper: PaperCanonicalRecord; variant?: SurfaceVariant }) {
  const links = orderedResourceLinks(paper);
  const markdownLinkHref = markdownHref(paper.source.paper_path);
  const translateLinkHref = translateConversationHref(paper.source.conversation_ids);
  const hasAnyResource = Boolean(links.length || markdownLinkHref || translateLinkHref);
  const taxonomyRows = [
    { label: "主题", value: <BadgeGroup values={paper.taxonomy.themes} /> },
    { label: "任务", value: <BadgeGroup values={paper.taxonomy.tasks} tone="gold" /> },
    { label: "方法", value: <BadgeGroup values={paper.taxonomy.methods} tone="green" /> },
    { label: "模态", value: <BadgeGroup values={paper.taxonomy.modalities} tone="processing" /> },
    { label: "创新类型", value: <BadgeGroup values={paper.taxonomy.novelty_types} tone="magenta" /> },
  ];

  return (
    <div className={`workspace-tab-stack${variant === "plain" ? " is-plain" : ""}`}>
      <SectionCard title="基础元信息" kicker="Metadata" variant={variant}>
        <KeyValueGrid
          items={[
            { label: "标题", value: paper.bibliography.title },
            { label: "作者", value: paper.bibliography.authors.length ? paper.bibliography.authors.join(" / ") : "暂无" },
            { label: "Venue", value: paper.bibliography.venue || "暂无" },
            { label: "年份", value: formatYear(paper.bibliography.year) },
            { label: "引用数", value: paper.bibliography.citation_count ?? "暂无" },
            { label: "DOI", value: paper.bibliography.identifiers.doi || "暂无" },
            { label: "arXiv", value: paper.bibliography.identifiers.arxiv || "暂无" },
          ]}
        />
      </SectionCard>
      <SectionCard title="资源链接" muted variant={variant}>
        {hasAnyResource ? (
          <Flex wrap="wrap" gap={10}>
            {links.map((item) => (
              <Button key={item.key} href={item.href} target="_blank" icon={<LinkOutlined />}>
                {item.label}
              </Button>
            ))}
            {markdownLinkHref ? (
              <Button href={markdownLinkHref} target="_blank" icon={<BookOutlined />}>
                {RESOURCE_LABELS.markdown}
              </Button>
            ) : null}
            {translateLinkHref ? (
              <Button href={translateLinkHref} target="_blank" icon={<LinkOutlined />}>
                {RESOURCE_LABELS.translate}
              </Button>
            ) : null}
          </Flex>
        ) : (
          <Paragraph className="workspace-empty-copy">暂无外部资源链接。</Paragraph>
        )}
      </SectionCard>
      <SectionCard title="Taxonomy" variant={variant}>
        <KeyValueGrid items={taxonomyRows} />
      </SectionCard>
      <SectionCard title="素材索引" muted variant={variant}>
        <KeyValueGrid
          items={[
            { label: "Figures", value: paper.assets.figures.length || "暂无" },
            { label: "Tables", value: paper.assets.tables.length || "暂无" },
            { label: "Claims", value: paper.claims.length || "暂无" },
            { label: "Relations", value: paper.relations.length || "暂无" },
          ]}
        />
      </SectionCard>
      <SectionCard title="结构化论断" variant={variant}>
        <ClaimList paper={paper} variant={variant} />
      </SectionCard>
    </div>
  );
}

function RelatedTab({
  detail,
  payload,
  variant = "card",
}: {
  detail: PaperDetailViewModel;
  payload: SiteIndexPayload;
  variant?: SurfaceVariant;
}) {
  const paper = detail.canonical;

  return (
    <div className={`workspace-tab-stack${variant === "plain" ? " is-plain" : ""}`}>
      <SectionCard title="下一篇线索" kicker="Related" variant={variant}>
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
      <SectionCard title="相关论文近邻" muted variant={variant}>
        <Tabs
          items={payload.navigation.neighbor_tabs.map((tab) => ({
            key: tab.key,
            label: tab.label,
            children: <NeighborList items={detail.neighbors[tab.key]} variant={variant} />,
          }))}
        />
      </SectionCard>
      <SectionCard title="关联关系" variant={variant}>
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
      { key: "summary", label: layoutMode === "home-compact" ? "摘要" : "Summary", children: <SummaryTab paper={detail.canonical} variant={variant} /> },
      { key: "method", label: layoutMode === "home-compact" ? "方法" : "Method", children: <MethodTab paper={detail.canonical} variant={variant} /> },
      { key: "metadata", label: layoutMode === "home-compact" ? "元信息" : "Metadata", children: <MetadataTab paper={detail.canonical} variant={variant} /> },
      { key: "related", label: layoutMode === "home-compact" ? "相关" : "Related", children: <RelatedTab detail={detail} payload={payload} variant={variant} /> },
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
  const primaryPdfLink = orderedResourceLinks(paper).find((item) => item.key === "pdf") ?? null;
  const translateLinkHref = translateConversationHref(paper.source.conversation_ids);
  const topTags = [
    paper.bibliography.venue || "未知来源",
    formatYear(paper.bibliography.year),
    paper.bibliography.citation_count !== null ? `引用 ${paper.bibliography.citation_count}` : "",
  ].filter(Boolean);
  const headlineTags = [...new Set([...paper.taxonomy.tasks, ...paper.taxonomy.methods, ...paper.taxonomy.themes])].slice(0, 4);

  return (
    <div className={`workspace-shell${layoutMode === "home-compact" ? " is-home-compact" : ""} ${className}`.trim()}>
      <div className="workspace-header">
        <div className="workspace-header-main">
          <Flex wrap="wrap" gap={8}>
            {topTags.map((item) => (
              <Tag key={item} className="chip-tag chip-tag-tone-blue">
                {item}
              </Tag>
            ))}
            {paper.editorial.verdict ? <Tag className={verdictTagClass(paper.editorial.verdict)}>{paper.editorial.verdict}</Tag> : null}
            <Tag className={chipToneClass("processing")}>{recommendedRouteLabel(paper.editorial.reading_route)}</Tag>
          </Flex>
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
              {layoutMode === "home-compact" && translateLinkHref ? (
                <Button href={translateLinkHref} target="_blank" icon={<BookOutlined />}>
                  查看翻译
                </Button>
              ) : null}
              {primaryPdfLink ? (
                <Button href={primaryPdfLink.href} target="_blank" icon={<LinkOutlined />}>
                  {primaryPdfLink.label}
                </Button>
              ) : null}
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

      {layoutMode === "home-compact" ? <ResearchPositionPanel paper={paper} /> : <QuickLookPanel paper={paper} />}

      {error ? <Alert type="warning" showIcon message="已显示缓存内容，刷新详情时出现问题" description={error} /> : null}

      <Tabs items={tabItems} className="workspace-tabs" />
    </div>
  );
}
