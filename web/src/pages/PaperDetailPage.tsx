import {
  Alert,
  App as AntApp,
  Button,
  Card,
  Col,
  Collapse,
  Empty,
  Flex,
  Grid,
  Input,
  Row,
  Space,
  Tabs,
  Tag,
  Typography,
} from "antd";
import {
  ArrowLeftOutlined,
  BookOutlined,
  CopyOutlined,
  FileSearchOutlined,
  LinkOutlined,
} from "@ant-design/icons";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  compactList,
  confidenceTone,
  filterFigureTableItems,
  firstExternalLinks,
  flattenRetrievalProfile,
  formatYear,
  markdownHref,
  paperRoute,
  recommendedRouteLabel,
  scoreLevelLabel,
  sharedSignalPreview,
  verdictTone,
} from "../lib/paper";
import type { FigureTableIndexItem, NeighborItem, PaperRecord, SitePayload } from "../types";

const { Title, Paragraph, Text } = Typography;

function scrollToId(id: string) {
  document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
}

function sectionTargetFromSupport(item: string): string | null {
  const lower = item.toLowerCase();
  if (!lower.startsWith("section:")) {
    return null;
  }
  const content = lower.replace("section:", "").trim();
  if (content.includes("abstract") || content.includes("summary") || content.includes("introduction")) {
    return "research-overview";
  }
  if (content.includes("method")) {
    return "method-core";
  }
  if (content.includes("experiment") || content.includes("eval")) {
    return "evaluation";
  }
  if (content.includes("conclusion")) {
    return "editorial-review";
  }
  return "materials-zone";
}

function labelFromSupport(item: string): { kind: "figures" | "tables"; label: string } | null {
  const lower = item.toLowerCase();
  if (lower.startsWith("figure:")) {
    return { kind: "figures", label: item.slice(item.indexOf(":") + 1).trim() };
  }
  if (lower.startsWith("table:")) {
    return { kind: "tables", label: item.slice(item.indexOf(":") + 1).trim() };
  }
  return null;
}

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

function truncateText(value: string | null | undefined, maxChars: number): string {
  const text = (value ?? "").trim();
  if (!text) {
    return "";
  }
  return text.length <= maxChars ? text : `${text.slice(0, maxChars - 1).trimEnd()}…`;
}

function relationHintLabel(value: string | null | undefined): string | null {
  if (value === "same-task") {
    return "同任务";
  }
  if (value === "same-method") {
    return "同方法";
  }
  if (value === "contrast") {
    return "对比阅读";
  }
  return value ?? null;
}

function useActiveSection(ids: string[]) {
  const [activeId, setActiveId] = useState<string>(ids[0] ?? "");

  useEffect(() => {
    const nodes = ids.map((id) => document.getElementById(id)).filter((node): node is HTMLElement => Boolean(node));
    if (!nodes.length) {
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((left, right) => right.intersectionRatio - left.intersectionRatio);
        if (visible[0]?.target?.id) {
          setActiveId(visible[0].target.id);
        }
      },
      {
        rootMargin: "-15% 0px -55% 0px",
        threshold: [0.1, 0.35, 0.6],
      },
    );

    nodes.forEach((node) => observer.observe(node));
    return () => observer.disconnect();
  }, [ids]);

  return activeId;
}

function SectionCard({
  id,
  title,
  kicker,
  summary,
  extra,
  strong = false,
  children,
}: {
  id: string;
  title: string;
  kicker?: string;
  summary?: string | null;
  extra?: ReactNode;
  strong?: boolean;
  children: ReactNode;
}) {
  return (
    <Card id={id} bordered={false} className={`surface-card reading-section ${strong ? "strong-section-card" : "soft-section-card"}`} extra={extra}>
      {kicker ? <Text className="section-kicker">{kicker}</Text> : null}
      <Title level={3} className="section-title">
        {title}
      </Title>
      {summary ? <Paragraph className="section-summary">{summary}</Paragraph> : null}
      {children}
    </Card>
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
        <Tag key={value} color={color}>
          {value}
        </Tag>
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

function ExternalLinkButtons({ paper }: { paper: PaperRecord }) {
  const navigate = useNavigate();
  const links = firstExternalLinks(paper.links);
  const markdownLink = markdownHref(paper.paper_path);

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

function DecisionHero({ paper }: { paper: PaperRecord }) {
  const digest = paper.reading_digest;
  const narrative = [
    { title: "问题", content: digest.narrative.problem },
    { title: "方法", content: digest.narrative.method },
    { title: "结果", content: digest.narrative.result },
  ].filter((item) => item.content);
  const positioning = compactList(
    [
      ...digest.positioning.task,
      ...digest.positioning.method,
      ...digest.positioning.modality,
      ...digest.positioning.novelty,
    ],
    6,
  );

  return (
    <Card bordered={false} className="hero-surface detail-hero v2-hero">
      <Space direction="vertical" size={20} style={{ width: "100%" }}>
        <Flex wrap="wrap" gap={8}>
          <Tag color="blue">{paper.venue || "未知 venue"}</Tag>
          <Tag color="cyan">{formatYear(paper.year)}</Tag>
          {paper.citation_count !== null ? <Tag color="gold">Citations {paper.citation_count}</Tag> : null}
          {paper.editorial_review.verdict ? <Tag color={verdictTone(paper.editorial_review.verdict)}>{paper.editorial_review.verdict}</Tag> : null}
        </Flex>

        <div>
          <Title className="detail-display-title">{paper.title}</Title>
          <Paragraph className="author-line">
            {paper.authors.length ? paper.authors.join(" / ") : "作者信息暂缺"} · {paper.venue || "未知 venue"} · {formatYear(paper.year)}
          </Paragraph>
          <Paragraph className="hero-one-liner detail-one-liner">
            {digest.value_statement || paper.summary.one_liner || "暂无首屏阅读判断。"}
          </Paragraph>
        </div>

        <Row gutter={[16, 16]}>
          <Col xs={24} lg={15}>
            <Card bordered={false} className="surface-card decision-strip-card">
              <Text className="section-kicker">阅读判断条</Text>
              <Space direction="vertical" size={10} style={{ width: "100%", marginTop: 12 }}>
                {digest.best_for ? <Paragraph className="decision-line">适合人群：{digest.best_for}</Paragraph> : null}
                <Paragraph className="decision-line">
                  推荐路径：{recommendedRouteLabel(digest.recommended_route)}
                </Paragraph>
                <Paragraph className="decision-line">
                  结果先看：{digest.result_headline || paper.benchmarks_or_eval.best_results[0] || "暂无前置结果判断。"}
                </Paragraph>
              </Space>
            </Card>
          </Col>
          <Col xs={24} lg={9}>
            <ExternalLinkButtons paper={paper} />
          </Col>
        </Row>

        {positioning.length ? (
          <div className="hero-tag-block">
            <Text className="hero-tag-label">定位标签</Text>
            <Flex wrap="wrap" gap={8} className="hero-tag-row">
              {positioning.map((tag) => (
                <Tag key={`${paper.paper_id}-${tag}`} className="soft-tag">
                  {tag}
                </Tag>
              ))}
            </Flex>
          </div>
        ) : null}

        {narrative.length ? (
          <Row gutter={[16, 16]} className="decision-story-grid">
            {narrative.map((item) => (
              <Col xs={24} md={8} key={item.title}>
                <Card bordered={false} className="subtle-card storyline-mini-card">
                  <Text className="section-kicker">{item.title}</Text>
                  <Paragraph className="storyline-copy">{item.content}</Paragraph>
                </Card>
              </Col>
            ))}
          </Row>
        ) : null}
      </Space>
    </Card>
  );
}

function DecisionCards({ paper }: { paper: PaperRecord }) {
  const digest = paper.reading_digest;
  const cards = [
    {
      title: "这篇解决什么",
      content: paper.research_problem.summary || digest.narrative.problem || "暂无研究问题摘要。",
      tags: compactList([...digest.positioning.task, ...paper.research_problem.gaps], 3),
    },
    {
      title: "方法核心",
      content: digest.narrative.method || paper.method_core.approach_summary || "暂无方法概述。",
      tags: compactList([...digest.positioning.method, ...paper.method_core.innovations], 3),
    },
    {
      title: "关键结果",
      content: digest.result_headline || paper.benchmarks_or_eval.best_results[0] || paper.benchmarks_or_eval.findings[0] || "暂无关键结果。",
      tags: compactList([...paper.benchmarks_or_eval.datasets, ...paper.benchmarks_or_eval.metrics], 3),
    },
    {
      title: "为什么继续看",
      content: digest.why_read[0] || paper.summary.research_value.summary || "暂无继续阅读理由。",
      tags: compactList([...digest.why_read.slice(1), ...digest.positioning.novelty], 3),
    },
  ];

  return (
    <Row gutter={[16, 16]} className="quick-card-grid">
      {cards.map((item) => (
        <Col xs={24} md={12} xl={6} key={item.title}>
          <Card bordered={false} className="surface-card quick-read-card decision-read-card">
            <Text className="section-kicker">{item.title}</Text>
            <Paragraph className="quick-card-content">{truncateText(item.content, 92) || "暂无内容。"}</Paragraph>
            <Flex wrap="wrap" gap={8}>
              {item.tags.length ? (
                item.tags.map((tag) => (
                  <Tag key={`${item.title}-${tag}`} className="soft-tag">
                    {truncateText(tag, 24)}
                  </Tag>
                ))
              ) : (
                <Text type="secondary">暂无标签</Text>
              )}
            </Flex>
          </Card>
        </Col>
      ))}
    </Row>
  );
}

function ResearchOverviewSection({ paper }: { paper: PaperRecord }) {
  return (
    <SectionCard
      id="research-overview"
      title="研究问题"
      kicker="理解层 / 强 section"
      strong
      summary={paper.reading_digest.narrative.problem || paper.research_problem.summary}
    >
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={14}>
          <Card bordered={false} className="surface-card emphasis-card">
            <Text className="section-kicker">问题与目标</Text>
            <Paragraph className="section-lead">{paper.research_problem.summary || "暂无研究问题摘要。"}</Paragraph>
            {paper.research_problem.goal ? (
              <Alert type="info" showIcon className="compact-alert" message="研究目标" description={paper.research_problem.goal} />
            ) : null}
          </Card>
        </Col>
        <Col xs={24} lg={10}>
          <Card bordered={false} className="subtle-card">
            <Text strong>研究缺口</Text>
            {paper.research_problem.gaps.length ? (
              <Space direction="vertical" size={8} style={{ width: "100%", marginTop: 12 }}>
                {paper.research_problem.gaps.map((gap) => (
                  <Card key={gap} bordered={false} className="subtle-card list-card">
                    <Paragraph style={{ marginBottom: 0 }}>{gap}</Paragraph>
                  </Card>
                ))}
              </Space>
            ) : (
              <Paragraph type="secondary" style={{ marginTop: 12, marginBottom: 0 }}>
                暂无结构化研究缺口。
              </Paragraph>
            )}
          </Card>
        </Col>
      </Row>

      <Card bordered={false} className="subtle-card">
        <Text strong>核心贡献</Text>
        {paper.core_contributions.length ? (
          <Space direction="vertical" size={8} style={{ width: "100%", marginTop: 12 }}>
            {paper.core_contributions.map((item) => (
              <Card key={item} bordered={false} className="subtle-card list-card">
                <Paragraph style={{ marginBottom: 0 }}>{item}</Paragraph>
              </Card>
            ))}
          </Space>
        ) : (
          <EmptyBlock description="暂无核心贡献整理。" />
        )}
      </Card>
    </SectionCard>
  );
}

function MethodCoreSection({ paper }: { paper: PaperRecord }) {
  return (
    <SectionCard
      id="method-core"
      title="方法主线"
      kicker="理解层 / 强 section"
      strong
      summary={paper.reading_digest.narrative.method || paper.method_core.approach_summary}
    >
      <Card bordered={false} className="surface-card emphasis-card">
        <Text className="section-kicker">一句话方法总述</Text>
        <Paragraph className="section-lead">{paper.method_core.approach_summary || "暂无方法概述。"}</Paragraph>
      </Card>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card bordered={false} className="subtle-card">
            <Text strong>Pipeline</Text>
            {paper.method_core.pipeline_steps.length ? (
              <ol className="ordered-list">
                {paper.method_core.pipeline_steps.map((step) => (
                  <li key={step}>{step}</li>
                ))}
              </ol>
            ) : (
              <Paragraph type="secondary" style={{ marginTop: 12, marginBottom: 0 }}>
                暂无明确流程拆解。
              </Paragraph>
            )}
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card bordered={false} className="subtle-card">
            <Text strong>方法创新</Text>
            {paper.method_core.innovations.length ? (
              <Space direction="vertical" size={8} style={{ width: "100%", marginTop: 12 }}>
                {paper.method_core.innovations.map((item) => (
                  <Card key={item} bordered={false} className="subtle-card list-card">
                    <Paragraph style={{ marginBottom: 0 }}>{item}</Paragraph>
                  </Card>
                ))}
              </Space>
            ) : (
              <Paragraph type="secondary" style={{ marginTop: 12, marginBottom: 0 }}>
                暂无结构化创新点。
              </Paragraph>
            )}
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} md={8}>
          <Card bordered={false} className="subtle-card">
            <Text strong>Ingredients</Text>
            <div style={{ marginTop: 12 }}>
              <BadgeGroup values={paper.method_core.ingredients} />
            </div>
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card bordered={false} className="subtle-card">
            <Text strong>Representation</Text>
            <div style={{ marginTop: 12 }}>
              <BadgeGroup values={paper.method_core.representation} />
            </div>
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card bordered={false} className="subtle-card">
            <Text strong>Task Boundary</Text>
            <div style={{ marginTop: 12 }}>
              <BadgeGroup values={[...paper.inputs_outputs.inputs, ...paper.inputs_outputs.outputs]} />
            </div>
          </Card>
        </Col>
      </Row>
    </SectionCard>
  );
}

function EvaluationSection({ paper }: { paper: PaperRecord }) {
  const groups = [
    { label: "Datasets", values: paper.benchmarks_or_eval.datasets },
    { label: "Metrics", values: paper.benchmarks_or_eval.metrics },
    { label: "Baselines", values: paper.benchmarks_or_eval.baselines },
    { label: "Key Findings", values: paper.benchmarks_or_eval.findings, findings: true },
  ];

  return (
    <SectionCard
      id="evaluation"
      title="关键结果"
      kicker="理解层 / 强 section"
      strong
      summary={paper.reading_digest.result_headline || paper.benchmarks_or_eval.best_results[0] || paper.benchmarks_or_eval.findings[0]}
    >
      <Card bordered={false} className="surface-card emphasis-card best-result-card">
        <Text className="section-kicker">Result Banner</Text>
        <Paragraph className="section-lead">
          {paper.reading_digest.result_headline || paper.benchmarks_or_eval.best_results[0] || "暂无前置结果判断。"}
        </Paragraph>
      </Card>

      {paper.benchmarks_or_eval.experiment_setup_summary ? (
        <Card bordered={false} className="surface-card setup-summary-card">
          <Text className="section-kicker">实验设置摘要</Text>
          <Paragraph className="long-copy">{paper.benchmarks_or_eval.experiment_setup_summary}</Paragraph>
        </Card>
      ) : null}

      <Row gutter={[16, 16]}>
        {groups.map((group) => (
          <Col xs={24} md={12} key={group.label}>
            <Card bordered={false} className="subtle-card eval-group-card">
              <Text strong>{group.label}</Text>
              {group.values.length ? (
                group.findings ? (
                  <Space direction="vertical" size={8} style={{ width: "100%", marginTop: 12 }}>
                    {group.values.map((item) => (
                      <Card key={item} bordered={false} className="finding-card">
                        <Paragraph style={{ marginBottom: 0 }}>{item}</Paragraph>
                      </Card>
                    ))}
                  </Space>
                ) : (
                  <Flex wrap="wrap" gap={8} style={{ marginTop: 12 }}>
                    {group.values.map((item) => (
                      <Tag key={item} className="soft-tag">
                        {item}
                      </Tag>
                    ))}
                  </Flex>
                )
              ) : (
                <Paragraph type="secondary" style={{ marginTop: 12, marginBottom: 0 }}>
                  暂无
                </Paragraph>
              )}
            </Card>
          </Col>
        ))}
      </Row>
    </SectionCard>
  );
}

function EditorialReviewSection({ paper }: { paper: PaperRecord }) {
  return (
    <SectionCard
      id="editorial-review"
      title="编辑判断"
      kicker="理解层 / 强 section"
      strong
      summary={paper.editorial_review.research_position || paper.editor_note?.summary || "帮助判断值不值得继续读。"}
    >
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={9}>
          <Card bordered={false} className="editor-note-card emphasis-card">
            <Text className="section-kicker">总评</Text>
            <Title level={4} style={{ marginTop: 10, marginBottom: 8 }}>
              {paper.editorial_review.verdict || "暂无明确总评"}
            </Title>
            <Paragraph style={{ marginBottom: 0 }}>
              {paper.editorial_review.research_position || paper.editor_note?.summary || "暂无编辑位置判断。"}
            </Paragraph>
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card bordered={false} className="subtle-card">
            <Text strong>值得看的点</Text>
            {paper.editorial_review.strengths.length ? (
              <Space direction="vertical" size={8} style={{ width: "100%", marginTop: 12 }}>
                {paper.editorial_review.strengths.map((item) => (
                  <Card key={item} bordered={false} className="subtle-card list-card">
                    <Paragraph style={{ marginBottom: 0 }}>{item}</Paragraph>
                  </Card>
                ))}
              </Space>
            ) : (
              <Paragraph type="secondary" style={{ marginTop: 12, marginBottom: 0 }}>
                暂无明确 strengths。
              </Paragraph>
            )}
          </Card>
        </Col>
        <Col xs={24} lg={7}>
          <Card bordered={false} className="subtle-card limitations-card">
            <Text strong>谨慎点</Text>
            {paper.editorial_review.cautions.length || paper.limitations.length ? (
              <Space direction="vertical" size={8} style={{ width: "100%", marginTop: 12 }}>
                {(paper.editorial_review.cautions.length ? paper.editorial_review.cautions : paper.limitations).map((item) => (
                  <Card key={item} bordered={false} className="subtle-card list-card">
                    <Paragraph style={{ marginBottom: 0 }}>{item}</Paragraph>
                  </Card>
                ))}
              </Space>
            ) : (
              <Paragraph type="secondary" style={{ marginTop: 12, marginBottom: 0 }}>
                暂无明确 cautions。
              </Paragraph>
            )}
          </Card>
        </Col>
      </Row>

      {paper.editorial_review.next_read_hint ? (
        <Card bordered={false} className="surface-card emphasis-card">
          <Text className="section-kicker">下一篇建议</Text>
          <Paragraph className="section-lead">{paper.editorial_review.next_read_hint}</Paragraph>
        </Card>
      ) : null}
    </SectionCard>
  );
}

function ComparisonSection({ paper }: { paper: PaperRecord }) {
  const context = paper.comparison_context;

  return (
    <SectionCard id="comparison" title="对比阅读" kicker="理解层 / 辅助 section" summary={context.recommended_next_read || "拿谁来比，为什么值得比。"}>
      <Row gutter={[16, 16]}>
        <Col xs={24} md={12}>
          <Card bordered={false} className="subtle-card">
            <Text strong>显式 Baselines</Text>
            <div style={{ marginTop: 12 }}>
              <BadgeGroup values={context.explicit_baselines} />
            </div>
          </Card>
        </Col>
        <Col xs={24} md={12}>
          <Card bordered={false} className="subtle-card">
            <Text strong>Contrast Methods</Text>
            <div style={{ marginTop: 12 }}>
              <BadgeGroup values={context.contrast_methods} color="processing" />
            </div>
          </Card>
        </Col>
      </Row>

      <Card bordered={false} className="subtle-card">
        <Text strong>对比维度</Text>
        {context.comparison_aspects.length ? (
          <Space direction="vertical" size={8} style={{ width: "100%", marginTop: 12 }}>
            {context.comparison_aspects.map((item) => (
              <Card key={`${item.aspect}-${item.difference}`} bordered={false} className="subtle-card list-card">
                <Text strong>{item.aspect}</Text>
                <Paragraph style={{ marginTop: 6, marginBottom: 0 }}>{item.difference}</Paragraph>
              </Card>
            ))}
          </Space>
        ) : (
          <Paragraph type="secondary" style={{ marginTop: 12, marginBottom: 0 }}>
            暂无结构化对比维度。
          </Paragraph>
        )}
      </Card>
    </SectionCard>
  );
}

function ClaimsPanel({
  paper,
  onSupportClick,
}: {
  paper: PaperRecord;
  onSupportClick: (item: string) => void;
}) {
  const [claimType, setClaimType] = useState<string>("all");
  const filteredClaims = useMemo(
    () => (claimType === "all" ? paper.key_claims : paper.key_claims.filter((item) => item.type === claimType)),
    [claimType, paper.key_claims],
  );

  return (
    <Space direction="vertical" size={16} style={{ width: "100%" }}>
      <Tabs
        activeKey={claimType}
        onChange={setClaimType}
        items={[
          { key: "all", label: "All" },
          { key: "method", label: "Method" },
          { key: "experiment", label: "Experiment" },
          { key: "capability", label: "Capability" },
          { key: "limitation", label: "Limitation" },
        ]}
      />
      {filteredClaims.length ? (
        filteredClaims.map((claim, index) => (
          <Card key={`${paper.paper_id}-claim-${index}`} bordered={false} className="claim-card">
            <Flex justify="space-between" align="start" gap={12} wrap="wrap">
              <Paragraph className="claim-text">{claim.claim}</Paragraph>
              <Tag color="geekblue">{claim.type}</Tag>
            </Flex>
            <Flex wrap="wrap" gap={8}>
              {claim.support.map((item) => (
                <Button key={`${paper.paper_id}-${index}-${item}`} size="small" className="support-chip" onClick={() => onSupportClick(item)}>
                  {item}
                </Button>
              ))}
              {claim.confidence ? <Tag color={confidenceTone(claim.confidence)}>可信度 {claim.confidence}</Tag> : null}
            </Flex>
          </Card>
        ))
      ) : (
        <EmptyBlock description="当前筛选下暂无关键论断。" />
      )}
    </Space>
  );
}

function FigureTablePanel({
  paper,
  activeKey,
  setActiveKey,
  highlightedLabel,
}: {
  paper: PaperRecord;
  activeKey: "figures" | "tables";
  setActiveKey: (key: "figures" | "tables") => void;
  highlightedLabel: string | null;
}) {
  const [query, setQuery] = useState("");

  const figureItems = useMemo(() => filterFigureTableItems(paper.figure_table_index.figures, query), [paper.figure_table_index.figures, query]);
  const tableItems = useMemo(() => filterFigureTableItems(paper.figure_table_index.tables, query), [paper.figure_table_index.tables, query]);

  const renderItem = (item: FigureTableIndexItem) => (
    <Card key={item.label} bordered={false} className={`subtle-card figure-item-card ${highlightedLabel === item.label ? "is-highlighted" : ""}`}>
      <Flex justify="space-between" align="start" gap={12} wrap="wrap">
        <Text strong>{item.label}</Text>
        <Flex wrap="wrap" gap={8}>
          <Tag color={item.importance === "high" ? "gold" : item.importance === "medium" ? "blue" : "default"}>{item.importance}</Tag>
          <Tag>{item.role}</Tag>
        </Flex>
      </Flex>
      <Paragraph className="long-copy" style={{ marginTop: 8, marginBottom: 0 }}>
        {item.caption}
      </Paragraph>
    </Card>
  );

  if (!paper.figure_table_index.figures.length && !paper.figure_table_index.tables.length) {
    return <EmptyBlock description="暂无图表索引。" />;
  }

  return (
    <Space direction="vertical" size={14} style={{ width: "100%" }}>
      <Input
        allowClear
        placeholder="搜索 Figure / Table label"
        prefix={<FileSearchOutlined />}
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        className="compact-search"
      />
      <Tabs
        activeKey={activeKey}
        onChange={(value) => setActiveKey(value as "figures" | "tables")}
        items={[
          {
            key: "figures",
            label: `Figures (${figureItems.length})`,
            children: figureItems.length ? <Space direction="vertical" size={12} style={{ width: "100%" }}>{figureItems.map(renderItem)}</Space> : <EmptyBlock description="没有命中 Figure。" />,
          },
          {
            key: "tables",
            label: `Tables (${tableItems.length})`,
            children: tableItems.length ? <Space direction="vertical" size={12} style={{ width: "100%" }}>{tableItems.map(renderItem)}</Space> : <EmptyBlock description="没有命中 Table。" />,
          },
        ]}
      />
    </Space>
  );
}

function NeighborList({ items }: { items: NeighborItem[] }) {
  if (!items.length) {
    return <EmptyBlock description="当前没有足够可靠的近邻。" />;
  }

  return (
    <Space direction="vertical" size={12} style={{ width: "100%" }}>
      {items.map((item) => (
        <Card key={`${item.paper_id}-${item.match_source}`} bordered={false} className="neighbor-card">
          <Flex justify="space-between" align="start" gap={12} wrap="wrap">
            <div style={{ minWidth: 0, flex: 1 }}>
              <Link to={paperRoute(item.route_path, item.paper_id)} className="paper-link small">
                {item.title}
              </Link>
              <Paragraph className="neighbor-reason-short">{item.reason_short || truncateText(item.reason, 50)}</Paragraph>
              <Paragraph type="secondary" style={{ marginTop: 6, marginBottom: 0 }}>
                {item.reason}
              </Paragraph>
              {item.relation_hint ? <Paragraph style={{ marginTop: 8, marginBottom: 0 }}>{relationHintLabel(item.relation_hint)}</Paragraph> : null}
            </div>
            <Tag color={item.score_level === "high" ? "gold" : item.score_level === "medium" ? "blue" : "default"}>{scoreLevelLabel(item.score_level)}</Tag>
          </Flex>
          <Flex wrap="wrap" gap={8} style={{ marginTop: 10 }}>
            {sharedSignalPreview(item.shared_signals).map((signal) => (
              <Tag key={`${item.paper_id}-${signal}`} className="soft-tag">
                {signal}
              </Tag>
            ))}
          </Flex>
        </Card>
      ))}
    </Space>
  );
}

function MaterialsSection({
  paper,
  payload,
  debugMode,
  onSupportClick,
  activeFigureTab,
  setActiveFigureTab,
  highlightedFigureLabel,
}: {
  paper: PaperRecord;
  payload: SitePayload;
  debugMode: boolean;
  onSupportClick: (item: string) => void;
  activeFigureTab: "figures" | "tables";
  setActiveFigureTab: (key: "figures" | "tables") => void;
  highlightedFigureLabel: string | null;
}) {
  const { message } = AntApp.useApp();

  const handleCopy = async () => {
    try {
      await copyText(JSON.stringify(paper, null, 2));
      message.success("已复制结构化 JSON。");
    } catch {
      message.error("复制失败。");
    }
  };

  const abstractTabs = [
    {
      key: "zh",
      label: "中文摘要",
      children: paper.abstract_zh ? <Paragraph className="long-copy">{paper.abstract_zh}</Paragraph> : <EmptyBlock description="暂无中文摘要。" />,
    },
    {
      key: "raw",
      label: "原始摘要",
      children: paper.abstract_raw ? <Paragraph className="long-copy">{paper.abstract_raw}</Paragraph> : <EmptyBlock description="暂无原始摘要。" />,
    },
  ];

  const items = [
    {
      key: "claims",
      label: "Claims & Evidence",
      children: <ClaimsPanel paper={paper} onSupportClick={onSupportClick} />,
    },
    {
      key: "figures",
      label: "图表索引",
      children: (
        <FigureTablePanel
          paper={paper}
          activeKey={activeFigureTab}
          setActiveKey={setActiveFigureTab}
          highlightedLabel={highlightedFigureLabel}
        />
      ),
    },
    {
      key: "neighbors",
      label: "Related Papers",
      children: (
        <Tabs
          items={payload.navigation.neighbor_tabs.map((tab) => ({
            key: tab.key,
            label: tab.label,
            children: <NeighborList items={paper.paper_neighbors[tab.key]} />,
          }))}
        />
      ),
    },
    {
      key: "abstracts",
      label: "摘要与原文",
      children: <Tabs defaultActiveKey={paper.abstract_zh ? "zh" : "raw"} items={abstractTabs} />,
    },
    {
      key: "retrieval",
      label: "检索画像",
      children: (
        <Space direction="vertical" size={12} style={{ width: "100%" }}>
          {flattenRetrievalProfile(paper.retrieval_profile).map((group) => (
            <Card key={group.label} bordered={false} className="subtle-card">
              <Text strong>{group.label}</Text>
              <div style={{ marginTop: 10 }}>
                <BadgeGroup values={group.values} />
              </div>
            </Card>
          ))}
        </Space>
      ),
    },
  ];

  if (debugMode) {
    items.push({
      key: "debug",
      label: "JSON / Debug",
      children: (
        <Space direction="vertical" size={12} style={{ width: "100%" }}>
          <Button icon={<CopyOutlined />} onClick={handleCopy}>
            复制 JSON
          </Button>
          <pre className="debug-json-block">{JSON.stringify(paper, null, 2)}</pre>
        </Space>
      ),
    });
  }

  return (
    <SectionCard
      id="materials-zone"
      title="资料区"
      kicker="按需展开"
      summary="把 Claims、图表、近邻、摘要和检索画像收进后半段，避免正文一直等权展开。"
    >
      <Collapse defaultActiveKey={[]} items={items} />
    </SectionCard>
  );
}

function OutlineCard({ items, activeId }: { items: Array<{ key: string; label: string }>; activeId: string }) {
  return (
    <Card bordered={false} className="surface-card sidebar-card">
      <Text className="section-kicker">页面目录</Text>
      <Space direction="vertical" size={8} style={{ width: "100%", marginTop: 14 }}>
        {items.map((item) => (
          <Button key={item.key} block className={item.key === activeId ? "toc-button is-active" : "toc-button"} onClick={() => scrollToId(item.key)}>
            {item.label}
          </Button>
        ))}
      </Space>
    </Card>
  );
}

function SidebarSnapshotCard({ paper }: { paper: PaperRecord }) {
  return (
    <Card bordered={false} className="surface-card sidebar-card">
      <Text className="section-kicker">Paper Snapshot</Text>
      <Title level={4} className="panel-title">
        阅读定位
      </Title>
      <MetaLine label="Venue / Year" value={`${paper.venue || "未知"} / ${formatYear(paper.year)}`} />
      <MetaLine label="Citations" value={paper.citation_count ?? "暂无"} />
      <MetaLine label="Verdict" value={paper.editorial_review.verdict || "暂无"} />
      <MetaLine label="Route" value={recommendedRouteLabel(paper.reading_digest.recommended_route)} />
      <MetaLine label="Task" value={<BadgeGroup values={paper.reading_digest.positioning.task} color="gold" />} />
      <MetaLine label="Method" value={<BadgeGroup values={paper.reading_digest.positioning.method} color="green" />} />
    </Card>
  );
}

function SidebarReadingRouteCard({ paper }: { paper: PaperRecord }) {
  const routeTargets = [
    { key: "method-core", label: "先看方法" },
    { key: "evaluation", label: "先看实验" },
    { key: "comparison", label: "先看对比" },
  ];

  return (
    <Card bordered={false} className="surface-card sidebar-card">
      <Text className="section-kicker">Reading Route</Text>
      <Space direction="vertical" size={8} style={{ width: "100%", marginTop: 12 }}>
        {routeTargets.map((item) => (
          <Button
            key={item.key}
            block
            type={item.label === recommendedRouteLabel(paper.reading_digest.recommended_route) ? "primary" : "default"}
            onClick={() => scrollToId(item.key)}
          >
            {item.label}
          </Button>
        ))}
      </Space>
    </Card>
  );
}

function SidebarLinksCard({ paper }: { paper: PaperRecord }) {
  const links = firstExternalLinks(paper.links);

  return (
    <Card bordered={false} className="surface-card sidebar-card">
      <Text className="section-kicker">Links & Tags</Text>
      <MetaLine label="Novelty" value={<BadgeGroup values={paper.reading_digest.positioning.novelty} color="magenta" />} />
      <MetaLine label="Modalities" value={<BadgeGroup values={paper.reading_digest.positioning.modality} color="processing" />} />
      <MetaLine
        label="Links"
        value={
          links.length ? (
            <Flex wrap="wrap" gap={8}>
              {links.map((item) => (
                <Button key={item.key} size="small" href={item.href} target="_blank">
                  {item.label}
                </Button>
              ))}
            </Flex>
          ) : (
            "暂无"
          )
        }
      />
    </Card>
  );
}

export function PaperDetailPage({ payload, debugMode }: { payload: SitePayload; debugMode: boolean }) {
  const screens = Grid.useBreakpoint();
  const navigate = useNavigate();
  const params = useParams();
  const { message } = AntApp.useApp();
  const paper = payload.papers.find((item) => item.paper_id === params.paperId);
  const [activeFigureTab, setActiveFigureTab] = useState<"figures" | "tables">("figures");
  const [highlightedFigureLabel, setHighlightedFigureLabel] = useState<string | null>(null);

  const outlineItems = useMemo(
    () => [
      { key: "research-overview", label: "研究问题" },
      { key: "method-core", label: "方法主线" },
      { key: "evaluation", label: "关键结果" },
      { key: "editorial-review", label: "编辑判断" },
      { key: "comparison", label: "对比阅读" },
      { key: "materials-zone", label: "资料区" },
    ],
    [],
  );
  const activeSection = useActiveSection(outlineItems.map((item) => item.key));

  if (!paper) {
    return (
      <Card bordered={false} className="surface-card">
        <Empty description="没有找到这篇论文。" />
        <Button style={{ marginTop: 16 }} icon={<ArrowLeftOutlined />} onClick={() => navigate("/")}>
          返回首页
        </Button>
      </Card>
    );
  }

  const handleSupportClick = async (item: string) => {
    const anchor = sectionTargetFromSupport(item);
    if (anchor) {
      scrollToId(anchor);
      return;
    }

    const labelTarget = labelFromSupport(item);
    if (labelTarget) {
      setActiveFigureTab(labelTarget.kind);
      setHighlightedFigureLabel(labelTarget.label);
      scrollToId("materials-zone");
      return;
    }

    try {
      await copyText(item);
      message.success(`已复制引用标记：${item}`);
    } catch {
      message.error("复制 support 标记失败。");
    }
  };

  const sidebar = (
    <Space direction="vertical" size={16} style={{ width: "100%" }}>
      <OutlineCard items={outlineItems} activeId={activeSection} />
      <SidebarSnapshotCard paper={paper} />
      <SidebarReadingRouteCard paper={paper} />
      <SidebarLinksCard paper={paper} />
    </Space>
  );

  return (
    <div className="page-stack">
      <DecisionHero paper={paper} />
      <DecisionCards paper={paper} />

      {!screens.xl ? <div>{sidebar}</div> : null}

      <Row gutter={[24, 24]} align="top">
        <Col xs={24} xl={17}>
          <Space direction="vertical" size={18} style={{ width: "100%" }}>
            <ResearchOverviewSection paper={paper} />
            <MethodCoreSection paper={paper} />
            <EvaluationSection paper={paper} />
            <EditorialReviewSection paper={paper} />
            <ComparisonSection paper={paper} />
            <MaterialsSection
              paper={paper}
              payload={payload}
              debugMode={debugMode}
              onSupportClick={handleSupportClick}
              activeFigureTab={activeFigureTab}
              setActiveFigureTab={(key) => {
                setActiveFigureTab(key);
                setHighlightedFigureLabel(null);
              }}
              highlightedFigureLabel={highlightedFigureLabel}
            />
          </Space>
        </Col>

        <Col xs={24} xl={7}>
          {screens.xl ? <div className="sticky-column">{sidebar}</div> : null}
        </Col>
      </Row>
    </div>
  );
}
