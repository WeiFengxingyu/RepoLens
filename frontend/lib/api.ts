import type {
  EvaluationCreateRequest,
  EvaluationRunResponse,
  EvaluationRunSummary,
  QACreateRequest,
  QATaskResponse,
  ReviewCreateRequest,
  ReviewTaskResponse,
  RepositoryDetail,
  RepositoryImportRequest,
  RepositoryStatusResponse,
  RepositorySummary,
  RetrievalRequest,
  RetrievalResponse
} from "@/types/workbench";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

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

export async function getReview(taskId: string): Promise<ReviewTaskResponse> {
  return request<ReviewTaskResponse>(`/api/reviews/${taskId}`);
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
    const body = (await response.json()) as { detail?: string };
    return body.detail ?? `Request failed with ${response.status}`;
  } catch {
    return `Request failed with ${response.status}`;
  }
}
