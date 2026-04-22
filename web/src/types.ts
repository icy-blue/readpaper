export interface SiteMeta {
  title: string;
  generated_at: string;
  paper_count: number;
}

export interface NavigationConfig {
  home_route: string;
  detail_route_template: string;
  neighbor_tabs: Array<{ key: "task" | "method" | "comparison"; label: string }>;
  filter_groups: Array<{ key: "themes" | "tasks" | "methods"; label: string }>;
}

export interface FilterItem {
  label: string;
  count: number;
  paper_ids: string[];
}

export interface Filters {
  themes: FilterItem[];
  tasks: FilterItem[];
  methods: FilterItem[];
}

export interface ScholarlyIdentifiers {
  doi: string | null;
  arxiv: string | null;
}

export interface ExternalLinks {
  pdf: string | null;
  project: string | null;
  code: string | null;
  data: string | null;
}

export interface Bibliography {
  title: string;
  authors: string[];
  year: number | string | null;
  venue: string;
  citation_count: number | null;
  identifiers: ScholarlyIdentifiers;
  links: ExternalLinks;
}

export interface SourceInfo {
  conversation_ids: string[];
  paper_path: string;
  route_path: string;
}

export interface StoryBlock {
  paper_one_liner: string | null;
  problem: string | null;
  method: string | null;
  result: string | null;
}

export interface ResearchProblem {
  summary: string | null;
  gaps: string[];
  goal: string | null;
}

export interface MethodBlock {
  summary: string | null;
  pipeline_steps: string[];
  innovations: string[];
  ingredients: string[];
  inputs: string[];
  outputs: string[];
  representations: string[];
}

export interface EvaluationBlock {
  headline: string | null;
  datasets: string[];
  metrics: string[];
  baselines: string[];
  key_findings: string[];
  setup_summary: string | null;
}

export interface ClaimItem {
  text: string;
  type: "method" | "experiment" | "capability" | "limitation" | string;
  support: string[];
  confidence: "high" | "medium" | "low" | string;
}

export interface ConclusionBlock {
  author: string | null;
  limitations: string[];
}

export interface EditorialBlock {
  verdict: "值得精读" | "值得浏览" | "只记结论" | string | null;
  summary: string | null;
  why_read: string[];
  strengths: string[];
  cautions: string[];
  reading_route: "method" | "evaluation" | "comparison" | "overview" | string;
  research_position: string | null;
  graph_worthy: boolean;
  next_read: string[];
}

export interface TaxonomyBlock {
  themes: string[];
  tasks: string[];
  methods: string[];
  modalities: string[];
  representations: string[];
  novelty_types: string[];
}

export interface ComparisonAspect {
  aspect: string;
  difference: string;
}

export interface ComparisonBlock {
  aspects: ComparisonAspect[];
  next_read: string[];
}

export interface FigureTableIndexItem {
  label: string;
  caption: string;
  role: string;
  importance: "high" | "medium" | "low" | string;
}

export interface AssetsBlock {
  figures: FigureTableIndexItem[];
  tables: FigureTableIndexItem[];
}

export interface RelationItem {
  type: string;
  target_kind: "local" | "external" | string;
  target_paper_id: string | null;
  target_semantic_scholar_paper_id: string | null;
  target_url: string | null;
  label: string | null;
  description: string | null;
  confidence?: number | null;
}

export interface PaperCanonicalRecord {
  id: string;
  source: SourceInfo;
  bibliography: Bibliography;
  abstracts: {
    raw: string | null;
    zh: string | null;
  };
  story: StoryBlock;
  research_problem: ResearchProblem;
  core_contributions: string[];
  method: MethodBlock;
  evaluation: EvaluationBlock;
  claims: ClaimItem[];
  conclusion: ConclusionBlock;
  editorial: EditorialBlock;
  taxonomy: TaxonomyBlock;
  comparison: ComparisonBlock;
  assets: AssetsBlock;
  relations: RelationItem[];
}

export interface PaperCardView {
  id: string;
  source: SourceInfo;
  bibliography: Bibliography;
  story: StoryBlock;
  editorial: EditorialBlock;
  taxonomy: TaxonomyBlock;
}

export interface NeighborItem {
  paper_id: string;
  title: string;
  score: number;
  score_level: "high" | "medium" | "low" | string;
  match_source: string;
  reason: string;
  reason_short: string | null;
  relation_hint?: string | null;
  paper_path: string;
  route_path: string;
  shared_signals: Record<string, string[]>;
}

export interface NeighborGroups {
  task: NeighborItem[];
  method: NeighborItem[];
  comparison: NeighborItem[];
}

export interface PaperDetailViewModel {
  canonical: PaperCanonicalRecord;
  neighbors: NeighborGroups;
}

export interface SiteIndexPayload {
  generated_at: string;
  paper_count: number;
  site_meta: SiteMeta;
  navigation: NavigationConfig;
  filters: Filters;
  featured: PaperCardView[];
  papers: PaperCardView[];
  recent_titles: string[];
}

export type SitePayload = SiteIndexPayload;
