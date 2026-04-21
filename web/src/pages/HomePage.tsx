import {
  Button,
  Card,
  Col,
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
import { FileSearchOutlined, FireOutlined, ReadOutlined } from "@ant-design/icons";
import { startTransition, useDeferredValue, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  cleanDisplayText,
  displayValueLabel,
  firstExternalLinks,
  formatYear,
  markdownHref,
  matchesTags,
  paperRoute,
  recommendedRouteLabel,
  routeTagClass,
  searchableText,
  verdictTagClass,
} from "../lib/paper";
import { TooltipTag, TooltipText } from "../components/OverflowTooltip";
import type { PaperCardView, SiteIndexPayload } from "../types";

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
  payload: SiteIndexPayload;
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
      <Card bordered={false} className="surface-card discovery-card control-panel-card">
        <Text className="section-kicker">论文检索台</Text>
        <Title level={4} className="panel-title">
          先判断值不值得读，再进入单篇深入
        </Title>
        <Paragraph type="secondary" className="panel-support-copy">
          首页只读 derived discovery payload，详情页再按需加载 canonical paper record。
        </Paragraph>
        <Input
          allowClear
          size="large"
          prefix={<FileSearchOutlined />}
          placeholder="搜索标题、作者、story、editorial、taxonomy"
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
            options={payload.filters.themes.map((item) => ({ label: `${displayValueLabel(item.label)} (${item.count})`, value: item.label }))}
            onChange={(value) => startTransition(() => setSelectedThemes(value))}
          />
          <Select
            mode="multiple"
            allowClear
            size="large"
            placeholder="按任务筛选"
            value={selectedTasks}
            options={payload.filters.tasks.map((item) => ({ label: `${displayValueLabel(item.label)} (${item.count})`, value: item.label }))}
            onChange={(value) => startTransition(() => setSelectedTasks(value))}
          />
          <Select
            mode="multiple"
            allowClear
            size="large"
            placeholder="按方法筛选"
            value={selectedMethods}
            options={payload.filters.methods.map((item) => ({ label: `${displayValueLabel(item.label)} (${item.count})`, value: item.label }))}
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

      <Card bordered={false} className="surface-card secondary-panel control-panel-card">
        <Text className="section-kicker">热门切口</Text>
        <Flex wrap="wrap" gap={8} style={{ marginTop: 12 }}>
          {payload.filters.themes.slice(0, 10).map((item) => (
            <TooltipTag key={item.label} label={displayValueLabel(item.label)} maxChars={20} className="chip-tag chip-tag-tone-blue" />
          ))}
        </Flex>
      </Card>
    </Space>
  );
}

function discoveryTags(paper: PaperCardView): string[] {
  return [...paper.taxonomy.tasks, ...paper.taxonomy.methods, ...paper.taxonomy.themes, ...paper.taxonomy.novelty_types].slice(0, 5);
}

function QuickEntryCard({ paper }: { paper: PaperCardView }) {
  return (
    <Card bordered={false} className="surface-card quick-entry-card">
      <Text className="section-kicker">推荐阅读</Text>
      <Link to={paperRoute(paper.source.route_path, paper.id)} className="paper-link small">
        {paper.bibliography.title}
      </Link>
      <TooltipText
        text={paper.editorial.summary || paper.story.paper_one_liner || "暂无阅读判断。"}
        as="paragraph"
        rows={3}
        className="quick-entry-copy"
      />
      <Flex wrap="wrap" gap={8}>
        {paper.editorial.verdict ? <Tag className={verdictTagClass(paper.editorial.verdict)}>{paper.editorial.verdict}</Tag> : null}
        <Tag className={routeTagClass(paper.editorial.reading_route)}>{recommendedRouteLabel(paper.editorial.reading_route)}</Tag>
      </Flex>
    </Card>
  );
}

function PaperListCard({ paper }: { paper: PaperCardView }) {
  const externalLinks = firstExternalLinks(paper.bibliography).slice(0, 3);
  const markdownLink = markdownHref(paper.source.paper_path);
  const reasons = paper.editorial.why_read.length ? paper.editorial.why_read : [paper.editorial.summary || paper.story.paper_one_liner || "暂无阅读摘要。"];

  return (
    <Card bordered={false} className="surface-card paper-list-card decision-paper-card">
      <Flex justify="space-between" align="start" gap={16} wrap="wrap">
        <div className="paper-card-main">
          <Flex wrap="wrap" gap={8} className="paper-decision-tags">
            {paper.editorial.verdict ? <Tag className={verdictTagClass(paper.editorial.verdict)}>{paper.editorial.verdict}</Tag> : null}
            <Tag className={routeTagClass(paper.editorial.reading_route)}>{recommendedRouteLabel(paper.editorial.reading_route)}</Tag>
            {paper.editorial.graph_worthy ? <Tag className="chip-tag chip-tag-worth">值得长期图谱</Tag> : null}
          </Flex>
          <Link to={paperRoute(paper.source.route_path, paper.id)} className="paper-link">
            {paper.bibliography.title}
          </Link>
          <Paragraph type="secondary" className="paper-meta-line">
            {paper.bibliography.venue || "未知 venue"} · {formatYear(paper.bibliography.year)}
          </Paragraph>
        </div>
        <Button type="primary" icon={<ReadOutlined />}>
          <Link to={paperRoute(paper.source.route_path, paper.id)}>进入阅读页</Link>
        </Button>
      </Flex>

      <TooltipText
        text={cleanDisplayText(paper.story.paper_one_liner || paper.editorial.summary, 110) || "暂无一句话结论。"}
        as="paragraph"
        rows={3}
        className="paper-summary-line"
      />

      <Row gutter={[12, 12]} className="paper-reason-grid card-grid-row">
        {[
          { title: "为什么读", values: reasons.slice(0, 3) },
          { title: "问题 / 方法 / 结果", values: [paper.story.problem, paper.story.method, paper.story.result].filter(Boolean) as string[] },
        ].map((group) => (
          <Col xs={24} md={12} key={group.title}>
            <Card bordered={false} className="subtle-card paper-micro-card">
              <Text strong>{group.title}</Text>
              <Space direction="vertical" size={8} style={{ width: "100%", marginTop: 12 }}>
                {group.values.length ? (
                  group.values.map((value) => <TooltipText key={value} text={cleanDisplayText(value, 80)} as="paragraph" rows={3} />)
                ) : (
                  <TooltipText text="暂无。" as="paragraph" rows={2} />
                )}
              </Space>
            </Card>
          </Col>
        ))}
      </Row>

      <Flex wrap="wrap" gap={8}>
        {discoveryTags(paper).map((tag) => (
          <TooltipTag key={`${paper.id}-${tag}`} label={displayValueLabel(tag)} maxChars={22} className="chip-tag chip-tag-tone-blue" />
        ))}
      </Flex>

      <Flex wrap="wrap" gap={10} className="paper-card-actions">
        {externalLinks.map((item) => (
          <Button key={`${paper.id}-${item.key}`} href={item.href} target="_blank">
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

export function HomePage({ payload }: { payload: SiteIndexPayload }) {
  const screens = Grid.useBreakpoint();
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
        matchesTags(paper.taxonomy.themes, selectedThemes) &&
        matchesTags(paper.taxonomy.tasks, selectedTasks) &&
        matchesTags(paper.taxonomy.methods, selectedMethods)
      );
    });

    papers = [...papers].sort((left, right) => {
      if (sortBy === "title-asc") {
        return left.bibliography.title.localeCompare(right.bibliography.title);
      }
      const leftYear = Number(left.bibliography.year ?? 0);
      const rightYear = Number(right.bibliography.year ?? 0);
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
      <Card bordered={false} className="hero-surface home-hero research-console-hero">
        <Row gutter={[24, 24]} align="middle">
          <Col xs={24} xl={14}>
            <Text className="section-kicker">Translate Paper Forest</Text>
            <Title className="display-title">把论文库拆成 canonical knowledge 和 derived reading views。</Title>
            <Paragraph className="hero-description">
              首页只负责发现、筛选和读前判断。进入单篇后，再按 story、method、evaluation、editorial 和 comparison 逐层深入。
            </Paragraph>
            {payload.recent_titles.length ? (
              <Flex wrap="wrap" gap={8} className="recent-tag-row">
                {payload.recent_titles.slice(0, 6).map((title) => (
                  <TooltipTag key={title} label={cleanDisplayText(title, 24)} maxChars={24} icon={<FireOutlined />} className="chip-tag chip-tag-highlight" />
                ))}
              </Flex>
            ) : null}
          </Col>
          <Col xs={24} xl={10}>
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

        {payload.featured.length ? (
          <Row gutter={[16, 16]} className="hero-quick-entry-grid">
            {payload.featured.map((paper) => (
              <Col xs={24} md={8} key={paper.id}>
                <QuickEntryCard paper={paper} />
              </Col>
            ))}
          </Row>
        ) : null}
      </Card>

      <Row gutter={[24, 24]} align="top">
        <Col xs={24} xl={7}>
          {screens.xl ? discoveryPanel : <div>{discoveryPanel}</div>}
        </Col>
        <Col xs={24} xl={17}>
          <Space direction="vertical" size={18} style={{ width: "100%" }}>
            {filteredPapers.length ? (
              filteredPapers.map((paper) => <PaperListCard key={paper.id} paper={paper} />)
            ) : (
              <Card bordered={false} className="surface-card paper-list-card">
                <Title level={4}>没有匹配结果</Title>
                <Paragraph type="secondary">可以调整检索词或筛选条件，或者先看看首页的 featured 论文。</Paragraph>
              </Card>
            )}
          </Space>
        </Col>
      </Row>
    </div>
  );
}
