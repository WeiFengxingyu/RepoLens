export async function createReview(input: { diff: string }) {
  const response = await fetch("/api/reviews", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  return response.json();
}
