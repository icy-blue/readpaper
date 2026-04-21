import {
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
  cleanDisplayText,
  compactList,
  chipToneClass,
  confidenceTone,
  displayClaimType,
  displayComparisonAspect,
  displayFigureRole,
  displayValueLabel,
  filterFigureTableItems,
  firstExternalLinks,
  flattenRetrievalProfile,
  formatYear,
  importanceTagClass,
  markdownHref,
  paperRoute,
  recommendedRouteLabel,
  scoreLevelLabel,
  scoreLevelTagClass,
  sharedSignalPreview,
  verdictTagClass,
} from "../lib/paper";
import type { FigureTableIndexItem, NeighborItem, PaperRecord, SitePayload } from "../types";
import { TooltipTag, TooltipText } from "../components/OverflowTooltip";

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

function compactTexts(values: Array<string | null | undefined>, maxChars = 88, limit = 4): string[] {
  const cleaned: string[] = [];
  values.forEach((value) => {
    const text = cleanDisplayText(value, maxChars);
    if (text && !cleaned.includes(text)) {
      cleaned.push(text);
    }
  });
  return cleaned.slice(0, limit);
}

function firstText(values: Array<string | null | undefined>, maxChars = 88): string | null {
  return compactTexts(values, maxChars, 1)[0] ?? null;
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
          <Tag className="chip-tag chip-tag-venue">{paper.venue || "未知来源"}</Tag>
          <Tag className="chip-tag chip-tag-year">{formatYear(paper.year)}</Tag>
          {paper.citation_count !== null ? <Tag className="chip-tag chip-tag-citation">引用 {paper.citation_count}</Tag> : null}
          {paper.editorial_review.verdict ? <Tag className={verdictTagClass(paper.editorial_review.verdict)}>{paper.editorial_review.verdict}</Tag> : null}
        </Flex>

        <div>
          <Title className="detail-display-title">{paper.title}</Title>
          <Paragraph className="author-line">
            {paper.authors.length ? paper.authors.join(" / ") : "作者信息暂缺"} · {paper.venue || "未知来源"} · {formatYear(paper.year)}
          </Paragraph>
          <TooltipText
            text={digest.value_statement || paper.summary.one_liner || "暂无首屏阅读判断。"}
            as="paragraph"
            rows={3}
            className="hero-one-liner detail-one-liner"
          />
        </div>

        <Row gutter={[16, 16]}>
          <Col xs={24} lg={15}>
            <Card bordered={false} className="surface-card decision-strip-card">
              <Text className="section-kicker">读前摘要</Text>
              <Space direction="vertical" size={10} style={{ width: "100%", marginTop: 12 }}>
                {digest.best_for ? <TooltipText text={`适合人群：${digest.best_for}`} as="paragraph" rows={2} className="decision-line" /> : null}
                <Paragraph className="decision-line">推荐路径：{recommendedRouteLabel(digest.recommended_route)}</Paragraph>
                <TooltipText
                  text={`结果先看：${digest.result_headline || paper.benchmarks_or_eval.best_results[0] || "暂无前置结果判断。"}`}
                  as="paragraph"
                  rows={2}
                  className="decision-line"
                />
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
                <TooltipTag key={`${paper.paper_id}-${tag}`} label={tag} className="chip-tag chip-tag-tone-blue" />
              ))}
            </Flex>
          </div>
        ) : null}
      </Space>
    </Card>
  );
}

function DecisionCards({ paper }: { paper: PaperRecord }) {
  const cards = [
    {
      title: "研究问题",
      content: firstText([paper.storyline.problem, paper.research_problem.summary], 88),
      tags: compactList(paper.reading_digest.positioning.task, 3),
    },
    {
      title: "方法概述",
      content: firstText([paper.storyline.method, paper.method_core.approach_summary], 88),
      tags: compactList(
        [
          ...paper.reading_digest.positioning.method,
          ...paper.method_core.ingredients,
          ...paper.method_core.representation,
          ...paper.inputs_outputs.inputs,
          ...paper.inputs_outputs.outputs,
        ],
        4,
      ),
    },
    {
      title: "实验结论",
      content: firstText([paper.storyline.outcome, paper.reading_digest.result_headline, paper.benchmarks_or_eval.best_results[0]], 88),
      tags: compactList([...paper.benchmarks_or_eval.datasets, ...paper.benchmarks_or_eval.metrics], 3),
    },
  ].filter((item) => item.content);

  if (!cards.length) {
    return null;
  }

  return (
    <Row gutter={[16, 16]} className="quick-card-grid">
      {cards.map((item) => (
        <Col xs={24} md={12} xl={8} key={item.title}>
          <Card bordered={false} className="surface-card quick-read-card decision-read-card">
            <Text className="section-kicker">{item.title}</Text>
            <TooltipText text={item.content} as="paragraph" rows={3} className="quick-card-content" />
            {item.tags.length ? (
              <Flex wrap="wrap" gap={8}>
                {item.tags.map((tag) => (
                  <TooltipTag key={`${item.title}-${tag}`} label={displayValueLabel(tag)} className="chip-tag chip-tag-tone-blue" />
                ))}
              </Flex>
            ) : null}
          </Card>
        </Col>
      ))}
    </Row>
  );
}

function ResearchOverviewSection({ paper }: { paper: PaperRecord }) {
  const summary =
    firstText([paper.storyline.problem, paper.reading_digest.narrative.problem, paper.research_problem.goal, paper.research_problem.summary], 100) ||
    "暂无研究问题摘要。";
  const goal = firstText([paper.research_problem.goal, paper.research_problem.summary], 92);
  const gaps = compactTexts(paper.research_problem.gaps, 82, 4).filter((item) => item !== summary && item !== goal);
  const contributions = compactTexts(paper.core_contributions, 86, 4);

  return (
    <SectionCard
      id="research-overview"
      title="研究问题"
      kicker="问题定义"
      strong
      summary={summary}
    >
      <Row gutter={[16, 16]} className="card-grid-row">
        <Col xs={24} lg={14}>
          <Card bordered={false} className="surface-card emphasis-card">
            <Text className="section-kicker">问题与目标</Text>
            <Paragraph className="section-lead">{summary}</Paragraph>
            {goal && goal !== summary ? (
              <Card bordered={false} className="focus-note-card goal-note-card">
                <Text className="focus-note-label">研究目标</Text>
                <Paragraph className="focus-note-copy">{goal}</Paragraph>
              </Card>
            ) : null}
          </Card>
        </Col>
        <Col xs={24} lg={10}>
          <Card bordered={false} className="subtle-card">
            <Text strong>研究缺口</Text>
            {gaps.length ? (
              <Space direction="vertical" size={8} style={{ width: "100%", marginTop: 12 }}>
                {gaps.map((gap) => (
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
        {contributions.length ? (
          <Space direction="vertical" size={8} style={{ width: "100%", marginTop: 12 }}>
            {contributions.map((item) => (
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
  const summary = firstText([paper.method_core.approach_summary, paper.reading_digest.narrative.method, paper.storyline.method], 100);
  const steps = compactTexts(paper.method_core.pipeline_steps, 100, 4);
  const innovations = compactTexts(paper.method_core.innovations, 88, 4);

  return (
    <SectionCard
      id="method-core"
      title="方法设计"
      kicker="方法设计"
      strong
      summary={summary}
    >
      <Card bordered={false} className="surface-card emphasis-card">
        <Text className="section-kicker">方案摘要</Text>
        <Paragraph className="section-lead">{summary || "暂无方法概述。"}</Paragraph>
      </Card>

      <Row gutter={[16, 16]} className="card-grid-row">
        <Col xs={24} lg={12}>
          <Card bordered={false} className="subtle-card">
            <Text strong>方法流程</Text>
            {steps.length ? (
              <ol className="ordered-list">
                {steps.map((step) => (
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
            <Text strong>主要创新</Text>
            {innovations.length ? (
              <Space direction="vertical" size={8} style={{ width: "100%", marginTop: 12 }}>
                {innovations.map((item) => (
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

      <Row gutter={[16, 16]} className="card-grid-row">
        <Col xs={24} md={8}>
          <Card bordered={false} className="subtle-card">
            <Text strong>关键组件</Text>
            <div style={{ marginTop: 12 }}>
              <BadgeGroup values={paper.method_core.ingredients} />
            </div>
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card bordered={false} className="subtle-card">
            <Text strong>表示形式</Text>
            <div style={{ marginTop: 12 }}>
              <BadgeGroup values={paper.method_core.representation} />
            </div>
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card bordered={false} className="subtle-card">
            <Text strong>输入 / 输出</Text>
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
    { label: "数据集", values: paper.benchmarks_or_eval.datasets },
    { label: "指标", values: paper.benchmarks_or_eval.metrics },
    { label: "对比方法", values: paper.benchmarks_or_eval.baselines },
    { label: "主要发现", values: compactTexts(paper.benchmarks_or_eval.findings, 92, 4), findings: true },
  ];
  const resultHeadline =
    firstText([paper.reading_digest.result_headline, paper.benchmarks_or_eval.best_results[0], paper.benchmarks_or_eval.findings[0], paper.storyline.outcome], 96) ||
    "暂无前置结果判断。";

  return (
    <SectionCard
      id="evaluation"
      title="实验结果"
      kicker="实验结果"
      strong
      summary={resultHeadline}
    >
      <Card bordered={false} className="surface-card emphasis-card best-result-card">
        <Text className="section-kicker">结论先看</Text>
        <Paragraph className="section-lead">{resultHeadline}</Paragraph>
      </Card>

      {paper.benchmarks_or_eval.experiment_setup_summary ? (
        <Card bordered={false} className="surface-card setup-summary-card">
          <Text className="section-kicker">实验设置摘要</Text>
          <Paragraph className="long-copy">{paper.benchmarks_or_eval.experiment_setup_summary}</Paragraph>
        </Card>
      ) : null}

      <Row gutter={[16, 16]} className="card-grid-row">
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
                      <TooltipTag key={item} label={item} className="chip-tag chip-tag-tone-blue" />
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
  const strengths = compactTexts(paper.editorial_review.strengths, 84, 4);
  const cautions = compactTexts(
    paper.editorial_review.cautions.length ? paper.editorial_review.cautions : paper.limitations,
    84,
    4,
  );

  return (
    <SectionCard
      id="editorial-review"
      title="阅读判断"
      kicker="阅读判断"
      strong
      summary={paper.editorial_review.research_position || paper.editor_note?.summary || "帮助判断值不值得继续读。"}
    >
      <Row gutter={[16, 16]} className="card-grid-row">
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
            {strengths.length ? (
              <Space direction="vertical" size={8} style={{ width: "100%", marginTop: 12 }}>
                {strengths.map((item) => (
                  <Card key={item} bordered={false} className="subtle-card list-card">
                    <Paragraph style={{ marginBottom: 0 }}>{item}</Paragraph>
                  </Card>
                ))}
              </Space>
            ) : (
              <Paragraph type="secondary" style={{ marginTop: 12, marginBottom: 0 }}>
                暂无明确亮点。
              </Paragraph>
            )}
          </Card>
        </Col>
        <Col xs={24} lg={7}>
          <Card bordered={false} className="subtle-card limitations-card">
            <Text strong>需注意</Text>
            {cautions.length ? (
              <Space direction="vertical" size={8} style={{ width: "100%", marginTop: 12 }}>
                {cautions.map((item) => (
                  <Card key={item} bordered={false} className="subtle-card list-card">
                    <Paragraph style={{ marginBottom: 0 }}>{item}</Paragraph>
                  </Card>
                ))}
              </Space>
            ) : (
              <Paragraph type="secondary" style={{ marginTop: 12, marginBottom: 0 }}>
                暂无明确风险提示。
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
    <SectionCard id="comparison" title="对比线索" kicker="对比线索" summary={context.recommended_next_read || "拿谁来比，为什么值得比。"}>
      <Row gutter={[16, 16]} className="card-grid-row">
        <Col xs={24} md={12}>
          <Card bordered={false} className="subtle-card">
            <Text strong>显式对照</Text>
            <div style={{ marginTop: 12 }}>
              <BadgeGroup values={context.explicit_baselines} />
            </div>
          </Card>
        </Col>
        <Col xs={24} md={12}>
          <Card bordered={false} className="subtle-card">
            <Text strong>候选对照路线</Text>
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
                <Text strong>{displayComparisonAspect(item.aspect)}</Text>
                <Paragraph style={{ marginTop: 6, marginBottom: 0 }}>{cleanDisplayText(item.difference, 96)}</Paragraph>
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
          { key: "all", label: "全部" },
          { key: "method", label: "方法" },
          { key: "experiment", label: "实验" },
          { key: "capability", label: "能力" },
          { key: "limitation", label: "局限" },
        ]}
      />
      {filteredClaims.length ? (
        filteredClaims.map((claim, index) => (
          <Card key={`${paper.paper_id}-claim-${index}`} bordered={false} className="claim-card">
            <Flex justify="space-between" align="start" gap={12} wrap="wrap">
              <Paragraph className="claim-text">{claim.claim}</Paragraph>
              <Tag className="chip-tag chip-tag-route-overview">{displayClaimType(claim.type)}</Tag>
            </Flex>
            <Flex wrap="wrap" gap={8}>
              {claim.support.map((item) => (
                <Button key={`${paper.paper_id}-${index}-${item}`} size="small" className="support-chip" onClick={() => onSupportClick(item)}>
                  {item}
                </Button>
              ))}
              {claim.confidence ? <Tag className={chipToneClass(confidenceTone(claim.confidence))}>可信度 {claim.confidence}</Tag> : null}
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
              <Tag className={importanceTagClass(item.importance)}>{item.importance}</Tag>
              <Tag className="chip-tag chip-tag-tone-cyan">{displayFigureRole(item.role)}</Tag>
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
        placeholder="搜索图表编号或说明"
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
            label: `图 (${figureItems.length})`,
            children: figureItems.length ? <Space direction="vertical" size={12} style={{ width: "100%" }}>{figureItems.map(renderItem)}</Space> : <EmptyBlock description="没有命中图条目。" />,
          },
          {
            key: "tables",
            label: `表 (${tableItems.length})`,
            children: tableItems.length ? <Space direction="vertical" size={12} style={{ width: "100%" }}>{tableItems.map(renderItem)}</Space> : <EmptyBlock description="没有命中表条目。" />,
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
              <TooltipText text={item.reason_short || item.reason} as="paragraph" maxChars={50} className="neighbor-reason-short" />
              <Paragraph type="secondary" style={{ marginTop: 6, marginBottom: 0 }}>
                {item.reason}
              </Paragraph>
              {item.relation_hint ? <Paragraph style={{ marginTop: 8, marginBottom: 0 }}>{relationHintLabel(item.relation_hint)}</Paragraph> : null}
            </div>
            <Tag className={scoreLevelTagClass(item.score_level)}>{scoreLevelLabel(item.score_level)}</Tag>
          </Flex>
          <Flex wrap="wrap" gap={8} style={{ marginTop: 10 }}>
            {sharedSignalPreview(item.shared_signals).map((signal) => (
              <TooltipTag key={`${item.paper_id}-${signal}`} label={signal} maxChars={24} className="chip-tag chip-tag-tone-blue" />
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
      label: "核心论断",
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
      label: "相关论文",
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
      label: "JSON / 调试",
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
      title="附录资料"
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
      <Text className="section-kicker">阅读摘要</Text>
      <Title level={4} className="panel-title">
        阅读定位
      </Title>
      <MetaLine label="来源 / 年份" value={`${paper.venue || "未知"} / ${formatYear(paper.year)}`} />
      <MetaLine label="引用数" value={paper.citation_count ?? "暂无"} />
      <MetaLine label="阅读判断" value={paper.editorial_review.verdict || "暂无"} />
      <MetaLine label="推荐路径" value={recommendedRouteLabel(paper.reading_digest.recommended_route)} />
      <MetaLine label="任务" value={<BadgeGroup values={paper.reading_digest.positioning.task} color="gold" />} />
      <MetaLine label="方法" value={<BadgeGroup values={paper.reading_digest.positioning.method} color="green" />} />
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
      <Text className="section-kicker">推荐顺序</Text>
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
      <Text className="section-kicker">链接与标签</Text>
      <MetaLine label="创新类型" value={<BadgeGroup values={paper.reading_digest.positioning.novelty} color="magenta" />} />
      <MetaLine label="模态" value={<BadgeGroup values={paper.reading_digest.positioning.modality} color="processing" />} />
      <MetaLine
        label="外部链接"
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
      { key: "method-core", label: "方法设计" },
      { key: "evaluation", label: "实验结果" },
      { key: "editorial-review", label: "阅读判断" },
      { key: "comparison", label: "对比线索" },
      { key: "materials-zone", label: "附录资料" },
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
