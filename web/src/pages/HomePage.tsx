import { Button, Drawer, Empty, Flex, Grid, Input, Modal, Select, Tag, Typography, type InputRef } from "antd";
import { FileSearchOutlined, FilterOutlined, LinkOutlined, ReadOutlined } from "@ant-design/icons";
import { startTransition, useDeferredValue, useEffect, useMemo, useRef, useState, type RefObject } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { PaperDetailWorkspace } from "../components/PaperDetailWorkspace";
import {
  displayValueLabel,
  formatLocalDateTime,
  formatLocalDateTimeDetail,
  matchesTags,
  matchesTitleQuery,
  paperRoute,
  recommendedRouteLabel,
  routeTagClass,
  selectedFilterSummary,
  verdictTagClass,
} from "../lib/paper";
import { TooltipTag } from "../components/OverflowTooltip";
import type { PaperCardView, SiteIndexPayload } from "../types";

const { Title, Paragraph, Text } = Typography;
const SORT_OPTIONS = [
  { label: "年份从新到旧", value: "year-desc" },
  { label: "年份从旧到新", value: "year-asc" },
  { label: "标题 A-Z", value: "title-asc" },
] as const;

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
  titleQuery,
  setTitleQuery,
  selectedThemes,
  selectedTasks,
  selectedMethods,
  draftThemes,
  setDraftThemes,
  draftTasks,
  setDraftTasks,
  draftMethods,
  setDraftMethods,
  advancedSearchOpen,
  openAdvancedSearch,
  closeAdvancedSearch,
  applyAdvancedSearch,
  clearDraftFilters,
  sortBy,
  setSortBy,
  resultsCount,
  searchInputRef,
}: {
  payload: SiteIndexPayload;
  titleQuery: string;
  setTitleQuery: (value: string) => void;
  selectedThemes: string[];
  selectedTasks: string[];
  selectedMethods: string[];
  draftThemes: string[];
  setDraftThemes: (value: string[]) => void;
  draftTasks: string[];
  setDraftTasks: (value: string[]) => void;
  draftMethods: string[];
  setDraftMethods: (value: string[]) => void;
  advancedSearchOpen: boolean;
  openAdvancedSearch: () => void;
  closeAdvancedSearch: () => void;
  applyAdvancedSearch: () => void;
  clearDraftFilters: () => void;
  sortBy: string;
  setSortBy: (value: string) => void;
  resultsCount: number;
  searchInputRef: RefObject<InputRef | null>;
}) {
  const generatedAtLabel = formatLocalDateTime(payload.site_meta.generated_at);
  const generatedAtDetail = formatLocalDateTimeDetail(payload.site_meta.generated_at);
  const sortLabel = SORT_OPTIONS.find((item) => item.value === sortBy)?.label || SORT_OPTIONS[0].label;
  const filterSummaries = [
    selectedThemes.length ? selectedFilterSummary("主题", selectedThemes.length) : "",
    selectedTasks.length ? selectedFilterSummary("任务", selectedTasks.length) : "",
    selectedMethods.length ? selectedFilterSummary("方法", selectedMethods.length) : "",
  ].filter(Boolean);
  const appliedFilterCount = selectedThemes.length + selectedTasks.length + selectedMethods.length;
  const contextItems = [
    `当前 ${resultsCount} 篇`,
    `总库 ${payload.site_meta.paper_count} 篇`,
    `排序 ${sortLabel}`,
    `更新于 ${generatedAtLabel}`,
    ...filterSummaries,
  ];

  return (
    <div className="console-toolbar">
      <div className="console-toolbar-main">
        <div className="console-toolbar-copy">
          <Text className="section-kicker">Translate Paper Forest</Text>
          <Title level={2} className="console-title">
            研究发现台
          </Title>
          <Paragraph className="console-support-copy">面向筛选、切换与深读的双栏工作台。</Paragraph>
        </div>

        <div className="console-toolbar-context">
          {contextItems.map((item) => (
            <Text
              key={item}
              className={`console-context-chip${filterSummaries.includes(item) ? " is-filter" : ""}`}
              title={item.startsWith("更新于 ") ? generatedAtDetail || payload.site_meta.generated_at : undefined}
            >
              {item}
            </Text>
          ))}
        </div>
      </div>

      <div className="console-toolbar-controls">
        <Input
          ref={searchInputRef}
          allowClear
          size="large"
          prefix={<FileSearchOutlined />}
          placeholder="搜索论文标题…"
          value={titleQuery}
          onChange={(event) => startTransition(() => setTitleQuery(event.target.value))}
          className="search-input console-search-control"
        />
        <Button
          icon={<FilterOutlined />}
          onClick={openAdvancedSearch}
          className={`console-advanced-trigger${appliedFilterCount ? " is-active" : ""}`}
        >
          <span>高级搜索</span>
          {appliedFilterCount ? <span className="console-advanced-count">{appliedFilterCount}</span> : null}
        </Button>
        <Select
          size="large"
          value={sortBy}
          options={SORT_OPTIONS.map((item) => ({ label: item.label, value: item.value }))}
          onChange={(value) => startTransition(() => setSortBy(value))}
          className="console-sort-control"
        />
      </div>

      {filterSummaries.length ? (
        <div className="console-active-filter-row">
          {filterSummaries.map((item) => (
            <Text key={item} className="console-active-filter-chip">
              {item}
            </Text>
          ))}
        </div>
      ) : null}

      <Modal
        title="高级搜索"
        open={advancedSearchOpen}
        onCancel={closeAdvancedSearch}
        width={880}
        className="console-advanced-modal"
        footer={[
          <Button key="clear" onClick={clearDraftFilters}>
            清空筛选
          </Button>,
          <Button key="cancel" onClick={closeAdvancedSearch}>
            取消
          </Button>,
          <Button key="confirm" type="primary" onClick={applyAdvancedSearch}>
            确认
          </Button>,
        ]}
        destroyOnHidden={false}
      >
        <div className="console-advanced-modal-body">
          <section className="console-advanced-section">
            <Text className="console-advanced-section-title">主题</Text>
            <Select
              mode="multiple"
              allowClear
              size="large"
              maxTagCount={0}
              maxTagPlaceholder={() => selectedFilterSummary("主题", draftThemes.length)}
              placeholder="按主题筛选"
              value={draftThemes}
              options={payload.filters.themes.map((item) => ({ label: `${displayValueLabel(item.label)} (${item.count})`, value: item.label }))}
              onChange={(value) => startTransition(() => setDraftThemes(value))}
              className="console-select-control"
            />
          </section>
          <section className="console-advanced-section">
            <Text className="console-advanced-section-title">任务</Text>
            <Select
              mode="multiple"
              allowClear
              size="large"
              maxTagCount={0}
              maxTagPlaceholder={() => selectedFilterSummary("任务", draftTasks.length)}
              placeholder="按任务筛选"
              value={draftTasks}
              options={payload.filters.tasks.map((item) => ({ label: `${displayValueLabel(item.label)} (${item.count})`, value: item.label }))}
              onChange={(value) => startTransition(() => setDraftTasks(value))}
              className="console-select-control"
            />
          </section>
          <section className="console-advanced-section">
            <Text className="console-advanced-section-title">方法</Text>
            <Select
              mode="multiple"
              allowClear
              size="large"
              maxTagCount={0}
              maxTagPlaceholder={() => selectedFilterSummary("方法", draftMethods.length)}
              placeholder="按方法筛选"
              value={draftMethods}
              options={payload.filters.methods.map((item) => ({ label: `${displayValueLabel(item.label)} (${item.count})`, value: item.label }))}
              onChange={(value) => startTransition(() => setDraftMethods(value))}
              className="console-select-control"
            />
          </section>
        </div>
      </Modal>
    </div>
  );
}

function PaperListItem({
  paper,
  selected,
  featured,
  onSelect,
  itemRef,
}: {
  paper: PaperCardView;
  selected: boolean;
  featured: boolean;
  onSelect: () => void;
  itemRef?: (node: HTMLButtonElement | null) => void;
}) {
  return (
    <button type="button" ref={itemRef} className={`paper-list-item${selected ? " is-selected" : ""}`} onClick={onSelect}>
      <Flex wrap="wrap" gap={8} className="paper-list-item-decision">
        {paper.editorial.verdict ? <Tag className={verdictTagClass(paper.editorial.verdict)}>{paper.editorial.verdict}</Tag> : null}
        <Tag className={routeTagClass(paper.editorial.reading_route)}>{recommendedRouteLabel(paper.editorial.reading_route)}</Tag>
        {featured || paper.editorial.graph_worthy ? <Tag className="chip-tag chip-tag-worth">精选</Tag> : null}
      </Flex>
      <Text className="paper-list-item-title">{paper.bibliography.title}</Text>
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
  const paperItemRefs = useRef(new Map<string, HTMLButtonElement>());
  const featuredIds = useMemo(() => new Set(payload.featured.map((paper) => paper.id)), [payload.featured]);

  const [titleQuery, setTitleQuery] = useState("");
  const [selectedThemes, setSelectedThemes] = useState<string[]>([]);
  const [selectedTasks, setSelectedTasks] = useState<string[]>([]);
  const [selectedMethods, setSelectedMethods] = useState<string[]>([]);
  const [draftThemes, setDraftThemes] = useState<string[]>([]);
  const [draftTasks, setDraftTasks] = useState<string[]>([]);
  const [draftMethods, setDraftMethods] = useState<string[]>([]);
  const [sortBy, setSortBy] = useState("year-desc");
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [advancedSearchOpen, setAdvancedSearchOpen] = useState(false);
  const deferredTitleQuery = useDeferredValue(titleQuery);

  function openAdvancedSearch() {
    setDraftThemes(selectedThemes);
    setDraftTasks(selectedTasks);
    setDraftMethods(selectedMethods);
    setAdvancedSearchOpen(true);
  }

  function closeAdvancedSearch() {
    setDraftThemes(selectedThemes);
    setDraftTasks(selectedTasks);
    setDraftMethods(selectedMethods);
    setAdvancedSearchOpen(false);
  }

  function clearDraftFilters() {
    startTransition(() => {
      setDraftThemes([]);
      setDraftTasks([]);
      setDraftMethods([]);
    });
  }

  function applyAdvancedSearch() {
    startTransition(() => {
      setSelectedThemes(draftThemes);
      setSelectedTasks(draftTasks);
      setSelectedMethods(draftMethods);
    });
    setAdvancedSearchOpen(false);
  }

  const filteredPapers = useMemo(() => {
    let papers = payload.papers.filter((paper) => {
      const searchOkay = matchesTitleQuery(paper.bibliography.title, deferredTitleQuery);
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
  }, [deferredTitleQuery, payload.papers, selectedMethods, selectedTasks, selectedThemes, sortBy]);

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
    const item = paperItemRefs.current.get(selectedPaperId);
    if (!item || isMobile) {
      return;
    }
    const frameId = window.requestAnimationFrame(() => {
      item.scrollIntoView({ block: "nearest" });
    });
    return () => window.cancelAnimationFrame(frameId);
  }, [isMobile, selectedPaperId]);

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (advancedSearchOpen || !filteredPapers.length || event.metaKey || event.ctrlKey || event.altKey) {
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
  }, [advancedSearchOpen, filteredPapers, navigate, selectedPaper, selectedPaperId, searchParams]);

  const openDetailAction = selectedPaper ? (
    <Button type="primary" icon={<ReadOutlined />} onClick={() => navigate(paperRoute(selectedPaper.source.route_path, selectedPaper.id))}>
      在独立页打开
    </Button>
  ) : null;

  return (
    <div className="page-stack console-page">
      <HomeToolbar
        payload={payload}
        titleQuery={titleQuery}
        setTitleQuery={setTitleQuery}
        selectedThemes={selectedThemes}
        selectedTasks={selectedTasks}
        selectedMethods={selectedMethods}
        draftThemes={draftThemes}
        setDraftThemes={setDraftThemes}
        draftTasks={draftTasks}
        setDraftTasks={setDraftTasks}
        draftMethods={draftMethods}
        setDraftMethods={setDraftMethods}
        advancedSearchOpen={advancedSearchOpen}
        openAdvancedSearch={openAdvancedSearch}
        closeAdvancedSearch={closeAdvancedSearch}
        applyAdvancedSearch={applyAdvancedSearch}
        clearDraftFilters={clearDraftFilters}
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
              <Button size="small" icon={<LinkOutlined />} onClick={() => navigate(paperRoute(selectedPaper.source.route_path, selectedPaper.id))}>
                在独立页打开
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
                  itemRef={(node) => {
                    if (node) {
                      paperItemRefs.current.set(paper.id, node);
                    } else {
                      paperItemRefs.current.delete(paper.id);
                    }
                  }}
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
