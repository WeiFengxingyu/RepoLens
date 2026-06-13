export type WorkbenchPanel = {
  title: string;
  status: "Ready" | "Planned" | "Blocked";
  detail: string;
};

export type RepositoryStatus =
  | "pending"
  | "cloning"
  | "scanning"
  | "parsing"
  | "chunking"
  | "ready"
  | "failed";

export type RepositoryImportRequest = {
  source: string;
  branch?: string;
  name?: string;
};

export type RepositorySummary = {
  id: string;
  name: string;
  source_type: string;
  status: RepositoryStatus;
  file_count: number;
  chunk_count: number;
  relation_count: number;
  updated_at: string;
};

export type RepositoryDetail = RepositorySummary & {
  source_url: string | null;
  local_path: string;
  branch: string | null;
  commit_hash: string | null;
  language_summary: Record<string, number>;
  parsed_file_count: number;
  skipped_file_count: number;
  error_message: string | null;
  created_at: string;
  indexed_at: string | null;
};

export type RepositoryStatusResponse = {
  id: string;
  status: RepositoryStatus;
  progress: {
    current_step: RepositoryStatus;
    file_count: number;
    parsed_file_count: number;
    chunk_count: number;
    relation_count: number;
  };
  error_message: string | null;
};

export type RetrievalRequest = {
  query: string;
  top_k?: number;
  use_bm25?: boolean;
  use_vector?: boolean;
  use_graph?: boolean;
};

export type EvidenceItem = {
  evidence_id: string;
  chunk_id: string;
  repository_id: string;
  file_path: string;
  start_line: number;
  end_line: number;
  symbol_name: string;
  symbol_type: string;
  language: string;
  source: string;
  sources: string[];
  score: number;
  bm25_score: number;
  vector_score: number;
  graph_score: number;
  snippet: string;
  metadata: Record<string, unknown>;
};

export type RetrievalDebug = {
  bm25_count: number;
  vector_count: number;
  graph_count: number;
  merged_count: number;
  evidence_count: number;
  vector_disabled_reason: string | null;
  context_truncated: boolean;
};

export type RetrievalResponse = {
  repository_id: string;
  query: string;
  evidences: EvidenceItem[];
  debug: RetrievalDebug;
};

export type QACreateRequest = {
  question: string;
  top_k?: number;
  use_bm25?: boolean;
  use_vector?: boolean;
  use_graph?: boolean;
};

export type QACitation = {
  evidence_id: string;
  chunk_id: string;
  file_path: string;
  start_line: number;
  end_line: number;
  symbol_name: string;
  symbol_type: string;
  language: string;
  score: number;
  sources: string[];
  snippet: string;
};

export type AgentTrace = {
  id: string;
  step_name: string;
  step_order: number;
  status: "running" | "completed" | "failed";
  input_summary: string;
  output_summary: string | null;
  evidence_ids: string[];
  tool_calls: Array<Record<string, unknown>>;
  token_usage: Record<string, unknown>;
  latency_ms: number | null;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
};

export type QATaskResponse = {
  task_id: string;
  repository_id: string;
  status: "pending" | "running" | "completed" | "failed";
  question: string;
  answer: string | null;
  citations: QACitation[];
  confidence: number | null;
  warnings: string[];
  error_message: string | null;
  traces: AgentTrace[];
  created_at: string;
  completed_at: string | null;
};

export type ReviewCreateRequest = {
  diff_text: string;
  top_k?: number;
  use_bm25?: boolean;
  use_vector?: boolean;
  use_graph?: boolean;
  run_static_check?: boolean;
};

export type ReviewLocation = {
  file_path: string;
  start_line: number;
  end_line: number;
};

export type ReviewRisk = {
  title?: string;
  severity?: string;
  location?: ReviewLocation;
  reason?: string;
  evidence_ids?: string[];
  impacted_symbols?: string[];
  suggestion?: string;
  [key: string]: unknown;
};

export type ReviewSuggestedTest = {
  target?: string;
  reason?: string;
  test_type?: string;
  related_risk_titles?: string[];
  file_path?: string | null;
  [key: string]: unknown;
};

export type ReviewCitation = {
  evidence_id?: string;
  chunk_id?: string;
  file_path?: string;
  start_line?: number;
  end_line?: number;
  symbol_name?: string;
  score?: number;
  sources?: string[];
  snippet?: string;
  [key: string]: unknown;
};

export type ReviewToolCall = {
  id: string;
  tool_name: string;
  status: "running" | "completed" | "failed" | "denied" | "disabled";
  permission_decision: "allow" | "deny" | "disabled";
  input_summary: string;
  output_summary: string | null;
  latency_ms: number | null;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
};

export type ReviewTaskResponse = {
  task_id: string;
  repository_id: string;
  status: "pending" | "running" | "completed" | "failed";
  summary: string | null;
  risk_level: string | null;
  risks: ReviewRisk[];
  impacted_symbols: string[];
  suggested_tests: ReviewSuggestedTest[];
  citations: ReviewCitation[];
  markdown: string | null;
  tool_calls: ReviewToolCall[];
  traces: AgentTrace[];
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
};

export type EvaluationStrategy = "all" | "vector_only" | "bm25_vector" | "bm25_vector_graph";

export type EvaluationCreateRequest = {
  name?: string;
  dataset_path: string;
  strategy: EvaluationStrategy;
  repository_map: Record<string, string>;
  top_k?: number;
};

export type EvaluationMetric = {
  strategy: string;
  sample_count: number;
  hit_at_5: number;
  mrr: number;
  citation_coverage: number;
  avg_latency_ms: number;
  p50_latency_ms: number;
  p95_latency_ms: number;
  avg_token_count: number;
  token_estimated: boolean;
  token_estimated_count: number;
  error_count: number;
};

export type EvaluationResult = {
  id: string;
  sample_id: string;
  sample_type: string;
  repository_key: string;
  strategy: string;
  hit_at_5: boolean;
  mrr: number;
  citation_coverage: number;
  latency_ms: number;
  token_count: number;
  token_estimated: boolean;
  matched_files: string[];
  matched_symbols: string[];
  citations: Array<Record<string, unknown>>;
  error_message: string | null;
};

export type EvaluationRunResponse = {
  run_id: string;
  name: string;
  dataset_path: string;
  strategy: string;
  status: "pending" | "running" | "completed" | "failed";
  sample_count: number;
  repository_map: Record<string, string>;
  metrics: EvaluationMetric[];
  results: EvaluationResult[];
  warnings: string[];
  error_message: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
};

export type EvaluationRunSummary = Omit<
  EvaluationRunResponse,
  "repository_map" | "results" | "warnings" | "started_at"
>;
