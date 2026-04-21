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
  support: string[];
  confidence: string;
}

export interface LinkSet {
  pdf: string | null;
  doi: string | null;
  arxiv: string | null;
  project: string | null;
  code: string | null;
  data: string | null;
}

export interface MethodCore {
  approach: string | null;
  innovation: string | null;
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
  experiment_setup_summary: string | null;
}

export interface ResearchTags {
  themes: string[];
  tasks: string[];
  methods: string[];
  modalities: string[];
  representations: string[];
}

export interface ComparisonContext {
  explicit_baselines: string[];
  contrast_methods: string[];
  contrast_notes: string[];
}

export interface NeighborItem {
  paper_id: string;
  title: string;
  score: number;
  match_source: string;
  reason: string;
  relation_hint?: string | null;
  paper_path: string;
  route_path: string;
  shared_signals: Record<string, string[]>;
}

export interface FigureTableIndexItem {
  label: string;
  caption: string;
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
  title: string;
  authors: string[];
  year: number | string | null;
  venue: string;
  citation_count: number | null;
  links: LinkSet;
  translate_created_at: string;
  paper_path: string;
  route_path: string;
  abstract_raw: string | null;
  abstract_zh: string | null;
  summary: {
    one_liner: string;
    abstract_summary: string | null;
    research_value: string | null;
    worth_long_term_graph: boolean;
  };
  research_problem: string | null;
  core_contributions: string[];
  key_claims: ClaimItem[];
  method_core: MethodCore;
  inputs_outputs: InputsOutputs;
  benchmarks_or_eval: Benchmarks;
  author_conclusion: string | null;
  editor_note: string | null;
  limitations: string[];
  novelty_type: string[];
  research_tags: ResearchTags;
  topics: TopicItem[];
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
