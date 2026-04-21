import {
  Alert,
  Button,
  Card,
  Col,
  Drawer,
  Empty,
  Flex,
  Grid,
  Input,
  Layout,
  Row,
  Select,
  Space,
  Spin,
  Statistic,
  Tabs,
  Tag,
  Typography,
} from "antd";
import {
  ArrowLeftOutlined,
  BookOutlined,
  FileSearchOutlined,
  FilterOutlined,
  FireOutlined,
  LinkOutlined,
  ReadOutlined,
} from "@ant-design/icons";
import { startTransition, useDeferredValue, useEffect, useState, type ReactNode } from "react";
import { Link, Route, Routes, useNavigate, useParams } from "react-router-dom";
import type { NeighborItem, PaperRecord, SitePayload } from "./types";

const { Header, Content } = Layout;
const { Title, Paragraph, Text } = Typography;

function inlinePayload(): SitePayload | null {
  const node = document.getElementById("paper-neighbors-data");
  const text = node?.textContent?.trim();
  if (!text || text === "__PAPER_NEIGHBORS_DATA__") {
    return null;
  }
  return JSON.parse(text) as SitePayload;
}

async function loadPayload(): Promise<SitePayload> {
  const embedded = inlinePayload();
  if (embedded) {
    return embedded;
  }
  const response = await fetch(new URL("paper-neighbors.json", window.location.href.split("#")[0]).toString());
  if (!response.ok) {
    throw new Error(`读取 paper-neighbors.json 失败: ${response.status}`);
  }
  return (await response.json()) as SitePayload;
}

function paperRoute(routePath: string | undefined, paperId: string): string {
  if (routePath?.startsWith("#")) {
    return routePath.slice(1);
  }
  return `/paper/${paperId}`;
}

function searchableText(paper: PaperRecord): string {
  return [
    paper.title,
    ...paper.authors,
    paper.venue,
    String(paper.year ?? ""),
    paper.abstract_raw ?? "",
    paper.abstract_zh ?? "",
    paper.summary.one_liner,
    paper.summary.abstract_summary,
    paper.summary.research_value ?? "",
    paper.research_problem ?? "",
    ...paper.core_contributions,
    paper.author_conclusion ?? "",
    paper.editor_note ?? "",
    ...paper.research_tags.themes,
    ...paper.research_tags.tasks,
    ...paper.research_tags.methods,
    ...paper.research_tags.representations,
  ]
    .join(" ")
    .toLowerCase();
}

function matchesTags(paperTags: string[], selected: string[]): boolean {
  if (!selected.length) {
    return true;
  }
  return selected.every((tag) => paperTags.includes(tag));
}

function isEmptyRecord(value: unknown[] | undefined): boolean {
  return !value || value.length === 0;
}

function ScrollOutline({ items }: { items: Array<{ key: string; label: string }> }) {
  return (
    <Card className="outline-card" bordered={false}>
      <Text className="panel-kicker">阅读导航</Text>
      <Space direction="vertical" size={8} style={{ width: "100%", marginTop: 12 }}>
        {items.map((item) => (
          <Button
            key={item.key}
            block
            onClick={() =>
              document.getElementById(item.key)?.scrollIntoView({ behavior: "smooth", block: "start" })
            }
          >
            {item.label}
          </Button>
        ))}
      </Space>
    </Card>
  );
}

function NeighborList({ items }: { items: NeighborItem[] }) {
  if (!items.length) {
    return <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="当前没有足够可靠的近邻。" />;
  }
  return (
    <Space direction="vertical" size={16} style={{ width: "100%" }}>
      {items.map((item) => (
        <Card key={`${item.paper_id}-${item.match_source}`} className="neighbor-card" bordered={false}>
          <Flex justify="space-between" align="start" gap={12}>
            <div>
              <Link to={paperRoute(item.route_path, item.paper_id)} className="paper-link">
                {item.title}
              </Link>
              <Paragraph type="secondary" style={{ marginTop: 8, marginBottom: 0 }}>
                {item.reason}
              </Paragraph>
              {item.relation_hint ? (
                <Paragraph style={{ marginTop: 8, marginBottom: 0 }}>{item.relation_hint}</Paragraph>
              ) : null}
            </div>
            <Tag color="geekblue">Score {item.score}</Tag>
          </Flex>
          <Flex gap={8} wrap="wrap" style={{ marginTop: 14 }}>
            {Object.entries(item.shared_signals).flatMap(([key, values]) =>
              values.map((value) => (
                <Tag key={`${item.paper_id}-${key}-${value}`} className="soft-tag">
                  {key}: {value}
                </Tag>
              ))
            )}
          </Flex>
        </Card>
      ))}
    </Space>
  );
}

function EvalValueGroup({
  label,
  values,
  paperId,
}: {
  label: string;
  values: string[];
  paperId: string;
}) {
  if (!values.length) {
    return (
      <div>
        <Text strong>{label}</Text>
        <Paragraph type="secondary" style={{ marginBottom: 0, marginTop: 6 }}>
          暂无
        </Paragraph>
      </div>
    );
  }

  if (label === "主要发现") {
    return (
      <div>
        <Text strong>{label}</Text>
        <Space direction="vertical" size={10} style={{ width: "100%", marginTop: 10 }}>
          {values.map((item) => (
            <Card key={`${paperId}-${label}-${item}`} bordered={false} className="sub-card finding-card">
              <Paragraph className="finding-text">{item}</Paragraph>
            </Card>
          ))}
        </Space>
      </div>
    );
  }

  return (
    <div>
      <Text strong>{label}</Text>
      <Flex wrap="wrap" gap={8} style={{ marginTop: 8 }}>
        {values.map((item) => (
          <Tag key={`${paperId}-${label}-${item}`} className="soft-tag">
            {item}
          </Tag>
        ))}
      </Flex>
    </div>
  );
}

function SectionCard({
  id,
  title,
  children,
  extra,
}: {
  id: string;
  title: string;
  children: ReactNode;
  extra?: ReactNode;
}) {
  return (
    <Card id={id} className="reading-card" bordered={false} extra={extra}>
      <Title level={3} style={{ marginTop: 0 }}>
        {title}
      </Title>
      {children}
    </Card>
  );
}

function FilterPanel({
  payload,
  query,
  setQuery,
  selectedThemes,
  setSelectedThemes,
  selectedTasks,
  setSelectedTasks,
  selectedMethods,
  setSelectedMethods,
  sortBy,
  setSortBy,
}: {
  payload: SitePayload;
  query: string;
  setQuery: (value: string) => void;
  selectedThemes: string[];
  setSelectedThemes: (value: string[]) => void;
  selectedTasks: string[];
  setSelectedTasks: (value: string[]) => void;
  selectedMethods: string[];
  setSelectedMethods: (value: string[]) => void;
  sortBy: string;
  setSortBy: (value: string) => void;
}) {
  return (
    <Space direction="vertical" size={16} style={{ width: "100%" }}>
      <Card bordered={false} className="panel-card">
        <Text className="panel-kicker">检索</Text>
        <Input
          allowClear
          prefix={<FileSearchOutlined />}
          placeholder="搜索标题、摘要、标签、venue"
          value={query}
          onChange={(event) => startTransition(() => setQuery(event.target.value))}
          style={{ marginTop: 12 }}
        />
        <Select
          mode="multiple"
          allowClear
          placeholder="按主题筛选"
          value={selectedThemes}
          options={payload.filters.themes.map((item) => ({ label: `${item.label} (${item.count})`, value: item.label }))}
          onChange={(value) => startTransition(() => setSelectedThemes(value))}
          style={{ width: "100%", marginTop: 12 }}
        />
        <Select
          mode="multiple"
          allowClear
          placeholder="按任务筛选"
          value={selectedTasks}
          options={payload.filters.tasks.map((item) => ({ label: `${item.label} (${item.count})`, value: item.label }))}
          onChange={(value) => startTransition(() => setSelectedTasks(value))}
          style={{ width: "100%", marginTop: 12 }}
        />
        <Select
          mode="multiple"
          allowClear
          placeholder="按方法筛选"
          value={selectedMethods}
          options={payload.filters.methods.map((item) => ({ label: `${item.label} (${item.count})`, value: item.label }))}
          onChange={(value) => startTransition(() => setSelectedMethods(value))}
          style={{ width: "100%", marginTop: 12 }}
        />
        <Select
          value={sortBy}
          options={[
            { label: "年份从新到旧", value: "year-desc" },
            { label: "年份从旧到新", value: "year-asc" },
            { label: "标题 A-Z", value: "title-asc" },
          ]}
          onChange={(value) => startTransition(() => setSortBy(value))}
          style={{ width: "100%", marginTop: 12 }}
        />
      </Card>

      <Card bordered={false} className="panel-card">
        <Text className="panel-kicker">热门标签</Text>
        <Flex wrap="wrap" gap={8} style={{ marginTop: 12 }}>
          {payload.filters.themes.slice(0, 8).map((item) => (
            <Tag key={item.label} className="soft-tag">
              {item.label}
            </Tag>
          ))}
        </Flex>
      </Card>
    </Space>
  );
}

function HomePage({ payload }: { payload: SitePayload }) {
  const screens = Grid.useBreakpoint();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [selectedThemes, setSelectedThemes] = useState<string[]>([]);
  const [selectedTasks, setSelectedTasks] = useState<string[]>([]);
  const [selectedMethods, setSelectedMethods] = useState<string[]>([]);
  const [sortBy, setSortBy] = useState("year-desc");
  const deferredQuery = useDeferredValue(query);

  let papers = payload.papers.filter((paper) => {
    const searchOkay = !deferredQuery.trim() || searchableText(paper).includes(deferredQuery.trim().toLowerCase());
    return (
      searchOkay &&
      matchesTags(paper.research_tags.themes, selectedThemes) &&
      matchesTags(paper.research_tags.tasks, selectedTasks) &&
      matchesTags(paper.research_tags.methods, selectedMethods)
    );
  });

  papers = [...papers].sort((left, right) => {
    if (sortBy === "title-asc") {
      return left.title.localeCompare(right.title);
    }
    const leftYear = Number(left.year ?? 0);
    const rightYear = Number(right.year ?? 0);
    return sortBy === "year-asc" ? leftYear - rightYear : rightYear - leftYear;
  });

  const filterPanel = (
    <FilterPanel
      payload={payload}
      query={query}
      setQuery={setQuery}
      selectedThemes={selectedThemes}
      setSelectedThemes={setSelectedThemes}
      selectedTasks={selectedTasks}
      setSelectedTasks={setSelectedTasks}
      selectedMethods={selectedMethods}
      setSelectedMethods={setSelectedMethods}
      sortBy={sortBy}
      setSortBy={setSortBy}
    />
  );

  return (
    <Row gutter={[24, 24]}>
      <Col span={24}>
        <Card bordered={false} className="hero-card">
          <Text className="hero-eyebrow">Ant Design Reading Desk</Text>
          <Title className="hero-title">用单页阅读流替代碎片化论文 HTML</Title>
          <Paragraph className="hero-copy">
            首页负责检索与发现，论文详情页负责深读与近邻切换。整个站点只保留一个入口文件和结构化数据，方便本地打开、长期演进和后续做更强的研究检索。
          </Paragraph>
          <Row gutter={[16, 16]} style={{ marginTop: 8 }}>
            <Col xs={12} md={6}>
              <Card bordered={false} className="stat-card">
                <Statistic title="论文数" value={payload.site_meta.paper_count} />
              </Card>
            </Col>
            <Col xs={12} md={6}>
              <Card bordered={false} className="stat-card">
                <Statistic title="主题标签" value={payload.filters.themes.length} />
              </Card>
            </Col>
            <Col xs={12} md={6}>
              <Card bordered={false} className="stat-card">
                <Statistic title="任务标签" value={payload.filters.tasks.length} />
              </Card>
            </Col>
            <Col xs={12} md={6}>
              <Card bordered={false} className="stat-card">
                <Statistic title="方法标签" value={payload.filters.methods.length} />
              </Card>
            </Col>
          </Row>
        </Card>
      </Col>

      <Col xs={24} lg={7} xl={6}>
        {screens.lg ? (
          <div className="sticky-column">{filterPanel}</div>
        ) : (
          <>
            <Button icon={<FilterOutlined />} onClick={() => setDrawerOpen(true)}>
              打开筛选器
            </Button>
            <Drawer open={drawerOpen} onClose={() => setDrawerOpen(false)} title="筛选论文" width={360}>
              {filterPanel}
            </Drawer>
          </>
        )}
      </Col>

      <Col xs={24} lg={17} xl={18}>
        <Card bordered={false} className="panel-card">
          <Flex justify="space-between" align="center" wrap="wrap" gap={12}>
            <div>
              <Text className="panel-kicker">探索结果</Text>
              <Title level={3} style={{ marginTop: 8, marginBottom: 0 }}>
                {papers.length ? `找到 ${papers.length} 篇可读论文` : "没有命中论文"}
              </Title>
            </div>
            <Text type="secondary">更新时间：{payload.site_meta.generated_at}</Text>
          </Flex>

          {payload.recent_titles.length ? (
            <Flex wrap="wrap" gap={8} style={{ marginTop: 18 }}>
              {payload.recent_titles.map((title) => (
                <Tag key={title} icon={<FireOutlined />} className="soft-tag">
                  {title}
                </Tag>
              ))}
            </Flex>
          ) : null}

          <Space direction="vertical" size={16} style={{ width: "100%", marginTop: 18 }}>
            {papers.length ? (
              papers.map((paper) => (
                <Card key={paper.paper_id} bordered={false} className="paper-card">
                  <Flex justify="space-between" align="start" gap={16} wrap="wrap">
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <Link to={paperRoute(paper.route_path, paper.paper_id)} className="paper-link">
                        {paper.title}
                      </Link>
                      <Paragraph type="secondary" style={{ marginTop: 8, marginBottom: 12 }}>
                        {paper.venue} · {paper.year || "未知年份"}
                      </Paragraph>
                      <Paragraph style={{ marginBottom: 12 }}>{paper.summary.one_liner || "暂无一句话结论。"}</Paragraph>
                      <Flex wrap="wrap" gap={8}>
                        {paper.research_tags.themes.slice(0, 2).map((tag) => (
                          <Tag key={`${paper.paper_id}-${tag}`} color="green">
                            {tag}
                          </Tag>
                        ))}
                        {paper.research_tags.tasks.slice(0, 2).map((tag) => (
                          <Tag key={`${paper.paper_id}-${tag}`} color="blue">
                            {tag}
                          </Tag>
                        ))}
                        {paper.research_tags.methods.slice(0, 2).map((tag) => (
                          <Tag key={`${paper.paper_id}-${tag}`} color="gold">
                            {tag}
                          </Tag>
                        ))}
                      </Flex>
                    </div>
                    <Space>
                      <Button icon={<ReadOutlined />} href={paper.route_path}>
                        进入阅读页
                      </Button>
                      <Button href={paper.paper_path} icon={<BookOutlined />}>
                        Markdown
                      </Button>
                    </Space>
                  </Flex>
                </Card>
              ))
            ) : (
              <Empty description="可以试试放宽筛选条件或搜索其他任务关键词。" />
            )}
          </Space>
        </Card>
      </Col>
    </Row>
  );
}

function DetailPage({ payload }: { payload: SitePayload }) {
  const screens = Grid.useBreakpoint();
  const navigate = useNavigate();
  const params = useParams();
  const paper = payload.papers.find((item) => item.paper_id === params.paperId);

  if (!paper) {
    return (
      <Card bordered={false} className="panel-card">
        <Empty description="没有找到这篇论文。" />
        <Button style={{ marginTop: 16 }} icon={<ArrowLeftOutlined />} onClick={() => navigate("/")}>
          返回首页
        </Button>
      </Card>
    );
  }

  const outlineItems = [
    { key: "summary", label: "一句话结论" },
    { key: "abstracts", label: "摘要双语" },
    { key: "problem", label: "研究问题" },
    { key: "contrib", label: "核心贡献" },
    { key: "claims", label: "核心论断" },
    { key: "method", label: "方法核心" },
    { key: "io", label: "输入输出" },
    { key: "eval", label: "评估快照" },
    { key: "notes", label: "结论与备注" },
    { key: "limits", label: "局限与标签" },
    { key: "relations", label: "Topics 与关系" },
    { key: "neighbors", label: "近邻阅读" },
  ];

  return (
    <Row gutter={[24, 24]}>
      <Col span={24}>
        <Card bordered={false} className="hero-card">
          <Flex justify="space-between" align="start" wrap="wrap" gap={16}>
            <div style={{ maxWidth: 820 }}>
              <Button type="link" icon={<ArrowLeftOutlined />} onClick={() => navigate("/")}>
                返回首页
              </Button>
              <Title className="detail-title">{paper.title}</Title>
              <Paragraph className="hero-copy">
                {paper.venue} · {paper.year || "未知年份"} · 收录于 {paper.translate_created_at || "未知时间"}
              </Paragraph>
              {paper.authors.length ? (
                <Paragraph style={{ marginBottom: 12 }}>作者：{paper.authors.join(" / ")}</Paragraph>
              ) : null}
              <Flex wrap="wrap" gap={8}>
                {paper.research_tags.themes.map((tag) => (
                  <Tag key={`${paper.paper_id}-${tag}`} color="green">
                    {tag}
                  </Tag>
                ))}
                {paper.novelty_type.map((tag) => (
                  <Tag key={`${paper.paper_id}-${tag}`} color="purple">
                    {tag}
                  </Tag>
                ))}
              </Flex>
            </div>
            <Space wrap>
              <Button href={paper.paper_path} icon={<BookOutlined />}>
                Markdown
              </Button>
              {paper.links.pdf ? (
                <Button href={paper.links.pdf} icon={<LinkOutlined />}>
                  PDF
                </Button>
              ) : null}
              {paper.links.code ? (
                <Button href={paper.links.code} icon={<LinkOutlined />}>
                  Code
                </Button>
              ) : null}
              {paper.links.project ? (
                <Button href={paper.links.project} icon={<LinkOutlined />}>
                  Project
                </Button>
              ) : null}
            </Space>
          </Flex>
        </Card>
      </Col>

      <Col xs={24} xl={17}>
        <Space direction="vertical" size={18} style={{ width: "100%" }}>
          <SectionCard id="summary" title="一句话结论">
            <Paragraph className="lead-text">{paper.summary.one_liner || "暂无一句话结论。"}</Paragraph>
            {paper.summary.abstract_summary ? <Paragraph>{paper.summary.abstract_summary}</Paragraph> : null}
            {paper.summary.research_value ? (
              <Alert type="success" showIcon message="研究价值" description={paper.summary.research_value} />
            ) : null}
          </SectionCard>

          <SectionCard id="abstracts" title="摘要双语">
            <Space direction="vertical" size={16} style={{ width: "100%" }}>
              {paper.abstract_raw ? (
                <div>
                  <Text strong>英文摘要</Text>
                  <Paragraph style={{ marginBottom: 0, marginTop: 6 }}>{paper.abstract_raw}</Paragraph>
                </div>
              ) : null}
              {paper.abstract_zh ? (
                <div>
                  <Text strong>中文摘要</Text>
                  <Paragraph style={{ marginBottom: 0, marginTop: 6 }}>{paper.abstract_zh}</Paragraph>
                </div>
              ) : (
                <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无摘要。" />
              )}
            </Space>
          </SectionCard>

          <SectionCard id="problem" title="研究问题">
            {paper.research_problem ? (
              <Paragraph style={{ marginBottom: 0 }}>{paper.research_problem}</Paragraph>
            ) : (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无研究问题摘要。" />
            )}
          </SectionCard>

          <SectionCard id="contrib" title="核心贡献">
            {paper.core_contributions.length ? (
              <Space direction="vertical" size={10} style={{ width: "100%" }}>
                {paper.core_contributions.map((item) => (
                  <Card key={`${paper.paper_id}-contrib-${item}`} bordered={false} className="sub-card">
                    <Paragraph style={{ marginBottom: 0 }}>{item}</Paragraph>
                  </Card>
                ))}
              </Space>
            ) : (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无核心贡献整理。" />
            )}
          </SectionCard>

          <SectionCard id="claims" title="核心论断">
            <Space direction="vertical" size={16} style={{ width: "100%" }}>
              {paper.key_claims.length ? (
                paper.key_claims.map((claim, index) => (
                  <Card key={`${paper.paper_id}-claim-${index}`} bordered={false} className="sub-card">
                    <Paragraph style={{ marginBottom: 12 }}>{claim.claim}</Paragraph>
                    <Flex wrap="wrap" gap={8}>
                      {claim.support.map((item) => (
                        <Tag key={`${paper.paper_id}-${item}`} className="soft-tag">
                          {item}
                        </Tag>
                      ))}
                      {claim.confidence ? <Tag color="geekblue">置信度 {claim.confidence}</Tag> : null}
                    </Flex>
                  </Card>
                ))
              ) : (
                <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无核心论断。" />
              )}
            </Space>
          </SectionCard>

          <SectionCard id="method" title="方法核心">
            <Space direction="vertical" size={14} style={{ width: "100%" }}>
              {[
                ["核心思路", paper.method_core.approach],
                ["主要创新", paper.method_core.innovation],
              ].map(([label, value]) =>
                value ? (
                  <div key={label}>
                    <Text strong>{label}</Text>
                    <Paragraph style={{ marginBottom: 0, marginTop: 6 }}>{value}</Paragraph>
                  </div>
                ) : null
              )}
              <Flex wrap="wrap" gap={8}>
                {[...paper.method_core.ingredients, ...paper.method_core.representation, ...paper.method_core.supervision].map(
                  (item) => (
                    <Tag key={`${paper.paper_id}-${item}`} className="soft-tag">
                      {item}
                    </Tag>
                  )
                )}
              </Flex>
            </Space>
          </SectionCard>

          <Row gutter={[18, 18]}>
            <Col xs={24} lg={12}>
              <SectionCard id="io" title="输入输出">
                <Space direction="vertical" size={12} style={{ width: "100%" }}>
                  <div>
                    <Text strong>输入</Text>
                    <Flex wrap="wrap" gap={8} style={{ marginTop: 8 }}>
                      {paper.inputs_outputs.inputs.map((item) => (
                        <Tag key={`${paper.paper_id}-input-${item}`}>{item}</Tag>
                      ))}
                    </Flex>
                  </div>
                  <div>
                    <Text strong>输出</Text>
                    <Flex wrap="wrap" gap={8} style={{ marginTop: 8 }}>
                      {paper.inputs_outputs.outputs.map((item) => (
                        <Tag key={`${paper.paper_id}-output-${item}`}>{item}</Tag>
                      ))}
                    </Flex>
                  </div>
                  <div>
                    <Text strong>模态</Text>
                    <Flex wrap="wrap" gap={8} style={{ marginTop: 8 }}>
                      {paper.inputs_outputs.modalities.map((item) => (
                        <Tag key={`${paper.paper_id}-modality-${item}`}>{item}</Tag>
                      ))}
                    </Flex>
                  </div>
                </Space>
              </SectionCard>
            </Col>
            <Col xs={24} lg={12}>
              <SectionCard id="eval" title="评估快照">
                <Space direction="vertical" size={12} style={{ width: "100%" }}>
                  {[
                    ["数据集", paper.benchmarks_or_eval.datasets],
                    ["指标", paper.benchmarks_or_eval.metrics],
                    ["对比方法", paper.benchmarks_or_eval.baselines],
                    ["主要发现", paper.benchmarks_or_eval.findings],
                  ].map(([label, values]) => (
                    <EvalValueGroup
                      key={label}
                      label={label}
                      values={Array.isArray(values) ? values : []}
                      paperId={paper.paper_id}
                    />
                  ))}
                  {paper.benchmarks_or_eval.experiment_setup_summary ? (
                    <div>
                      <Text strong>实验设置摘要</Text>
                      <Paragraph style={{ marginBottom: 0, marginTop: 6 }}>
                        {paper.benchmarks_or_eval.experiment_setup_summary}
                      </Paragraph>
                    </div>
                  ) : null}
                </Space>
              </SectionCard>
            </Col>
          </Row>

          <SectionCard id="notes" title="结论与备注">
            <Space direction="vertical" size={16} style={{ width: "100%" }}>
              {paper.author_conclusion ? (
                <div>
                  <Text strong>作者结论</Text>
                  <Paragraph style={{ marginBottom: 0, marginTop: 6 }}>{paper.author_conclusion}</Paragraph>
                </div>
              ) : null}
              {paper.editor_note ? (
                <div>
                  <Text strong>编者按</Text>
                  <Paragraph style={{ marginBottom: 0, marginTop: 6 }}>{paper.editor_note}</Paragraph>
                </div>
              ) : null}
              {!paper.author_conclusion && !paper.editor_note ? (
                <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无结论与备注。" />
              ) : null}
            </Space>
          </SectionCard>

          <Row gutter={[18, 18]}>
            <Col xs={24} lg={12}>
              <SectionCard id="limits" title="局限与标签">
                {paper.limitations.length ? (
                  <Space direction="vertical" size={8}>
                    {paper.limitations.map((item) => (
                      <Paragraph key={`${paper.paper_id}-${item}`} style={{ marginBottom: 0 }}>
                        {item}
                      </Paragraph>
                    ))}
                  </Space>
                ) : (
                  <Paragraph type="secondary">暂无明确记录的论文局限。</Paragraph>
                )}
                <Flex wrap="wrap" gap={8} style={{ marginTop: 12 }}>
                  {[
                    ...paper.research_tags.tasks,
                    ...paper.research_tags.methods,
                    ...paper.research_tags.representations,
                  ].map((item) => (
                    <Tag key={`${paper.paper_id}-research-${item}`} className="soft-tag">
                      {item}
                    </Tag>
                  ))}
                </Flex>
              </SectionCard>
            </Col>
            <Col xs={24} lg={12}>
              <SectionCard id="figures" title="图表索引">
                {!isEmptyRecord(paper.figure_table_index.figures) || !isEmptyRecord(paper.figure_table_index.tables) ? (
                  <Space direction="vertical" size={12} style={{ width: "100%" }}>
                    {paper.figure_table_index.figures?.slice(0, 8).map((item) => (
                      <Card key={`${paper.paper_id}-figure-${item.label}`} bordered={false} className="sub-card">
                        <Text strong>{item.label}</Text>
                        <Paragraph style={{ marginBottom: 0, marginTop: 6 }}>{item.caption}</Paragraph>
                      </Card>
                    ))}
                    {paper.figure_table_index.tables?.slice(0, 8).map((item) => (
                      <Card key={`${paper.paper_id}-table-${item.label}`} bordered={false} className="sub-card">
                        <Text strong>{item.label}</Text>
                        <Paragraph style={{ marginBottom: 0, marginTop: 6 }}>{item.caption}</Paragraph>
                      </Card>
                    ))}
                  </Space>
                ) : (
                  <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无图表索引。" />
                )}
              </SectionCard>
            </Col>
          </Row>

          <SectionCard id="relations" title="Topics 与关系">
            <Space direction="vertical" size={16} style={{ width: "100%" }}>
              {paper.topics.length ? (
                <div>
                  <Text strong>Topics</Text>
                  <Flex wrap="wrap" gap={8} style={{ marginTop: 8 }}>
                    {paper.topics.map((topic) => (
                      <Tag key={`${paper.paper_id}-topic-${topic.slug}`} className="soft-tag">
                        {topic.name} {topic.role ? `(${topic.role})` : ""}
                      </Tag>
                    ))}
                  </Flex>
                </div>
              ) : null}
              {paper.paper_relations.length ? (
                <Space direction="vertical" size={10} style={{ width: "100%" }}>
                  {paper.paper_relations.map((item) => (
                    <Card
                      key={`${paper.paper_id}-relation-${item.target_paper_id}-${item.relation_type}`}
                      bordered={false}
                      className="sub-card"
                    >
                      <Text strong>
                        {item.target_paper_id} · {item.relation_type}
                      </Text>
                      <Paragraph style={{ marginBottom: 0, marginTop: 6 }}>{item.description}</Paragraph>
                    </Card>
                  ))}
                </Space>
              ) : null}
              {!paper.topics.length && !paper.paper_relations.length ? (
                <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无 topics 或论文关系。" />
              ) : null}
            </Space>
          </SectionCard>

          <SectionCard id="neighbors" title="近邻阅读">
            <Tabs
              items={payload.navigation.neighbor_tabs.map((tab) => ({
                key: tab.key,
                label: tab.label,
                children: <NeighborList items={paper.paper_neighbors[tab.key]} />,
              }))}
            />
          </SectionCard>
        </Space>
      </Col>

      <Col xs={24} xl={7}>
        {screens.xl ? (
          <div className="sticky-column">
            <ScrollOutline items={outlineItems} />
          </div>
        ) : (
          <Card bordered={false} className="panel-card">
            <ScrollOutline items={outlineItems} />
          </Card>
        )}
      </Col>
    </Row>
  );
}

export default function App() {
  const [payload, setPayload] = useState<SitePayload | null>(null);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    let cancelled = false;
    loadPayload()
      .then((result) => {
        if (cancelled) {
          return;
        }
        startTransition(() => {
          setPayload(result);
          setError("");
        });
      })
      .catch((reason: unknown) => {
        if (cancelled) {
          return;
        }
        setError(reason instanceof Error ? reason.message : "加载站点数据失败。");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <Layout className="app-shell">
      <Header className="app-header">
        <div className="brand-lockup">
          <Text className="brand-label">Translate Paper Forest</Text>
          <Title level={4} style={{ margin: 0, color: "#1d2f2b" }}>
            单页研究阅读站
          </Title>
        </div>
      </Header>
      <Content className="app-content">
        {!payload && !error ? (
          <div className="loading-state">
            <Spin size="large" />
          </div>
        ) : null}
        {error ? <Alert type="error" message="站点加载失败" description={error} showIcon /> : null}
        {payload ? (
          <Routes>
            <Route path="/" element={<HomePage payload={payload} />} />
            <Route path="/paper/:paperId" element={<DetailPage payload={payload} />} />
            <Route path="*" element={<HomePage payload={payload} />} />
          </Routes>
        ) : null}
      </Content>
    </Layout>
  );
}
