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
import {
  cleanDisplayText,
  displayValueLabel,
  firstExternalLinks,
  routeTagClass,
  formatYear,
  markdownHref,
  matchesTags,
  paperRoute,
  recommendedRouteLabel,
  searchableText,
  verdictTagClass,
} from "../lib/paper";
import { TooltipTag, TooltipText } from "../components/OverflowTooltip";
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
      <Card bordered={false} className="surface-card discovery-card control-panel-card">
        <Text className="section-kicker">论文检索台</Text>
        <Title level={4} className="panel-title">
          先筛选，再进入单篇阅读
        </Title>
        <Paragraph type="secondary" className="panel-support-copy">
          首页负责发现与判断，详情页负责深入理解与对比。
        </Paragraph>
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

function positioningTags(paper: PaperRecord): string[] {
  return [
    ...paper.reading_digest.positioning.task,
    ...paper.reading_digest.positioning.method,
    ...paper.reading_digest.positioning.modality,
    ...paper.reading_digest.positioning.novelty,
  ].slice(0, 5);
}

function QuickEntryCard({ paper }: { paper: PaperRecord }) {
  return (
    <Card bordered={false} className="surface-card quick-entry-card">
      <Text className="section-kicker">推荐阅读</Text>
      <Link to={paperRoute(paper.route_path, paper.paper_id)} className="paper-link small">
        {paper.title}
      </Link>
      <TooltipText
        text={paper.reading_digest.value_statement || paper.summary.one_liner || "暂无阅读判断。"}
        as="paragraph"
        rows={3}
        className="quick-entry-copy"
      />
      <Flex wrap="wrap" gap={8}>
        {paper.editorial_review.verdict ? <Tag className={verdictTagClass(paper.editorial_review.verdict)}>{paper.editorial_review.verdict}</Tag> : null}
        <Tag className={routeTagClass(paper.reading_digest.recommended_route)}>{recommendedRouteLabel(paper.reading_digest.recommended_route)}</Tag>
      </Flex>
    </Card>
  );
}

function PaperListCard({ paper }: { paper: PaperRecord }) {
  const externalLinks = firstExternalLinks(paper.links).slice(0, 3);
  const markdownLink = markdownHref(paper.paper_path);

  return (
    <Card bordered={false} className="surface-card paper-list-card decision-paper-card">
      <Flex justify="space-between" align="start" gap={16} wrap="wrap">
        <div className="paper-card-main">
          <Flex wrap="wrap" gap={8} className="paper-decision-tags">
            {paper.editorial_review.verdict ? <Tag className={verdictTagClass(paper.editorial_review.verdict)}>{paper.editorial_review.verdict}</Tag> : null}
            <Tag className={routeTagClass(paper.reading_digest.recommended_route)}>{recommendedRouteLabel(paper.reading_digest.recommended_route)}</Tag>
            {paper.summary.worth_long_term_graph ? <Tag className="chip-tag chip-tag-worth">值得长期图谱</Tag> : null}
          </Flex>
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
      </Flex>

      <TooltipText
        text={cleanDisplayText(paper.reading_digest.value_statement || paper.summary.one_liner, 110) || "暂无一句话结论。"}
        as="paragraph"
        rows={3}
        className="paper-summary-line"
      />

      {paper.reading_digest.best_for ? (
        <TooltipText
          text={`适合谁读：${cleanDisplayText(paper.reading_digest.best_for, 72) || paper.reading_digest.best_for}`}
          as="paragraph"
          rows={2}
          className="paper-support-line"
        />
      ) : null}

      <Row gutter={[12, 12]} className="paper-reason-grid card-grid-row">
        {[
          {
            title: "为什么读",
            values: paper.reading_digest.why_read.length ? paper.reading_digest.why_read : paper.summary.research_value.points,
          },
          {
            title: "结果先看",
            values: [cleanDisplayText(paper.reading_digest.result_headline || paper.benchmarks_or_eval.best_results[0], 82) || "暂无前置结果判断。"],
          },
        ].map((group) => (
          <Col xs={24} md={12} key={group.title}>
            <Card bordered={false} className="subtle-card paper-micro-card">
              <Text strong>{group.title}</Text>
              <Space direction="vertical" size={8} style={{ width: "100%", marginTop: 12 }}>
                {group.values.map((value) => (
                  <TooltipText key={value} text={cleanDisplayText(value, 80)} as="paragraph" rows={3} />
                ))}
              </Space>
            </Card>
          </Col>
        ))}
      </Row>

      <Flex wrap="wrap" gap={8}>
        {positioningTags(paper).map((tag) => (
          <TooltipTag key={`${paper.paper_id}-${tag}`} label={displayValueLabel(tag)} maxChars={22} className="chip-tag chip-tag-tone-blue" />
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

  const featuredPapers = useMemo(
    () =>
      payload.papers
        .filter((paper) => paper.summary.worth_long_term_graph || paper.editorial_review.verdict === "值得精读")
        .slice(0, 3),
    [payload.papers],
  );

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
            <Title className="display-title">把论文站做成研究工作台，而不是信息堆栈。</Title>
            <Paragraph className="hero-description">
              先在首页完成筛选与阅读判断，再进入单篇页依次看研究问题、方法设计、实验结果与对比线索。每篇论文都优先回答值不值得读、该从哪里切入、下一篇该看谁。
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

        {featuredPapers.length ? (
          <Row gutter={[16, 16]} className="hero-quick-entry-grid">
            {featuredPapers.map((paper) => (
              <Col xs={24} md={8} key={paper.paper_id}>
                <QuickEntryCard paper={paper} />
              </Col>
            ))}
          </Row>
        ) : null}
      </Card>

      <Row gutter={[24, 24]} align="top">
        <Col xs={24} lg={8} xl={7}>
          {screens.lg ? (
            <div className="sticky-column">{discoveryPanel}</div>
          ) : (
            <>
              <Button icon={<FilterOutlined />} size="large" onClick={() => setDrawerOpen(true)}>
                打开发现面板
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
              <Text className="section-kicker">判断结果</Text>
              <Title level={3} className="panel-title">
                {filteredPapers.length ? `找到 ${filteredPapers.length} 篇可进入阅读流的论文` : "没有命中论文"}
              </Title>
            </div>
              <Text type="secondary">结果卡只保留读前决策信息，不再平铺长摘要。</Text>
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
