import {
  App as AntApp,
  Button,
  Card,
  Col,
  Collapse,
  Empty,
  Flex,
  Input,
  Row,
  Space,
  Tabs,
  Tag,
  Typography,
} from "antd";
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

function SectionCard({
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
    <Card bordered={false} className="surface-card reading-section strong-section-card">
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
  return (
    <Card bordered={false} className="hero-surface detail-hero v2-hero">
      <Space direction="vertical" size={20} style={{ width: "100%" }}>
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
            rows={3}
            className="hero-one-liner detail-one-liner"
          />
        </div>

        <Row gutter={[16, 16]}>
          <Col xs={24} lg={15}>
            <Card bordered={false} className="surface-card decision-strip-card">
              <Text className="section-kicker">读前摘要</Text>
              <Space direction="vertical" size={10} style={{ width: "100%", marginTop: 12 }}>
                {paper.editorial.summary ? <Paragraph className="decision-line">{paper.editorial.summary}</Paragraph> : null}
                <Paragraph className="decision-line">推荐路径：{recommendedRouteLabel(paper.editorial.reading_route)}</Paragraph>
                {paper.evaluation.headline ? <Paragraph className="decision-line">结果先看：{paper.evaluation.headline}</Paragraph> : null}
              </Space>
            </Card>
          </Col>
          <Col xs={24} lg={9}>
            <ExternalLinkButtons paper={paper} />
          </Col>
        </Row>

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
      </Space>
    </Card>
  );
}

function ResearchSection({ paper }: { paper: PaperCanonicalRecord }) {
  const summary = paper.research_problem.summary || paper.story.problem || "暂无研究问题摘要。";
  return (
    <SectionCard title="研究问题" kicker="story / problem" summary={summary}>
      <Row gutter={[16, 16]} className="card-grid-row">
        <Col xs={24} lg={14}>
          <Card bordered={false} className="surface-card emphasis-card">
            <Text className="section-kicker">问题与目标</Text>
            <Paragraph className="section-lead">{summary}</Paragraph>
            {paper.research_problem.goal ? (
              <Card bordered={false} className="focus-note-card goal-note-card">
                <Text className="focus-note-label">研究目标</Text>
                <Paragraph className="focus-note-copy">{paper.research_problem.goal}</Paragraph>
              </Card>
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

function MethodSection({ paper }: { paper: PaperCanonicalRecord }) {
  return (
    <SectionCard title="方法设计" kicker="canonical method" summary={paper.method.summary || paper.story.method || "暂无方法概述。"}>
      <Card bordered={false} className="surface-card emphasis-card">
        <Text className="section-kicker">方案摘要</Text>
        <Paragraph className="section-lead">{paper.method.summary || paper.story.method || "暂无方法摘要。"}</Paragraph>
      </Card>

      <Row gutter={[16, 16]} className="card-grid-row">
        <Col xs={24} lg={12}>
          <Card bordered={false} className="subtle-card">
            <Text strong>方法流程</Text>
            {paper.method.pipeline_steps.length ? (
              <ol className="ordered-list">
                {paper.method.pipeline_steps.map((step) => (
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
            {paper.method.innovations.length ? (
              <Space direction="vertical" size={8} style={{ width: "100%", marginTop: 12 }}>
                {paper.method.innovations.map((item) => (
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
        <Col xs={24} md={6}>
          <Card bordered={false} className="subtle-card">
            <Text strong>关键组件</Text>
            <div style={{ marginTop: 12 }}>
              <BadgeGroup values={paper.method.ingredients} />
            </div>
          </Card>
        </Col>
        <Col xs={24} md={6}>
          <Card bordered={false} className="subtle-card">
            <Text strong>输入</Text>
            <div style={{ marginTop: 12 }}>
              <BadgeGroup values={paper.method.inputs} />
            </div>
          </Card>
        </Col>
        <Col xs={24} md={6}>
          <Card bordered={false} className="subtle-card">
            <Text strong>输出</Text>
            <div style={{ marginTop: 12 }}>
              <BadgeGroup values={paper.method.outputs} />
            </div>
          </Card>
        </Col>
        <Col xs={24} md={6}>
          <Card bordered={false} className="subtle-card">
            <Text strong>表示形式</Text>
            <div style={{ marginTop: 12 }}>
              <BadgeGroup values={paper.method.representations} />
            </div>
          </Card>
        </Col>
      </Row>
    </SectionCard>
  );
}

function EvaluationSection({ paper }: { paper: PaperCanonicalRecord }) {
  return (
    <SectionCard title="实验结果" kicker="evaluation" summary={paper.evaluation.headline || paper.story.result || "暂无实验结论。"}>
      <Card bordered={false} className="surface-card emphasis-card best-result-card">
        <Text className="section-kicker">结论先看</Text>
        <Paragraph className="section-lead">{paper.evaluation.headline || paper.story.result || "暂无前置结果判断。"}</Paragraph>
      </Card>

      {paper.evaluation.setup_summary ? (
        <Card bordered={false} className="surface-card setup-summary-card">
          <Text className="section-kicker">实验设置摘要</Text>
          <Paragraph className="long-copy">{paper.evaluation.setup_summary}</Paragraph>
        </Card>
      ) : null}

      <Row gutter={[16, 16]} className="card-grid-row">
        {[
          { label: "数据集", values: paper.evaluation.datasets, finding: false },
          { label: "指标", values: paper.evaluation.metrics, finding: false },
          { label: "对比方法", values: paper.evaluation.baselines, finding: false },
          { label: "主要发现", values: paper.evaluation.key_findings, finding: true },
        ].map((group) => (
          <Col xs={24} md={12} key={group.label}>
            <Card bordered={false} className="subtle-card eval-group-card">
              <Text strong>{group.label}</Text>
              {group.values.length ? (
                group.finding ? (
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

function EditorialSection({ paper }: { paper: PaperCanonicalRecord }) {
  return (
    <SectionCard title="阅读判断" kicker="editorial" summary={paper.editorial.research_position || paper.editorial.summary || "帮助判断值不值得继续读。"}>
      <Row gutter={[16, 16]} className="card-grid-row">
        <Col xs={24} lg={9}>
          <Card bordered={false} className="editor-note-card emphasis-card">
            <Text className="section-kicker">总评</Text>
            <Title level={4} style={{ marginTop: 10, marginBottom: 8 }}>
              {paper.editorial.verdict || "暂无明确总评"}
            </Title>
            <Paragraph style={{ marginBottom: 0 }}>{paper.editorial.summary || paper.editorial.research_position || "暂无编辑判断摘要。"}</Paragraph>
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card bordered={false} className="subtle-card">
            <Text strong>为什么读 / Strengths</Text>
            <Space direction="vertical" size={8} style={{ width: "100%", marginTop: 12 }}>
              {[...paper.editorial.why_read, ...paper.editorial.strengths].length ? (
                [...paper.editorial.why_read, ...paper.editorial.strengths].map((item) => (
                  <Card key={item} bordered={false} className="subtle-card list-card">
                    <Paragraph style={{ marginBottom: 0 }}>{item}</Paragraph>
                  </Card>
                ))
              ) : (
                <Paragraph type="secondary" style={{ marginBottom: 0 }}>
                  暂无明确亮点。
                </Paragraph>
              )}
            </Space>
          </Card>
        </Col>
        <Col xs={24} lg={7}>
          <Card bordered={false} className="subtle-card limitations-card">
            <Text strong>需注意</Text>
            <Space direction="vertical" size={8} style={{ width: "100%", marginTop: 12 }}>
              {(paper.editorial.cautions.length ? paper.editorial.cautions : paper.conclusion.limitations).length ? (
                (paper.editorial.cautions.length ? paper.editorial.cautions : paper.conclusion.limitations).map((item) => (
                  <Card key={item} bordered={false} className="subtle-card list-card">
                    <Paragraph style={{ marginBottom: 0 }}>{item}</Paragraph>
                  </Card>
                ))
              ) : (
                <Paragraph type="secondary" style={{ marginBottom: 0 }}>
                  暂无明确风险提示。
                </Paragraph>
              )}
            </Space>
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} className="card-grid-row">
        <Col xs={24} md={12}>
          <Card bordered={false} className="subtle-card">
            <Text strong>研究定位</Text>
            <Paragraph style={{ marginTop: 12, marginBottom: 0 }}>{paper.editorial.research_position || "暂无定位描述。"}</Paragraph>
          </Card>
        </Col>
        <Col xs={24} md={12}>
          <Card bordered={false} className="subtle-card">
            <Text strong>下一篇建议</Text>
            <div style={{ marginTop: 12 }}>
              <BadgeGroup values={paper.editorial.next_read} color="processing" />
            </div>
          </Card>
        </Col>
      </Row>
    </SectionCard>
  );
}

function ComparisonSection({ paper, neighbors }: { paper: PaperCanonicalRecord; neighbors: PaperDetailViewModel["neighbors"] }) {
  return (
    <SectionCard title="对比线索" kicker="comparison" summary={paper.comparison.next_read[0] || "拿谁来比，为什么值得比。"}>
      <Row gutter={[16, 16]} className="card-grid-row">
        <Col xs={24} md={12}>
          <Card bordered={false} className="subtle-card">
            <Text strong>显式基线</Text>
            <div style={{ marginTop: 12 }}>
              <BadgeGroup values={paper.evaluation.baselines} />
            </div>
          </Card>
        </Col>
        <Col xs={24} md={12}>
          <Card bordered={false} className="subtle-card">
            <Text strong>下一篇建议</Text>
            <div style={{ marginTop: 12 }}>
              <BadgeGroup values={paper.comparison.next_read} color="processing" />
            </div>
          </Card>
        </Col>
      </Row>

      <Card bordered={false} className="subtle-card">
        <Text strong>对比维度</Text>
        {paper.comparison.aspects.length ? (
          <Space direction="vertical" size={8} style={{ width: "100%", marginTop: 12 }}>
            {paper.comparison.aspects.map((item) => (
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

      <Tabs
        items={[
          { key: "task", label: "任务近邻", children: <NeighborList items={neighbors.task} /> },
          { key: "method", label: "方法近邻", children: <NeighborList items={neighbors.method} /> },
          { key: "comparison", label: "对比近邻", children: <NeighborList items={neighbors.comparison} /> },
        ]}
      />
    </SectionCard>
  );
}

function ClaimsPanel({ paper }: { paper: PaperCanonicalRecord }) {
  if (!paper.claims.length) {
    return <EmptyBlock description="暂无结构化 claims。" />;
  }
  return (
    <Space direction="vertical" size={12} style={{ width: "100%" }}>
      {paper.claims.map((claim, index) => (
        <Card key={`${paper.id}-claim-${index}`} bordered={false} className="claim-card">
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
        </Card>
      ))}
    </Space>
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
    <Card key={item.label} bordered={false} className="subtle-card figure-item-card">
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

  if (!paper.assets.figures.length && !paper.assets.tables.length) {
    return <EmptyBlock description="暂无图表索引。" />;
  }

  return (
    <Space direction="vertical" size={14} style={{ width: "100%" }}>
      <Input allowClear placeholder="搜索图表编号或说明" value={query} onChange={(event) => setQuery(event.target.value)} className="compact-search" />
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
        <Space direction="vertical" size={12} style={{ width: "100%" }}>
          {paper.relations.map((item) => (
            <Card key={`${item.type}-${item.target_paper_id}`} bordered={false} className="subtle-card list-card">
              <Text strong>{item.type}</Text>
              <Paragraph style={{ marginTop: 6, marginBottom: 0 }}>{item.label || item.target_paper_id}</Paragraph>
              {item.description ? <Paragraph type="secondary" style={{ marginBottom: 0 }}>{item.description}</Paragraph> : null}
            </Card>
          ))}
        </Space>
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
        <Space direction="vertical" size={12} style={{ width: "100%" }}>
          <Button icon={<CopyOutlined />} onClick={handleCopy}>
            复制 JSON
          </Button>
          <pre className="debug-json-block">{JSON.stringify(detail, null, 2)}</pre>
        </Space>
      ),
    });
  }

  return (
    <SectionCard title="附录资料" kicker="materials" summary="Claims、图表、摘要和 relations 收在后半段，避免正文信息流反复跳转。">
      <Collapse defaultActiveKey={[]} items={items} />
    </SectionCard>
  );
}

function SidebarSnapshotCard({ paper }: { paper: PaperCanonicalRecord }) {
  return (
    <Card bordered={false} className="surface-card sidebar-card">
      <Text className="section-kicker">阅读摘要</Text>
      <Title level={4} className="panel-title">
        Canonical Snapshot
      </Title>
      <MetaLine label="来源 / 年份" value={`${paper.bibliography.venue || "未知"} / ${formatYear(paper.bibliography.year)}`} />
      <MetaLine label="引用数" value={paper.bibliography.citation_count ?? "暂无"} />
      <MetaLine label="阅读判断" value={paper.editorial.verdict || "暂无"} />
      <MetaLine label="推荐路径" value={recommendedRouteLabel(paper.editorial.reading_route)} />
      <MetaLine label="任务" value={<BadgeGroup values={paper.taxonomy.tasks} color="gold" />} />
      <MetaLine label="方法" value={<BadgeGroup values={paper.taxonomy.methods} color="green" />} />
    </Card>
  );
}

function SidebarLinksCard({ paper }: { paper: PaperCanonicalRecord }) {
  const links = firstExternalLinks(paper.bibliography);
  const markdownLink = markdownHref(paper.source.paper_path);
  return (
    <Card bordered={false} className="surface-card sidebar-card">
      <Text className="section-kicker">链接与标签</Text>
      <MetaLine label="创新类型" value={<BadgeGroup values={paper.taxonomy.novelty_types} color="magenta" />} />
      <MetaLine label="模态" value={<BadgeGroup values={paper.taxonomy.modalities} color="processing" />} />
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
      {markdownLink ? <MetaLine label="Markdown" value={<Button size="small" href={markdownLink} target="_blank">打开</Button>} /> : null}
    </Card>
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
      <Card bordered={false} className="surface-card">
        <Title level={4}>缺少论文 ID</Title>
        <Button onClick={() => navigate("/")}>返回首页</Button>
      </Card>
    );
  }

  if (loadError) {
    return (
      <Card bordered={false} className="surface-card">
        <Title level={4}>加载失败</Title>
        <Paragraph>{loadError}</Paragraph>
        <Button onClick={() => navigate("/")}>返回首页</Button>
      </Card>
    );
  }

  if (!detail) {
    return (
      <Card bordered={false} className="surface-card">
        <Paragraph>正在加载论文详情…</Paragraph>
      </Card>
    );
  }

  const paper = detail.canonical;

  return (
    <div className="page-stack">
      <DecisionHero paper={paper} />

      <Row gutter={[24, 24]} align="top">
        <Col xs={24} xl={17}>
          <Space direction="vertical" size={24} style={{ width: "100%" }}>
            <ResearchSection paper={paper} />
            <MethodSection paper={paper} />
            <EvaluationSection paper={paper} />
            <EditorialSection paper={paper} />
            <ComparisonSection paper={paper} neighbors={detail.neighbors} />
            <MaterialsSection detail={detail} debugMode={debugMode} activeFigureTab={activeFigureTab} setActiveFigureTab={setActiveFigureTab} />
          </Space>
        </Col>
        <Col xs={24} xl={7}>
          <Space direction="vertical" size={16} style={{ width: "100%" }}>
            <SidebarSnapshotCard paper={paper} />
            <SidebarLinksCard paper={paper} />
            <Card bordered={false} className="surface-card sidebar-card">
              <Text className="section-kicker">返回与导航</Text>
              <Space direction="vertical" size={8} style={{ width: "100%", marginTop: 12 }}>
                <Button block icon={<ArrowLeftOutlined />} onClick={() => navigate("/")}>
                  返回首页
                </Button>
                <Button block icon={<LinkOutlined />} onClick={() => navigate(paperRoute(payload.navigation.home_route, paper.id))}>
                  回到站点入口
                </Button>
              </Space>
            </Card>
          </Space>
        </Col>
      </Row>
    </div>
  );
}
