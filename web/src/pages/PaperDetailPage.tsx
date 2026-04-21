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
  CheckCircleFilled,
  ClockCircleOutlined,
  CopyOutlined,
  ExperimentOutlined,
  FileSearchOutlined,
  LinkOutlined,
  NodeIndexOutlined,
  ReadOutlined,
} from "@ant-design/icons";
import { useMemo, useState, type ReactNode } from "react";
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
  relationTargetRoute,
  relationTargetTitle,
  scoreBand,
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
  if (content.includes("abstract") || content.includes("summary")) {
    return "summary-overview";
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
    <Flex vertical gap={10} className="hero-actions">
      <Button icon={<ArrowLeftOutlined />} onClick={() => navigate("/")}>
        返回首页
      </Button>
      {markdownLink ? (
        <Button href={markdownLink} target="_blank" icon={<BookOutlined />}>
          Markdown
        </Button>
      ) : null}
      {links.map((item) => (
        <Button key={item.key} href={item.href} target="_blank" icon={<LinkOutlined />}>
          {item.label}
        </Button>
      ))}
    </Flex>
  );
}

function CoverageStatusBar({ paper }: { paper: PaperRecord }) {
  const status = paper.translate_status;
  const completion =
    status.completed_unit_count !== null && status.total_unit_count !== null
      ? `${status.completed_unit_count} / ${status.total_unit_count}`
      : "未知";

  return (
    <Card bordered={false} className={`surface-card coverage-card ${status.is_partial ? "is-partial" : ""}`}>
      <Flex justify="space-between" align="start" gap={20} wrap="wrap">
        <Flex gap={24} wrap="wrap">
          <div>
            <Text className="section-kicker">整理时间</Text>
            <Paragraph className="status-value">{formatDate(paper.translate_created_at)}</Paragraph>
          </div>
          <div>
            <Text className="section-kicker">当前状态</Text>
            <Paragraph className="status-value">{status.state || "未知"}</Paragraph>
          </div>
          <div>
            <Text className="section-kicker">完成度</Text>
            <Paragraph className="status-value">{completion}</Paragraph>
          </div>
        </Flex>
        <Flex gap={8} wrap="wrap" justify="end">
          <Tag icon={<ClockCircleOutlined />} color={status.is_partial ? "warning" : "success"}>
            {status.is_partial ? "部分完成" : "完整记录"}
          </Tag>
          {status.active_scope ? <Tag color="processing">当前范围：{status.active_scope}</Tag> : null}
        </Flex>
      </Flex>
      {status.coverage_notes.length ? (
        <Collapse
          ghost
          style={{ marginTop: 8 }}
          items={[
            {
              key: "coverage-notes",
              label: "查看覆盖说明",
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

function HeroHeader({ paper }: { paper: PaperRecord }) {
  const quickCards = [
    {
      title: "研究问题",
      content: paper.research_problem || "暂无研究问题摘要。",
      icon: <ReadOutlined />,
    },
    {
      title: "一句话结论",
      content: paper.summary.one_liner || "暂无一句话结论。",
      icon: <CheckCircleFilled />,
    },
    {
      title: "核心方法",
      content: paper.method_core.approach || "暂无方法摘要。",
      icon: <ExperimentOutlined />,
    },
    {
      title: "长期跟踪价值",
      content: paper.summary.research_value || "暂无研究价值说明。",
      icon: <NodeIndexOutlined />,
    },
  ];

  return (
    <Card bordered={false} className="hero-surface detail-hero">
      <Row gutter={[24, 24]}>
        <Col xs={24} xl={17}>
          <Text className="section-kicker">Paper Overview</Text>
          <Title className="detail-display-title">{paper.title}</Title>
          {paper.authors.length ? (
            <Paragraph className="author-line">{paper.authors.join(" / ")}</Paragraph>
          ) : (
            <Paragraph className="author-line is-muted">作者信息暂缺</Paragraph>
          )}
          <Paragraph className="hero-description detail-one-liner">
            {paper.summary.one_liner || "暂无一句话结论。"}
          </Paragraph>
          <Flex wrap="wrap" gap={8} className="meta-badge-row">
            <Tag color="blue">
              {paper.venue || "未知 venue"} / {formatYear(paper.year)}
            </Tag>
            {paper.citation_count !== null ? <Tag color="cyan">Citations {paper.citation_count}</Tag> : null}
            {paper.summary.worth_long_term_graph ? <Tag color="success">值得进入长期知识图谱</Tag> : null}
            {paper.topics.map((topic) => (
              <Tag key={`${paper.paper_id}-topic-${topic.slug}`} color="magenta">
                {topic.name}
              </Tag>
            ))}
            {compactList(paper.research_tags.themes, 3).map((theme) => (
              <Tag key={`${paper.paper_id}-theme-${theme}`} color="green">
                {theme}
              </Tag>
            ))}
            {compactList(paper.research_tags.tasks, 3).map((task) => (
              <Tag key={`${paper.paper_id}-task-${task}`} color="gold">
                {task}
              </Tag>
            ))}
          </Flex>
        </Col>
        <Col xs={24} xl={7}>
          <ExternalLinkButtons paper={paper} />
        </Col>
      </Row>

      <Row gutter={[16, 16]} className="quick-card-grid">
        {quickCards.map((item) => (
          <Col xs={24} md={12} xl={6} key={item.title}>
            <Card bordered={false} className="surface-card quick-read-card">
              <Text className="section-kicker">{item.title}</Text>
              <Paragraph className="quick-card-content">{item.content}</Paragraph>
            </Card>
          </Col>
        ))}
      </Row>
    </Card>
  );
}

function SummarySection({ paper }: { paper: PaperRecord }) {
  return (
    <SectionCard id="summary-overview" title="摘要与定位" kicker="理解">
      <div className="content-block">
        <Text strong>快速摘要</Text>
        <Paragraph>{paper.summary.abstract_summary || paper.summary.one_liner || "暂无快速摘要。"}</Paragraph>
        {paper.summary.research_value ? (
          <Alert type="success" showIcon message="研究价值" description={paper.summary.research_value} />
        ) : null}
      </div>

      <div className="content-block">
        <Text strong>研究问题</Text>
        <Paragraph>{paper.research_problem || "暂无研究问题摘要。"}</Paragraph>
      </div>

      <div className="content-block">
        <Text strong>核心贡献</Text>
        {paper.core_contributions.length ? (
          <Space direction="vertical" size={10} style={{ width: "100%", marginTop: 10 }}>
            {paper.core_contributions.map((item) => (
              <Card key={item} bordered={false} className="subtle-card">
                <Paragraph style={{ marginBottom: 0 }}>{item}</Paragraph>
              </Card>
            ))}
          </Space>
        ) : (
          <EmptyBlock description="暂无核心贡献整理。" />
        )}
      </div>

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
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card bordered={false} className="surface-card method-highlight-card">
            <Text className="section-kicker">核心做法</Text>
            <Paragraph className="long-copy">{paper.method_core.approach || "暂无核心做法总结。"}</Paragraph>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card bordered={false} className="surface-card method-highlight-card accent">
            <Text className="section-kicker">方法创新</Text>
            <Paragraph className="long-copy">{paper.method_core.innovation || "暂无方法创新总结。"}</Paragraph>
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={8}>
          <Card bordered={false} className="subtle-card">
            <Text strong>Ingredients</Text>
            <div style={{ marginTop: 10 }}>
              <BadgeGroup values={paper.method_core.ingredients} />
            </div>
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card bordered={false} className="subtle-card">
            <Text strong>Representation</Text>
            <div style={{ marginTop: 10 }}>
              <BadgeGroup values={paper.method_core.representation} />
            </div>
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card bordered={false} className="subtle-card">
            <Text strong>Supervision</Text>
            <div style={{ marginTop: 10 }}>
              <BadgeGroup values={paper.method_core.supervision} />
            </div>
          </Card>
        </Col>
      </Row>

      <div className="content-block">
        <Text strong>与相近方法差异</Text>
        {paper.method_core.differences.length ? (
          <Space direction="vertical" size={10} style={{ width: "100%", marginTop: 10 }}>
            {paper.method_core.differences.map((item) => (
              <Card key={item} bordered={false} className="subtle-card">
                <Paragraph style={{ marginBottom: 0 }}>{item}</Paragraph>
              </Card>
            ))}
          </Space>
        ) : (
          <Paragraph type="secondary">暂无明确差异提示。</Paragraph>
        )}
      </div>
    </SectionCard>
  );
}

function InputOutputSection({ paper }: { paper: PaperRecord }) {
  return (
    <SectionCard id="input-output" title="输入输出与任务设置" kicker="任务边界">
      <Row gutter={[16, 16]}>
        <Col xs={24} md={8}>
          <Card bordered={false} className="subtle-card">
            <Text strong>输入</Text>
            <div style={{ marginTop: 12 }}>
              <BadgeGroup values={paper.inputs_outputs.inputs} />
            </div>
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card bordered={false} className="subtle-card">
            <Text strong>输出</Text>
            <div style={{ marginTop: 12 }}>
              <BadgeGroup values={paper.inputs_outputs.outputs} />
            </div>
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card bordered={false} className="subtle-card">
            <Text strong>模态</Text>
            <div style={{ marginTop: 12 }}>
              <BadgeGroup values={paper.inputs_outputs.modalities} color="processing" />
            </div>
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} md={12}>
          <Card bordered={false} className="subtle-card">
            <Text strong>Tasks</Text>
            <div style={{ marginTop: 12 }}>
              <BadgeGroup values={paper.research_tags.tasks} color="gold" />
            </div>
          </Card>
        </Col>
        <Col xs={24} md={12}>
          <Card bordered={false} className="subtle-card">
            <Text strong>Representations</Text>
            <div style={{ marginTop: 12 }}>
              <BadgeGroup values={paper.research_tags.representations} color="purple" />
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
  return (
    <SectionCard id="claims" title="关键论断与证据" kicker="怎么证明">
      {paper.key_claims.length ? (
        <Space direction="vertical" size={16} style={{ width: "100%" }}>
          {paper.key_claims.map((claim, index) => (
            <Card key={`${paper.paper_id}-claim-${index}`} bordered={false} className="claim-card">
              <Paragraph className="claim-text">{claim.claim}</Paragraph>
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
        <EmptyBlock description="暂无关键论断。" />
      )}
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
    <SectionCard id="evaluation" title="实验与评估" kicker="可验证">
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
                  <Space direction="vertical" size={10} style={{ width: "100%", marginTop: 12 }}>
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
    <SectionCard id="conclusion" title="局限、作者结论与编者按" kicker="怎么看待">
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={8}>
          <Card bordered={false} className="subtle-card limitations-card">
            <Text strong>局限</Text>
            {paper.limitations.length ? (
              <Space direction="vertical" size={10} style={{ width: "100%", marginTop: 12 }}>
                {paper.limitations.map((item) => (
                  <Paragraph key={item} style={{ marginBottom: 0 }}>
                    {item}
                  </Paragraph>
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
          <Card bordered={false} className="editor-note-card">
            <Text strong>编者按</Text>
            <Paragraph className="long-copy" style={{ marginTop: 12, marginBottom: 0 }}>
              {paper.editor_note || "暂无编者按。"}
            </Paragraph>
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
      <Text strong>{item.label}</Text>
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

function OutlineCard({ items }: { items: Array<{ key: string; label: string }> }) {
  return (
    <Card bordered={false} className="surface-card sidebar-card">
      <Text className="section-kicker">页面目录</Text>
      <Space direction="vertical" size={8} style={{ width: "100%", marginTop: 14 }}>
        {items.map((item) => (
          <Button key={item.key} block onClick={() => scrollToId(item.key)}>
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
      <MetaLine label="Methods" value={<BadgeGroup values={paper.research_tags.methods} color="gold" />} />
      <MetaLine label="Modalities" value={<BadgeGroup values={paper.research_tags.modalities} color="processing" />} />
      <MetaLine label="Representations" value={<BadgeGroup values={paper.research_tags.representations} color="purple" />} />
    </Card>
  );
}

function SidebarTopicCard({ paper }: { paper: PaperRecord }) {
  return (
    <Card bordered={false} className="surface-card sidebar-card">
      <Text className="section-kicker">Topic / Tag</Text>
      <Title level={4} className="panel-title">
        延展导航
      </Title>
      <MetaLine
        label="Topics"
        value={
          paper.topics.length ? (
            <Flex wrap="wrap" gap={8}>
              {paper.topics.map((topic) => (
                <Tag key={topic.slug} color="magenta">
                  {topic.name}
                </Tag>
              ))}
            </Flex>
          ) : (
            "暂无"
          )
        }
      />
      <MetaLine label="Themes" value={<BadgeGroup values={paper.research_tags.themes} color="green" />} />
      <MetaLine label="Tasks" value={<BadgeGroup values={paper.research_tags.tasks} color="gold" />} />
    </Card>
  );
}

function SidebarComparisonCard({ paper }: { paper: PaperRecord }) {
  return (
    <Card bordered={false} className="surface-card sidebar-card">
      <Text className="section-kicker">对比阅读线索</Text>
      <MetaLine label="Baselines" value={<BadgeGroup values={paper.comparison_context.explicit_baselines} />} />
      <MetaLine label="Contrast methods" value={<BadgeGroup values={paper.comparison_context.contrast_methods} />} />
      <MetaLine
        label="差异提示"
        value={
          paper.comparison_context.contrast_notes.length ? (
            <Space direction="vertical" size={8} style={{ width: "100%" }}>
              {paper.comparison_context.contrast_notes.map((item) => (
                <Paragraph key={item} style={{ marginBottom: 0 }}>
                  {item}
                </Paragraph>
              ))}
            </Space>
          ) : (
            "暂无"
          )
        }
      />
    </Card>
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
          <Flex justify="space-between" align="start" gap={12}>
            <div style={{ minWidth: 0 }}>
              <Link to={paperRoute(item.route_path, item.paper_id)} className="paper-link small">
                {item.title}
              </Link>
              <Paragraph type="secondary" style={{ marginTop: 6, marginBottom: 0 }}>
                {item.reason}
              </Paragraph>
              {item.relation_hint ? (
                <Paragraph style={{ marginTop: 8, marginBottom: 0 }}>{item.relation_hint}</Paragraph>
              ) : null}
            </div>
            <Tag color="geekblue">{scoreBand(item.score)}</Tag>
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

function SidebarNeighborsCard({ paper, payload }: { paper: PaperRecord; payload: SitePayload }) {
  return (
    <Card bordered={false} className="surface-card sidebar-card">
      <Text className="section-kicker">相邻论文</Text>
      <Tabs
        items={payload.navigation.neighbor_tabs.map((tab) => ({
          key: tab.key,
          label: tab.label,
          children: <NeighborList items={paper.paper_neighbors[tab.key]} />,
        }))}
      />
    </Card>
  );
}

function SidebarRelationsCard({ paper, payload }: { paper: PaperRecord; payload: SitePayload }) {
  const items = paper.paper_relations.slice(0, 5);
  return (
    <Card bordered={false} className="surface-card sidebar-card">
      <Text className="section-kicker">关系图谱入口</Text>
      {items.length ? (
        <Space direction="vertical" size={10} style={{ width: "100%", marginTop: 12 }}>
          {items.map((item) => {
            const route = relationTargetRoute(payload, item);
            const title = relationTargetTitle(payload, item);
            return (
              <Card key={`${item.target_paper_id}-${item.relation_type}`} bordered={false} className="subtle-card">
                <Text strong>{item.relation_type}</Text>
                <Paragraph style={{ marginTop: 6, marginBottom: 6 }}>
                  {route ? <Link to={route}>{title}</Link> : title}
                </Paragraph>
                <Paragraph type="secondary" style={{ marginBottom: 0 }}>
                  {item.description}
                </Paragraph>
              </Card>
            );
          })}
        </Space>
      ) : (
        <Paragraph type="secondary" style={{ marginTop: 12, marginBottom: 0 }}>
          暂无稳定关系记录。
        </Paragraph>
      )}
    </Card>
  );
}

function RetrievalProfileSection({ paper }: { paper: PaperRecord }) {
  return (
    <SectionCard id="retrieval-profile" title="检索画像" kicker="高级检索">
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
            children: (
              <pre className="debug-json-block">{JSON.stringify(paper, null, 2)}</pre>
            ),
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

  const outlineItems = [
    { key: "summary-overview", label: "摘要与定位" },
    { key: "method-core", label: "方法核心" },
    { key: "input-output", label: "输入输出" },
    { key: "claims", label: "关键论断" },
    { key: "evaluation", label: "实验评估" },
    { key: "conclusion", label: "局限与结论" },
    { key: "figures", label: "图表索引" },
    { key: "retrieval-profile", label: "检索画像" },
  ];

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
      <OutlineCard items={outlineItems} />
      <SidebarMetaCard paper={paper} />
      <SidebarTopicCard paper={paper} />
      <SidebarComparisonCard paper={paper} />
      <SidebarNeighborsCard paper={paper} payload={payload} />
      <SidebarRelationsCard paper={paper} payload={payload} />
    </Space>
  );

  return (
    <div className="page-stack">
      <HeroHeader paper={paper} />
      <CoverageStatusBar paper={paper} />

      <Row gutter={[24, 24]} align="top">
        <Col xs={24} xl={17}>
          <Space direction="vertical" size={18} style={{ width: "100%" }}>
            <SummarySection paper={paper} />
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
