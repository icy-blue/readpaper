export interface SiteMeta {
  title: string;
  generated_at: string;
  paper_count: number;
}

export interface NavigationConfig {
  home_route: string;
  neighbor_tabs: Array<{ key: "problem" | "method" | "evaluation"; label: string }>;
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

export interface EditorialBlock {
  research_position: string | null;
  graph_worthy: boolean;
}

export interface TaxonomyBlock {
  themes: string[];
  tasks: string[];
  methods: string[];
  modalities: string[];
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

export interface DiscoveryAxesBlock {
  problem: string[];
  method: string[];
  evaluation: string[];
  risk: string[];
}

export interface RelationItem {
  type: string;
  target_kind: "local" | "external" | string;
  target_paper_id: string | null;
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
  research_risks: string[];
  editorial: EditorialBlock;
  taxonomy: TaxonomyBlock;
  comparison: ComparisonBlock;
  discovery_axes: DiscoveryAxesBlock;
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
  problem: NeighborItem[];
  method: NeighborItem[];
  evaluation: NeighborItem[];
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
