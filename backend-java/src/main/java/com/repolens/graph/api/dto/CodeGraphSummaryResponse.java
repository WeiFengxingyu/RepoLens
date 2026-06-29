package com.repolens.graph.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public record CodeGraphSummaryResponse(
        @JsonProperty("repository_id")
        String repositoryId,
        @JsonProperty("symbol_count")
        long symbolCount,
        @JsonProperty("relation_count")
        long relationCount,
        @JsonProperty("route_count")
        long routeCount
) {
}
