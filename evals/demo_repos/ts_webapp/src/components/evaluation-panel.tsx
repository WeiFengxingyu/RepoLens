import { useEvaluation } from "@/hooks/use-evaluation";


export function EvaluationPanel() {
  const { result, loading, error, run } = useEvaluation();

  return (
    <section>
      <h2>Evaluation</h2>
      <button type="button" disabled={loading} onClick={() => run({ strategy: "bm25_vector_graph" })}>
        Run evaluation
      </button>
      {error ? <p>{error}</p> : null}
      {result ? <pre>{JSON.stringify(result.metrics, null, 2)}</pre> : null}
    </section>
  );
}
