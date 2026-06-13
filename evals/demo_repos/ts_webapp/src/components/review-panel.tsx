import { useState } from "react";

import { createReview } from "@/lib/reviews";


export function ReviewPanel() {
  const [diff, setDiff] = useState("");
  const [status, setStatus] = useState("idle");

  async function submitReview() {
    if (!diff.trim()) return;
    setStatus("loading");
    await createReview({ diff });
    setStatus("submitted");
  }

  return (
    <section>
      <h2>Review</h2>
      <textarea value={diff} onChange={(event) => setDiff(event.target.value)} />
      <button type="button" disabled={!diff.trim() || status === "loading"} onClick={submitReview}>
        Run review
      </button>
    </section>
  );
}
