export async function readApiError(response: Response): Promise<string> {
  try {
    const body = await response.json();
    return body.detail ?? `Request failed with ${response.status}`;
  } catch {
    return `Request failed with ${response.status}`;
  }
}


export function readError(error: unknown): string {
  return error instanceof Error ? error.message : "Unexpected error";
}
