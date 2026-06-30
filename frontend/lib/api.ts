import type {
  ChangeRequestReviewCreateRequest,
  ChangeRequestReviewResponse,
  AuditLogResponse,
  EvaluationCreateRequest,
  EvaluationRunResponse,
  EvaluationRunSummary,
  JobResponse,
  McpToolCallAudit,
  McpToolCallRequest,
  McpToolCallResponse,
  McpToolInfo,
  MultiAgentReviewCreateRequest,
  MultiAgentReviewResponse,
  OrganizationCreateRequest,
  OrganizationResponse,
  QACreateRequest,
  QATaskResponse,
  ProjectCreateRequest,
  ProjectResponse,
  QuotaBucketResponse,
  RepositoryBindingCreateRequest,
  RepositoryBindingResponse,
  ReviewCreateRequest,
  ReviewRulesetCreateRequest,
  ReviewRulesetResponse,
  ReviewTaskResponse,
  RepositoryDetail,
  RepositoryImportRequest,
  RepositoryStatusResponse,
  RepositorySummary,
  RetrievalRequest,
  RetrievalResponse,
  WebhookJobResponse,
  WebhookReviewRequest,
  WorkerResponse,
  V1BenchmarkCreateRequest,
  V1BenchmarkResponse
} from "@/types/workbench";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8080";

export const API_ROUTES = {
  health: "/health",
  status: "/api/status",
  repositories: "/api/repositories"
} as const;

export async function listRepositories(): Promise<RepositorySummary[]> {
  return request<RepositorySummary[]>(API_ROUTES.repositories);
}

export async function importRepository(
  payload: RepositoryImportRequest
): Promise<RepositoryDetail> {
  return request<RepositoryDetail>(API_ROUTES.repositories, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function getRepository(repositoryId: string): Promise<RepositoryDetail> {
  return request<RepositoryDetail>(`${API_ROUTES.repositories}/${repositoryId}`);
}

export async function getRepositoryStatus(
  repositoryId: string
): Promise<RepositoryStatusResponse> {
  return request<RepositoryStatusResponse>(
    `${API_ROUTES.repositories}/${repositoryId}/status`
  );
}

export async function retrieveRepository(
  repositoryId: string,
  payload: RetrievalRequest
): Promise<RetrievalResponse> {
  return request<RetrievalResponse>(`${API_ROUTES.repositories}/${repositoryId}/retrieve`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function askRepositoryQuestion(
  repositoryId: string,
  payload: QACreateRequest
): Promise<QATaskResponse> {
  return request<QATaskResponse>(`${API_ROUTES.repositories}/${repositoryId}/questions`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function createReview(
  repositoryId: string,
  payload: ReviewCreateRequest
): Promise<ReviewTaskResponse> {
  return request<ReviewTaskResponse>(`${API_ROUTES.repositories}/${repositoryId}/reviews`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function createChangeRequestReview(
  repositoryId: string,
  payload: ChangeRequestReviewCreateRequest
): Promise<ChangeRequestReviewResponse> {
  return request<ChangeRequestReviewResponse>(
    `${API_ROUTES.repositories}/${repositoryId}/change-requests/reviews`,
    {
      method: "POST",
      body: JSON.stringify(payload)
    }
  );
}

export async function createMultiAgentReview(
  repositoryId: string,
  payload: MultiAgentReviewCreateRequest
): Promise<MultiAgentReviewResponse> {
  return request<MultiAgentReviewResponse>(
    `${API_ROUTES.repositories}/${repositoryId}/multi-agent-reviews`,
    {
      method: "POST",
      body: JSON.stringify(payload)
    }
  );
}

export async function getReview(taskId: string): Promise<ReviewTaskResponse> {
  return request<ReviewTaskResponse>(`/api/reviews/${taskId}`);
}

export async function getMultiAgentReview(taskId: string): Promise<MultiAgentReviewResponse> {
  return request<MultiAgentReviewResponse>(`/api/multi-agent-reviews/${taskId}`);
}

export async function createEvaluation(
  payload: EvaluationCreateRequest
): Promise<EvaluationRunResponse> {
  return request<EvaluationRunResponse>("/api/evaluations", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function listEvaluations(): Promise<EvaluationRunSummary[]> {
  return request<EvaluationRunSummary[]>("/api/evaluations");
}

export async function getEvaluation(runId: string): Promise<EvaluationRunResponse> {
  return request<EvaluationRunResponse>(`/api/evaluations/${runId}`);
}

export async function createV1Benchmark(
  payload: V1BenchmarkCreateRequest
): Promise<V1BenchmarkResponse> {
  return request<V1BenchmarkResponse>("/api/v1-benchmarks", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function listMcpTools(): Promise<McpToolInfo[]> {
  return request<McpToolInfo[]>("/api/mcp/tools");
}

export async function listMcpToolCalls(limit = 50): Promise<McpToolCallAudit[]> {
  return request<McpToolCallAudit[]>(`/api/mcp/tool-calls?limit=${limit}`);
}

export async function callMcpTool(
  payload: McpToolCallRequest
): Promise<McpToolCallResponse> {
  return request<McpToolCallResponse>("/api/mcp/tools/call", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function createOrganization(
  payload: OrganizationCreateRequest
): Promise<OrganizationResponse> {
  return request<OrganizationResponse>("/api/organizations", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function listOrganizations(limit = 20): Promise<OrganizationResponse[]> {
  return request<OrganizationResponse[]>(`/api/organizations?limit=${limit}`);
}

export async function createProject(
  organizationId: string,
  payload: ProjectCreateRequest
): Promise<ProjectResponse> {
  return request<ProjectResponse>(`/api/organizations/${organizationId}/projects`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function listProjects(organizationId: string): Promise<ProjectResponse[]> {
  return request<ProjectResponse[]>(`/api/organizations/${organizationId}/projects`);
}

export async function bindRepositoryToProject(
  projectId: string,
  repositoryId: string,
  payload: RepositoryBindingCreateRequest
): Promise<RepositoryBindingResponse> {
  return request<RepositoryBindingResponse>(
    `/api/projects/${projectId}/repositories/${repositoryId}/bind`,
    {
      method: "POST",
      body: JSON.stringify(payload)
    }
  );
}

export async function listProjectBindings(
  projectId: string
): Promise<RepositoryBindingResponse[]> {
  return request<RepositoryBindingResponse[]>(`/api/projects/${projectId}/repositories`);
}

export async function createReviewRuleset(
  projectId: string,
  payload: ReviewRulesetCreateRequest
): Promise<ReviewRulesetResponse> {
  return request<ReviewRulesetResponse>(`/api/projects/${projectId}/rulesets`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function listReviewRulesets(
  projectId: string
): Promise<ReviewRulesetResponse[]> {
  return request<ReviewRulesetResponse[]>(`/api/projects/${projectId}/rulesets`);
}

export async function listProjectQuota(projectId: string): Promise<QuotaBucketResponse[]> {
  return request<QuotaBucketResponse[]>(`/api/projects/${projectId}/quota`);
}

export async function listAuditLogs(limit = 50): Promise<AuditLogResponse[]> {
  return request<AuditLogResponse[]>(`/api/audit-logs?limit=${limit}`);
}

export async function triggerWebhookReview(
  provider: string,
  payload: WebhookReviewRequest
): Promise<WebhookJobResponse> {
  return request<WebhookJobResponse>(`/api/webhooks/${provider}`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function listJobs(limit = 30): Promise<JobResponse[]> {
  return request<JobResponse[]>(`/api/jobs?limit=${limit}`);
}

export async function getJob(jobId: string): Promise<JobResponse> {
  return request<JobResponse>(`/api/jobs/${jobId}`);
}

export async function listWorkers(): Promise<WorkerResponse[]> {
  return request<WorkerResponse[]>("/api/workers");
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    }
  });

  if (!response.ok) {
    const message = await readErrorMessage(response);
    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

async function readErrorMessage(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: unknown; message?: unknown };
    return normalizeErrorBody(body, response.status);
  } catch {
    return `Request failed with ${response.status}`;
  }
}

function normalizeErrorBody(
  body: { detail?: unknown; message?: unknown },
  status: number
): string {
  if (typeof body.message === "string" && body.message.trim()) {
    return redactSensitiveText(body.message);
  }
  return normalizeErrorDetail(body.detail, status);
}

function normalizeErrorDetail(detail: unknown, status: number): string {
  if (typeof detail === "string" && detail.trim()) {
    return redactSensitiveText(detail);
  }
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (typeof item === "string") {
          return item;
        }
        if (item && typeof item === "object" && "msg" in item) {
          const message = (item as { msg?: unknown }).msg;
          return typeof message === "string" ? message : "";
        }
        return "";
      })
      .filter(Boolean);
    if (messages.length) {
      return redactSensitiveText(messages.join("; "));
    }
  }
  return `Request failed with ${status}`;
}

function redactSensitiveText(value: string): string {
  return value
    .replace(/authorization\s*[:=]\s*bearer\s+[^\s,;]+/gi, "Authorization: Bearer [redacted]")
    .replace(/bearer\s+[^\s,;]+/gi, "Bearer [redacted]");
}
