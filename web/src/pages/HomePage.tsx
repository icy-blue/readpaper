import {
  Button,
  Card,
  Col,
  Drawer,
  Empty,
  Flex,
  Grid,
  Input,
  Row,
  Select,
  Space,
  Statistic,
  Tag,
  Typography,
} from "antd";
import { FileSearchOutlined, FilterOutlined, FireOutlined, ReadOutlined } from "@ant-design/icons";
import { startTransition, useDeferredValue, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { firstExternalLinks, formatYear, markdownHref, matchesTags, paperRoute, searchableText } from "../lib/paper";
import type { PaperRecord, SitePayload } from "../types";

const { Title, Paragraph, Text } = Typography;

function DiscoveryPanel({
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
      <Card bordered={false} className="surface-card discovery-card">
        <Text className="section-kicker">发现工作台</Text>
        <Title level={4} className="panel-title">
          按主题、任务和方法进入论文
        </Title>
        <Input
          allowClear
          size="large"
          prefix={<FileSearchOutlined />}
          placeholder="搜索标题、摘要、标签、作者、venue"
          value={query}
          onChange={(event) => startTransition(() => setQuery(event.target.value))}
          className="search-input"
        />
        <Space direction="vertical" size={12} style={{ width: "100%", marginTop: 18 }}>
          <Select
            mode="multiple"
            allowClear
            size="large"
            placeholder="按主题筛选"
            value={selectedThemes}
            options={payload.filters.themes.map((item) => ({ label: `${item.label} (${item.count})`, value: item.label }))}
            onChange={(value) => startTransition(() => setSelectedThemes(value))}
          />
          <Select
            mode="multiple"
            allowClear
            size="large"
            placeholder="按任务筛选"
            value={selectedTasks}
            options={payload.filters.tasks.map((item) => ({ label: `${item.label} (${item.count})`, value: item.label }))}
            onChange={(value) => startTransition(() => setSelectedTasks(value))}
          />
          <Select
            mode="multiple"
            allowClear
            size="large"
            placeholder="按方法筛选"
            value={selectedMethods}
            options={payload.filters.methods.map((item) => ({ label: `${item.label} (${item.count})`, value: item.label }))}
            onChange={(value) => startTransition(() => setSelectedMethods(value))}
          />
          <Select
            size="large"
            value={sortBy}
            options={[
              { label: "年份从新到旧", value: "year-desc" },
              { label: "年份从旧到新", value: "year-asc" },
              { label: "标题 A-Z", value: "title-asc" },
            ]}
            onChange={(value) => startTransition(() => setSortBy(value))}
          />
        </Space>
      </Card>

      <Card bordered={false} className="surface-card secondary-panel">
        <Text className="section-kicker">热门切口</Text>
        <Flex wrap="wrap" gap={8} style={{ marginTop: 12 }}>
          {payload.filters.themes.slice(0, 10).map((item) => (
            <Tag key={item.label} className="soft-tag">
              {item.label}
            </Tag>
          ))}
        </Flex>
      </Card>
    </Space>
  );
}

function PaperListCard({ paper }: { paper: PaperRecord }) {
  const externalLinks = firstExternalLinks(paper.links).slice(0, 3);
  const markdownLink = markdownHref(paper.paper_path);

  return (
    <Card bordered={false} className="surface-card paper-list-card">
      <div className="paper-card-header">
        <div className="paper-card-main">
          <Link to={paperRoute(paper.route_path, paper.paper_id)} className="paper-link">
            {paper.title}
          </Link>
          <Paragraph type="secondary" className="paper-meta-line">
            {paper.venue || "未知 venue"} · {formatYear(paper.year)}
          </Paragraph>
        </div>
        <Button type="primary" icon={<ReadOutlined />}>
          <Link to={paperRoute(paper.route_path, paper.paper_id)}>进入阅读页</Link>
        </Button>
      </div>

      <Paragraph className="paper-summary-line">{paper.summary.one_liner || "暂无一句话结论。"}</Paragraph>

      <Flex wrap="wrap" gap={8}>
        {paper.summary.worth_long_term_graph ? <Tag color="success">值得长期图谱</Tag> : null}
        {paper.research_tags.themes.slice(0, 2).map((tag) => (
          <Tag key={`${paper.paper_id}-theme-${tag}`} color="green">
            {tag}
          </Tag>
        ))}
        {paper.research_tags.tasks.slice(0, 2).map((tag) => (
          <Tag key={`${paper.paper_id}-task-${tag}`} color="blue">
            {tag}
          </Tag>
        ))}
        {paper.research_tags.methods.slice(0, 2).map((tag) => (
          <Tag key={`${paper.paper_id}-method-${tag}`} color="gold">
            {tag}
          </Tag>
        ))}
      </Flex>

      <Flex wrap="wrap" gap={10} className="paper-card-actions">
        {externalLinks.map((item) => (
          <Button key={`${paper.paper_id}-${item.key}`} href={item.href} target="_blank">
            {item.label}
          </Button>
        ))}
        {markdownLink ? (
          <Button href={markdownLink} target="_blank">
            Markdown
          </Button>
        ) : null}
      </Flex>
    </Card>
  );
}

export function HomePage({ payload }: { payload: SitePayload }) {
  const screens = Grid.useBreakpoint();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [selectedThemes, setSelectedThemes] = useState<string[]>([]);
  const [selectedTasks, setSelectedTasks] = useState<string[]>([]);
  const [selectedMethods, setSelectedMethods] = useState<string[]>([]);
  const [sortBy, setSortBy] = useState("year-desc");
  const deferredQuery = useDeferredValue(query);

  const filteredPapers = useMemo(() => {
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

    return papers;
  }, [deferredQuery, payload.papers, selectedMethods, selectedTasks, selectedThemes, sortBy]);

  const discoveryPanel = (
    <DiscoveryPanel
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
    <div className="page-stack">
      <Card bordered={false} className="hero-surface home-hero">
        <Row gutter={[24, 24]} align="middle">
          <Col xs={24} xl={15}>
            <Text className="section-kicker">Translate Paper Forest</Text>
            <Title className="display-title">让单篇论文真正可读、可比、可延展。</Title>
            <Paragraph className="hero-description">
              首页负责发现，详情页负责深读。每篇论文都围绕研究问题、方法、证据、判断与相邻论文组织，而不是把结构化字段简单堆起来。
            </Paragraph>
            {payload.recent_titles.length ? (
              <Flex wrap="wrap" gap={8} className="recent-tag-row">
                {payload.recent_titles.map((title) => (
                  <Tag key={title} icon={<FireOutlined />} className="soft-tag">
                    {title}
                  </Tag>
                ))}
              </Flex>
            ) : null}
          </Col>
          <Col xs={24} xl={9}>
            <Row gutter={[12, 12]}>
              <Col span={12}>
                <Card bordered={false} className="surface-card stat-surface">
                  <Statistic title="论文数" value={payload.site_meta.paper_count} />
                </Card>
              </Col>
              <Col span={12}>
                <Card bordered={false} className="surface-card stat-surface">
                  <Statistic title="主题标签" value={payload.filters.themes.length} />
                </Card>
              </Col>
              <Col span={12}>
                <Card bordered={false} className="surface-card stat-surface">
                  <Statistic title="任务标签" value={payload.filters.tasks.length} />
                </Card>
              </Col>
              <Col span={12}>
                <Card bordered={false} className="surface-card stat-surface">
                  <Statistic title="方法标签" value={payload.filters.methods.length} />
                </Card>
              </Col>
            </Row>
            <Paragraph type="secondary" className="generated-at-line">
              最近生成：{payload.site_meta.generated_at}
            </Paragraph>
          </Col>
        </Row>
      </Card>

      <Row gutter={[24, 24]} align="top">
        <Col xs={24} lg={8} xl={7}>
          {screens.lg ? (
            <div className="sticky-column">{discoveryPanel}</div>
          ) : (
            <>
              <Button icon={<FilterOutlined />} size="large" onClick={() => setDrawerOpen(true)}>
                打开筛选器
              </Button>
              <Drawer
                open={drawerOpen}
                onClose={() => setDrawerOpen(false)}
                title="发现工作台"
                width={360}
                styles={{ body: { padding: 12 } }}
              >
                {discoveryPanel}
              </Drawer>
            </>
          )}
        </Col>

        <Col xs={24} lg={16} xl={17}>
          <Card bordered={false} className="surface-card results-surface">
            <Flex justify="space-between" align="end" wrap="wrap" gap={12}>
              <div>
                <Text className="section-kicker">发现结果</Text>
                <Title level={3} className="panel-title">
                  {filteredPapers.length ? `找到 ${filteredPapers.length} 篇可读论文` : "没有命中论文"}
                </Title>
              </div>
              <Text type="secondary">按阅读判断信息组织，不做详情堆叠预览</Text>
            </Flex>

            <Space direction="vertical" size={16} style={{ width: "100%", marginTop: 22 }}>
              {filteredPapers.length ? (
                filteredPapers.map((paper) => <PaperListCard key={paper.paper_id} paper={paper} />)
              ) : (
                <Empty description="可以试试放宽筛选条件，或搜索其他研究任务与方法。" />
              )}
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  );
}
