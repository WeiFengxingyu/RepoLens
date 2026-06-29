package com.repolens.retrieval.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

public record RetrievalResponse(
        @JsonProperty("repository_id")
        String repositoryId,

        String query,

        List<EvidenceResponse> evidences,

        RetrievalDebugResponse debug
) {
}
