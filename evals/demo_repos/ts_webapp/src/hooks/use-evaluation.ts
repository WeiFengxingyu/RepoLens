import { useState } from "react";

import { runEvaluation } from "@/lib/evaluations";
import { readError } from "@/lib/api-errors";


type EvaluationInput = {
  strategy: string;
};


export function useEvaluation() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<{ metrics: unknown } | null>(null);

  async function run(input: EvaluationInput) {
    setLoading(true);
    setError("");
    try {
      const response = await runEvaluation(input);
      setResult(response);
      setLoading(false);
    } catch (error) {
      setError(readError(error));
      setLoading(false);
    }
  }

  return { result, loading, error, run };
}
