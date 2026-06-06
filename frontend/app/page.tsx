"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  API_BASE_URL,
  askRepositoryQuestion,
  getRepository,
  getRepositoryStatus,
  importRepository,
  listRepositories,
  retrieveRepository
} from "@/lib/api";
import type {
  AgentTrace,
  EvidenceItem,
  QACitation,
  QATaskResponse,
  RepositoryDetail,
  RepositoryStatus,
  RepositoryStatusResponse,
  RepositorySummary,
  RetrievalResponse
} from "@/types/workbench";

const metricLabels = [
  ["file_count", "Files"],
  ["parsed_file_count", "Parsed"],
  ["skipped_file_count", "Skipped"],
  ["chunk_count", "Chunks"],
  ["relation_count", "Relations"]
] as const;

export default function Home() {
  const [source, setSource] = useState("");
  const [branch, setBranch] = useState("");
  const [repositories, setRepositories] = useState<RepositorySummary[]>([]);
  const [selectedRepository, setSelectedRepository] = useState<RepositoryDetail | null>(null);
  const [selectedStatus, setSelectedStatus] = useState<RepositoryStatusResponse | null>(null);
  const [query, setQuery] = useState("");
  const [topK, setTopK] = useState(10);
  const [useBm25, setUseBm25] = useState(true);
  const [useVector, setUseVector] = useState(true);
  const [useGraph, setUseGraph] = useState(true);
  const [question, setQuestion] = useState("");
  const [qaTopK, setQaTopK] = useState(8);
  const [qaUseBm25, setQaUseBm25] = useState(true);
  const [qaUseVector, setQaUseVector] = useState(true);
  const [qaUseGraph, setQaUseGraph] = useState(true);
  const [qaResult, setQaResult] = useState<QATaskResponse | null>(null);
  const [qaState, setQaState] = useState<"idle" | "asking" | "ready" | "failed">("idle");
  const [qaError, setQaError] = useState<string | null>(null);
  const [retrievalResult, setRetrievalResult] = useState<RetrievalResponse | null>(null);
  const [retrievalState, setRetrievalState] = useState<
    "idle" | "searching" | "ready" | "empty" | "failed"
  >("idle");
  const [retrievalError, setRetrievalError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    void loadRepositories();
  }, []);

  const selectedMetrics = useMemo(() => {
    if (!selectedRepository) {
      return [];
    }
    return metricLabels.map(([key, label]) => ({
      key,
      label,
      value: selectedRepository[key]
    }));
  }, [selectedRepository]);

  async function loadRepositories(preferredId?: string) {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const items = await listRepositories();
      setRepositories(items);
      const nextId = preferredId ?? selectedRepository?.id ?? items[0]?.id;
      if (nextId) {
        await selectRepository(nextId);
      } else {
        setSelectedRepository(null);
        setSelectedStatus(null);
      }
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Unable to load repositories.");
    } finally {
      setIsLoading(false);
    }
  }

  async function selectRepository(repositoryId: string) {
    setErrorMessage(null);
    const [detail, status] = await Promise.all([
      getRepository(repositoryId),
      getRepositoryStatus(repositoryId)
    ]);
    setSelectedRepository(detail);
    setSelectedStatus(status);
    setRetrievalResult(null);
    setRetrievalState("idle");
    setRetrievalError(null);
    setQaResult(null);
    setQaState("idle");
    setQaError(null);
  }

  async function handleImport(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!source.trim()) {
      setErrorMessage("Repository source is required.");
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);
    try {
      const imported = await importRepository({
        source: source.trim(),
        branch: branch.trim() || undefined
      });
      setSource("");
      setBranch("");
      await loadRepositories(imported.id);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Import failed.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleRetrieve(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedRepository || selectedRepository.status !== "ready") {
      setRetrievalError("Select a ready repository first.");
      setRetrievalState("failed");
      return;
    }
    if (!query.trim()) {
      setRetrievalError("Query is required.");
      setRetrievalState("failed");
      return;
    }

    setRetrievalState("searching");
    setRetrievalError(null);
    try {
      const result = await retrieveRepository(selectedRepository.id, {
        query: query.trim(),
        top_k: topK,
        use_bm25: useBm25,
        use_vector: useVector,
        use_graph: useGraph
      });
      setRetrievalResult(result);
      setRetrievalState(result.evidences.length > 0 ? "ready" : "empty");
    } catch (error) {
      setRetrievalResult(null);
      setRetrievalState("failed");
      setRetrievalError(error instanceof Error ? error.message : "Retrieval failed.");
    }
  }

  async function handleAsk(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedRepository || selectedRepository.status !== "ready") {
      setQaError("Select a ready repository first.");
      setQaState("failed");
      return;
    }
    if (!question.trim()) {
      setQaError("Question is required.");
      setQaState("failed");
      return;
    }

    setQaState("asking");
    setQaError(null);
    try {
      const result = await askRepositoryQuestion(selectedRepository.id, {
        question: question.trim(),
        top_k: qaTopK,
        use_bm25: qaUseBm25,
        use_vector: qaUseVector,
        use_graph: qaUseGraph
      });
      setQaResult(result);
      setQaState(result.status === "failed" ? "failed" : "ready");
      setQaError(result.error_message);
    } catch (error) {
      setQaResult(null);
      setQaState("failed");
      setQaError(error instanceof Error ? error.message : "Question failed.");
    }
  }

  return (
    <main className="min-h-screen bg-surface px-4 py-5 text-ink sm:px-6">
      <section className="mx-auto flex max-w-7xl flex-col gap-5">
        <header className="flex flex-col gap-2 border-b border-line pb-4 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-sm font-medium text-muted">RepoLens Workbench</p>
            <h1 className="text-2xl font-semibold">Repository Retrieval</h1>
          </div>
          <div className="text-sm text-muted">Phase 3</div>
        </header>

        <section className="grid gap-4 lg:grid-cols-[380px_1fr]">
          <aside className="flex flex-col gap-4">
            <form className="rounded-md border border-line bg-white p-4" onSubmit={handleImport}>
              <div className="flex items-center justify-between gap-3">
                <h2 className="text-base font-semibold">Repository</h2>
                <StatusBadge status={selectedRepository?.status ?? "pending"} />
              </div>

              <label className="mt-4 block text-xs font-medium uppercase text-muted" htmlFor="source">
                Source
              </label>
              <input
                id="source"
                className="mt-2 w-full rounded-md border border-line bg-white px-3 py-2 text-sm outline-none focus:border-ink"
                placeholder="F:\\Desktop\\agent"
                value={source}
                onChange={(event) => setSource(event.target.value)}
              />

              <label className="mt-3 block text-xs font-medium uppercase text-muted" htmlFor="branch">
                Branch
              </label>
              <input
                id="branch"
                className="mt-2 w-full rounded-md border border-line bg-white px-3 py-2 text-sm outline-none focus:border-ink"
                placeholder="main"
                value={branch}
                onChange={(event) => setBranch(event.target.value)}
              />

              <button
                className="mt-4 w-full rounded-md bg-ink px-3 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:bg-muted"
                disabled={isSubmitting}
                type="submit"
              >
                {isSubmitting ? "Importing" : "Import"}
              </button>

              <div className="mt-3 text-xs text-muted">{API_BASE_URL}</div>
            </form>

            <section className="rounded-md border border-line bg-white p-4">
              <div className="flex items-center justify-between gap-3">
                <h2 className="text-base font-semibold">Repositories</h2>
                <button
                  className="rounded-md border border-line px-3 py-1.5 text-xs font-medium text-ink disabled:text-muted"
                  disabled={isLoading}
                  onClick={() => void loadRepositories()}
                  type="button"
                >
                  Refresh
                </button>
              </div>

              <div className="mt-3 flex flex-col gap-2">
                {repositories.length === 0 ? (
                  <div className="rounded-md border border-dashed border-line px-3 py-6 text-center text-sm text-muted">
                    No repositories
                  </div>
                ) : (
                  repositories.map((repository) => (
                    <button
                      key={repository.id}
                      className={`rounded-md border px-3 py-3 text-left ${
                        selectedRepository?.id === repository.id
                          ? "border-ink bg-surface"
                          : "border-line bg-white"
                      }`}
                      onClick={() => void selectRepository(repository.id)}
                      type="button"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <div className="min-w-0 truncate text-sm font-medium">{repository.name}</div>
                        <StatusBadge status={repository.status} />
                      </div>
                      <div className="mt-2 flex gap-3 text-xs text-muted">
                        <span>{repository.file_count} files</span>
                        <span>{repository.chunk_count} chunks</span>
                        <span>{repository.relation_count} relations</span>
                      </div>
                    </button>
                  ))
                )}
              </div>
            </section>
          </aside>

          <section className="flex flex-col gap-4">
            {errorMessage ? (
              <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
                {errorMessage}
              </div>
            ) : null}

            <section className="rounded-md border border-line bg-white p-4">
              <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                <div>
                  <h2 className="text-lg font-semibold">
                    {selectedRepository?.name ?? "No repository selected"}
                  </h2>
                  <p className="mt-1 break-all text-sm text-muted">
                    {selectedRepository?.local_path ?? "Import or select a repository."}
                  </p>
                </div>
                <StatusBadge status={selectedRepository?.status ?? "pending"} />
              </div>

              <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
                {selectedMetrics.map((metric) => (
                  <Metric key={metric.key} label={metric.label} value={metric.value} />
                ))}
              </div>
            </section>

            <section className="grid gap-4 xl:grid-cols-[0.8fr_1.2fr]">
              <article className="rounded-md border border-line bg-white p-4">
                <h2 className="text-base font-semibold">Languages</h2>
                <div className="mt-4 flex flex-col gap-3">
                  {selectedRepository &&
                  Object.keys(selectedRepository.language_summary).length > 0 ? (
                    Object.entries(selectedRepository.language_summary).map(([language, count]) => (
                      <LanguageRow key={language} count={count} language={language} />
                    ))
                  ) : (
                    <div className="rounded-md border border-dashed border-line px-3 py-6 text-center text-sm text-muted">
                      No language data
                    </div>
                  )}
                </div>
              </article>

              <article className="rounded-md border border-line bg-white p-4">
                <h2 className="text-base font-semibold">Index Status</h2>
                <div className="mt-4 grid gap-3 md:grid-cols-2">
                  <InfoItem label="Current step" value={selectedStatus?.progress.current_step ?? "-"} />
                  <InfoItem label="Source type" value={selectedRepository?.source_type ?? "-"} />
                  <InfoItem label="Branch" value={selectedRepository?.branch ?? "-"} />
                  <InfoItem
                    label="Commit"
                    value={selectedRepository?.commit_hash?.slice(0, 12) ?? "-"}
                  />
                  <InfoItem
                    label="Updated"
                    value={formatDate(selectedRepository?.updated_at)}
                  />
                  <InfoItem
                    label="Indexed"
                    value={formatDate(selectedRepository?.indexed_at)}
                  />
                </div>
                {selectedRepository?.error_message || selectedStatus?.error_message ? (
                  <div className="mt-4 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
                    {selectedRepository?.error_message ?? selectedStatus?.error_message}
                  </div>
                ) : null}
              </article>
            </section>

            <section className="rounded-md border border-line bg-white p-4">
              <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                <div>
                  <h2 className="text-base font-semibold">Ask</h2>
                  <div className="mt-1 text-sm text-muted">{qaState}</div>
                </div>
                {qaResult?.confidence !== null && qaResult?.confidence !== undefined ? (
                  <div className="rounded-md border border-line bg-surface px-3 py-2 text-right">
                    <div className="text-xs uppercase text-muted">Confidence</div>
                    <div className="text-sm font-semibold">{formatScore(qaResult.confidence)}</div>
                  </div>
                ) : null}
              </div>

              <form className="mt-4 grid gap-3" onSubmit={handleAsk}>
                <textarea
                  className="min-h-24 rounded-md border border-line bg-white px-3 py-2 text-sm outline-none focus:border-ink disabled:bg-surface"
                  disabled={!selectedRepository || qaState === "asking"}
                  placeholder="Where is repository import implemented?"
                  value={question}
                  onChange={(event) => setQuestion(event.target.value)}
                />
                <div className="grid gap-3 md:grid-cols-[120px_1fr_auto] md:items-center">
                  <input
                    className="min-h-10 rounded-md border border-line bg-white px-3 py-2 text-sm outline-none focus:border-ink disabled:bg-surface"
                    disabled={qaState === "asking"}
                    min={1}
                    max={20}
                    type="number"
                    value={qaTopK}
                    onChange={(event) => setQaTopK(Number(event.target.value))}
                  />
                  <div className="flex flex-wrap gap-3 text-sm text-muted">
                    <Toggle label="BM25" checked={qaUseBm25} onChange={setQaUseBm25} />
                    <Toggle label="Vector" checked={qaUseVector} onChange={setQaUseVector} />
                    <Toggle label="Graph" checked={qaUseGraph} onChange={setQaUseGraph} />
                  </div>
                  <button
                    className="min-h-10 rounded-md bg-ink px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:bg-muted"
                    disabled={
                      !selectedRepository ||
                      selectedRepository.status !== "ready" ||
                      qaState === "asking"
                    }
                    type="submit"
                  >
                    {qaState === "asking" ? "Asking" : "Ask"}
                  </button>
                </div>
              </form>

              {qaError ? (
                <div className="mt-4 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
                  {qaError}
                </div>
              ) : null}

              {qaResult?.warnings.length ? (
                <div className="mt-4 flex flex-col gap-2">
                  {qaResult.warnings.map((warning) => (
                    <div
                      key={warning}
                      className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800"
                    >
                      {warning}
                    </div>
                  ))}
                </div>
              ) : null}

              {qaResult?.answer ? (
                <div className="mt-4 rounded-md border border-line bg-surface p-3">
                  <pre className="whitespace-pre-wrap text-sm leading-6 text-ink">{qaResult.answer}</pre>
                </div>
              ) : null}

              {qaResult?.citations.length ? (
                <div className="mt-4 flex flex-col gap-3">
                  <h3 className="text-sm font-semibold">Citations</h3>
                  {qaResult.citations.map((citation, index) => (
                    <CitationCard key={`${citation.evidence_id}-${index}`} citation={citation} index={index} />
                  ))}
                </div>
              ) : null}

              {qaResult?.traces.length ? (
                <TracePanel traces={qaResult.traces} />
              ) : null}
            </section>

            <section className="rounded-md border border-line bg-white p-4">
              <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                <div>
                  <h2 className="text-base font-semibold">Evidence</h2>
                  <div className="mt-1 text-sm text-muted">{retrievalState}</div>
                </div>
                {retrievalResult ? (
                  <div className="grid grid-cols-3 gap-2 text-right text-xs text-muted sm:grid-cols-5">
                    <DebugMetric label="BM25" value={retrievalResult.debug.bm25_count} />
                    <DebugMetric label="Vector" value={retrievalResult.debug.vector_count} />
                    <DebugMetric label="Graph" value={retrievalResult.debug.graph_count} />
                    <DebugMetric label="Merged" value={retrievalResult.debug.merged_count} />
                    <DebugMetric label="Evidence" value={retrievalResult.debug.evidence_count} />
                  </div>
                ) : null}
              </div>

              <form className="mt-4 grid gap-3 lg:grid-cols-[1fr_120px_auto]" onSubmit={handleRetrieve}>
                <input
                  className="min-h-10 rounded-md border border-line bg-white px-3 py-2 text-sm outline-none focus:border-ink disabled:bg-surface"
                  disabled={!selectedRepository || retrievalState === "searching"}
                  placeholder="repository import flow"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                />
                <input
                  className="min-h-10 rounded-md border border-line bg-white px-3 py-2 text-sm outline-none focus:border-ink disabled:bg-surface"
                  disabled={retrievalState === "searching"}
                  min={1}
                  max={50}
                  type="number"
                  value={topK}
                  onChange={(event) => setTopK(Number(event.target.value))}
                />
                <button
                  className="min-h-10 rounded-md bg-ink px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:bg-muted"
                  disabled={
                    !selectedRepository ||
                    selectedRepository.status !== "ready" ||
                    retrievalState === "searching"
                  }
                  type="submit"
                >
                  {retrievalState === "searching" ? "Searching" : "Search"}
                </button>
              </form>

              <div className="mt-3 flex flex-wrap gap-3 text-sm text-muted">
                <Toggle label="BM25" checked={useBm25} onChange={setUseBm25} />
                <Toggle label="Vector" checked={useVector} onChange={setUseVector} />
                <Toggle label="Graph" checked={useGraph} onChange={setUseGraph} />
              </div>

              {retrievalError ? (
                <div className="mt-4 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
                  {retrievalError}
                </div>
              ) : null}

              {retrievalResult?.debug.vector_disabled_reason ? (
                <div className="mt-4 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
                  {retrievalResult.debug.vector_disabled_reason}
                </div>
              ) : null}

              <div className="mt-4 flex flex-col gap-3">
                {retrievalState === "empty" ? (
                  <div className="rounded-md border border-dashed border-line px-3 py-6 text-center text-sm text-muted">
                    No evidence
                  </div>
                ) : null}
                {retrievalResult?.evidences.map((evidence) => (
                  <EvidenceCard key={evidence.evidence_id} evidence={evidence} />
                ))}
              </div>
            </section>
          </section>
        </section>
      </section>
    </main>
  );
}

function StatusBadge({ status }: { status: RepositoryStatus }) {
  const className =
    status === "ready"
      ? "border-emerald-200 bg-emerald-50 text-emerald-700"
      : status === "failed"
        ? "border-red-200 bg-red-50 text-red-700"
        : "border-blue-200 bg-blue-50 text-blue-700";

  return (
    <span className={`shrink-0 rounded-md border px-2 py-1 text-xs font-medium ${className}`}>
      {status}
    </span>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md border border-line bg-surface p-3">
      <div className="text-xs uppercase text-muted">{label}</div>
      <div className="mt-2 text-xl font-semibold">{value}</div>
    </div>
  );
}

function LanguageRow({ language, count }: { language: string; count: number }) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-md border border-line bg-surface px-3 py-2">
      <div className="text-sm font-medium">{language}</div>
      <div className="text-sm text-muted">{count}</div>
    </div>
  );
}

function InfoItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-line bg-surface p-3">
      <div className="text-xs uppercase text-muted">{label}</div>
      <div className="mt-2 break-all text-sm font-medium">{value}</div>
    </div>
  );
}

function Toggle({
  label,
  checked,
  onChange
}: {
  label: string;
  checked: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <label className="flex items-center gap-2">
      <input checked={checked} onChange={(event) => onChange(event.target.checked)} type="checkbox" />
      <span>{label}</span>
    </label>
  );
}

function DebugMetric({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <div className="uppercase">{label}</div>
      <div className="text-sm font-semibold text-ink">{value}</div>
    </div>
  );
}

function EvidenceCard({ evidence }: { evidence: EvidenceItem }) {
  return (
    <article className="rounded-md border border-line bg-surface p-3">
      <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
        <div className="min-w-0">
          <div className="break-all text-sm font-semibold">
            {evidence.file_path}:{evidence.start_line}-{evidence.end_line}
          </div>
          <div className="mt-1 text-sm text-muted">{evidence.symbol_name}</div>
        </div>
        <div className="flex flex-wrap gap-2 md:justify-end">
          <SourcePill value={formatScore(evidence.score)} />
          {evidence.sources.map((source) => (
            <SourcePill key={source} value={source} />
          ))}
        </div>
      </div>
      <pre className="mt-3 max-h-72 overflow-auto rounded-md border border-line bg-white p-3 text-xs leading-5 text-ink">
        {evidence.snippet}
      </pre>
    </article>
  );
}

function CitationCard({ citation, index }: { citation: QACitation; index: number }) {
  return (
    <article className="rounded-md border border-line bg-surface p-3">
      <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
        <div className="min-w-0">
          <div className="break-all text-sm font-semibold">
            [{index + 1}] {citation.file_path}:{citation.start_line}-{citation.end_line}
          </div>
          <div className="mt-1 text-sm text-muted">{citation.symbol_name}</div>
        </div>
        <div className="flex flex-wrap gap-2 md:justify-end">
          <SourcePill value={formatScore(citation.score)} />
          {citation.sources.map((source) => (
            <SourcePill key={source} value={source} />
          ))}
        </div>
      </div>
      <pre className="mt-3 max-h-56 overflow-auto rounded-md border border-line bg-white p-3 text-xs leading-5 text-ink">
        {citation.snippet}
      </pre>
    </article>
  );
}

function TracePanel({ traces }: { traces: AgentTrace[] }) {
  return (
    <div className="mt-4">
      <h3 className="text-sm font-semibold">Trace</h3>
      <div className="mt-3 flex flex-col gap-3">
        {traces.map((trace) => (
          <article key={trace.id} className="rounded-md border border-line bg-surface p-3">
            <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
              <div>
                <div className="text-sm font-semibold">
                  {trace.step_order}. {trace.step_name}
                </div>
                <div className="mt-1 text-xs uppercase text-muted">{trace.status}</div>
              </div>
              <div className="flex flex-wrap gap-2">
                <SourcePill value={`${trace.latency_ms ?? 0} ms`} />
                <SourcePill value={`${trace.evidence_ids.length} evidence`} />
                <SourcePill value={`${Number(trace.token_usage.total_tokens ?? 0)} tokens`} />
              </div>
            </div>
            <div className="mt-3 grid gap-2 lg:grid-cols-2">
              <TraceText label="Input" value={trace.input_summary} />
              <TraceText label="Output" value={trace.output_summary ?? "-"} />
            </div>
            {trace.tool_calls.length ? (
              <pre className="mt-3 max-h-48 overflow-auto rounded-md border border-line bg-white p-3 text-xs leading-5 text-ink">
                {JSON.stringify(trace.tool_calls, null, 2)}
              </pre>
            ) : null}
            {trace.error_message ? (
              <div className="mt-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
                {trace.error_message}
              </div>
            ) : null}
          </article>
        ))}
      </div>
    </div>
  );
}

function TraceText({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-line bg-white p-3">
      <div className="text-xs uppercase text-muted">{label}</div>
      <div className="mt-2 break-words text-sm">{value}</div>
    </div>
  );
}

function SourcePill({ value }: { value: string }) {
  return (
    <span className="rounded-md border border-line bg-white px-2 py-1 text-xs font-medium text-muted">
      {value}
    </span>
  );
}

function formatScore(value: number) {
  return value.toFixed(3);
}

function formatDate(value?: string | null) {
  if (!value) {
    return "-";
  }
  return new Intl.DateTimeFormat("en", {
    dateStyle: "short",
    timeStyle: "short"
  }).format(new Date(value));
}
