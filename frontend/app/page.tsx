"use client";

import { useEffect, useMemo, useState } from "react";
import type { FormEvent, ReactNode } from "react";
import {
  API_BASE_URL,
  askRepositoryQuestion,
  callMcpTool,
  createEvaluation,
  createReview,
  getRepository,
  getRepositoryStatus,
  importRepository,
  listEvaluations,
  listMcpToolCalls,
  listMcpTools,
  listRepositories,
  retrieveRepository
} from "@/lib/api";
import type {
  AgentTrace,
  EvaluationRunResponse,
  EvaluationRunSummary,
  EvaluationStrategy,
  EvidenceItem,
  McpToolCallAudit,
  McpToolCallResponse,
  McpToolInfo,
  QACitation,
  QATaskResponse,
  RepositoryDetail,
  RepositoryStatus,
  RepositoryStatusResponse,
  RepositorySummary,
  RetrievalResponse,
  ReviewCitation,
  ReviewRisk,
  ReviewSuggestedTest,
  ReviewTaskResponse,
  ReviewToolCall
} from "@/types/workbench";

type WorkbenchTab = "search" | "ask" | "review" | "mcp" | "eval";
type AsyncState = "idle" | "running" | "ready" | "empty" | "failed";

const tabs: Array<{ id: WorkbenchTab; label: string }> = [
  { id: "search", label: "Search" },
  { id: "ask", label: "Ask" },
  { id: "review", label: "Review" },
  { id: "mcp", label: "MCP" },
  { id: "eval", label: "Eval" }
];

const metricLabels: Array<{
  key: keyof Pick<
    RepositoryDetail,
    "file_count" | "parsed_file_count" | "skipped_file_count" | "chunk_count" | "relation_count"
  >;
  label: string;
}> = [
  { key: "file_count", label: "Files" },
  { key: "parsed_file_count", label: "Parsed" },
  { key: "skipped_file_count", label: "Skipped" },
  { key: "chunk_count", label: "Chunks" },
  { key: "relation_count", label: "Relations" }
];

const defaultQuery = "RepositoryApplicationService index task retrieval";
const defaultQuestion = "Where is repository import and indexing started?";
const defaultDiff = `diff --git a/src/main/java/com/demo/SecurityConfig.java b/src/main/java/com/demo/SecurityConfig.java
--- a/src/main/java/com/demo/SecurityConfig.java
+++ b/src/main/java/com/demo/SecurityConfig.java
@@ -2,6 +2,8 @@ package demo;
 class SecurityConfig {
   void configure() {
-    requireAuth();
+    permitAll();
+    return null;
   }
 }`;

export default function Home() {
  const [source, setSource] = useState("");
  const [branch, setBranch] = useState("");
  const [repositories, setRepositories] = useState<RepositorySummary[]>([]);
  const [selectedRepository, setSelectedRepository] = useState<RepositoryDetail | null>(null);
  const [selectedStatus, setSelectedStatus] = useState<RepositoryStatusResponse | null>(null);
  const [activeTab, setActiveTab] = useState<WorkbenchTab>("search");

  const [query, setQuery] = useState(defaultQuery);
  const [topK, setTopK] = useState(10);
  const [useBm25, setUseBm25] = useState(true);
  const [useVector, setUseVector] = useState(true);
  const [useGraph, setUseGraph] = useState(true);
  const [retrievalResult, setRetrievalResult] = useState<RetrievalResponse | null>(null);
  const [retrievalState, setRetrievalState] = useState<AsyncState>("idle");
  const [retrievalError, setRetrievalError] = useState<string | null>(null);

  const [question, setQuestion] = useState(defaultQuestion);
  const [qaResult, setQaResult] = useState<QATaskResponse | null>(null);
  const [qaState, setQaState] = useState<AsyncState>("idle");
  const [qaError, setQaError] = useState<string | null>(null);

  const [diffText, setDiffText] = useState(defaultDiff);
  const [reviewResult, setReviewResult] = useState<ReviewTaskResponse | null>(null);
  const [reviewState, setReviewState] = useState<AsyncState>("idle");
  const [reviewError, setReviewError] = useState<string | null>(null);

  const [mcpTools, setMcpTools] = useState<McpToolInfo[]>([]);
  const [mcpAudits, setMcpAudits] = useState<McpToolCallAudit[]>([]);
  const [mcpCallResult, setMcpCallResult] = useState<McpToolCallResponse | null>(null);
  const [mcpState, setMcpState] = useState<AsyncState>("idle");
  const [mcpError, setMcpError] = useState<string | null>(null);

  const [evaluationName, setEvaluationName] = useState("java-v1-demo");
  const [evaluationDataset, setEvaluationDataset] = useState("evals/datasets/repolens_java_v1_eval.jsonl");
  const [evaluationStrategy, setEvaluationStrategy] = useState<EvaluationStrategy>("all");
  const [evaluationResult, setEvaluationResult] = useState<EvaluationRunResponse | null>(null);
  const [evaluationRuns, setEvaluationRuns] = useState<EvaluationRunSummary[]>([]);
  const [evaluationState, setEvaluationState] = useState<AsyncState>("idle");
  const [evaluationError, setEvaluationError] = useState<string | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    void loadRepositories();
  }, []);

  useEffect(() => {
    if (activeTab === "mcp") {
      void loadMcpData();
    }
    if (activeTab === "eval") {
      void loadEvaluationRuns();
    }
  }, [activeTab]);

  const selectedMetrics = useMemo(() => {
    if (!selectedRepository) {
      return [];
    }
    return metricLabels.map((metric) => ({
      ...metric,
      value: selectedRepository[metric.key]
    }));
  }, [selectedRepository]);

  const isReady = selectedRepository?.status === "ready";

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
    setMcpCallResult(null);
    setEvaluationResult(null);
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

    setRetrievalState("running");
    setRetrievalError(null);
    try {
      const result = await retrieveRepository(selectedRepository.id, retrievalPayload(query));
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

    setQaState("running");
    setQaError(null);
    try {
      const result = await askRepositoryQuestion(selectedRepository.id, {
        question: question.trim(),
        top_k: topK,
        use_bm25: useBm25,
        use_vector: useVector,
        use_graph: useGraph
      });
      setQaResult(result);
      setQaState(result.citations.length > 0 ? "ready" : "empty");
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

    setReviewState("running");
    setReviewError(null);
    try {
      const result = await createReview(selectedRepository.id, {
        diff_text: diffText,
        top_k: topK,
        use_bm25: useBm25,
        use_vector: useVector,
        use_graph: useGraph,
        run_static_check: false
      });
      setReviewResult(result);
      setReviewState("ready");
    } catch (error) {
      setReviewResult(null);
      setReviewState("failed");
      setReviewError(error instanceof Error ? error.message : "Review failed.");
    }
  }

  async function loadMcpData() {
    setMcpState("running");
    setMcpError(null);
    try {
      const [tools, audits] = await Promise.all([listMcpTools(), listMcpToolCalls(30)]);
      setMcpTools(tools);
      setMcpAudits(audits);
      setMcpState(tools.length || audits.length ? "ready" : "empty");
    } catch (error) {
      setMcpState("failed");
      setMcpError(error instanceof Error ? error.message : "Unable to load MCP data.");
    }
  }

  async function handleMcpSearch() {
    if (!selectedRepository || selectedRepository.status !== "ready") {
      setMcpError("Select a ready repository first.");
      setMcpState("failed");
      return;
    }

    setMcpState("running");
    setMcpError(null);
    try {
      const result = await callMcpTool({
        name: "repolens.search",
        arguments: {
          repository_id: selectedRepository.id,
          query: query.trim() || defaultQuery,
          top_k: topK,
          use_bm25: useBm25,
          use_vector: useVector,
          use_graph: useGraph
        },
        client_name: "workbench",
        client_session_id: "java-v1-demo"
      });
      setMcpCallResult(result);
      const audits = await listMcpToolCalls(30);
      setMcpAudits(audits);
      setMcpState("ready");
    } catch (error) {
      setMcpState("failed");
      setMcpError(error instanceof Error ? error.message : "MCP call failed.");
    }
  }

  async function loadEvaluationRuns() {
    try {
      setEvaluationRuns(await listEvaluations());
    } catch {
      setEvaluationRuns([]);
    }
  }

  async function handleEvaluation(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedRepository || selectedRepository.status !== "ready") {
      setEvaluationError("Select a ready repository first.");
      setEvaluationState("failed");
      return;
    }
    if (!evaluationDataset.trim()) {
      setEvaluationError("Dataset path is required.");
      setEvaluationState("failed");
      return;
    }

    setEvaluationState("running");
    setEvaluationError(null);
    try {
      const result = await createEvaluation({
        name: evaluationName.trim() || undefined,
        dataset_path: evaluationDataset.trim(),
        strategy: evaluationStrategy,
        repository_map: {
          java_demo: selectedRepository.id
        },
        top_k: Math.min(20, Math.max(1, topK))
      });
      setEvaluationResult(result);
      setEvaluationRuns(await listEvaluations());
      setEvaluationState("ready");
    } catch (error) {
      setEvaluationResult(null);
      setEvaluationState("failed");
      setEvaluationError(error instanceof Error ? error.message : "Evaluation failed.");
    }
  }

  function retrievalPayload(value: string) {
    return {
      query: value.trim(),
      top_k: topK,
      use_bm25: useBm25,
      use_vector: useVector,
      use_graph: useGraph
    };
  }

  return (
    <main className="min-h-screen bg-surface px-4 py-5 text-ink sm:px-6">
      <section className="mx-auto flex max-w-7xl flex-col gap-5">
        <header className="flex flex-col gap-2 border-b border-line pb-4 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-sm font-medium text-muted">RepoLens Java</p>
            <h1 className="text-2xl font-semibold">V1 Code Agent Workbench</h1>
          </div>
          <div className="text-sm text-muted">Java 21 / Spring Boot / MCP</div>
        </header>

        {errorMessage ? <Alert tone="red" message={errorMessage} /> : null}

        <section className="grid gap-4 lg:grid-cols-[360px_minmax(0,1fr)]">
          <aside className="flex flex-col gap-4">
            <RepositoryImportForm
              branch={branch}
              isSubmitting={isSubmitting}
              selectedRepository={selectedRepository}
              source={source}
              onBranchChange={setBranch}
              onSourceChange={setSource}
              onSubmit={handleImport}
            />

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
                  <EmptyState label={isLoading ? "Loading" : "No repositories"} />
                ) : (
                  repositories.map((repository) => (
                    <RepositoryListItem
                      key={repository.id}
                      active={selectedRepository?.id === repository.id}
                      repository={repository}
                      onSelect={() => void selectRepository(repository.id)}
                    />
                  ))
                )}
              </div>
            </section>

            <section className="rounded-md border border-line bg-white p-4">
              <h2 className="text-base font-semibold">Runtime</h2>
              <div className="mt-3 break-all text-xs text-muted">{API_BASE_URL}</div>
            </section>
          </aside>

          <section className="min-w-0 flex flex-col gap-4">
            <RepositoryOverview
              metrics={selectedMetrics}
              repository={selectedRepository}
              status={selectedStatus}
            />

            <section className="rounded-md border border-line bg-white p-4">
              <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                <div>
                  <h2 className="text-base font-semibold">Workspace</h2>
                  <div className="mt-1 text-sm text-muted">{activeTabStatus()}</div>
                </div>
                <div className="flex flex-wrap gap-2">
                  {tabs.map((tab) => (
                    <button
                      key={tab.id}
                      className={`rounded-md border px-3 py-1.5 text-sm font-medium ${
                        activeTab === tab.id
                          ? "border-ink bg-ink text-white"
                          : "border-line bg-white text-ink"
                      }`}
                      onClick={() => setActiveTab(tab.id)}
                      type="button"
                    >
                      {tab.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="mt-4">{renderActiveTab()}</div>
            </section>
          </section>
        </section>
      </section>
    </main>
  );

  function activeTabStatus(): string {
    const statusMap: Record<WorkbenchTab, AsyncState> = {
      search: retrievalState,
      ask: qaState,
      review: reviewState,
      mcp: mcpState,
      eval: evaluationState
    };
    return statusMap[activeTab];
  }

  function renderActiveTab() {
    if (activeTab === "search") {
      return renderSearchPanel();
    }
    if (activeTab === "ask") {
      return renderAskPanel();
    }
    if (activeTab === "review") {
      return renderReviewPanel();
    }
    if (activeTab === "mcp") {
      return renderMcpPanel();
    }
    return renderEvaluationPanel();
  }

  function renderSharedRetrievalControls() {
    return (
      <div className="flex flex-wrap gap-3 text-sm text-muted">
        <Toggle label="BM25" checked={useBm25} onChange={setUseBm25} />
        <Toggle label="Vector" checked={useVector} onChange={setUseVector} />
        <Toggle label="Graph" checked={useGraph} onChange={setUseGraph} />
      </div>
    );
  }

  function renderSearchPanel() {
    return (
      <section>
        <form className="grid gap-3 lg:grid-cols-[1fr_120px_auto]" onSubmit={handleRetrieve}>
          <input
            className="min-h-10 rounded-md border border-line bg-white px-3 py-2 text-sm outline-none focus:border-ink disabled:bg-surface"
            disabled={!selectedRepository || retrievalState === "running"}
            placeholder="RepositoryApplicationService"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
          <NumberInput disabled={retrievalState === "running"} value={topK} onChange={setTopK} />
          <RunButton disabled={!isReady || retrievalState === "running"}>
            {retrievalState === "running" ? "Searching" : "Search"}
          </RunButton>
        </form>

        <div className="mt-3">{renderSharedRetrievalControls()}</div>
        {retrievalError ? <Alert tone="red" message={retrievalError} /> : null}
        {retrievalResult?.debug.vector_disabled_reason ? (
          <Alert tone="amber" message={retrievalResult.debug.vector_disabled_reason} />
        ) : null}

        {retrievalResult ? <RetrievalDebug result={retrievalResult} /> : null}
        <EvidenceList evidences={retrievalResult?.evidences ?? []} empty={retrievalState === "empty"} />
      </section>
    );
  }

  function renderAskPanel() {
    return (
      <section className="grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
        <form className="flex flex-col gap-3" onSubmit={handleAsk}>
          <textarea
            className="min-h-36 rounded-md border border-line bg-white px-3 py-2 text-sm outline-none focus:border-ink disabled:bg-surface"
            disabled={!selectedRepository || qaState === "running"}
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
          />
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            {renderSharedRetrievalControls()}
            <RunButton disabled={!isReady || qaState === "running"}>
              {qaState === "running" ? "Asking" : "Ask"}
            </RunButton>
          </div>
          {qaError ? <Alert tone="red" message={qaError} /> : null}
        </form>

        <section className="min-w-0">
          {qaResult ? (
            <div className="flex flex-col gap-3">
              <ResultHeader title="Answer" status={qaResult.status} detail={confidenceText(qaResult)} />
              <div className="rounded-md border border-line bg-surface p-3 text-sm leading-6">
                {qaResult.answer ?? "-"}
              </div>
              <CitationList citations={qaResult.citations} />
              <TraceList traces={qaResult.traces} />
            </div>
          ) : (
            <EmptyState label="No answer yet" />
          )}
        </section>
      </section>
    );
  }

  function renderReviewPanel() {
    return (
      <section className="grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
        <form className="flex flex-col gap-3" onSubmit={handleReview}>
          <textarea
            className="min-h-80 rounded-md border border-line bg-white px-3 py-2 font-mono text-xs leading-5 outline-none focus:border-ink disabled:bg-surface"
            disabled={!selectedRepository || reviewState === "running"}
            value={diffText}
            onChange={(event) => setDiffText(event.target.value)}
          />
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            {renderSharedRetrievalControls()}
            <RunButton disabled={!isReady || reviewState === "running"}>
              {reviewState === "running" ? "Reviewing" : "Review"}
            </RunButton>
          </div>
          {reviewError ? <Alert tone="red" message={reviewError} /> : null}
        </form>

        <section className="min-w-0">
          {reviewResult ? (
            <div className="flex flex-col gap-3">
              <ResultHeader
                title="Review"
                status={reviewResult.status}
                detail={`risk ${reviewResult.risk_level ?? "-"}`}
              />
              <div className="rounded-md border border-line bg-surface p-3 text-sm leading-6">
                {reviewResult.summary ?? "-"}
              </div>
              <RiskList risks={reviewResult.risks} />
              <SuggestedTestList tests={reviewResult.suggested_tests} />
              <ReviewCitationList citations={reviewResult.citations} />
              <ToolCallList calls={reviewResult.tool_calls} />
              <TraceList traces={reviewResult.traces} />
            </div>
          ) : (
            <EmptyState label="No review yet" />
          )}
        </section>
      </section>
    );
  }

  function renderMcpPanel() {
    return (
      <section className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
        <div className="flex flex-col gap-3">
          <div className="flex flex-wrap gap-2">
            <button
              className="rounded-md border border-line px-3 py-2 text-sm font-medium text-ink"
              onClick={() => void loadMcpData()}
              type="button"
            >
              Refresh
            </button>
            <RunButton disabled={!isReady || mcpState === "running"} onClick={() => void handleMcpSearch()}>
              {mcpState === "running" ? "Calling" : "Call Search Tool"}
            </RunButton>
          </div>
          {mcpError ? <Alert tone="red" message={mcpError} /> : null}
          <ToolRegistry tools={mcpTools} />
          {mcpCallResult ? (
            <div className="rounded-md border border-line bg-surface p-3 text-sm">
              <div className="font-semibold">{mcpCallResult.tool_name}</div>
              <div className="mt-1 text-muted">
                {mcpCallResult.status} / {mcpCallResult.permission_decision}
              </div>
              {mcpCallResult.error_message ? (
                <div className="mt-2 text-red-700">{mcpCallResult.error_message}</div>
              ) : null}
            </div>
          ) : null}
        </div>
        <AuditList audits={mcpAudits} />
      </section>
    );
  }

  function renderEvaluationPanel() {
    return (
      <section className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
        <form className="flex flex-col gap-3" onSubmit={handleEvaluation}>
          <input
            className="rounded-md border border-line bg-white px-3 py-2 text-sm outline-none focus:border-ink"
            value={evaluationName}
            onChange={(event) => setEvaluationName(event.target.value)}
          />
          <input
            className="rounded-md border border-line bg-white px-3 py-2 text-sm outline-none focus:border-ink"
            value={evaluationDataset}
            onChange={(event) => setEvaluationDataset(event.target.value)}
          />
          <select
            className="rounded-md border border-line bg-white px-3 py-2 text-sm outline-none focus:border-ink"
            value={evaluationStrategy}
            onChange={(event) => setEvaluationStrategy(event.target.value as EvaluationStrategy)}
          >
            <option value="all">all</option>
            <option value="vector_only">vector_only</option>
            <option value="bm25_vector">bm25_vector</option>
            <option value="bm25_vector_graph">bm25_vector_graph</option>
          </select>
          <RunButton disabled={!isReady || evaluationState === "running"}>
            {evaluationState === "running" ? "Running" : "Run Evaluation"}
          </RunButton>
          {evaluationError ? <Alert tone="red" message={evaluationError} /> : null}
        </form>

        <div className="flex min-w-0 flex-col gap-3">
          {evaluationResult ? <EvaluationResultPanel run={evaluationResult} /> : <EmptyState label="No evaluation yet" />}
          <EvaluationRunList runs={evaluationRuns} />
        </div>
      </section>
    );
  }
}

function RepositoryImportForm({
  branch,
  isSubmitting,
  selectedRepository,
  source,
  onBranchChange,
  onSourceChange,
  onSubmit
}: {
  branch: string;
  isSubmitting: boolean;
  selectedRepository: RepositoryDetail | null;
  source: string;
  onBranchChange: (value: string) => void;
  onSourceChange: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
}) {
  return (
    <form className="rounded-md border border-line bg-white p-4" onSubmit={onSubmit}>
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-base font-semibold">Repository</h2>
        <StatusBadge status={selectedRepository?.status ?? "pending"} />
      </div>

      <label className="mt-4 block text-xs font-medium uppercase text-muted" htmlFor="source">
        Local path
      </label>
      <input
        id="source"
        className="mt-2 w-full rounded-md border border-line bg-white px-3 py-2 text-sm outline-none focus:border-ink"
        placeholder="F:\\Desktop\\agent\\RepoLens\\backend-java"
        value={source}
        onChange={(event) => onSourceChange(event.target.value)}
      />

      <label className="mt-3 block text-xs font-medium uppercase text-muted" htmlFor="branch">
        Branch
      </label>
      <input
        id="branch"
        className="mt-2 w-full rounded-md border border-line bg-white px-3 py-2 text-sm outline-none focus:border-ink"
        placeholder="main"
        value={branch}
        onChange={(event) => onBranchChange(event.target.value)}
      />

      <button
        className="mt-4 w-full rounded-md bg-ink px-3 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:bg-muted"
        disabled={isSubmitting}
        type="submit"
      >
        {isSubmitting ? "Importing" : "Import"}
      </button>
    </form>
  );
}

function RepositoryOverview({
  metrics,
  repository,
  status
}: {
  metrics: Array<{ key: string; label: string; value: number }>;
  repository: RepositoryDetail | null;
  status: RepositoryStatusResponse | null;
}) {
  return (
    <>
      <section className="rounded-md border border-line bg-white p-4">
        <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div className="min-w-0">
            <h2 className="truncate text-lg font-semibold">{repository?.name ?? "No repository selected"}</h2>
            <p className="mt-1 break-all text-sm text-muted">{repository?.local_path ?? "-"}</p>
          </div>
          <StatusBadge status={repository?.status ?? "pending"} />
        </div>

        <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
          {metrics.map((metric) => (
            <Metric key={metric.key} label={metric.label} value={metric.value} />
          ))}
        </div>
      </section>

      <section className="grid min-w-0 gap-4 xl:grid-cols-[0.85fr_1.15fr]">
        <section className="rounded-md border border-line bg-white p-4">
          <h2 className="text-base font-semibold">Languages</h2>
          <div className="mt-4 flex flex-col gap-3">
            {repository && Object.keys(repository.language_summary).length > 0 ? (
              Object.entries(repository.language_summary).map(([language, count]) => (
                <LanguageRow key={language} count={count} language={language} />
              ))
            ) : (
              <EmptyState label="No language data" />
            )}
          </div>
        </section>

        <section className="rounded-md border border-line bg-white p-4">
          <h2 className="text-base font-semibold">Index Status</h2>
          <div className="mt-4 grid gap-x-6 gap-y-3 md:grid-cols-2">
            <InfoItem label="Current step" value={status?.progress.current_step ?? "-"} />
            <InfoItem label="Source type" value={repository?.source_type ?? "-"} />
            <InfoItem label="Branch" value={repository?.branch ?? "-"} />
            <InfoItem label="Commit" value={repository?.commit_hash?.slice(0, 12) ?? "-"} />
            <InfoItem label="Updated" value={formatDate(repository?.updated_at)} />
            <InfoItem label="Indexed" value={formatDate(repository?.indexed_at)} />
          </div>
          {repository?.error_message || status?.error_message ? (
            <Alert tone="red" message={repository?.error_message ?? status?.error_message ?? ""} />
          ) : null}
        </section>
      </section>
    </>
  );
}

function RepositoryListItem({
  active,
  repository,
  onSelect
}: {
  active: boolean;
  repository: RepositorySummary;
  onSelect: () => void;
}) {
  return (
    <button
      className={`rounded-md border px-3 py-3 text-left ${
        active ? "border-ink bg-surface" : "border-line bg-white"
      }`}
      onClick={onSelect}
      type="button"
    >
      <div className="flex items-center justify-between gap-3">
        <div className="min-w-0 truncate text-sm font-medium">{repository.name}</div>
        <StatusBadge status={repository.status} />
      </div>
      <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-xs text-muted">
        <span>{repository.file_count} files</span>
        <span>{repository.chunk_count} chunks</span>
        <span>{repository.relation_count} relations</span>
      </div>
    </button>
  );
}

function StatusBadge({ status }: { status: RepositoryStatus }) {
  const className =
    status === "ready"
      ? "border-emerald-200 bg-emerald-50 text-emerald-700"
      : status === "failed"
        ? "border-red-200 bg-red-50 text-red-700"
        : status === "indexing"
          ? "border-sky-200 bg-sky-50 text-sky-700"
          : "border-blue-200 bg-blue-50 text-blue-700";

  return <span className={`shrink-0 rounded-md border px-2 py-1 text-xs font-medium ${className}`}>{status}</span>;
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md border border-line bg-surface p-3">
      <div className="text-xs uppercase text-muted">{label}</div>
      <div className="mt-2 text-xl font-semibold">{formatNumber(value)}</div>
    </div>
  );
}

function LanguageRow({ language, count }: { language: string; count: number }) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-line pb-2 last:border-b-0 last:pb-0">
      <span className="text-sm font-medium">{language}</span>
      <span className="text-sm text-muted">{count}</span>
    </div>
  );
}

function InfoItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0 border-b border-line pb-2">
      <div className="text-xs uppercase text-muted">{label}</div>
      <div className="mt-1 truncate text-sm font-medium">{value}</div>
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

function NumberInput({
  disabled,
  value,
  onChange
}: {
  disabled?: boolean;
  value: number;
  onChange: (value: number) => void;
}) {
  return (
    <input
      className="min-h-10 rounded-md border border-line bg-white px-3 py-2 text-sm outline-none focus:border-ink disabled:bg-surface"
      disabled={disabled}
      max={20}
      min={1}
      type="number"
      value={value}
      onChange={(event) => onChange(Number(event.target.value))}
    />
  );
}

function RunButton({
  children,
  disabled,
  onClick
}: {
  children: ReactNode;
  disabled?: boolean;
  onClick?: () => void;
}) {
  return (
    <button
      className="min-h-10 rounded-md bg-ink px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:bg-muted"
      disabled={disabled}
      onClick={onClick}
      type={onClick ? "button" : "submit"}
    >
      {children}
    </button>
  );
}

function RetrievalDebug({ result }: { result: RetrievalResponse }) {
  return (
    <div className="mt-4 grid grid-cols-3 gap-2 text-xs text-muted sm:grid-cols-5">
      <DebugMetric label="BM25" value={result.debug.bm25_count} />
      <DebugMetric label="Vector" value={result.debug.vector_count} />
      <DebugMetric label="Graph" value={result.debug.graph_count} />
      <DebugMetric label="Merged" value={result.debug.merged_count} />
      <DebugMetric label="Evidence" value={result.debug.evidence_count} />
    </div>
  );
}

function DebugMetric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md border border-line bg-surface p-2 text-right">
      <div className="uppercase">{label}</div>
      <div className="text-sm font-semibold text-ink">{value}</div>
    </div>
  );
}

function EvidenceList({ evidences, empty }: { evidences: EvidenceItem[]; empty: boolean }) {
  return (
    <div className="mt-4 flex flex-col gap-3">
      {empty ? <EmptyState label="No evidence" /> : null}
      {evidences.map((evidence) => (
        <EvidenceCard key={evidence.evidence_id} evidence={evidence} />
      ))}
    </div>
  );
}

function EvidenceCard({ evidence }: { evidence: EvidenceItem }) {
  const route = routePath(evidence.metadata);
  const annotations = stringListValue(evidence.metadata.annotations);

  return (
    <article className="rounded-md border border-line bg-surface p-3">
      <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
        <div className="min-w-0">
          <div className="break-all text-sm font-semibold">
            {evidence.file_path}:{evidence.start_line}-{evidence.end_line}
          </div>
          <div className="mt-1 break-words text-sm text-muted">{evidence.symbol_name}</div>
        </div>
        <div className="flex flex-wrap gap-2 md:justify-end">
          <SourcePill value={evidence.source} />
          <SourcePill value={formatScore(evidence.score)} />
          <SourcePill value={`BM25 ${formatScore(evidence.bm25_score)}`} />
        </div>
      </div>

      {route || annotations.length ? (
        <div className="mt-3 flex flex-wrap gap-2">
          {route ? <SourcePill value={route} /> : null}
          {annotations.map((annotation) => (
            <SourcePill key={annotation} value={`@${annotation}`} />
          ))}
        </div>
      ) : null}

      <pre className="mt-3 max-h-80 overflow-auto whitespace-pre-wrap break-words rounded-md border border-line bg-white p-3 text-xs leading-5 text-ink">
        {evidence.snippet}
      </pre>
    </article>
  );
}

function ResultHeader({ title, status, detail }: { title: string; status: string; detail?: string }) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line pb-2">
      <h3 className="text-sm font-semibold">{title}</h3>
      <div className="text-xs text-muted">
        {status}
        {detail ? ` / ${detail}` : ""}
      </div>
    </div>
  );
}

function CitationList({ citations }: { citations: QACitation[] }) {
  if (!citations.length) {
    return <EmptyState label="No citations" />;
  }
  return (
    <div className="flex flex-col gap-2">
      {citations.map((citation) => (
        <div key={citation.evidence_id} className="rounded-md border border-line bg-white p-3 text-sm">
          <div className="break-all font-medium">
            {citation.file_path}:{citation.start_line}-{citation.end_line}
          </div>
          <div className="mt-1 text-muted">{citation.symbol_name}</div>
        </div>
      ))}
    </div>
  );
}

function TraceList({ traces }: { traces: AgentTrace[] }) {
  if (!traces.length) {
    return <EmptyState label="No trace" />;
  }
  return (
    <div className="flex flex-col gap-2">
      {traces.map((trace) => (
        <div key={trace.id} className="rounded-md border border-line bg-white p-3 text-sm">
          <div className="flex items-center justify-between gap-3">
            <span className="font-medium">{trace.step_name}</span>
            <span className="text-xs text-muted">{trace.status}</span>
          </div>
          <div className="mt-1 text-muted">{trace.output_summary ?? trace.input_summary}</div>
        </div>
      ))}
    </div>
  );
}

function RiskList({ risks }: { risks: ReviewRisk[] }) {
  if (!risks.length) {
    return <EmptyState label="No risks" />;
  }
  return (
    <div className="flex flex-col gap-2">
      {risks.map((risk, index) => (
        <div key={`${risk.title ?? "risk"}-${index}`} className="rounded-md border border-line bg-white p-3 text-sm">
          <div className="font-medium">
            [{stringValue(risk.severity)}] {stringValue(risk.title)}
          </div>
          <div className="mt-1 text-muted">{stringValue(risk.reason)}</div>
          {risk.location ? (
            <div className="mt-1 break-all text-xs text-muted">
              {risk.location.file_path}:{risk.location.start_line}-{risk.location.end_line}
            </div>
          ) : null}
        </div>
      ))}
    </div>
  );
}

function SuggestedTestList({ tests }: { tests: ReviewSuggestedTest[] }) {
  if (!tests.length) {
    return <EmptyState label="No suggested tests" />;
  }
  return (
    <div className="flex flex-col gap-2">
      {tests.map((test, index) => (
        <div key={`${test.target ?? "test"}-${index}`} className="rounded-md border border-line bg-white p-3 text-sm">
          <div className="font-medium">{stringValue(test.test_type)} / {stringValue(test.target)}</div>
          <div className="mt-1 text-muted">{stringValue(test.reason)}</div>
        </div>
      ))}
    </div>
  );
}

function ReviewCitationList({ citations }: { citations: ReviewCitation[] }) {
  if (!citations.length) {
    return <EmptyState label="No review citations" />;
  }
  return (
    <div className="flex flex-col gap-2">
      {citations.slice(0, 5).map((citation, index) => (
        <div key={`${citation.evidence_id ?? "citation"}-${index}`} className="rounded-md border border-line bg-white p-3 text-sm">
          <div className="break-all font-medium">
            {stringValue(citation.file_path)}:{numberValue(citation.start_line)}-{numberValue(citation.end_line)}
          </div>
          <div className="mt-1 text-muted">{stringValue(citation.symbol_name)}</div>
        </div>
      ))}
    </div>
  );
}

function ToolCallList({ calls }: { calls: ReviewToolCall[] }) {
  if (!calls.length) {
    return <EmptyState label="No tool calls" />;
  }
  return (
    <div className="flex flex-col gap-2">
      {calls.map((call) => (
        <div key={call.id} className="rounded-md border border-line bg-white p-3 text-sm">
          <div className="flex items-center justify-between gap-3">
            <span className="font-medium">{call.tool_name}</span>
            <span className="text-xs text-muted">{call.status} / {call.permission_decision}</span>
          </div>
          <div className="mt-1 text-muted">{call.output_summary ?? call.input_summary}</div>
        </div>
      ))}
    </div>
  );
}

function ToolRegistry({ tools }: { tools: McpToolInfo[] }) {
  if (!tools.length) {
    return <EmptyState label="No tools" />;
  }
  return (
    <div className="flex flex-col gap-2">
      {tools.map((tool) => (
        <div key={tool.name} className="rounded-md border border-line bg-white p-3 text-sm">
          <div className="flex items-center justify-between gap-3">
            <span className="font-medium">{tool.name}</span>
            <span className="text-xs text-muted">{tool.enabled ? "enabled" : "disabled"}</span>
          </div>
          <div className="mt-1 text-muted">{tool.description}</div>
          <div className="mt-1 text-xs text-muted">{tool.permission_policy}</div>
        </div>
      ))}
    </div>
  );
}

function AuditList({ audits }: { audits: McpToolCallAudit[] }) {
  if (!audits.length) {
    return <EmptyState label="No audit records" />;
  }
  return (
    <div className="flex max-h-[560px] flex-col gap-2 overflow-auto">
      {audits.map((audit) => (
        <div key={audit.id} className="rounded-md border border-line bg-white p-3 text-sm">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span className="font-medium">{audit.tool_name}</span>
            <span className="text-xs text-muted">{audit.status} / {audit.permission_decision}</span>
          </div>
          <div className="mt-1 break-all text-xs text-muted">
            in {audit.input_hash ?? "-"} / out {audit.output_hash ?? "-"}
          </div>
          <div className="mt-1 text-xs text-muted">{audit.latency_ms ?? 0} ms</div>
        </div>
      ))}
    </div>
  );
}

function EvaluationResultPanel({ run }: { run: EvaluationRunResponse }) {
  return (
    <div className="flex flex-col gap-3">
      <ResultHeader title={run.name} status={run.status} detail={`${run.sample_count} samples`} />
      <div className="overflow-auto rounded-md border border-line">
        <table className="w-full min-w-[720px] border-collapse text-sm">
          <thead className="bg-surface text-left text-xs uppercase text-muted">
            <tr>
              <th className="border-b border-line px-3 py-2">Strategy</th>
              <th className="border-b border-line px-3 py-2">Hit@5</th>
              <th className="border-b border-line px-3 py-2">MRR</th>
              <th className="border-b border-line px-3 py-2">Coverage</th>
              <th className="border-b border-line px-3 py-2">Avg latency</th>
              <th className="border-b border-line px-3 py-2">Errors</th>
            </tr>
          </thead>
          <tbody>
            {run.metrics.map((metric) => (
              <tr key={metric.strategy}>
                <td className="border-b border-line px-3 py-2 font-medium">{metric.strategy}</td>
                <td className="border-b border-line px-3 py-2">{formatPercent(metric.hit_at_5)}</td>
                <td className="border-b border-line px-3 py-2">{formatScore(metric.mrr)}</td>
                <td className="border-b border-line px-3 py-2">{formatPercent(metric.citation_coverage)}</td>
                <td className="border-b border-line px-3 py-2">{metric.avg_latency_ms.toFixed(1)} ms</td>
                <td className="border-b border-line px-3 py-2">{metric.error_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="flex flex-col gap-2">
        {run.results.slice(0, 6).map((result) => (
          <div key={result.id} className="rounded-md border border-line bg-white p-3 text-sm">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className="font-medium">{result.sample_id}</span>
              <span className="text-xs text-muted">{result.strategy} / {result.hit_at_5 ? "hit" : "miss"}</span>
            </div>
            <div className="mt-1 break-all text-xs text-muted">{result.matched_files.join(", ") || "-"}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function EvaluationRunList({ runs }: { runs: EvaluationRunSummary[] }) {
  if (!runs.length) {
    return <EmptyState label="No previous runs" />;
  }
  return (
    <div className="flex flex-col gap-2">
      {runs.slice(0, 5).map((run) => (
        <div key={run.run_id} className="rounded-md border border-line bg-white p-3 text-sm">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span className="font-medium">{run.name}</span>
            <span className="text-xs text-muted">{run.status}</span>
          </div>
          <div className="mt-1 text-xs text-muted">{formatDate(run.completed_at ?? run.created_at)}</div>
        </div>
      ))}
    </div>
  );
}

function SourcePill({ value }: { value: string }) {
  return (
    <span className="max-w-full break-all rounded-md border border-line bg-white px-2 py-1 text-xs font-medium text-ink">
      {value}
    </span>
  );
}

function EmptyState({ label }: { label: string }) {
  return (
    <div className="rounded-md border border-dashed border-line px-3 py-6 text-center text-sm text-muted">
      {label}
    </div>
  );
}

function Alert({ message, tone }: { message: string; tone: "red" | "amber" }) {
  const className =
    tone === "red"
      ? "border-red-200 bg-red-50 text-red-800"
      : "border-amber-200 bg-amber-50 text-amber-800";
  return <div className={`mt-4 rounded-md border px-3 py-2 text-sm ${className}`}>{message}</div>;
}

function routePath(metadata: Record<string, unknown>): string | null {
  const route = metadata.route;
  if (typeof route === "string" && route.trim()) {
    return route;
  }
  if (route && typeof route === "object" && "path" in route) {
    const path = (route as { path?: unknown }).path;
    return typeof path === "string" && path.trim() ? path : null;
  }
  return null;
}

function stringListValue(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter((item): item is string => typeof item === "string" && item.trim().length > 0);
}

function stringValue(value: unknown): string {
  return typeof value === "string" && value.trim() ? value : "-";
}

function numberValue(value: unknown): number {
  return typeof value === "number" ? value : 0;
}

function confidenceText(result: QATaskResponse): string {
  return result.confidence == null ? "confidence -" : `confidence ${formatPercent(result.confidence)}`;
}

function formatDate(value: string | null | undefined): string {
  if (!value) {
    return "-";
  }
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat("en-US").format(value);
}

function formatScore(value: number): string {
  return value.toFixed(3);
}

function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}
