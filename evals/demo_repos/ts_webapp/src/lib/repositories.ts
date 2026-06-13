export type RepositorySummary = {
  id: string;
  name: string;
  status: string;
};


export async function fetchRepositories(): Promise<RepositorySummary[]> {
  const response = await fetch("/api/repositories");
  if (!response.ok) return [];
  return response.json();
}


export async function importRepository(source: string): Promise<RepositorySummary> {
  const response = await fetch("/api/repositories", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ source }),
  });
  return response.json();
}
