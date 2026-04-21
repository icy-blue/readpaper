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
  ClockCircleOutlined,
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
  formatDate,
  formatYear,
  markdownHref,
  paperRoute,
  scoreLevelLabel,
  sharedSignalPreview,
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
    return "conclusion";
  }
  if (content.includes("figure") || content.includes("table")) {
    return "figures";
  }
  return null;
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

function nonEmpty(values: Array<string | null | undefined>): string[] {
  return values.map((value) => (value ?? "").trim()).filter(Boolean);
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
  extra,
  children,
}: {
  id: string;
  title: string;
  kicker?: string;
  extra?: ReactNode;
  children: ReactNode;
}) {
  return (
    <Card id={id} bordered={false} className="surface-card reading-section" extra={extra}>
      {kicker ? <Text className="section-kicker">{kicker}</Text> : null}
      <Title level={3} className="section-title">
        {title}
      </Title>
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

function HeroHeader({ paper }: { paper: PaperRecord }) {
  const primaryTags = compactList(
    [
      ...paper.research_tags.methods,
      ...paper.topics.map((topic) => topic.name),
      ...paper.research_tags.tasks,
      ...paper.research_tags.themes,
    ],
    8,
  );

  return (
    <Card bordered={false} className="hero-surface detail-hero">
      <Space direction="vertical" size={18} style={{ width: "100%" }}>
        <Flex wrap="wrap" gap={8}>
          <Tag color="blue">{paper.venue || "未知 venue"}</Tag>
          <Tag color="cyan">{formatYear(paper.year)}</Tag>
          {paper.citation_count !== null ? <Tag color="gold">Citations {paper.citation_count}</Tag> : null}
          {paper.summary.worth_long_term_graph ? <Tag color="success">Worth Tracking</Tag> : null}
        </Flex>

        <div>
          <Title className="detail-display-title">{paper.title}</Title>
          <Paragraph className="author-line">
            {paper.authors.length ? paper.authors.join(" / ") : "作者信息暂缺"}
            {" · "}
            {paper.venue || "未知 venue"}
            {" · "}
            {formatYear(paper.year)}
          </Paragraph>
          <Paragraph className="hero-one-liner">
            {paper.summary.one_liner || "暂无一句话总结。"}
          </Paragraph>
        </div>

        <ExternalLinkButtons paper={paper} />

        <div className="hero-tag-block">
          <Text className="hero-tag-label">Primary Tags</Text>
          <Flex wrap="wrap" gap={8} className="hero-tag-row">
            {primaryTags.length ? (
              primaryTags.map((tag) => (
                <Tag key={`${paper.paper_id}-${tag}`} className="soft-tag">
                  {tag}
                </Tag>
              ))
            ) : (
              <Text type="secondary">暂无主标签</Text>
            )}
          </Flex>
        </div>
      </Space>
    </Card>
  );
}

function CoverageStatusBar({ paper }: { paper: PaperRecord }) {
  const status = paper.translate_status;
  const completion =
    status.completed_unit_count !== null && status.total_unit_count !== null
      ? `${status.completed_unit_count}/${status.total_unit_count}`
      : "未知";

  return (
    <Card bordered={false} className={`surface-card coverage-strip ${status.is_partial ? "is-partial" : ""}`}>
      <Flex justify="space-between" align="center" gap={16} wrap="wrap">
        <Flex wrap="wrap" gap={16}>
          <Text>阅读状态：{status.state || "未知"}</Text>
          <Text>覆盖：{completion}</Text>
          <Text>{status.is_partial ? "部分完成" : "完整记录"}</Text>
          <Text>最近整理：{formatDate(paper.translate_created_at)}</Text>
        </Flex>
        <Tag icon={<ClockCircleOutlined />} color={status.is_partial ? "warning" : "success"}>
          {status.is_partial ? "部分完成" : "已完成"}
        </Tag>
      </Flex>
      {status.coverage_notes.length ? (
        <Collapse
          ghost
          items={[
            {
              key: "coverage-notes",
              label: "展开覆盖说明",
              children: (
                <Space direction="vertical" size={8} style={{ width: "100%" }}>
                  {status.coverage_notes.map((note) => (
                    <Paragraph key={note} style={{ marginBottom: 0 }}>
                      {note}
                    </Paragraph>
                  ))}
                </Space>
              ),
            },
          ]}
        />
      ) : null}
    </Card>
  );
}

function StorylineStrip({ paper }: { paper: PaperRecord }) {
  const items = [
    { title: "问题", content: paper.storyline.problem },
    { title: "方法", content: paper.storyline.method },
    { title: "结果", content: paper.storyline.outcome },
  ].filter((item) => item.content);

  if (!items.length) {
    return null;
  }

  return (
    <Card bordered={false} className="surface-card storyline-strip">
      <Row gutter={[16, 16]}>
        {items.map((item) => (
          <Col xs={24} md={8} key={item.title}>
            <div className="storyline-item">
              <Text className="section-kicker">{item.title}</Text>
              <Paragraph className="storyline-copy">{item.content}</Paragraph>
            </div>
          </Col>
        ))}
      </Row>
    </Card>
  );
}

function QuickScanCards({ paper }: { paper: PaperRecord }) {
  const cards = [
    {
      title: "研究问题",
      content: paper.research_problem.summary || "暂无研究问题摘要。",
      tags: compactList([...paper.research_problem.gaps, ...paper.research_tags.tasks], 3),
    },
    {
      title: "核心方法",
      content: paper.method_core.approach_summary || "暂无方法概述。",
      tags: compactList([...paper.research_tags.methods, ...paper.method_core.ingredients], 3),
    },
    {
      title: "关键结果",
      content: paper.benchmarks_or_eval.best_results[0] || paper.benchmarks_or_eval.findings[0] || "暂无关键结果。",
      tags: compactList(
        [...paper.benchmarks_or_eval.datasets, ...paper.benchmarks_or_eval.metrics, ...paper.benchmarks_or_eval.baselines],
        3,
      ),
    },
    {
      title: "阅读判断",
      content: paper.summary.research_value.summary || "暂无阅读判断。",
      tags: compactList([...paper.summary.research_value.points, ...paper.novelty_type], 3),
    },
  ];

  return (
    <Row gutter={[16, 16]} className="quick-card-grid">
      {cards.map((item) => (
        <Col xs={24} md={12} xl={6} key={item.title}>
          <Card bordered={false} className="surface-card quick-read-card standardized">
            <Text className="section-kicker">{item.title}</Text>
            <Paragraph className="quick-card-content">{truncateText(item.content, 90) || "暂无内容。"}</Paragraph>
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
    <SectionCard id="research-overview" title="研究概述" kicker="是什么">
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card bordered={false} className="surface-card emphasis-card">
            <Text className="section-kicker">研究问题</Text>
            <Paragraph className="section-lead">{paper.research_problem.summary || "暂无研究问题摘要。"}</Paragraph>
            {paper.research_problem.goal ? (
              <Alert
                type="info"
                showIcon
                className="compact-alert"
                message="研究目标"
                description={paper.research_problem.goal}
              />
            ) : null}
            {paper.research_problem.gaps.length ? (
              <Space direction="vertical" size={8} style={{ width: "100%", marginTop: 12 }}>
                {paper.research_problem.gaps.map((gap) => (
                  <Card key={gap} bordered={false} className="subtle-card list-card">
                    <Paragraph style={{ marginBottom: 0 }}>{gap}</Paragraph>
                  </Card>
                ))}
              </Space>
            ) : null}
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card bordered={false} className="surface-card">
            <Text className="section-kicker">核心贡献</Text>
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
        </Col>
      </Row>

      <Tabs
        defaultActiveKey={paper.abstract_zh ? "zh" : "raw"}
        items={[
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
        ]}
      />
    </SectionCard>
  );
}

function MethodCoreSection({ paper }: { paper: PaperRecord }) {
  return (
    <SectionCard id="method-core" title="方法核心" kicker="怎么做">
      <Card bordered={false} className="surface-card emphasis-card">
        <Text className="section-kicker">一句话方法总结</Text>
        <Paragraph className="section-lead">{paper.method_core.approach_summary || "暂无方法概述。"}</Paragraph>
      </Card>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card bordered={false} className="subtle-card">
            <Text strong>流程</Text>
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
            <Text strong>创新点</Text>
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
        <Col xs={24} lg={8}>
          <Card bordered={false} className="subtle-card">
            <Text strong>Ingredients</Text>
            <div style={{ marginTop: 12 }}>
              <BadgeGroup values={paper.method_core.ingredients} />
            </div>
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card bordered={false} className="subtle-card">
            <Text strong>Representation</Text>
            <div style={{ marginTop: 12 }}>
              <BadgeGroup values={paper.method_core.representation} />
            </div>
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card bordered={false} className="subtle-card">
            <Text strong>Supervision</Text>
            <div style={{ marginTop: 12 }}>
              <BadgeGroup values={paper.method_core.supervision} />
            </div>
          </Card>
        </Col>
      </Row>

      <Card bordered={false} className="subtle-card">
        <Text strong>与相近方法差异</Text>
        {paper.method_core.differences.length ? (
          <Space direction="vertical" size={8} style={{ width: "100%", marginTop: 12 }}>
            {paper.method_core.differences.map((item) => (
              <Card key={item} bordered={false} className="subtle-card list-card">
                <Paragraph style={{ marginBottom: 0 }}>{item}</Paragraph>
              </Card>
            ))}
          </Space>
        ) : (
          <Paragraph type="secondary" style={{ marginTop: 12, marginBottom: 0 }}>
            暂无结构化差异说明。
          </Paragraph>
        )}
      </Card>
    </SectionCard>
  );
}

function InputOutputSection({ paper }: { paper: PaperRecord }) {
  const cards = [
    { title: "输入", values: paper.inputs_outputs.inputs },
    { title: "输出", values: paper.inputs_outputs.outputs },
    { title: "模态", values: paper.inputs_outputs.modalities },
    { title: "任务类型", values: paper.research_tags.tasks },
  ];

  return (
    <SectionCard id="input-output" title="输入输出与任务" kicker="任务边界">
      <Row gutter={[16, 16]}>
        {cards.map((card) => (
          <Col xs={24} md={12} xl={6} key={card.title}>
            <Card bordered={false} className="subtle-card">
              <Text strong>{card.title}</Text>
              <div style={{ marginTop: 12 }}>
                <BadgeGroup values={card.values} />
              </div>
            </Card>
          </Col>
        ))}
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} md={12}>
          <Card bordered={false} className="subtle-card">
            <Text strong>Representations</Text>
            <div style={{ marginTop: 12 }}>
              <BadgeGroup values={paper.research_tags.representations} color="processing" />
            </div>
          </Card>
        </Col>
        <Col xs={24} md={12}>
          <Card bordered={false} className="subtle-card">
            <Text strong>Task Tags</Text>
            <div style={{ marginTop: 12 }}>
              <BadgeGroup values={paper.research_tags.themes} color="gold" />
            </div>
          </Card>
        </Col>
      </Row>
    </SectionCard>
  );
}

function KeyClaimsSection({
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
    <SectionCard id="claims" title="关键论断与证据" kicker="怎么证明">
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
        <Space direction="vertical" size={16} style={{ width: "100%" }}>
          {filteredClaims.map((claim, index) => (
            <Card key={`${paper.paper_id}-claim-${index}`} bordered={false} className="claim-card">
              <Flex justify="space-between" align="start" gap={12} wrap="wrap">
                <Paragraph className="claim-text">{claim.claim}</Paragraph>
                <Tag color="geekblue">{claim.type}</Tag>
              </Flex>
              <Flex wrap="wrap" gap={8}>
                {claim.support.map((item) => (
                  <Button
                    key={`${paper.paper_id}-${index}-${item}`}
                    size="small"
                    className="support-chip"
                    onClick={() => onSupportClick(item)}
                  >
                    {item}
                  </Button>
                ))}
                {claim.confidence ? <Tag color={confidenceTone(claim.confidence)}>可信度 {claim.confidence}</Tag> : null}
              </Flex>
            </Card>
          ))}
        </Space>
      ) : (
        <EmptyBlock description="当前筛选下暂无关键论断。" />
      )}
    </SectionCard>
  );
}

function EvaluationSection({ paper }: { paper: PaperRecord }) {
  const groups = [
    { label: "Datasets", values: paper.benchmarks_or_eval.datasets },
    { label: "Metrics", values: paper.benchmarks_or_eval.metrics },
    { label: "Baselines", values: paper.benchmarks_or_eval.baselines },
    { label: "Findings", values: paper.benchmarks_or_eval.findings, findings: true },
  ];

  return (
    <SectionCard id="evaluation" title="实验与评估" kicker="结果怎样">
      {paper.benchmarks_or_eval.best_results[0] ? (
        <Card bordered={false} className="surface-card emphasis-card best-result-card">
          <Text className="section-kicker">高亮结果</Text>
          <Paragraph className="section-lead">{paper.benchmarks_or_eval.best_results[0]}</Paragraph>
        </Card>
      ) : null}

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

function ConclusionSection({ paper }: { paper: PaperRecord }) {
  return (
    <SectionCard id="conclusion" title="局限 / 作者结论 / 编辑判断" kicker="怎么判断">
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={8}>
          <Card bordered={false} className="subtle-card limitations-card">
            <Text strong>局限</Text>
            {paper.limitations.length ? (
              <Space direction="vertical" size={8} style={{ width: "100%", marginTop: 12 }}>
                {paper.limitations.map((item) => (
                  <Card key={item} bordered={false} className="subtle-card list-card">
                    <Paragraph style={{ marginBottom: 0 }}>{item}</Paragraph>
                  </Card>
                ))}
              </Space>
            ) : (
              <Paragraph type="secondary" style={{ marginTop: 12, marginBottom: 0 }}>
                暂无明确记录的局限。
              </Paragraph>
            )}
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card bordered={false} className="subtle-card">
            <Text strong>作者结论</Text>
            <Paragraph className="long-copy" style={{ marginTop: 12, marginBottom: 0 }}>
              {paper.author_conclusion || "暂无作者结论摘录。"}
            </Paragraph>
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card bordered={false} className="editor-note-card emphasis-card">
            <Text strong>编辑判断</Text>
            <Text type="secondary">整理者观点</Text>
            <Paragraph className="long-copy" style={{ marginTop: 12, marginBottom: 0 }}>
              {paper.editor_note?.summary || "暂无编辑判断。"}
            </Paragraph>
            {paper.editor_note?.points.length ? (
              <Space direction="vertical" size={8} style={{ width: "100%", marginTop: 12 }}>
                {paper.editor_note.points.map((item) => (
                  <Card key={item} bordered={false} className="subtle-card list-card">
                    <Paragraph style={{ marginBottom: 0 }}>{item}</Paragraph>
                  </Card>
                ))}
              </Space>
            ) : null}
          </Card>
        </Col>
      </Row>
    </SectionCard>
  );
}

function FigureTableSection({
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
    <Card
      key={item.label}
      bordered={false}
      className={`subtle-card figure-item-card ${highlightedLabel === item.label ? "is-highlighted" : ""}`}
    >
      <Flex justify="space-between" align="start" gap={12} wrap="wrap">
        <Text strong>{item.label}</Text>
        <Flex wrap="wrap" gap={8}>
          <Tag color={item.importance === "high" ? "gold" : item.importance === "medium" ? "blue" : "default"}>
            {item.importance}
          </Tag>
          <Tag>{item.role}</Tag>
        </Flex>
      </Flex>
      <Paragraph className="long-copy" style={{ marginTop: 8, marginBottom: 0 }}>
        {item.caption}
      </Paragraph>
    </Card>
  );

  return (
    <SectionCard
      id="figures"
      title="图表索引"
      kicker="证据入口"
      extra={
        <Input
          allowClear
          placeholder="搜索 Figure / Table label"
          prefix={<FileSearchOutlined />}
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          className="compact-search"
        />
      }
    >
      {!paper.figure_table_index.figures.length && !paper.figure_table_index.tables.length ? (
        <EmptyBlock description="暂无图表索引。" />
      ) : (
        <Tabs
          activeKey={activeKey}
          onChange={(value) => setActiveKey(value as "figures" | "tables")}
          items={[
            {
              key: "figures",
              label: `Figures (${figureItems.length})`,
              children: figureItems.length ? (
                <Space direction="vertical" size={12} style={{ width: "100%" }}>
                  {figureItems.map(renderItem)}
                </Space>
              ) : (
                <EmptyBlock description="没有命中 Figure。" />
              ),
            },
            {
              key: "tables",
              label: `Tables (${tableItems.length})`,
              children: tableItems.length ? (
                <Space direction="vertical" size={12} style={{ width: "100%" }}>
                  {tableItems.map(renderItem)}
                </Space>
              ) : (
                <EmptyBlock description="没有命中 Table。" />
              ),
            },
          ]}
        />
      )}
    </SectionCard>
  );
}

function ComparisonSection({ paper }: { paper: PaperRecord }) {
  const context = paper.comparison_context;

  return (
    <SectionCard id="comparison" title="对比阅读" kicker="拿谁来比">
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

      <Card bordered={false} className="surface-card">
        <Text className="section-kicker">对比维度</Text>
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

      {context.recommended_next_read ? (
        <Card bordered={false} className="surface-card emphasis-card">
          <Text className="section-kicker">一句推荐</Text>
          <Paragraph className="section-lead">{context.recommended_next_read}</Paragraph>
        </Card>
      ) : null}
    </SectionCard>
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
              {item.relation_hint ? (
                <Paragraph style={{ marginTop: 8, marginBottom: 0 }}>{relationHintLabel(item.relation_hint)}</Paragraph>
              ) : null}
            </div>
            <Tag color={item.score_level === "high" ? "gold" : item.score_level === "medium" ? "blue" : "default"}>
              {scoreLevelLabel(item.score_level)}
            </Tag>
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

function NeighborSection({ paper, payload }: { paper: PaperRecord; payload: SitePayload }) {
  return (
    <SectionCard id="neighbors" title="相邻论文" kicker="下一篇看什么">
      <Tabs
        items={payload.navigation.neighbor_tabs.map((tab) => ({
          key: tab.key,
          label: tab.label,
          children: <NeighborList items={paper.paper_neighbors[tab.key]} />,
        }))}
      />
    </SectionCard>
  );
}

function OutlineCard({ items, activeId }: { items: Array<{ key: string; label: string }>; activeId: string }) {
  return (
    <Card bordered={false} className="surface-card sidebar-card">
      <Text className="section-kicker">页面目录</Text>
      <Space direction="vertical" size={8} style={{ width: "100%", marginTop: 14 }}>
        {items.map((item) => (
          <Button
            key={item.key}
            block
            className={item.key === activeId ? "toc-button is-active" : "toc-button"}
            onClick={() => scrollToId(item.key)}
          >
            {item.label}
          </Button>
        ))}
      </Space>
    </Card>
  );
}

function SidebarMetaCard({ paper }: { paper: PaperRecord }) {
  return (
    <Card bordered={false} className="surface-card sidebar-card">
      <Text className="section-kicker">元信息</Text>
      <Title level={4} className="panel-title">
        阅读定位
      </Title>
      <MetaLine label="Venue / Year" value={`${paper.venue || "未知"} / ${formatYear(paper.year)}`} />
      <MetaLine label="Citations" value={paper.citation_count ?? "暂无"} />
      <MetaLine label="Novelty" value={<BadgeGroup values={paper.novelty_type} />} />
      <MetaLine label="Modalities" value={<BadgeGroup values={paper.research_tags.modalities} color="processing" />} />
      <MetaLine label="Representations" value={<BadgeGroup values={paper.research_tags.representations} color="purple" />} />
    </Card>
  );
}

function SidebarTagsLinksCard({ paper }: { paper: PaperRecord }) {
  const links = firstExternalLinks(paper.links);

  return (
    <Card bordered={false} className="surface-card sidebar-card">
      <Text className="section-kicker">标签与外链</Text>
      <MetaLine label="Topics" value={<BadgeGroup values={paper.topics.map((topic) => topic.name)} color="magenta" />} />
      <MetaLine label="Tasks" value={<BadgeGroup values={paper.research_tags.tasks} color="gold" />} />
      <MetaLine label="Methods" value={<BadgeGroup values={paper.research_tags.methods} color="green" />} />
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

function RetrievalProfileSection({ paper }: { paper: PaperRecord }) {
  return (
    <SectionCard id="retrieval-profile" title="检索画像" kicker="折叠附加信息">
      <Collapse
        items={[
          {
            key: "retrieval-profile-panel",
            label: "查看检索画像",
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
        ]}
      />
    </SectionCard>
  );
}

function DebugJsonSection({ paper }: { paper: PaperRecord }) {
  const { message } = AntApp.useApp();

  const handleCopy = async () => {
    try {
      await copyText(JSON.stringify(paper, null, 2));
      message.success("已复制结构化 JSON。");
    } catch {
      message.error("复制失败。");
    }
  };

  return (
    <SectionCard
      id="debug-json"
      title="原始结构化记录"
      kicker="Debug"
      extra={
        <Button icon={<CopyOutlined />} onClick={handleCopy}>
          复制 JSON
        </Button>
      }
    >
      <Collapse
        items={[
          {
            key: "debug-json-panel",
            label: "查看只读 JSON",
            children: <pre className="debug-json-block">{JSON.stringify(paper, null, 2)}</pre>,
          },
        ]}
      />
    </SectionCard>
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
      { key: "research-overview", label: "研究概述" },
      { key: "method-core", label: "方法核心" },
      { key: "input-output", label: "输入输出" },
      { key: "claims", label: "关键论断" },
      { key: "evaluation", label: "实验评估" },
      { key: "conclusion", label: "局限与结论" },
      { key: "figures", label: "图表索引" },
      { key: "comparison", label: "对比阅读" },
      { key: "neighbors", label: "相邻论文" },
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
      scrollToId("figures");
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
      <SidebarMetaCard paper={paper} />
      <SidebarTagsLinksCard paper={paper} />
    </Space>
  );

  return (
    <div className="page-stack">
      <HeroHeader paper={paper} />
      <CoverageStatusBar paper={paper} />
      <StorylineStrip paper={paper} />
      <QuickScanCards paper={paper} />

      <Row gutter={[24, 24]} align="top">
        <Col xs={24} xl={17}>
          <Space direction="vertical" size={18} style={{ width: "100%" }}>
            <ResearchOverviewSection paper={paper} />
            <MethodCoreSection paper={paper} />
            <InputOutputSection paper={paper} />
            <KeyClaimsSection paper={paper} onSupportClick={handleSupportClick} />
            <EvaluationSection paper={paper} />
            <ConclusionSection paper={paper} />
            <FigureTableSection
              paper={paper}
              activeKey={activeFigureTab}
              setActiveKey={(key) => {
                setActiveFigureTab(key);
                setHighlightedFigureLabel(null);
              }}
              highlightedLabel={highlightedFigureLabel}
            />
            <ComparisonSection paper={paper} />
            <NeighborSection paper={paper} payload={payload} />
            {!screens.xl ? sidebar : null}
            <RetrievalProfileSection paper={paper} />
            {debugMode ? <DebugJsonSection paper={paper} /> : null}
          </Space>
        </Col>

        <Col xs={24} xl={7}>
          {screens.xl ? <div className="sticky-column">{sidebar}</div> : null}
        </Col>
      </Row>
    </div>
  );
}
