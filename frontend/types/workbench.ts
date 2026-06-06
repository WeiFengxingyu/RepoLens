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
