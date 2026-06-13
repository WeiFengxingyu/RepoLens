export async function runEvaluation(input: { strategy: string }) {
  const response = await fetch("/api/evaluations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  return response.json();
}
