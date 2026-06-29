package com.repolens.evaluation.application;

import java.util.List;
import java.util.Locale;

public enum EvaluationStrategy {
    VECTOR_ONLY("vector_only", false, true, false),
    BM25_VECTOR("bm25_vector", true, true, false),
    BM25_VECTOR_GRAPH("bm25_vector_graph", true, true, true);

    private final String value;
    private final boolean useBm25;
    private final boolean useVector;
    private final boolean useGraph;

    EvaluationStrategy(String value, boolean useBm25, boolean useVector, boolean useGraph) {
        this.value = value;
        this.useBm25 = useBm25;
        this.useVector = useVector;
        this.useGraph = useGraph;
    }

    public String value() {
        return value;
    }

    public boolean useBm25() {
        return useBm25;
    }

    public boolean useVector() {
        return useVector;
    }

    public boolean useGraph() {
        return useGraph;
    }

    public static List<EvaluationStrategy> expand(String raw) {
        String normalized = raw == null ? "all" : raw.trim().toLowerCase(Locale.ROOT);
        if (normalized.isBlank() || "all".equals(normalized)) {
            return List.of(VECTOR_ONLY, BM25_VECTOR, BM25_VECTOR_GRAPH);
        }
        for (EvaluationStrategy strategy : values()) {
            if (strategy.value.equals(normalized)) {
                return List.of(strategy);
            }
        }
        throw new IllegalArgumentException("Unsupported evaluation strategy: " + raw);
    }
}
