import type {
  EditorialReview,
  FigureTableIndexItem,
  LinkSet,
  NeighborItem,
  PaperRecord,
  PaperRelation,
  RetrievalProfile,
  SitePayload,
} from "../types";

type JsonRecord = Record<string, unknown>;

const REBUILD_COMMANDS = [
  "python3 scripts/normalize_papers.py --raw-dir outputs/raw --papers-dir outputs/papers",
  "python3 scripts/backfill_paper_neighbors.py --papers-dir outputs/papers",
  "python3 scripts/render_markdown_site.py --papers-dir outputs/papers --site-dir outputs/site",
  "npm run build:web",
  "python3 scripts/render_html_dashboard.py --neighbors-json outputs/site/paper-neighbors.json --output outputs/site/index.html",
];

function isRecord(value: unknown): value is JsonRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
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

function expectBoolean(issues: string[], path: string, value: unknown): void {
  if (typeof value !== "boolean") {
    issues.push(`${path} 必须是布尔值`);
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

function expectNumberOrStringOrNull(issues: string[], path: string, value: unknown): void {
  if (value !== null && value !== undefined && typeof value !== "number" && typeof value !== "string") {
    issues.push(`${path} 必须是数字、字符串或 null`);
  }
}

function expectStringArray(issues: string[], path: string, value: unknown): void {
  if (!Array.isArray(value) || value.some((item) => typeof item !== "string")) {
    issues.push(`${path} 必须是字符串数组`);
  }
}

function expectObjectArray(issues: string[], path: string, value: unknown): JsonRecord[] | null {
  if (!Array.isArray(value) || value.some((item) => !isRecord(item))) {
    issues.push(`${path} 必须是对象数组`);
    return null;
  }
  return value;
}

function validateFilterItems(issues: string[], path: string, value: unknown): void {
  const items = expectObjectArray(issues, path, value);
  items?.forEach((item, index) => {
    expectString(issues, `${path}[${index}].label`, item.label);
    expectOptionalNumber(issues, `${path}[${index}].count`, item.count);
    expectStringArray(issues, `${path}[${index}].paper_ids`, item.paper_ids);
  });
}

function validateLinkSet(issues: string[], path: string, value: unknown): void {
  const record = expectRecord(issues, path, value);
  if (!record) {
    return;
  }
  (["pdf", "doi", "arxiv", "project", "code", "data"] as Array<keyof LinkSet>).forEach((key) => {
    expectOptionalString(issues, `${path}.${key}`, record[key]);
  });
}

function validateSummaryBlock(issues: string[], path: string, value: unknown): void {
  const record = expectRecord(issues, path, value);
  if (!record) {
    return;
  }
  expectString(issues, `${path}.one_liner`, record.one_liner);
  expectOptionalString(issues, `${path}.abstract_summary`, record.abstract_summary);
  expectBoolean(issues, `${path}.worth_long_term_graph`, record.worth_long_term_graph);

  const researchValue = expectRecord(issues, `${path}.research_value`, record.research_value);
  if (!researchValue) {
    return;
  }
  expectOptionalString(issues, `${path}.research_value.summary`, researchValue.summary);
  expectStringArray(issues, `${path}.research_value.points`, researchValue.points);
}

function validateReadingDigest(issues: string[], path: string, value: unknown): void {
  const record = expectRecord(issues, path, value);
  if (!record) {
    return;
  }
  expectOptionalString(issues, `${path}.value_statement`, record.value_statement);
  expectOptionalString(issues, `${path}.best_for`, record.best_for);
  expectStringArray(issues, `${path}.why_read`, record.why_read);
  expectString(issues, `${path}.recommended_route`, record.recommended_route);

  const positioning = expectRecord(issues, `${path}.positioning`, record.positioning);
  if (positioning) {
    expectStringArray(issues, `${path}.positioning.task`, positioning.task);
    expectStringArray(issues, `${path}.positioning.modality`, positioning.modality);
    expectStringArray(issues, `${path}.positioning.method`, positioning.method);
    expectStringArray(issues, `${path}.positioning.novelty`, positioning.novelty);
  }

  const narrative = expectRecord(issues, `${path}.narrative`, record.narrative);
  if (narrative) {
    expectOptionalString(issues, `${path}.narrative.problem`, narrative.problem);
    expectOptionalString(issues, `${path}.narrative.method`, narrative.method);
    expectOptionalString(issues, `${path}.narrative.result`, narrative.result);
  }

  expectOptionalString(issues, `${path}.result_headline`, record.result_headline);
}

function validateStoryline(issues: string[], path: string, value: unknown): void {
  const record = expectRecord(issues, path, value);
  if (!record) {
    return;
  }
  expectOptionalString(issues, `${path}.problem`, record.problem);
  expectOptionalString(issues, `${path}.method`, record.method);
  expectOptionalString(issues, `${path}.outcome`, record.outcome);
}

function validateResearchProblem(issues: string[], path: string, value: unknown): void {
  const record = expectRecord(issues, path, value);
  if (!record) {
    return;
  }
  expectOptionalString(issues, `${path}.summary`, record.summary);
  expectStringArray(issues, `${path}.gaps`, record.gaps);
  expectOptionalString(issues, `${path}.goal`, record.goal);
}

function validateClaimItems(issues: string[], path: string, value: unknown): void {
  const items = expectObjectArray(issues, path, value);
  items?.forEach((item, index) => {
    expectString(issues, `${path}[${index}].claim`, item.claim);
    expectOptionalString(issues, `${path}[${index}].type`, item.type);
    expectStringArray(issues, `${path}[${index}].support`, item.support);
    expectOptionalString(issues, `${path}[${index}].confidence`, item.confidence);
  });
}

function validateMethodCore(issues: string[], path: string, value: unknown): void {
  const record = expectRecord(issues, path, value);
  if (!record) {
    return;
  }
  expectOptionalString(issues, `${path}.approach_summary`, record.approach_summary);
  expectStringArray(issues, `${path}.pipeline_steps`, record.pipeline_steps);
  expectStringArray(issues, `${path}.innovations`, record.innovations);
  expectStringArray(issues, `${path}.ingredients`, record.ingredients);
  expectStringArray(issues, `${path}.representation`, record.representation);
  expectStringArray(issues, `${path}.supervision`, record.supervision);
  expectStringArray(issues, `${path}.differences`, record.differences);
}

function validateInputsOutputs(issues: string[], path: string, value: unknown): void {
  const record = expectRecord(issues, path, value);
  if (!record) {
    return;
  }
  expectStringArray(issues, `${path}.inputs`, record.inputs);
  expectStringArray(issues, `${path}.outputs`, record.outputs);
  expectStringArray(issues, `${path}.modalities`, record.modalities);
}

function validateBenchmarks(issues: string[], path: string, value: unknown): void {
  const record = expectRecord(issues, path, value);
  if (!record) {
    return;
  }
  expectStringArray(issues, `${path}.datasets`, record.datasets);
  expectStringArray(issues, `${path}.metrics`, record.metrics);
  expectStringArray(issues, `${path}.baselines`, record.baselines);
  expectStringArray(issues, `${path}.findings`, record.findings);
  expectStringArray(issues, `${path}.best_results`, record.best_results);
  expectOptionalString(issues, `${path}.experiment_setup_summary`, record.experiment_setup_summary);
}

function validateResearchTags(issues: string[], path: string, value: unknown): void {
  const record = expectRecord(issues, path, value);
  if (!record) {
    return;
  }
  expectStringArray(issues, `${path}.themes`, record.themes);
  expectStringArray(issues, `${path}.tasks`, record.tasks);
  expectStringArray(issues, `${path}.methods`, record.methods);
  expectStringArray(issues, `${path}.modalities`, record.modalities);
  expectStringArray(issues, `${path}.representations`, record.representations);
}

function validateRetrievalProfile(issues: string[], path: string, value: unknown): void {
  const record = expectRecord(issues, path, value);
  if (!record) {
    return;
  }
  expectStringArray(issues, `${path}.problem_spaces`, record.problem_spaces);
  expectStringArray(issues, `${path}.task_axes`, record.task_axes);
  expectStringArray(issues, `${path}.approach_axes`, record.approach_axes);
  expectStringArray(issues, `${path}.input_axes`, record.input_axes);
  expectStringArray(issues, `${path}.output_axes`, record.output_axes);
  expectStringArray(issues, `${path}.modality_axes`, record.modality_axes);
  expectStringArray(issues, `${path}.comparison_axes`, record.comparison_axes);
}

function validateComparisonContext(issues: string[], path: string, value: unknown): void {
  const record = expectRecord(issues, path, value);
  if (!record) {
    return;
  }
  expectStringArray(issues, `${path}.explicit_baselines`, record.explicit_baselines);
  expectStringArray(issues, `${path}.contrast_methods`, record.contrast_methods);
  expectOptionalString(issues, `${path}.recommended_next_read`, record.recommended_next_read);

  const aspects = expectObjectArray(issues, `${path}.comparison_aspects`, record.comparison_aspects);
  aspects?.forEach((item, index) => {
    expectString(issues, `${path}.comparison_aspects[${index}].aspect`, item.aspect);
    expectString(issues, `${path}.comparison_aspects[${index}].difference`, item.difference);
  });
}

function validateEditorialReview(issues: string[], path: string, value: unknown): void {
  const record = expectRecord(issues, path, value);
  if (!record) {
    return;
  }
  expectOptionalString(issues, `${path}.verdict`, record.verdict);
  expectStringArray(issues, `${path}.strengths`, record.strengths);
  expectStringArray(issues, `${path}.cautions`, record.cautions);
  expectOptionalString(issues, `${path}.research_position`, record.research_position);
  expectOptionalString(issues, `${path}.next_read_hint`, record.next_read_hint);
}

function validateNeighborGroups(issues: string[], path: string, value: unknown): void {
  const record = expectRecord(issues, path, value);
  if (!record) {
    return;
  }
  (["task", "method", "comparison"] as Array<keyof PaperRecord["paper_neighbors"]>).forEach((key) => {
    const items = expectObjectArray(issues, `${path}.${key}`, record[key]);
    items?.forEach((item, index) => {
      expectString(issues, `${path}.${key}[${index}].paper_id`, item.paper_id);
      expectString(issues, `${path}.${key}[${index}].title`, item.title);
      expectOptionalNumber(issues, `${path}.${key}[${index}].score`, item.score);
      expectOptionalString(issues, `${path}.${key}[${index}].score_level`, item.score_level);
      expectOptionalString(issues, `${path}.${key}[${index}].match_source`, item.match_source);
      expectOptionalString(issues, `${path}.${key}[${index}].reason`, item.reason);
      expectOptionalString(issues, `${path}.${key}[${index}].reason_short`, item.reason_short);
      expectOptionalString(issues, `${path}.${key}[${index}].paper_path`, item.paper_path);
      expectOptionalString(issues, `${path}.${key}[${index}].route_path`, item.route_path);
      expectRecord(issues, `${path}.${key}[${index}].shared_signals`, item.shared_signals);
    });
  });
}

function validateFigureTableIndex(issues: string[], path: string, value: unknown): void {
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
      expectOptionalString(issues, `${path}.${key}[${index}].importance`, item.importance);
    });
  });
}

function validateEditorNote(issues: string[], path: string, value: unknown): void {
  if (value === null || value === undefined) {
    return;
  }
  const record = expectRecord(issues, path, value);
  if (!record) {
    return;
  }
  expectOptionalString(issues, `${path}.summary`, record.summary);
  expectStringArray(issues, `${path}.points`, record.points);
}

function validateTopics(issues: string[], path: string, value: unknown): void {
  const items = expectObjectArray(issues, path, value);
  items?.forEach((item, index) => {
    expectString(issues, `${path}[${index}].slug`, item.slug);
    expectString(issues, `${path}[${index}].name`, item.name);
    expectString(issues, `${path}[${index}].role`, item.role);
  });
}

function validatePaperRelations(issues: string[], path: string, value: unknown): void {
  const items = expectObjectArray(issues, path, value);
  items?.forEach((item, index) => {
    expectString(issues, `${path}[${index}].target_paper_id`, item.target_paper_id);
    expectString(issues, `${path}[${index}].relation_type`, item.relation_type);
    expectString(issues, `${path}[${index}].description`, item.description);
    expectOptionalNumber(issues, `${path}[${index}].confidence`, item.confidence);
  });
}

function validatePaperRecord(issues: string[], path: string, value: unknown): void {
  const record = expectRecord(issues, path, value);
  if (!record) {
    return;
  }
  expectString(issues, `${path}.paper_id`, record.paper_id);
  expectStringArray(issues, `${path}.source_conversation_ids`, record.source_conversation_ids);
  expectString(issues, `${path}.title`, record.title);
  expectStringArray(issues, `${path}.authors`, record.authors);
  expectNumberOrStringOrNull(issues, `${path}.year`, record.year);
  expectString(issues, `${path}.venue`, record.venue);
  expectOptionalNumber(issues, `${path}.citation_count`, record.citation_count);
  expectString(issues, `${path}.paper_path`, record.paper_path);
  expectString(issues, `${path}.route_path`, record.route_path);
  expectOptionalString(issues, `${path}.abstract_raw`, record.abstract_raw);
  expectOptionalString(issues, `${path}.abstract_zh`, record.abstract_zh);
  expectOptionalString(issues, `${path}.author_conclusion`, record.author_conclusion);

  validateLinkSet(issues, `${path}.links`, record.links);
  validateSummaryBlock(issues, `${path}.summary`, record.summary);
  validateReadingDigest(issues, `${path}.reading_digest`, record.reading_digest);
  validateStoryline(issues, `${path}.storyline`, record.storyline);
  validateResearchProblem(issues, `${path}.research_problem`, record.research_problem);
  expectStringArray(issues, `${path}.core_contributions`, record.core_contributions);
  validateClaimItems(issues, `${path}.key_claims`, record.key_claims);
  validateMethodCore(issues, `${path}.method_core`, record.method_core);
  validateInputsOutputs(issues, `${path}.inputs_outputs`, record.inputs_outputs);
  validateBenchmarks(issues, `${path}.benchmarks_or_eval`, record.benchmarks_or_eval);
  validateEditorNote(issues, `${path}.editor_note`, record.editor_note);
  validateEditorialReview(issues, `${path}.editorial_review`, record.editorial_review);
  expectStringArray(issues, `${path}.limitations`, record.limitations);
  expectStringArray(issues, `${path}.novelty_type`, record.novelty_type);
  validateResearchTags(issues, `${path}.research_tags`, record.research_tags);
  validateTopics(issues, `${path}.topics`, record.topics);
  validateRetrievalProfile(issues, `${path}.retrieval_profile`, record.retrieval_profile);
  validateComparisonContext(issues, `${path}.comparison_context`, record.comparison_context);
  validateNeighborGroups(issues, `${path}.paper_neighbors`, record.paper_neighbors);
  validatePaperRelations(issues, `${path}.paper_relations`, record.paper_relations);
  validateFigureTableIndex(issues, `${path}.figure_table_index`, record.figure_table_index);
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

export function validatePayload(payload: unknown): SitePayload {
  const issues: string[] = [];
  const record = expectRecord(issues, "payload", payload);
  if (!record) {
    throw validationError(issues);
  }

  expectString(issues, "payload.generated_at", record.generated_at);
  expectOptionalNumber(issues, "payload.paper_count", record.paper_count);
  expectStringArray(issues, "payload.recent_titles", record.recent_titles);

  const siteMeta = expectRecord(issues, "payload.site_meta", record.site_meta);
  if (siteMeta) {
    expectString(issues, "payload.site_meta.title", siteMeta.title);
    expectString(issues, "payload.site_meta.generated_at", siteMeta.generated_at);
    expectOptionalNumber(issues, "payload.site_meta.paper_count", siteMeta.paper_count);
  }

  const navigation = expectRecord(issues, "payload.navigation", record.navigation);
  if (navigation) {
    expectString(issues, "payload.navigation.home_route", navigation.home_route);
    expectString(issues, "payload.navigation.detail_route_template", navigation.detail_route_template);
    const neighborTabs = expectObjectArray(issues, "payload.navigation.neighbor_tabs", navigation.neighbor_tabs);
    neighborTabs?.forEach((item, index) => {
      expectString(issues, `payload.navigation.neighbor_tabs[${index}].key`, item.key);
      expectString(issues, `payload.navigation.neighbor_tabs[${index}].label`, item.label);
    });
    const filterGroups = expectObjectArray(issues, "payload.navigation.filter_groups", navigation.filter_groups);
    filterGroups?.forEach((item, index) => {
      expectString(issues, `payload.navigation.filter_groups[${index}].key`, item.key);
      expectString(issues, `payload.navigation.filter_groups[${index}].label`, item.label);
    });
  }

  const filters = expectRecord(issues, "payload.filters", record.filters);
  if (filters) {
    validateFilterItems(issues, "payload.filters.themes", filters.themes);
    validateFilterItems(issues, "payload.filters.tasks", filters.tasks);
    validateFilterItems(issues, "payload.filters.methods", filters.methods);
  }

  const papers = expectObjectArray(issues, "payload.papers", record.papers);
  papers?.forEach((paper, index) => validatePaperRecord(issues, `payload.papers[${index}]`, paper));

  if (issues.length) {
    throw validationError(issues);
  }
  return payload as SitePayload;
}

export function inlinePayload(): SitePayload | null {
  const node = document.getElementById("paper-neighbors-data");
  const text = node?.textContent?.trim();
  if (!text || text === "__PAPER_NEIGHBORS_DATA__") {
    return null;
  }
  return validatePayload(JSON.parse(text));
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
  return validatePayload(await response.json());
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
  const comparisonAspects = paper.comparison_context.comparison_aspects.flatMap((item) => [item.aspect, item.difference]);
  return [
    paper.title,
    ...paper.authors,
    paper.venue,
    String(paper.year ?? ""),
    paper.abstract_raw ?? "",
    paper.abstract_zh ?? "",
    paper.summary.one_liner,
    paper.reading_digest.value_statement ?? "",
    paper.reading_digest.best_for ?? "",
    ...paper.reading_digest.why_read,
    paper.reading_digest.result_headline ?? "",
    ...paper.reading_digest.positioning.task,
    ...paper.reading_digest.positioning.modality,
    ...paper.reading_digest.positioning.method,
    ...paper.reading_digest.positioning.novelty,
    paper.reading_digest.narrative.problem ?? "",
    paper.reading_digest.narrative.method ?? "",
    paper.reading_digest.narrative.result ?? "",
    paper.summary.abstract_summary ?? "",
    paper.summary.research_value.summary ?? "",
    ...paper.summary.research_value.points,
    paper.storyline.problem ?? "",
    paper.storyline.method ?? "",
    paper.storyline.outcome ?? "",
    paper.research_problem.summary ?? "",
    ...paper.research_problem.gaps,
    paper.research_problem.goal ?? "",
    ...paper.core_contributions,
    paper.author_conclusion ?? "",
    paper.editor_note?.summary ?? "",
    ...(paper.editor_note?.points ?? []),
    paper.editorial_review.verdict ?? "",
    ...paper.editorial_review.strengths,
    ...paper.editorial_review.cautions,
    paper.editorial_review.research_position ?? "",
    paper.editorial_review.next_read_hint ?? "",
    ...paper.research_tags.themes,
    ...paper.research_tags.tasks,
    ...paper.research_tags.methods,
    ...paper.research_tags.representations,
    ...paper.retrieval_profile.problem_spaces,
    ...comparisonAspects,
  ]
    .join(" ")
    .toLowerCase();
}

export function recommendedRouteLabel(value: PaperRecord["reading_digest"]["recommended_route"]): string {
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

export function verdictTone(value: EditorialReview["verdict"]): "gold" | "blue" | "default" {
  if (value === "值得精读") {
    return "gold";
  }
  if (value === "值得浏览") {
    return "blue";
  }
  return "default";
}

export function matchesTags(paperTags: string[], selected: string[]): boolean {
  if (!selected.length) {
    return true;
  }
  return selected.every((tag) => paperTags.includes(tag));
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

export function scoreLevelLabel(level: string | null | undefined): string {
  if (level === "high") {
    return "高相关";
  }
  if (level === "medium") {
    return "中相关";
  }
  if (level === "low") {
    return "低相关";
  }
  return "相关";
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
    return [...items].sort((left, right) => {
      const importanceScore = { high: 0, medium: 1, low: 2 };
      const leftRank = importanceScore[left.importance as keyof typeof importanceScore] ?? 3;
      const rightRank = importanceScore[right.importance as keyof typeof importanceScore] ?? 3;
      if (leftRank !== rightRank) {
        return leftRank - rightRank;
      }
      return left.label.localeCompare(right.label);
    });
  }
  return items.filter((item) => `${item.label} ${item.caption} ${item.role} ${item.importance}`.toLowerCase().includes(keyword));
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
