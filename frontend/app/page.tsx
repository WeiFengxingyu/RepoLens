"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  API_BASE_URL,
  askRepositoryQuestion,
  createEvaluation,
  createReview,
  getRepository,
  getRepositoryStatus,
  importRepository,
  listRepositories,
  retrieveRepository
} from "@/lib/api";
import type {
  AgentTrace,
  EvidenceItem,
  EvaluationMetric,
  EvaluationResult,
  EvaluationRunResponse,
  EvaluationStrategy,
  QACitation,
  QATaskResponse,
  ReviewCitation,
  ReviewRisk,
  ReviewSuggestedTest,
  ReviewTaskResponse,
  ReviewToolCall,
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

const demoRetrievalQuery =
  "Where is repository import implemented and which scanner chunking modules does it use?";
const demoQuestion =
  "Describe the frontend data flow from DashboardPage to RepositoryList and the repository API client.";
const demoReviewDiff = `diff --git a/src/app/dashboard/page.tsx b/src/app/dashboard/page.tsx
--- a/src/app/dashboard/page.tsx
+++ b/src/app/dashboard/page.tsx
@@ -1,8 +1,9 @@
 export default async function DashboardPage() {
   const repositories = await fetchRepositories();
+  const visible = repositories.slice(0, 5);
   return (
     <main>
       <h1>RepoLens Dashboard</h1>
-      <RepositoryList repositories={repositories} />
+      <RepositoryList repositories={visible} />
     </main>
   );
 }`;

export default function Home() {
  const [source, setSource] = useState("");
  const [branch, setBranch] = useState("");
  const [repositories, setRepositories] = useState<RepositorySummary[]>([]);
  const [selectedRepository, setSelectedRepository] = useState<RepositoryDetail | null>(null);
  const [selectedStatus, setSelectedStatus] = useState<RepositoryStatusResponse | null>(null);
  const [query, setQuery] = useState(demoRetrievalQuery);
  const [topK, setTopK] = useState(10);
  const [useBm25, setUseBm25] = useState(true);
  const [useVector, setUseVector] = useState(true);
  const [useGraph, setUseGraph] = useState(true);
  const [question, setQuestion] = useState(demoQuestion);
  const [qaTopK, setQaTopK] = useState(8);
  const [qaUseBm25, setQaUseBm25] = useState(true);
  const [qaUseVector, setQaUseVector] = useState(true);
  const [qaUseGraph, setQaUseGraph] = useState(true);
  const [qaResult, setQaResult] = useState<QATaskResponse | null>(null);
  const [qaState, setQaState] = useState<"idle" | "asking" | "ready" | "failed">("idle");
  const [qaError, setQaError] = useState<string | null>(null);
  const [diffText, setDiffText] = useState(demoReviewDiff);
  const [reviewTopK, setReviewTopK] = useState(8);
  const [reviewUseBm25, setReviewUseBm25] = useState(true);
  const [reviewUseVector, setReviewUseVector] = useState(true);
  const [reviewUseGraph, setReviewUseGraph] = useState(true);
  const [reviewRunStaticCheck, setReviewRunStaticCheck] = useState(false);
  const [reviewResult, setReviewResult] = useState<ReviewTaskResponse | null>(null);
  const [reviewState, setReviewState] = useState<"idle" | "reviewing" | "ready" | "failed">("idle");
  const [reviewError, setReviewError] = useState<string | null>(null);
  const [evaluationName, setEvaluationName] = useState("P0+ baseline");
  const [evaluationDatasetPath, setEvaluationDatasetPath] = useState(
    "evals/datasets/p0_plus_eval.jsonl"
  );
  const [evaluationStrategy, setEvaluationStrategy] = useState<EvaluationStrategy>("all");
  const [evaluationRepositoryKey, setEvaluationRepositoryKey] = useState("python_demo,ts_demo");
  const [evaluationTopK, setEvaluationTopK] = useState(5);
  const [evaluationResult, setEvaluationResult] = useState<EvaluationRunResponse | null>(null);
  const [evaluationState, setEvaluationState] = useState<
    "idle" | "running" | "ready" | "failed"
  >("idle");
  const [evaluationError, setEvaluationError] = useState<string | null>(null);
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
    setReviewResult(null);
    setReviewState("idle");
    setReviewError(null);
    setEvaluationResult(null);
    setEvaluationState("idle");
    setEvaluationError(null);
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

  async function handleReview(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedRepository || selectedRepository.status !== "ready") {
      setReviewError("Select a ready repository first.");
      setReviewState("failed");
      return;
    }
    if (!diffText.trim()) {
      setReviewError("Diff text is required.");
      setReviewState("failed");
      return;
    }

    setReviewState("reviewing");
    setReviewError(null);
    try {
      const result = await createReview(selectedRepository.id, {
        diff_text: diffText.trim(),
        top_k: reviewTopK,
        use_bm25: reviewUseBm25,
        use_vector: reviewUseVector,
        use_graph: reviewUseGraph,
        run_static_check: reviewRunStaticCheck
      });
      setReviewResult(result);
      setReviewState(result.status === "failed" ? "failed" : "ready");
      setReviewError(result.error_message);
    } catch (error) {
      setReviewResult(null);
      setReviewState("failed");
      setReviewError(error instanceof Error ? error.message : "Review failed.");
    }
  }

  async function handleEvaluation(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedRepository || selectedRepository.status !== "ready") {
      setEvaluationError("Select a ready repository first.");
      setEvaluationState("failed");
      return;
    }
    if (!evaluationDatasetPath.trim()) {
      setEvaluationError("Dataset path is required.");
      setEvaluationState("failed");
      return;
    }
    const repositoryMap = buildEvaluationRepositoryMap(
      evaluationRepositoryKey,
      repositories,
      selectedRepository
    );
    if (!Object.keys(repositoryMap).length) {
      setEvaluationError("Repository key is required.");
      setEvaluationState("failed");
      return;
    }
    const missingKeys = evaluationRepositoryKeys(evaluationRepositoryKey).filter(
      (key) => !repositoryMap[key]
    );
    if (missingKeys.length) {
      setEvaluationError(`Missing ready repository for key(s): ${missingKeys.join(", ")}`);
      setEvaluationState("failed");
      return;
    }

    setEvaluationState("running");
    setEvaluationError(null);
    try {
      const result = await createEvaluation({
        name: evaluationName.trim() || "P0+ baseline",
        dataset_path: evaluationDatasetPath.trim(),
        strategy: evaluationStrategy,
        repository_map: repositoryMap,
        top_k: evaluationTopK
      });
      setEvaluationResult(result);
      setEvaluationState(result.status === "failed" ? "failed" : "ready");
      setEvaluationError(result.error_message);
    } catch (error) {
      setEvaluationResult(null);
      setEvaluationState("failed");
      setEvaluationError(error instanceof Error ? error.message : "Evaluation failed.");
    }
  }

  return (
    <main className="min-h-screen bg-surface px-4 py-5 text-ink sm:px-6">
      <section className="mx-auto flex max-w-7xl flex-col gap-5">
        <header className="flex flex-col gap-2 border-b border-line pb-4 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-sm font-medium text-muted">RepoLens Workbench</p>
            <h1 className="text-2xl font-semibold">Repository Review</h1>
          </div>
          <div className="text-sm text-muted">Phase 5</div>
        </header>

        <section className="grid gap-4 lg:grid-cols-[380px_minmax(0,1fr)]">
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

          <section className="min-w-0 flex flex-col gap-4">
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

            <section className="grid min-w-0 gap-4 xl:grid-cols-[0.8fr_1.2fr]">
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

            <section className="min-w-0 rounded-md border border-line bg-white p-4">
              <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                <div>
                  <h2 className="text-base font-semibold">Evaluation</h2>
                  <div className="mt-1 text-sm text-muted">{evaluationState}</div>
                </div>
                {evaluationResult ? (
                  <div className="rounded-md border border-line bg-surface px-3 py-2 text-right">
                    <div className="text-xs uppercase text-muted">Samples</div>
                    <div className="text-sm font-semibold">{evaluationResult.sample_count}</div>
                  </div>
                ) : null}
              </div>

              <form className="mt-4 grid gap-3" onSubmit={handleEvaluation}>
                <div className="grid gap-3 md:grid-cols-2">
                  <input
                    className="min-h-10 rounded-md border border-line bg-white px-3 py-2 text-sm outline-none focus:border-ink disabled:bg-surface"
                    disabled={evaluationState === "running"}
                    value={evaluationName}
                    onChange={(event) => setEvaluationName(event.target.value)}
                  />
                  <input
                    className="min-h-10 rounded-md border border-line bg-white px-3 py-2 text-sm outline-none focus:border-ink disabled:bg-surface"
                    disabled={evaluationState === "running"}
                    value={evaluationDatasetPath}
                    onChange={(event) => setEvaluationDatasetPath(event.target.value)}
                  />
                </div>
                <div className="grid gap-3 md:grid-cols-[1fr_140px_120px_auto] md:items-center">
                  <input
                    className="min-h-10 rounded-md border border-line bg-white px-3 py-2 text-sm outline-none focus:border-ink disabled:bg-surface"
                    disabled={evaluationState === "running"}
                    value={evaluationRepositoryKey}
                    onChange={(event) => setEvaluationRepositoryKey(event.target.value)}
                  />
                  <select
                    className="min-h-10 rounded-md border border-line bg-white px-3 py-2 text-sm outline-none focus:border-ink disabled:bg-surface"
                    disabled={evaluationState === "running"}
                    value={evaluationStrategy}
                    onChange={(event) =>
                      setEvaluationStrategy(event.target.value as EvaluationStrategy)
                    }
                  >
                    <option value="all">all</option>
                    <option value="vector_only">vector_only</option>
                    <option value="bm25_vector">bm25_vector</option>
                    <option value="bm25_vector_graph">bm25_vector_graph</option>
                  </select>
                  <input
                    className="min-h-10 rounded-md border border-line bg-white px-3 py-2 text-sm outline-none focus:border-ink disabled:bg-surface"
                    disabled={evaluationState === "running"}
                    min={1}
                    max={20}
                    type="number"
                    value={evaluationTopK}
                    onChange={(event) => setEvaluationTopK(Number(event.target.value))}
                  />
                  <button
                    className="min-h-10 rounded-md bg-ink px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:bg-muted"
                    disabled={
                      !selectedRepository ||
                      selectedRepository.status !== "ready" ||
                      evaluationState === "running"
                    }
                    type="submit"
                  >
                    {evaluationState === "running" ? "Running" : "Run"}
                  </button>
                </div>
              </form>

              {evaluationError ? (
                <div className="mt-4 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
                  {evaluationError}
                </div>
              ) : null}

              {evaluationResult?.warnings.length ? (
                <div className="mt-4 flex flex-col gap-2">
                  {evaluationResult.warnings.slice(0, 5).map((warning) => (
                    <div
                      key={warning}
                      className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800"
                    >
                      {warning}
                    </div>
                  ))}
                </div>
              ) : null}

              {evaluationResult?.metrics.length ? (
                <EvaluationMetricsTable metrics={evaluationResult.metrics} />
              ) : null}

              {evaluationResult?.results.length ? (
                <EvaluationResultsTable results={evaluationResult.results} />
              ) : null}
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
                  <h2 className="text-base font-semibold">Review</h2>
                  <div className="mt-1 text-sm text-muted">{reviewState}</div>
                </div>
                {reviewResult ? (
                  <div className="rounded-md border border-line bg-surface px-3 py-2 text-right">
                    <div className="text-xs uppercase text-muted">Risk</div>
                    <div className="text-sm font-semibold">{reviewResult.risk_level ?? "-"}</div>
                  </div>
                ) : null}
              </div>

              <form className="mt-4 grid gap-3" onSubmit={handleReview}>
                <textarea
                  className="min-h-44 rounded-md border border-line bg-white px-3 py-2 font-mono text-xs leading-5 outline-none focus:border-ink disabled:bg-surface"
                  disabled={!selectedRepository || reviewState === "reviewing"}
                  placeholder="diff --git a/app.py b/app.py"
                  value={diffText}
                  onChange={(event) => setDiffText(event.target.value)}
                />
                <div className="grid gap-3 md:grid-cols-[120px_1fr_auto] md:items-center">
                  <input
                    className="min-h-10 rounded-md border border-line bg-white px-3 py-2 text-sm outline-none focus:border-ink disabled:bg-surface"
                    disabled={reviewState === "reviewing"}
                    min={1}
                    max={50}
                    type="number"
                    value={reviewTopK}
                    onChange={(event) => setReviewTopK(Number(event.target.value))}
                  />
                  <div className="flex flex-wrap gap-3 text-sm text-muted">
                    <Toggle label="BM25" checked={reviewUseBm25} onChange={setReviewUseBm25} />
                    <Toggle label="Vector" checked={reviewUseVector} onChange={setReviewUseVector} />
                    <Toggle label="Graph" checked={reviewUseGraph} onChange={setReviewUseGraph} />
                    <Toggle
                      label="Static check"
                      checked={reviewRunStaticCheck}
                      onChange={setReviewRunStaticCheck}
                    />
                  </div>
                  <button
                    className="min-h-10 rounded-md bg-ink px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:bg-muted"
                    disabled={
                      !selectedRepository ||
                      selectedRepository.status !== "ready" ||
                      reviewState === "reviewing"
                    }
                    type="submit"
                  >
                    {reviewState === "reviewing" ? "Reviewing" : "Review"}
                  </button>
                </div>
              </form>

              {reviewError ? (
                <div className="mt-4 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
                  {reviewError}
                </div>
              ) : null}

              {reviewResult?.summary ? (
                <div className="mt-4 rounded-md border border-line bg-surface p-3 text-sm leading-6">
                  {reviewResult.summary}
                </div>
              ) : null}

              {reviewResult?.risks.length ? (
                <div className="mt-4 flex flex-col gap-3">
                  <h3 className="text-sm font-semibold">Risks</h3>
                  {reviewResult.risks.map((risk, index) => (
                    <ReviewRiskCard key={`${risk.title ?? "risk"}-${index}`} risk={risk} />
                  ))}
                </div>
              ) : null}

              {reviewResult?.suggested_tests.length ? (
                <div className="mt-4 flex flex-col gap-3">
                  <h3 className="text-sm font-semibold">Suggested Tests</h3>
                  {reviewResult.suggested_tests.map((test, index) => (
                    <SuggestedTestCard key={`${test.target ?? "test"}-${index}`} test={test} />
                  ))}
                </div>
              ) : null}

              {reviewResult?.citations.length ? (
                <div className="mt-4 flex flex-col gap-3">
                  <h3 className="text-sm font-semibold">Review Citations</h3>
                  {reviewResult.citations.map((citation, index) => (
                    <ReviewCitationCard
                      key={`${citation.evidence_id ?? "citation"}-${index}`}
                      citation={citation}
                      index={index}
                    />
                  ))}
                </div>
              ) : null}

              {reviewResult?.markdown ? (
                <pre className="mt-4 max-h-80 overflow-auto whitespace-pre-wrap break-words rounded-md border border-line bg-surface p-3 text-xs leading-5 text-ink">
                  {reviewResult.markdown}
                </pre>
              ) : null}

              {reviewResult?.tool_calls.length ? (
                <ToolCallsPanel toolCalls={reviewResult.tool_calls} />
              ) : null}

              {reviewResult?.traces.length ? (
                <TracePanel traces={reviewResult.traces} />
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

function evaluationRepositoryKeys(value: string): string[] {
  return value
    .split(/[,\s]+/)
    .map((key) => key.trim())
    .filter(Boolean);
}

function buildEvaluationRepositoryMap(
  value: string,
  repositories: RepositorySummary[],
  selectedRepository: RepositoryDetail | null
): Record<string, string> {
  const keys = evaluationRepositoryKeys(value);
  const map: Record<string, string> = {};
  for (const key of keys) {
    const matchingRepository = repositories.find(
      (repository) => repository.name === key && repository.status === "ready"
    );
    if (matchingRepository) {
      map[key] = matchingRepository.id;
    } else if (keys.length === 1 && selectedRepository?.status === "ready") {
      map[key] = selectedRepository.id;
    }
  }
  return map;
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

function ReviewRiskCard({ risk }: { risk: ReviewRisk }) {
  const location = risk.location;
  return (
    <article className="rounded-md border border-line bg-surface p-3">
      <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
        <div className="min-w-0">
          <div className="break-words text-sm font-semibold">{risk.title ?? "Review risk"}</div>
          <div className="mt-1 break-all text-sm text-muted">
            {location
              ? `${location.file_path}:${location.start_line}-${location.end_line}`
              : "-"}
          </div>
        </div>
        <div className="flex flex-wrap gap-2 md:justify-end">
          <SourcePill value={risk.severity ?? "unknown"} />
          <SourcePill value={`${risk.evidence_ids?.length ?? 0} evidence`} />
        </div>
      </div>
      {risk.reason ? <div className="mt-3 text-sm leading-6">{risk.reason}</div> : null}
      {risk.suggestion ? (
        <div className="mt-3 rounded-md border border-line bg-white p-3 text-sm leading-6">
          {risk.suggestion}
        </div>
      ) : null}
      {risk.impacted_symbols?.length ? (
        <div className="mt-3 flex flex-wrap gap-2">
          {risk.impacted_symbols.map((symbol) => (
            <SourcePill key={symbol} value={symbol} />
          ))}
        </div>
      ) : null}
    </article>
  );
}

function SuggestedTestCard({ test }: { test: ReviewSuggestedTest }) {
  return (
    <article className="rounded-md border border-line bg-surface p-3">
      <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
        <div className="min-w-0">
          <div className="break-words text-sm font-semibold">{test.target ?? "Focused test"}</div>
          <div className="mt-1 break-all text-sm text-muted">{test.file_path ?? "-"}</div>
        </div>
        <SourcePill value={test.test_type ?? "test"} />
      </div>
      {test.reason ? <div className="mt-3 text-sm leading-6">{test.reason}</div> : null}
      {test.related_risk_titles?.length ? (
        <div className="mt-3 flex flex-wrap gap-2">
          {test.related_risk_titles.map((title) => (
            <SourcePill key={title} value={title} />
          ))}
        </div>
      ) : null}
    </article>
  );
}

function ReviewCitationCard({
  citation,
  index
}: {
  citation: ReviewCitation;
  index: number;
}) {
  return (
    <article className="rounded-md border border-line bg-surface p-3">
      <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
        <div className="min-w-0">
          <div className="break-all text-sm font-semibold">
            [{index + 1}] {citation.file_path ?? "-"}:{citation.start_line ?? 0}-
            {citation.end_line ?? 0}
          </div>
          <div className="mt-1 text-sm text-muted">{citation.symbol_name ?? citation.evidence_id}</div>
        </div>
        <div className="flex flex-wrap gap-2 md:justify-end">
          <SourcePill value={formatOptionalScore(citation.score)} />
          {(citation.sources ?? []).map((source) => (
            <SourcePill key={source} value={source} />
          ))}
        </div>
      </div>
      {citation.snippet ? (
        <pre className="mt-3 max-h-56 overflow-auto rounded-md border border-line bg-white p-3 text-xs leading-5 text-ink">
          {citation.snippet}
        </pre>
      ) : null}
    </article>
  );
}

function EvaluationMetricsTable({ metrics }: { metrics: EvaluationMetric[] }) {
  return (
    <div className="mt-4 max-w-full overflow-x-auto rounded-md border border-line">
      <table className="w-full min-w-[840px] border-collapse text-left text-sm">
        <thead className="bg-surface text-xs uppercase text-muted">
          <tr>
            <th className="px-3 py-2">Strategy</th>
            <th className="px-3 py-2">Samples</th>
            <th className="px-3 py-2">Hit@5</th>
            <th className="px-3 py-2">MRR</th>
            <th className="px-3 py-2">Coverage</th>
            <th className="px-3 py-2">Avg ms</th>
            <th className="px-3 py-2">P95 ms</th>
            <th className="px-3 py-2">Avg tokens</th>
            <th className="px-3 py-2">Errors</th>
          </tr>
        </thead>
        <tbody>
          {metrics.map((metric) => (
            <tr key={metric.strategy} className="border-t border-line">
              <td className="px-3 py-2 font-medium">{metric.strategy}</td>
              <td className="px-3 py-2">{metric.sample_count}</td>
              <td className="px-3 py-2">{formatPercent(metric.hit_at_5)}</td>
              <td className="px-3 py-2">{formatScore(metric.mrr)}</td>
              <td className="px-3 py-2">{formatPercent(metric.citation_coverage)}</td>
              <td className="px-3 py-2">{formatNumber(metric.avg_latency_ms)}</td>
              <td className="px-3 py-2">{metric.p95_latency_ms}</td>
              <td className="px-3 py-2">
                {formatNumber(metric.avg_token_count)}
                {metric.token_estimated ? " est" : ""}
              </td>
              <td className="px-3 py-2">{metric.error_count}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function EvaluationResultsTable({ results }: { results: EvaluationResult[] }) {
  return (
    <div className="mt-4 max-h-96 max-w-full overflow-auto rounded-md border border-line">
      <table className="w-full min-w-[920px] border-collapse text-left text-sm">
        <thead className="sticky top-0 bg-surface text-xs uppercase text-muted">
          <tr>
            <th className="px-3 py-2">Sample</th>
            <th className="px-3 py-2">Type</th>
            <th className="px-3 py-2">Strategy</th>
            <th className="px-3 py-2">Hit</th>
            <th className="px-3 py-2">MRR</th>
            <th className="px-3 py-2">Coverage</th>
            <th className="px-3 py-2">Latency</th>
            <th className="px-3 py-2">Matched</th>
            <th className="px-3 py-2">Error</th>
          </tr>
        </thead>
        <tbody>
          {results.map((result) => (
            <tr key={result.id} className="border-t border-line">
              <td className="px-3 py-2 font-medium">{result.sample_id}</td>
              <td className="px-3 py-2">{result.sample_type}</td>
              <td className="px-3 py-2">{result.strategy}</td>
              <td className="px-3 py-2">{result.hit_at_5 ? "yes" : "no"}</td>
              <td className="px-3 py-2">{formatScore(result.mrr)}</td>
              <td className="px-3 py-2">{formatPercent(result.citation_coverage)}</td>
              <td className="px-3 py-2">{result.latency_ms} ms</td>
              <td className="max-w-72 truncate px-3 py-2">
                {[...result.matched_files, ...result.matched_symbols].join(", ") || "-"}
              </td>
              <td className="max-w-72 truncate px-3 py-2">{result.error_message ?? "-"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ToolCallsPanel({ toolCalls }: { toolCalls: ReviewToolCall[] }) {
  return (
    <div className="mt-4">
      <h3 className="text-sm font-semibold">Tool Calls</h3>
      <div className="mt-3 flex flex-col gap-3">
        {toolCalls.map((toolCall) => (
          <ToolCallRow key={toolCall.id} toolCall={toolCall} />
        ))}
      </div>
    </div>
  );
}

function ToolCallRow({ toolCall }: { toolCall: ReviewToolCall }) {
  return (
    <article className="rounded-md border border-line bg-surface p-3">
      <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
        <div className="min-w-0">
          <div className="break-words text-sm font-semibold">{toolCall.tool_name}</div>
          <div className="mt-1 text-sm text-muted">{toolCall.input_summary}</div>
        </div>
        <div className="flex flex-wrap gap-2 md:justify-end">
          <SourcePill value={toolCall.status} />
          <SourcePill value={toolCall.permission_decision} />
          <SourcePill value={`${toolCall.latency_ms ?? 0} ms`} />
        </div>
      </div>
      {toolCall.output_summary ? (
        <div className="mt-3 rounded-md border border-line bg-white p-3 text-sm leading-6">
          {toolCall.output_summary}
        </div>
      ) : null}
      {toolCall.error_message ? (
        <div className="mt-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
          {toolCall.error_message}
        </div>
      ) : null}
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
              <div className="mt-3 flex flex-col gap-2">
                {trace.tool_calls.map((toolCall, index) => (
                  <TraceToolCallRow key={`${trace.id}-tool-${index}`} toolCall={toolCall} />
                ))}
              </div>
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

function TraceToolCallRow({ toolCall }: { toolCall: Record<string, unknown> }) {
  return (
    <div className="rounded-md border border-line bg-white p-3">
      <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
        <div className="min-w-0">
          <div className="break-words text-sm font-semibold">
            {stringValue(toolCall.tool_name) || stringValue(toolCall.name) || "tool"}
          </div>
          <div className="mt-1 text-sm text-muted">
            {stringValue(toolCall.input_summary) || stringValue(toolCall.output_summary) || "-"}
          </div>
        </div>
        <div className="flex flex-wrap gap-2 md:justify-end">
          <SourcePill value={stringValue(toolCall.status) || "-"} />
          <SourcePill value={stringValue(toolCall.permission_decision) || "-"} />
          <SourcePill value={`${numberValue(toolCall.latency_ms)} ms`} />
        </div>
      </div>
      {stringValue(toolCall.error_message) ? (
        <div className="mt-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
          {stringValue(toolCall.error_message)}
        </div>
      ) : null}
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

function formatOptionalScore(value?: number) {
  return typeof value === "number" ? formatScore(value) : "-";
}

function formatPercent(value: number) {
  return `${Math.round(value * 1000) / 10}%`;
}

function formatNumber(value: number) {
  return Number.isInteger(value) ? String(value) : value.toFixed(1);
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

function stringValue(value: unknown) {
  return typeof value === "string" ? value : "";
}

function numberValue(value: unknown) {
  return typeof value === "number" ? value : 0;
}
