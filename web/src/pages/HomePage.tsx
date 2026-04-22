import { Button, Drawer, Empty, Flex, Grid, Input, Select, Tag, Typography, type InputRef } from "antd";
import { FileSearchOutlined, LinkOutlined, ReadOutlined } from "@ant-design/icons";
import { startTransition, useDeferredValue, useEffect, useMemo, useRef, useState, type RefObject } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { PaperDetailWorkspace } from "../components/PaperDetailWorkspace";
import {
  cleanDisplayText,
  displayValueLabel,
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

function discoveryTags(paper: PaperCardView): string[] {
  return [...paper.taxonomy.tasks, ...paper.taxonomy.methods, ...paper.taxonomy.themes].slice(0, 3);
}

function authorSummary(paper: PaperCardView): string {
  if (!paper.bibliography.authors.length) {
    return "作者待补充";
  }
  return paper.bibliography.authors.length > 1 ? `${paper.bibliography.authors[0]} 等` : paper.bibliography.authors[0];
}

function HomeToolbar({
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
  resultsCount,
  searchInputRef,
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
  resultsCount: number;
  searchInputRef: RefObject<InputRef | null>;
}) {
  return (
    <div className="console-toolbar">
      <div className="console-toolbar-main">
        <div className="console-toolbar-copy">
          <Text className="section-kicker">Translate Paper Forest</Text>
          <Title level={2} className="console-title">
            研究发现台
          </Title>
          <Paragraph className="console-support-copy">
            左侧快速扫读，右侧按需展开 Summary / Method / Metadata / Related。
          </Paragraph>
        </div>

        <div className="console-toolbar-stats">
          <div className="console-stat-tile">
            <Text className="console-stat-label">当前结果</Text>
            <Text className="console-stat-value">{resultsCount}</Text>
          </div>
          <div className="console-stat-tile">
            <Text className="console-stat-label">论文总数</Text>
            <Text className="console-stat-value">{payload.site_meta.paper_count}</Text>
          </div>
          <div className="console-stat-tile">
            <Text className="console-stat-label">精选条目</Text>
            <Text className="console-stat-value">{payload.featured.length}</Text>
          </div>
          <div className="console-stat-tile">
            <Text className="console-stat-label">最近生成</Text>
            <Text className="console-stat-value is-compact">{payload.site_meta.generated_at}</Text>
          </div>
        </div>
      </div>

      <div className="console-toolbar-controls">
        <Input
          ref={searchInputRef}
          allowClear
          size="large"
          prefix={<FileSearchOutlined />}
          placeholder="搜索标题、作者、story、editorial、taxonomy"
          value={query}
          onChange={(event) => startTransition(() => setQuery(event.target.value))}
          className="search-input"
        />
        <Select
          mode="multiple"
          allowClear
          size="large"
          placeholder="主题"
          value={selectedThemes}
          options={payload.filters.themes.map((item) => ({ label: `${displayValueLabel(item.label)} (${item.count})`, value: item.label }))}
          onChange={(value) => startTransition(() => setSelectedThemes(value))}
        />
        <Select
          mode="multiple"
          allowClear
          size="large"
          placeholder="任务"
          value={selectedTasks}
          options={payload.filters.tasks.map((item) => ({ label: `${displayValueLabel(item.label)} (${item.count})`, value: item.label }))}
          onChange={(value) => startTransition(() => setSelectedTasks(value))}
        />
        <Select
          mode="multiple"
          allowClear
          size="large"
          placeholder="方法"
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
      </div>

      <div className="console-toolbar-foot">
        <div className="console-chip-row">
          {payload.featured.map((paper) => (
            <TooltipTag key={paper.id} label={paper.bibliography.title} maxChars={24} className="chip-tag chip-tag-highlight" />
          ))}
        </div>
        <div className="console-chip-row">
          {payload.recent_titles.slice(0, 4).map((title) => (
            <TooltipTag key={title} label={cleanDisplayText(title, 24)} maxChars={24} className="chip-tag chip-tag-route-overview" />
          ))}
        </div>
      </div>
    </div>
  );
}

function PaperListItem({
  paper,
  selected,
  featured,
  onSelect,
}: {
  paper: PaperCardView;
  selected: boolean;
  featured: boolean;
  onSelect: () => void;
}) {
  return (
    <button type="button" className={`paper-list-item${selected ? " is-selected" : ""}`} onClick={onSelect}>
      <div className="paper-list-item-header">
        <div className="paper-list-item-title-block">
          <Text className="paper-list-item-title">{paper.bibliography.title}</Text>
          <Flex wrap="wrap" gap={8}>
            {paper.editorial.verdict ? <Tag className={verdictTagClass(paper.editorial.verdict)}>{paper.editorial.verdict}</Tag> : null}
            <Tag className={routeTagClass(paper.editorial.reading_route)}>{recommendedRouteLabel(paper.editorial.reading_route)}</Tag>
            {featured || paper.editorial.graph_worthy ? <Tag className="chip-tag chip-tag-worth">精选</Tag> : null}
          </Flex>
        </div>
      </div>

      <TooltipText
        text={paper.story.paper_one_liner || paper.editorial.summary || "暂无一句话摘要。"}
        as="paragraph"
        rows={2}
        className="paper-list-item-summary"
      />

      <Paragraph className="paper-list-item-meta">
        {authorSummary(paper)} · {paper.bibliography.venue || "未知 venue"} · {paper.bibliography.year || "未知年份"}
      </Paragraph>

      <Flex wrap="wrap" gap={8} className="paper-list-item-tags">
        {discoveryTags(paper).map((tag) => (
          <TooltipTag key={`${paper.id}-${tag}`} label={displayValueLabel(tag)} maxChars={18} className="chip-tag chip-tag-tone-blue" />
        ))}
      </Flex>
    </button>
  );
}

function isEditableTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) {
    return false;
  }
  return Boolean(
    target.isContentEditable ||
      target.closest("input, textarea, select, [contenteditable='true']") ||
      target.closest(".ant-select") ||
      target.closest(".ant-drawer"),
  );
}

export function HomePage({ payload }: { payload: SiteIndexPayload }) {
  const screens = Grid.useBreakpoint();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const searchInputRef = useRef<InputRef>(null);
  const featuredIds = useMemo(() => new Set(payload.featured.map((paper) => paper.id)), [payload.featured]);

  const [query, setQuery] = useState("");
  const [selectedThemes, setSelectedThemes] = useState<string[]>([]);
  const [selectedTasks, setSelectedTasks] = useState<string[]>([]);
  const [selectedMethods, setSelectedMethods] = useState<string[]>([]);
  const [sortBy, setSortBy] = useState("year-desc");
  const [drawerOpen, setDrawerOpen] = useState(false);
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

  const requestedPaperId = searchParams.get("paper") ?? "";
  const selectedPaperId = filteredPapers.some((paper) => paper.id === requestedPaperId) ? requestedPaperId : filteredPapers[0]?.id ?? "";
  const selectedPaper = filteredPapers.find((paper) => paper.id === selectedPaperId) ?? null;
  const isDesktop = Boolean(screens.xl);
  const isTablet = Boolean(screens.md && !screens.xl);
  const isMobile = !screens.md;

  function updateSelectedPaper(paperId: string, replace = false) {
    const nextParams = new URLSearchParams(searchParams);
    if (paperId) {
      nextParams.set("paper", paperId);
    } else {
      nextParams.delete("paper");
    }
    setSearchParams(nextParams, { replace });
  }

  function handleSelectPaper(paper: PaperCardView) {
    if (isMobile) {
      navigate(paperRoute(paper.source.route_path, paper.id));
      return;
    }
    updateSelectedPaper(paper.id);
    if (isTablet) {
      setDrawerOpen(true);
    }
  }

  useEffect(() => {
    if (requestedPaperId !== selectedPaperId) {
      updateSelectedPaper(selectedPaperId, true);
    }
  }, [requestedPaperId, selectedPaperId]);

  useEffect(() => {
    if (!isTablet) {
      setDrawerOpen(false);
    }
  }, [isTablet]);

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (!filteredPapers.length || event.metaKey || event.ctrlKey || event.altKey) {
        return;
      }
      if (event.key === "/" && !isEditableTarget(event.target)) {
        event.preventDefault();
        searchInputRef.current?.focus({ cursor: "all" });
        return;
      }
      if (isEditableTarget(event.target)) {
        return;
      }
      const currentIndex = filteredPapers.findIndex((paper) => paper.id === selectedPaperId);
      if (event.key === "ArrowDown") {
        event.preventDefault();
        const nextPaper = filteredPapers[Math.min(currentIndex + 1, filteredPapers.length - 1)] ?? filteredPapers[0];
        if (nextPaper) {
          updateSelectedPaper(nextPaper.id);
        }
        return;
      }
      if (event.key === "ArrowUp") {
        event.preventDefault();
        const nextPaper = filteredPapers[Math.max(currentIndex - 1, 0)] ?? filteredPapers[0];
        if (nextPaper) {
          updateSelectedPaper(nextPaper.id);
        }
        return;
      }
      if (event.key === "Enter" && selectedPaper) {
        event.preventDefault();
        navigate(paperRoute(selectedPaper.source.route_path, selectedPaper.id));
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [filteredPapers, navigate, selectedPaper, selectedPaperId, searchParams]);

  const openDetailAction = selectedPaper ? (
    <Button type="primary" icon={<ReadOutlined />} onClick={() => navigate(paperRoute(selectedPaper.source.route_path, selectedPaper.id))}>
      打开独立详情页
    </Button>
  ) : null;

  return (
    <div className="page-stack console-page">
      <HomeToolbar
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
        resultsCount={filteredPapers.length}
        searchInputRef={searchInputRef}
      />

      <div className="console-layout">
        <section className="console-list-panel">
          <div className="console-panel-header">
            <div>
              <Text className="section-kicker">Results</Text>
              <Title level={4} className="console-panel-title">
                {filteredPapers.length ? `${filteredPapers.length} 篇候选论文` : "没有匹配结果"}
              </Title>
            </div>
            {selectedPaper ? (
              <Button icon={<LinkOutlined />} onClick={() => navigate(paperRoute(selectedPaper.source.route_path, selectedPaper.id))}>
                详情页
              </Button>
            ) : null}
          </div>

          {filteredPapers.length ? (
            <div className="paper-list-scroll">
              {filteredPapers.map((paper) => (
                <PaperListItem
                  key={paper.id}
                  paper={paper}
                  selected={paper.id === selectedPaperId}
                  featured={featuredIds.has(paper.id)}
                  onSelect={() => handleSelectPaper(paper)}
                />
              ))}
            </div>
          ) : (
            <div className="console-empty-panel">
              <Empty description="可以调整检索词或筛选条件，再试一次。" />
            </div>
          )}
        </section>

        {isDesktop ? (
          <section className="console-detail-panel">
            <PaperDetailWorkspace
              paperId={selectedPaperId}
              payload={payload}
              headerActions={openDetailAction}
              className="console-workspace"
            />
          </section>
        ) : null}
      </div>

      <Drawer
        placement="right"
        title="论文详情"
        width={screens.lg ? 760 : "100%"}
        open={drawerOpen && isTablet && Boolean(selectedPaperId)}
        onClose={() => setDrawerOpen(false)}
        className="console-detail-drawer"
      >
        <PaperDetailWorkspace
          paperId={selectedPaperId}
          payload={payload}
          headerActions={openDetailAction}
          className="console-workspace is-drawer"
        />
      </Drawer>
    </div>
  );
}
