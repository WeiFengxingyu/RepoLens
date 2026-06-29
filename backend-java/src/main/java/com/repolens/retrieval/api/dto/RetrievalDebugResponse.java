package com.repolens.retrieval.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public record RetrievalDebugResponse(
        @JsonProperty("bm25_count")
        int bm25Count,

        @JsonProperty("vector_count")
        int vectorCount,

        @JsonProperty("graph_count")
        int graphCount,

        @JsonProperty("merged_count")
        int mergedCount,

        @JsonProperty("evidence_count")
        int evidenceCount,

        @JsonProperty("vector_disabled_reason")
        String vectorDisabledReason,

        @JsonProperty("context_truncated")
        boolean contextTruncated
) {
}
