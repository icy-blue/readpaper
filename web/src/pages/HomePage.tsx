import { Button, Drawer, Empty, Flex, Grid, Input, Modal, Popover, Select, Tooltip, Typography } from "antd";
import {
  CalendarOutlined,
  CheckOutlined,
  DownOutlined,
  FileSearchOutlined,
  FilterOutlined,
  FontSizeOutlined,
} from "@ant-design/icons";
import { startTransition, useDeferredValue, useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { useSearchParams } from "react-router-dom";
import { PaperDetailWorkspace } from "../components/PaperDetailWorkspace";
import {
  displayValueLabel,
  formatLocalDateTime,
  formatLocalDateTimeDetail,
  matchesTags,
  matchesTitleQuery,
  selectedFilterSummary,
} from "../lib/paper";
import { OverflowCount, TooltipTag } from "../components/OverflowTooltip";
import type { PaperCardView, SiteIndexPayload } from "../types";

const { Title, Paragraph, Text } = Typography;
const HOME_HEADER_SLOT_ID = "home-header-slot";
type SortField = "year" | "title";
type SortDirection = "asc" | "desc";

const SORT_FIELD_OPTIONS = [
  { label: "年份", value: "year" },
  { label: "标题", value: "title" },
] as const;

function sortFieldOf(sortBy: string): SortField {
  return sortBy.startsWith("title") ? "title" : "year";
}

function sortDirectionOf(sortBy: string): SortDirection {
  return sortBy.endsWith("asc") ? "asc" : "desc";
}

function buildSortValue(field: SortField, direction: SortDirection): string {
  return `${field}-${direction}`;
}

function sortDirectionOptions(field: SortField) {
  if (field === "year") {
    return [
      { label: "从晚到早", value: "desc" as const },
      { label: "从早到晚", value: "asc" as const },
    ];
  }

  return [
    { label: "A → Z", value: "asc" as const },
    { label: "Z → A", value: "desc" as const },
  ];
}

function sortButtonLabel(field: SortField, direction: SortDirection): string {
  if (field === "year") {
    return `排序：年份 ${direction === "desc" ? "↓" : "↑"}`;
  }
  return `排序：标题 ${direction === "asc" ? "A → Z" : "Z → A"}`;
}

function sortButtonCompactLabel(field: SortField, direction: SortDirection): string {
  if (field === "year") {
    return direction === "desc" ? "年↓" : "年↑";
  }
  return direction === "asc" ? "A-Z" : "Z-A";
}

function discoveryTags(paper: PaperCardView): string[] {
  return [...new Set([...paper.taxonomy.tasks, ...paper.taxonomy.methods, ...paper.taxonomy.themes])];
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
  inHeader,
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
  inHeader: boolean;
}) {
  const sortField = sortFieldOf(sortBy);
  const sortDirection = sortDirectionOf(sortBy);
  const [sortMenuOpen, setSortMenuOpen] = useState(false);
  const appliedFilterCount = selectedThemes.length + selectedTasks.length + selectedMethods.length;
  const activeSortDirectionOptions = sortDirectionOptions(sortField);

  function updateSort(nextSortBy: string) {
    startTransition(() => setSortBy(nextSortBy));
    setSortMenuOpen(false);
  }

  const sortMenu = (
    <div className="console-sort-menu" role="menu" aria-label="排序选项">
      <section className="console-sort-menu-group" aria-labelledby="sort-field-title">
        <Text id="sort-field-title" className="console-sort-menu-title">
          排序字段
        </Text>
        <div className="console-sort-menu-options">
          {SORT_FIELD_OPTIONS.map((item) => {
            const isActive = sortField === item.value;
            return (
              <button
                key={item.value}
                type="button"
                className={`console-sort-menu-option${isActive ? " is-active" : ""}`}
                onClick={() => updateSort(buildSortValue(item.value, sortDirection))}
                aria-pressed={isActive}
              >
                <span className="console-sort-menu-option-copy">
                  <span className="console-sort-menu-option-label">{item.label}</span>
                </span>
                <span className="console-sort-menu-option-mark" aria-hidden="true">
                  {isActive ? <CheckOutlined /> : null}
                </span>
              </button>
            );
          })}
        </div>
      </section>

      <section className="console-sort-menu-group" aria-labelledby="sort-direction-title">
        <Text id="sort-direction-title" className="console-sort-menu-title">
          排序方向
        </Text>
        <div className="console-sort-menu-options">
          {activeSortDirectionOptions.map((item) => {
            const isActive = sortDirection === item.value;
            return (
              <button
                key={item.value}
                type="button"
                className={`console-sort-menu-option${isActive ? " is-active" : ""}`}
                onClick={() => updateSort(buildSortValue(sortField, item.value))}
                aria-pressed={isActive}
              >
                <span className="console-sort-menu-option-copy">
                  <span className="console-sort-menu-option-label">{item.label}</span>
                </span>
                <span className="console-sort-menu-option-mark" aria-hidden="true">
                  {isActive ? <CheckOutlined /> : null}
                </span>
              </button>
            );
          })}
        </div>
      </section>
    </div>
  );

  return (
    <>
      <div className={`console-toolbar${inHeader ? " is-header" : " is-inline"}`}>
        <div className="console-toolbar-controls">
          <span className="console-toolbar-control-shell">
            <Input
              allowClear
              size="large"
              prefix={<FileSearchOutlined />}
              placeholder="搜索论文标题…"
              value={titleQuery}
              onChange={(event) => startTransition(() => setTitleQuery(event.target.value))}
              className="search-input console-search-control"
            />
          </span>
          <span className="console-toolbar-control-shell">
            <Button
              icon={<FilterOutlined />}
              onClick={openAdvancedSearch}
              className={`console-advanced-trigger${appliedFilterCount ? " is-active" : ""}`}
            >
              <span>筛选</span>
              {appliedFilterCount ? <span className="console-advanced-count">{appliedFilterCount}</span> : null}
            </Button>
          </span>
          <Popover
            trigger="click"
            open={sortMenuOpen}
            onOpenChange={setSortMenuOpen}
            placement={inHeader ? "bottomRight" : "bottomLeft"}
            content={sortMenu}
            overlayClassName="console-sort-popover"
          >
            <Tooltip title={sortButtonLabel(sortField, sortDirection)} trigger={["hover", "focus"]}>
              <span className="console-sort-trigger-shell">
                <Button
                  className={`console-sort-trigger${sortMenuOpen ? " is-open" : ""}`}
                  aria-label={sortButtonLabel(sortField, sortDirection)}
                >
                  <span className="console-sort-trigger-main">
                    {sortField === "year" ? <CalendarOutlined /> : <FontSizeOutlined />}
                    <span>{sortButtonCompactLabel(sortField, sortDirection)}</span>
                  </span>
                  <DownOutlined className={`console-sort-trigger-caret${sortMenuOpen ? " is-open" : ""}`} />
                </Button>
              </span>
            </Tooltip>
          </Popover>
        </div>
      </div>

      <Modal
        title="筛选"
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
    </>
  );
}

function PaperListItem({
  paper,
  selected,
  onSelect,
  itemRef,
}: {
  paper: PaperCardView;
  selected: boolean;
  onSelect: () => void;
  itemRef?: (node: HTMLButtonElement | null) => void;
}) {
  const tagLabels = discoveryTags(paper).map((tag) => displayValueLabel(tag));
  const visibleTagLabels = tagLabels.slice(0, 2);
  const hiddenTagLabels = tagLabels.slice(2);

  return (
    <button type="button" ref={itemRef} className={`paper-list-item${selected ? " is-selected" : ""}`} onClick={onSelect}>
      <Text className="paper-list-item-title">{paper.bibliography.title}</Text>
      <Paragraph className="paper-list-item-meta">
        {authorSummary(paper)} · {paper.bibliography.venue || "未知 venue"} · {paper.bibliography.year || "未知年份"}
      </Paragraph>
      {paper.story.paper_one_liner ? (
        <Paragraph className="workspace-body-copy">{paper.story.paper_one_liner}</Paragraph>
      ) : null}
      {paper.editorial.research_position ? (
        <Paragraph className="workspace-support-copy">{paper.editorial.research_position}</Paragraph>
      ) : null}
      <div className="paper-list-item-tags">
        {visibleTagLabels.map((tagLabel) => (
          <TooltipTag key={`${paper.id}-${tagLabel}`} label={tagLabel} maxChars={18} className="chip-tag chip-tag-tone-blue" />
        ))}
        <OverflowCount items={hiddenTagLabels} mode="tag" className="chip-tag chip-tag-tone-blue" />
      </div>
    </button>
  );
}

export function HomePage({ payload }: { payload: SiteIndexPayload }) {
  const screens = Grid.useBreakpoint();
  const [searchParams, setSearchParams] = useSearchParams();
  const paperItemRefs = useRef(new Map<string, HTMLButtonElement>());
  const [headerSlot, setHeaderSlot] = useState<HTMLElement | null>(null);

  const [titleQuery, setTitleQuery] = useState("");
  const [selectedThemes, setSelectedThemes] = useState<string[]>([]);
  const [selectedTasks, setSelectedTasks] = useState<string[]>([]);
  const [selectedMethods, setSelectedMethods] = useState<string[]>([]);
  const [draftThemes, setDraftThemes] = useState<string[]>([]);
  const [draftTasks, setDraftTasks] = useState<string[]>([]);
  const [draftMethods, setDraftMethods] = useState<string[]>([]);
  const [sortBy, setSortBy] = useState("year-desc");
  const [advancedSearchOpen, setAdvancedSearchOpen] = useState(false);
  const deferredTitleQuery = useDeferredValue(titleQuery);
  const generatedAtLabel = formatLocalDateTime(payload.site_meta.generated_at);
  const generatedAtDetail = formatLocalDateTimeDetail(payload.site_meta.generated_at);
  const filterSummaries = [
    selectedThemes.length ? selectedFilterSummary("主题", selectedThemes.length) : "",
    selectedTasks.length ? selectedFilterSummary("任务", selectedTasks.length) : "",
    selectedMethods.length ? selectedFilterSummary("方法", selectedMethods.length) : "",
  ].filter(Boolean);
  const panelSubtitle = filterSummaries.length ? filterSummaries.join(" · ") : `更新于 ${generatedAtLabel}`;
  const panelSubtitleTitle = filterSummaries.length ? panelSubtitle : generatedAtDetail || payload.site_meta.generated_at;

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
      if (sortBy === "title-desc") {
        return right.bibliography.title.localeCompare(left.bibliography.title);
      }
      const leftYear = Number(left.bibliography.year ?? 0);
      const rightYear = Number(right.bibliography.year ?? 0);
      return sortBy === "year-asc" ? leftYear - rightYear : rightYear - leftYear;
    });

    return papers;
  }, [deferredTitleQuery, payload.papers, selectedMethods, selectedTasks, selectedThemes, sortBy]);

  const requestedPaperId = searchParams.get("paper") ?? "";
  const detailRequested = searchParams.get("detail") === "1";
  const selectedPaperId = filteredPapers.some((paper) => paper.id === requestedPaperId) ? requestedPaperId : filteredPapers[0]?.id ?? "";
  const isDesktop = Boolean(screens.xl);
  const isMobile = !screens.md;
  const detailDrawerOpen = !isDesktop && detailRequested && Boolean(selectedPaperId);

  useEffect(() => {
    if (!isDesktop) {
      setHeaderSlot(null);
      return;
    }

    setHeaderSlot(document.getElementById(HOME_HEADER_SLOT_ID));
  }, [isDesktop]);

  function updateSelectedPaper(paperId: string, openDetail: boolean, replace = false) {
    const nextParams = new URLSearchParams(searchParams);
    if (paperId) {
      nextParams.set("paper", paperId);
    } else {
      nextParams.delete("paper");
    }
    if (openDetail) {
      nextParams.set("detail", "1");
    } else {
      nextParams.delete("detail");
    }
    setSearchParams(nextParams, { replace });
  }

  function handleSelectPaper(paper: PaperCardView) {
    updateSelectedPaper(paper.id, !isDesktop);
  }

  useEffect(() => {
    const nextDetailRequested = !isDesktop && detailRequested && Boolean(selectedPaperId);
    if (requestedPaperId !== selectedPaperId || detailRequested !== nextDetailRequested) {
      updateSelectedPaper(selectedPaperId, nextDetailRequested, true);
    }
  }, [detailRequested, isDesktop, requestedPaperId, selectedPaperId]);

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
  const toolbar = (
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
      inHeader={isDesktop}
    />
  );

  return (
    <div className="page-stack console-page">
      {isDesktop && headerSlot ? createPortal(toolbar, headerSlot) : null}
      {!isDesktop || !headerSlot ? toolbar : null}

      <div className="console-layout">
        <section className="console-list-panel">
          <div className="console-panel-header">
            <div>
              <Text className="section-kicker">论文列表</Text>
              <Title level={4} className="console-panel-title">
                {filteredPapers.length ? `共 ${filteredPapers.length} 篇论文` : "暂无匹配论文"}
              </Title>
              <Paragraph className="panel-support-copy console-panel-subtitle" title={panelSubtitleTitle}>
                {panelSubtitle}
              </Paragraph>
            </div>
          </div>

          {filteredPapers.length ? (
            <div className="paper-list-scroll">
              {filteredPapers.map((paper) => (
                <PaperListItem
                  key={paper.id}
                  paper={paper}
                  selected={paper.id === selectedPaperId}
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
              layoutMode="home-compact"
              className="console-workspace"
            />
          </section>
        ) : null}
      </div>

      <Drawer
        placement="right"
        title="论文详情"
        width={screens.lg ? 760 : "100%"}
        open={detailDrawerOpen}
        onClose={() => updateSelectedPaper(selectedPaperId, false)}
        className="console-detail-drawer"
      >
        <PaperDetailWorkspace
          paperId={selectedPaperId}
          payload={payload}
          layoutMode="home-compact"
          className="console-workspace is-drawer"
        />
      </Drawer>
    </div>
  );
}
