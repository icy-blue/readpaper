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

export interface ClaimItem {
  claim: string;
  type: "method" | "experiment" | "capability" | "limitation" | string;
  support: string[];
  confidence: "high" | "medium" | "low" | string;
}

export interface LinkSet {
  pdf: string | null;
  doi: string | null;
  arxiv: string | null;
  project: string | null;
  code: string | null;
  data: string | null;
}

export interface SummaryBlock {
  one_liner: string;
  abstract_summary: string | null;
  research_value: {
    summary: string | null;
    points: string[];
  };
  worth_long_term_graph: boolean;
}

export interface Storyline {
  problem: string | null;
  method: string | null;
  outcome: string | null;
}

export interface ResearchProblem {
  summary: string | null;
  gaps: string[];
  goal: string | null;
}

export interface MethodCore {
  approach_summary: string | null;
  pipeline_steps: string[];
  innovations: string[];
  ingredients: string[];
  representation: string[];
  supervision: string[];
  differences: string[];
}

export interface InputsOutputs {
  inputs: string[];
  outputs: string[];
  modalities: string[];
}

export interface Benchmarks {
  datasets: string[];
  metrics: string[];
  baselines: string[];
  findings: string[];
  best_results: string[];
  experiment_setup_summary: string | null;
}

export interface ResearchTags {
  themes: string[];
  tasks: string[];
  methods: string[];
  modalities: string[];
  representations: string[];
}

export interface RetrievalProfile {
  problem_spaces: string[];
  task_axes: string[];
  approach_axes: string[];
  input_axes: string[];
  output_axes: string[];
  modality_axes: string[];
  comparison_axes: string[];
}

export interface ComparisonContext {
  explicit_baselines: string[];
  contrast_methods: string[];
  comparison_aspects: Array<{
    aspect: string;
    difference: string;
  }>;
  recommended_next_read: string | null;
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

export interface FigureTableIndexItem {
  label: string;
  caption: string;
  role: string;
  importance: "high" | "medium" | "low" | string;
}

export interface FigureTableIndex {
  figures: FigureTableIndexItem[];
  tables: FigureTableIndexItem[];
}

export interface TopicItem {
  slug: string;
  name: string;
  role: string;
}

export interface PaperRelation {
  target_paper_id: string;
  relation_type: string;
  description: string;
  confidence?: number | null;
}

export interface PaperRecord {
  paper_id: string;
  source_conversation_ids: string[];
  title: string;
  authors: string[];
  year: number | string | null;
  venue: string;
  citation_count: number | null;
  links: LinkSet;
  paper_path: string;
  route_path: string;
  abstract_raw: string | null;
  abstract_zh: string | null;
  summary: SummaryBlock;
  storyline: Storyline;
  research_problem: ResearchProblem;
  core_contributions: string[];
  key_claims: ClaimItem[];
  method_core: MethodCore;
  inputs_outputs: InputsOutputs;
  benchmarks_or_eval: Benchmarks;
  author_conclusion: string | null;
  editor_note: {
    summary: string | null;
    points: string[];
  } | null;
  limitations: string[];
  novelty_type: string[];
  research_tags: ResearchTags;
  topics: TopicItem[];
  retrieval_profile: RetrievalProfile;
  comparison_context: ComparisonContext;
  paper_neighbors: {
    task: NeighborItem[];
    method: NeighborItem[];
    comparison: NeighborItem[];
  };
  paper_relations: PaperRelation[];
  figure_table_index: FigureTableIndex;
}

export interface SitePayload {
  generated_at: string;
  paper_count: number;
  site_meta: SiteMeta;
  navigation: NavigationConfig;
  filters: Filters;
  papers: PaperRecord[];
  recent_titles: string[];
}
