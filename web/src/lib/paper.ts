import type {
  Bibliography,
  EditorialBlock,
  FigureTableIndexItem,
  NeighborItem,
  PaperCardView,
  PaperDetailViewModel,
  RelationItem,
  SiteIndexPayload,
} from "../types";

type JsonRecord = Record<string, unknown>;

const DISPLAY_VALUE_LABELS: Record<string, string> = {
  "point cloud": "点云",
  "text prompt": "文本提示",
  "segmentation mask": "分割掩码",
  "bounding box": "边界框",
  normals: "法向量",
  "3d": "3D",
  text: "文本",
  image: "图像",
  "representation modeling": "表示建模",
  "architecture design": "架构设计",
  "data curation": "数据构建",
};

const FIGURE_ROLE_LABELS: Record<string, string> = {
  method_overview: "方法总览",
  qualitative_result: "定性结果",
  quantitative_result: "定量结果",
  ablation: "消融实验",
  failure_case: "失败案例",
};

const COMPARISON_ASPECT_LABELS: Record<string, string> = {
  method: "方法差异",
  result: "结果差异",
};

const CLAIM_TYPE_LABELS: Record<string, string> = {
  method: "方法",
  experiment: "实验",
  result: "结果",
  capability: "能力",
  limitation: "局限",
};

const RELATION_TYPE_LABELS: Record<string, string> = {
  compares_to: "对比",
  extends: "扩展",
  uses_dataset: "使用数据集",
  uses_method: "使用方法",
  inspired_by: "受启发于",
  same_problem: "同一问题",
};

const SIGNAL_LABELS: Record<string, string> = {
  tasks: "任务",
  themes: "主题",
  methods: "方法",
  modalities: "模态",
  representations: "表示",
  targets: "线索",
};

const REBUILD_COMMANDS = [
  "使用 repo 内置 extract-paper-meta skill 为目标论文刷新 outputs/meta/<paper-id>.json",
  "python3 scripts/normalize_papers.py --raw-dir outputs/raw --meta-dir outputs/meta --papers-dir outputs/papers",
  "python3 scripts/build_site_derivatives.py --papers-dir outputs/papers --site-dir outputs/site",
  "python3 scripts/render_markdown_site.py --papers-dir outputs/papers --site-dir outputs/site",
  "npm run build:web",
  "python3 scripts/render_html_dashboard.py --site-index-json outputs/site/site-index.json --output outputs/site/index.html",
];

function isRecord(value: unknown): value is JsonRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function validationError(issues: string[]): Error {
  const visibleIssues = issues.slice(0, 8).map((issue) => `- ${issue}`);
  if (issues.length > visibleIssues.length) {
    visibleIssues.push(`- 另有 ${issues.length - visibleIssues.length} 处结构错误`);
  }
  return new Error(
    [
      "检测到站点数据不是当前前端要求的新 schema，已停止渲染。",
      "",
      "请重新执行以下流程后刷新页面：",
      ...REBUILD_COMMANDS.map((command) => `  ${command}`),
      "",
      "首批校验失败项：",
      ...visibleIssues,
    ].join("\n"),
  );
}

function expectRecord(issues: string[], path: string, value: unknown): JsonRecord | null {
  if (!isRecord(value)) {
    issues.push(`${path} 必须是对象`);
    return null;
  }
  return value;
}

function expectString(issues: string[], path: string, value: unknown): void {
  if (typeof value !== "string") {
    issues.push(`${path} 必须是字符串`);
  }
}

function expectStringArray(issues: string[], path: string, value: unknown): void {
  if (!Array.isArray(value) || value.some((item) => typeof item !== "string")) {
    issues.push(`${path} 必须是字符串数组`);
  }
}

function expectOptionalString(issues: string[], path: string, value: unknown): void {
  if (value !== null && value !== undefined && typeof value !== "string") {
    issues.push(`${path} 必须是字符串或 null`);
  }
}

function expectOptionalNumber(issues: string[], path: string, value: unknown): void {
  if (value !== null && value !== undefined && typeof value !== "number") {
    issues.push(`${path} 必须是数字或 null`);
  }
}

function expectBoolean(issues: string[], path: string, value: unknown): void {
  if (typeof value !== "boolean") {
    issues.push(`${path} 必须是布尔值`);
  }
}

function expectObjectArray(issues: string[], path: string, value: unknown): JsonRecord[] | null {
  if (!Array.isArray(value) || value.some((item) => !isRecord(item))) {
    issues.push(`${path} 必须是对象数组`);
    return null;
  }
  return value;
}

function validateBibliography(issues: string[], path: string, value: unknown): void {
  const record = expectRecord(issues, path, value);
  if (!record) {
    return;
  }
  expectString(issues, `${path}.title`, record.title);
  expectStringArray(issues, `${path}.authors`, record.authors);
  expectString(issues, `${path}.venue`, record.venue);
  expectOptionalNumber(issues, `${path}.citation_count`, record.citation_count);

  const identifiers = expectRecord(issues, `${path}.identifiers`, record.identifiers);
  if (identifiers) {
    expectOptionalString(issues, `${path}.identifiers.doi`, identifiers.doi);
    expectOptionalString(issues, `${path}.identifiers.arxiv`, identifiers.arxiv);
  }

  const links = expectRecord(issues, `${path}.links`, record.links);
  if (links) {
    expectOptionalString(issues, `${path}.links.pdf`, links.pdf);
    expectOptionalString(issues, `${path}.links.project`, links.project);
    expectOptionalString(issues, `${path}.links.code`, links.code);
    expectOptionalString(issues, `${path}.links.data`, links.data);
  }
}

function validateSource(issues: string[], path: string, value: unknown): void {
  const record = expectRecord(issues, path, value);
  if (!record) {
    return;
  }
  expectStringArray(issues, `${path}.conversation_ids`, record.conversation_ids);
  expectString(issues, `${path}.paper_path`, record.paper_path);
  expectString(issues, `${path}.route_path`, record.route_path);
}

function validateStory(issues: string[], path: string, value: unknown): void {
  const record = expectRecord(issues, path, value);
  if (!record) {
    return;
  }
  expectOptionalString(issues, `${path}.paper_one_liner`, record.paper_one_liner);
  expectOptionalString(issues, `${path}.problem`, record.problem);
  expectOptionalString(issues, `${path}.method`, record.method);
  expectOptionalString(issues, `${path}.result`, record.result);
}

function validateEditorial(issues: string[], path: string, value: unknown): void {
  const record = expectRecord(issues, path, value);
  if (!record) {
    return;
  }
  expectOptionalString(issues, `${path}.verdict`, record.verdict);
  expectOptionalString(issues, `${path}.summary`, record.summary);
  expectStringArray(issues, `${path}.why_read`, record.why_read);
  expectStringArray(issues, `${path}.strengths`, record.strengths);
  expectStringArray(issues, `${path}.cautions`, record.cautions);
  expectString(issues, `${path}.reading_route`, record.reading_route);
  expectOptionalString(issues, `${path}.research_position`, record.research_position);
  expectBoolean(issues, `${path}.graph_worthy`, record.graph_worthy);
  expectStringArray(issues, `${path}.next_read`, record.next_read);
}

function validateTaxonomy(issues: string[], path: string, value: unknown): void {
  const record = expectRecord(issues, path, value);
  if (!record) {
    return;
  }
  expectStringArray(issues, `${path}.themes`, record.themes);
  expectStringArray(issues, `${path}.tasks`, record.tasks);
  expectStringArray(issues, `${path}.methods`, record.methods);
  expectStringArray(issues, `${path}.modalities`, record.modalities);
  expectStringArray(issues, `${path}.representations`, record.representations);
  expectStringArray(issues, `${path}.novelty_types`, record.novelty_types);
}

function validateNeighborGroups(issues: string[], path: string, value: unknown): void {
  const record = expectRecord(issues, path, value);
  if (!record) {
    return;
  }
  (["task", "method", "comparison"] as const).forEach((key) => {
    const items = expectObjectArray(issues, `${path}.${key}`, record[key]);
    items?.forEach((item, index) => {
      expectString(issues, `${path}.${key}[${index}].paper_id`, item.paper_id);
      expectString(issues, `${path}.${key}[${index}].title`, item.title);
      expectOptionalNumber(issues, `${path}.${key}[${index}].score`, item.score);
      expectOptionalString(issues, `${path}.${key}[${index}].score_level`, item.score_level);
      expectOptionalString(issues, `${path}.${key}[${index}].reason`, item.reason);
      expectOptionalString(issues, `${path}.${key}[${index}].reason_short`, item.reason_short);
      expectRecord(issues, `${path}.${key}[${index}].shared_signals`, item.shared_signals);
    });
  });
}

function validateAssets(issues: string[], path: string, value: unknown): void {
  const record = expectRecord(issues, path, value);
  if (!record) {
    return;
  }
  (["figures", "tables"] as const).forEach((key) => {
    const items = expectObjectArray(issues, `${path}.${key}`, record[key]);
    items?.forEach((item, index) => {
      expectString(issues, `${path}.${key}[${index}].label`, item.label);
      expectString(issues, `${path}.${key}[${index}].caption`, item.caption);
      expectString(issues, `${path}.${key}[${index}].role`, item.role);
      expectString(issues, `${path}.${key}[${index}].importance`, item.importance);
    });
  });
}

function validateRelations(issues: string[], path: string, value: unknown): void {
  const items = expectObjectArray(issues, path, value);
  items?.forEach((item, index) => {
    expectString(issues, `${path}[${index}].type`, item.type);
    expectString(issues, `${path}[${index}].target_kind`, item.target_kind);
    expectOptionalString(issues, `${path}[${index}].target_paper_id`, item.target_paper_id);
    expectOptionalString(issues, `${path}[${index}].label`, item.label);
    expectOptionalString(issues, `${path}[${index}].description`, item.description);
    expectOptionalNumber(issues, `${path}[${index}].confidence`, item.confidence);
    if ("target_semantic_scholar_paper_id" in item) {
      issues.push(`${path}[${index}].target_semantic_scholar_paper_id 已废弃，需重建数据`);
    }
    if ("target_url" in item) {
      issues.push(`${path}[${index}].target_url 已废弃，需重建数据`);
    }
    if (item.target_kind !== "local" && item.target_kind !== "external") {
      issues.push(`${path}[${index}].target_kind 只允许 local 或 external`);
    }
    if (item.target_kind === "local" && typeof item.target_paper_id !== "string") {
      issues.push(`${path}[${index}] local relation 必须包含 target_paper_id`);
    }
    if (item.target_kind === "external" && typeof item.label !== "string") {
      issues.push(`${path}[${index}] external relation 必须包含 label`);
    }
  });
}

function validatePaperCard(issues: string[], path: string, value: unknown): void {
  const record = expectRecord(issues, path, value);
  if (!record) {
    return;
  }
  expectString(issues, `${path}.id`, record.id);
  validateSource(issues, `${path}.source`, record.source);
  validateBibliography(issues, `${path}.bibliography`, record.bibliography);
  validateStory(issues, `${path}.story`, record.story);
  validateEditorial(issues, `${path}.editorial`, record.editorial);
  validateTaxonomy(issues, `${path}.taxonomy`, record.taxonomy);
}

function validateCanonical(issues: string[], path: string, value: unknown): void {
  const record = expectRecord(issues, path, value);
  if (!record) {
    return;
  }
  validatePaperCard(issues, path, value);
  const abstracts = expectRecord(issues, `${path}.abstracts`, record.abstracts);
  if (abstracts) {
    expectOptionalString(issues, `${path}.abstracts.raw`, abstracts.raw);
    expectOptionalString(issues, `${path}.abstracts.zh`, abstracts.zh);
  }
  const researchProblem = expectRecord(issues, `${path}.research_problem`, record.research_problem);
  if (researchProblem) {
    expectOptionalString(issues, `${path}.research_problem.summary`, researchProblem.summary);
    expectStringArray(issues, `${path}.research_problem.gaps`, researchProblem.gaps);
    expectOptionalString(issues, `${path}.research_problem.goal`, researchProblem.goal);
  }
  expectStringArray(issues, `${path}.core_contributions`, record.core_contributions);
  const method = expectRecord(issues, `${path}.method`, record.method);
  if (method) {
    expectOptionalString(issues, `${path}.method.summary`, method.summary);
    expectStringArray(issues, `${path}.method.pipeline_steps`, method.pipeline_steps);
    expectStringArray(issues, `${path}.method.innovations`, method.innovations);
    expectStringArray(issues, `${path}.method.ingredients`, method.ingredients);
    expectStringArray(issues, `${path}.method.inputs`, method.inputs);
    expectStringArray(issues, `${path}.method.outputs`, method.outputs);
    expectStringArray(issues, `${path}.method.representations`, method.representations);
  }
  const evaluation = expectRecord(issues, `${path}.evaluation`, record.evaluation);
  if (evaluation) {
    expectOptionalString(issues, `${path}.evaluation.headline`, evaluation.headline);
    expectStringArray(issues, `${path}.evaluation.datasets`, evaluation.datasets);
    expectStringArray(issues, `${path}.evaluation.metrics`, evaluation.metrics);
    expectStringArray(issues, `${path}.evaluation.baselines`, evaluation.baselines);
    expectStringArray(issues, `${path}.evaluation.key_findings`, evaluation.key_findings);
    expectOptionalString(issues, `${path}.evaluation.setup_summary`, evaluation.setup_summary);
  }
  expectObjectArray(issues, `${path}.claims`, record.claims);
  const conclusion = expectRecord(issues, `${path}.conclusion`, record.conclusion);
  if (conclusion) {
    expectOptionalString(issues, `${path}.conclusion.author`, conclusion.author);
    expectStringArray(issues, `${path}.conclusion.limitations`, conclusion.limitations);
  }
  const comparison = expectRecord(issues, `${path}.comparison`, record.comparison);
  if (comparison) {
    expectObjectArray(issues, `${path}.comparison.aspects`, comparison.aspects);
    expectStringArray(issues, `${path}.comparison.next_read`, comparison.next_read);
  }
  validateAssets(issues, `${path}.assets`, record.assets);
  validateRelations(issues, `${path}.relations`, record.relations);
}

export function validatePayload(payload: unknown): SiteIndexPayload {
  const issues: string[] = [];
  const record = expectRecord(issues, "payload", payload);
  if (!record) {
    throw validationError(issues);
  }
  expectString(issues, "payload.generated_at", record.generated_at);
  expectOptionalNumber(issues, "payload.paper_count", record.paper_count);
  expectStringArray(issues, "payload.recent_titles", record.recent_titles);
  expectObjectArray(issues, "payload.papers", record.papers)?.forEach((paper, index) =>
    validatePaperCard(issues, `payload.papers[${index}]`, paper),
  );
  expectObjectArray(issues, "payload.featured", record.featured)?.forEach((paper, index) =>
    validatePaperCard(issues, `payload.featured[${index}]`, paper),
  );
  const filters = expectRecord(issues, "payload.filters", record.filters);
  if (filters) {
    (["themes", "tasks", "methods"] as const).forEach((key) => {
      expectObjectArray(issues, `payload.filters.${key}`, filters[key]);
    });
  }
  const navigation = expectRecord(issues, "payload.navigation", record.navigation);
  if (navigation) {
    expectString(issues, "payload.navigation.home_route", navigation.home_route);
    expectString(issues, "payload.navigation.detail_route_template", navigation.detail_route_template);
    expectObjectArray(issues, "payload.navigation.neighbor_tabs", navigation.neighbor_tabs);
    expectObjectArray(issues, "payload.navigation.filter_groups", navigation.filter_groups);
  }
  if (issues.length) {
    throw validationError(issues);
  }
  return payload as SiteIndexPayload;
}

export function validatePaperDetailPayload(payload: unknown): PaperDetailViewModel {
  const issues: string[] = [];
  const record = expectRecord(issues, "paper", payload);
  if (!record) {
    throw validationError(issues);
  }
  validateCanonical(issues, "paper.canonical", record.canonical);
  validateNeighborGroups(issues, "paper.neighbors", record.neighbors);
  if (issues.length) {
    throw validationError(issues);
  }
  return payload as PaperDetailViewModel;
}

function siteJsonUrl(path: string): string {
  return new URL(path, window.location.href.split("#")[0]).toString();
}

export async function loadPayload(): Promise<SiteIndexPayload> {
  const response = await fetch(siteJsonUrl("site-index.json"));
  if (!response.ok) {
    throw new Error(`读取 site-index.json 失败: ${response.status}`);
  }
  return validatePayload(await response.json());
}

export async function loadPaperDetail(paperId: string): Promise<PaperDetailViewModel> {
  const response = await fetch(siteJsonUrl(`papers/${paperId}.json`));
  if (!response.ok) {
    throw new Error(`读取 papers/${paperId}.json 失败: ${response.status}`);
  }
  return validatePaperDetailPayload(await response.json());
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

export function searchableText(paper: PaperCardView): string {
  return [
    paper.bibliography.title,
    ...paper.bibliography.authors,
    paper.bibliography.venue,
    String(paper.bibliography.year ?? ""),
    paper.story.paper_one_liner ?? "",
    paper.story.problem ?? "",
    paper.story.method ?? "",
    paper.story.result ?? "",
    paper.editorial.summary ?? "",
    ...paper.editorial.why_read,
    ...paper.taxonomy.themes,
    ...paper.taxonomy.tasks,
    ...paper.taxonomy.methods,
    ...paper.taxonomy.modalities,
    ...paper.taxonomy.novelty_types,
  ]
    .join(" ")
    .toLowerCase();
}

export function cleanDisplayText(value: string | null | undefined, maxChars?: number): string | null {
  const text = typeof value === "string" ? value.replace(/\s+/g, " ").trim() : "";
  if (!text) {
    return null;
  }
  if (!maxChars || text.length <= maxChars) {
    return text;
  }
  return text.slice(0, maxChars - 1).trimEnd() + "…";
}

export function displayValueLabel(value: string | null | undefined): string {
  const content = cleanDisplayText(value) ?? "";
  return DISPLAY_VALUE_LABELS[content.toLowerCase()] || content;
}

export function recommendedRouteLabel(value: EditorialBlock["reading_route"]): string {
  if (value === "method") {
    return "先看方法";
  }
  if (value === "evaluation") {
    return "先看实验";
  }
  if (value === "comparison") {
    return "先看对比";
  }
  return "先看概述";
}

export function verdictTagClass(value: EditorialBlock["verdict"]): string {
  if (value === "值得精读") {
    return "chip-tag chip-tag-verdict-strong";
  }
  if (value === "值得浏览") {
    return "chip-tag chip-tag-verdict-browse";
  }
  return "chip-tag chip-tag-verdict-muted";
}

export function routeTagClass(value: EditorialBlock["reading_route"]): string {
  if (value === "method") {
    return "chip-tag chip-tag-route-method";
  }
  if (value === "evaluation") {
    return "chip-tag chip-tag-route-evaluation";
  }
  if (value === "comparison") {
    return "chip-tag chip-tag-route-comparison";
  }
  return "chip-tag chip-tag-route-overview";
}

export function scoreLevelTagClass(value: NeighborItem["score_level"]): string {
  if (value === "high") {
    return "chip-tag chip-tag-worth";
  }
  if (value === "medium") {
    return "chip-tag chip-tag-tone-blue";
  }
  return "chip-tag chip-tag-verdict-muted";
}

export function scoreLevelLabel(level: string | null | undefined): string {
  if (level === "high") {
    return "高相关";
  }
  if (level === "medium") {
    return "中相关";
  }
  return "低相关";
}

export function importanceTagClass(value: FigureTableIndexItem["importance"]): string {
  if (value === "high") {
    return "chip-tag chip-tag-worth";
  }
  if (value === "medium") {
    return "chip-tag chip-tag-tone-blue";
  }
  return "chip-tag chip-tag-verdict-muted";
}

export function chipToneClass(value?: string | null): string {
  if (value === "green") {
    return "chip-tag chip-tag-route-method";
  }
  if (value === "gold") {
    return "chip-tag chip-tag-worth";
  }
  if (value === "processing") {
    return "chip-tag chip-tag-tone-blue";
  }
  if (value === "magenta") {
    return "chip-tag chip-tag-highlight";
  }
  return "chip-tag chip-tag-tone-blue";
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

export function displayFigureRole(value: string): string {
  return FIGURE_ROLE_LABELS[value] || value;
}

export function displayComparisonAspect(value: string): string {
  return COMPARISON_ASPECT_LABELS[value] || value;
}

export function displayClaimType(value: string): string {
  const normalized = value.trim().toLowerCase();
  return CLAIM_TYPE_LABELS[normalized] || value;
}

export function displayRelationType(value: string): string {
  return RELATION_TYPE_LABELS[value] || value;
}

export function relationTargetLabel(item: RelationItem): string {
  return item.label || item.target_paper_id || "未命名关系目标";
}

export function semanticScholarSearchUrl(title: string | null | undefined): string | null {
  const normalized = cleanDisplayText(title);
  if (!normalized) {
    return null;
  }
  return `https://www.semanticscholar.org/search?q=${encodeURIComponent(normalized)}&sort=relevance`;
}

export function relationConfidenceLabel(value: number | null | undefined): string | null {
  if (typeof value !== "number") {
    return null;
  }
  return `可信度 ${value.toFixed(2)}`;
}

export function filterFigureTableItems(items: FigureTableIndexItem[], query: string): FigureTableIndexItem[] {
  const normalized = query.trim().toLowerCase();
  if (!normalized) {
    return items;
  }
  return items.filter((item) => `${item.label} ${item.caption} ${item.role}`.toLowerCase().includes(normalized));
}

export function matchesTags(paperTags: string[], selected: string[]): boolean {
  if (!selected.length) {
    return true;
  }
  return selected.every((value) => paperTags.includes(value));
}

export function formatYear(value: number | string | null | undefined): string {
  if (typeof value === "number") {
    return String(value);
  }
  if (typeof value === "string" && value.trim()) {
    return value;
  }
  return "未知年份";
}

export function firstExternalLinks(bibliography: Bibliography): Array<{ key: string; label: string; href: string }> {
  const result: Array<{ key: string; label: string; href: string }> = [];
  const links = bibliography.links;
  const identifiers = bibliography.identifiers;
  if (links.pdf) {
    result.push({ key: "pdf", label: "PDF", href: links.pdf });
  }
  if (links.code) {
    result.push({ key: "code", label: "Code", href: links.code });
  }
  if (links.project) {
    result.push({ key: "project", label: "Project", href: links.project });
  }
  if (links.data) {
    result.push({ key: "data", label: "Data", href: links.data });
  }
  if (identifiers.doi) {
    result.push({ key: "doi", label: "DOI", href: `https://doi.org/${identifiers.doi}` });
  }
  if (identifiers.arxiv) {
    result.push({ key: "arxiv", label: "arXiv", href: `https://arxiv.org/abs/${identifiers.arxiv}` });
  }
  return result;
}

export function sharedSignalPreview(sharedSignals: NeighborItem["shared_signals"]): string[] {
  const result: string[] = [];
  Object.entries(sharedSignals).forEach(([key, values]) => {
    const prefix = SIGNAL_LABELS[key] || key;
    values.slice(0, 2).forEach((value) => result.push(`${prefix}: ${displayValueLabel(value)}`));
  });
  return result;
}

export function debugEnabled(): boolean {
  return new URLSearchParams(window.location.search).get("debug") === "1";
}
