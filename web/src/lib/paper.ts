import type {
  FigureTableIndexItem,
  LinkSet,
  NeighborItem,
  PaperRecord,
  PaperRelation,
  RetrievalProfile,
  SitePayload,
} from "../types";

export function inlinePayload(): SitePayload | null {
  const node = document.getElementById("paper-neighbors-data");
  const text = node?.textContent?.trim();
  if (!text || text === "__PAPER_NEIGHBORS_DATA__") {
    return null;
  }
  return JSON.parse(text) as SitePayload;
}

export async function loadPayload(): Promise<SitePayload> {
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

export function paperRoute(routePath: string | undefined, paperId: string): string {
  if (routePath?.startsWith("#")) {
    return routePath.slice(1);
  }
  return `/paper/${paperId}`;
}

export function markdownHref(path: string | undefined): string | undefined {
  if (!path) {
    return undefined;
  }
  if (path.startsWith("#")) {
    return path;
  }
  return path.replace(/^\/+/, "");
}

export function searchableText(paper: PaperRecord): string {
  return [
    paper.title,
    ...paper.authors,
    paper.venue,
    String(paper.year ?? ""),
    paper.abstract_raw ?? "",
    paper.abstract_zh ?? "",
    paper.summary.one_liner,
    paper.summary.abstract_summary ?? "",
    paper.summary.research_value ?? "",
    paper.research_problem ?? "",
    ...paper.core_contributions,
    paper.author_conclusion ?? "",
    paper.editor_note ?? "",
    ...paper.research_tags.themes,
    ...paper.research_tags.tasks,
    ...paper.research_tags.methods,
    ...paper.research_tags.representations,
    ...paper.retrieval_profile.problem_spaces,
  ]
    .join(" ")
    .toLowerCase();
}

export function matchesTags(paperTags: string[], selected: string[]): boolean {
  if (!selected.length) {
    return true;
  }
  return selected.every((tag) => paperTags.includes(tag));
}

export function formatDate(value: string | null | undefined): string {
  if (!value) {
    return "未知时间";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export function formatYear(value: number | string | null | undefined): string {
  return value === null || value === undefined || value === "" ? "未知年份" : String(value);
}

export function normalizeExternalLink(kind: keyof LinkSet, value: string | null): string | null {
  if (!value) {
    return null;
  }
  if (/^https?:\/\//i.test(value)) {
    return value;
  }
  if (kind === "arxiv") {
    return `https://arxiv.org/abs/${value}`;
  }
  if (kind === "doi") {
    return `https://doi.org/${value}`;
  }
  return value;
}

export function firstExternalLinks(links: LinkSet): Array<{ key: keyof LinkSet; label: string; href: string }> {
  const labels: Record<keyof LinkSet, string> = {
    pdf: "PDF",
    arxiv: "arXiv",
    project: "Project",
    code: "Code",
    doi: "DOI",
    data: "Data",
  };
  return (["pdf", "arxiv", "project", "code", "doi", "data"] as Array<keyof LinkSet>)
    .map((key) => ({ key, label: labels[key], href: normalizeExternalLink(key, links[key]) }))
    .filter((item): item is { key: keyof LinkSet; label: string; href: string } => Boolean(item.href));
}

export function relationTargetTitle(payload: SitePayload, relation: PaperRelation): string {
  const target = payload.papers.find((paper) => paper.paper_id === relation.target_paper_id);
  return target?.title ?? relation.target_paper_id;
}

export function relationTargetRoute(payload: SitePayload, relation: PaperRelation): string | null {
  const target = payload.papers.find((paper) => paper.paper_id === relation.target_paper_id);
  return target ? paperRoute(target.route_path, target.paper_id) : null;
}

export function confidenceTone(confidence: string | null | undefined): "green" | "gold" | "default" {
  if (confidence === "high") {
    return "green";
  }
  if (confidence === "medium") {
    return "gold";
  }
  return "default";
}

export function scoreBand(score: number): string {
  if (score >= 12) {
    return "高相关";
  }
  if (score >= 7) {
    return "中相关";
  }
  return "低相关";
}

export function sharedSignalPreview(sharedSignals: NeighborItem["shared_signals"]): string[] {
  return Object.entries(sharedSignals)
    .flatMap(([key, values]) => values.slice(0, 2).map((value) => `${key}: ${value}`))
    .slice(0, 3);
}

export function compactList(values: string[], limit = 4): string[] {
  return values.filter(Boolean).slice(0, limit);
}

export function flattenRetrievalProfile(profile: RetrievalProfile): Array<{ label: string; values: string[] }> {
  return [
    { label: "Problem spaces", values: profile.problem_spaces },
    { label: "Task axes", values: profile.task_axes },
    { label: "Approach axes", values: profile.approach_axes },
    { label: "Input axes", values: profile.input_axes },
    { label: "Output axes", values: profile.output_axes },
    { label: "Modality axes", values: profile.modality_axes },
    { label: "Comparison axes", values: profile.comparison_axes },
  ];
}

export function filterFigureTableItems(items: FigureTableIndexItem[], query: string): FigureTableIndexItem[] {
  const keyword = query.trim().toLowerCase();
  if (!keyword) {
    return items;
  }
  return items.filter((item) => `${item.label} ${item.caption}`.toLowerCase().includes(keyword));
}

export function debugEnabled(): boolean {
  const search = new URLSearchParams(window.location.search);
  if (search.get("debug") === "1") {
    return true;
  }

  const hash = window.location.hash;
  const queryIndex = hash.indexOf("?");
  if (queryIndex === -1) {
    return false;
  }
  const hashSearch = new URLSearchParams(hash.slice(queryIndex + 1));
  return hashSearch.get("debug") === "1";
}
