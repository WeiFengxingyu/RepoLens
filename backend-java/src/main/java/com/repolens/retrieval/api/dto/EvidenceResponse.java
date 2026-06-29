package com.repolens.retrieval.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;
import java.util.Map;

public record EvidenceResponse(
        @JsonProperty("evidence_id")
        String evidenceId,

        @JsonProperty("chunk_id")
        String chunkId,

        @JsonProperty("repository_id")
        String repositoryId,

        @JsonProperty("file_path")
        String filePath,

        @JsonProperty("start_line")
        int startLine,

        @JsonProperty("end_line")
        int endLine,

        @JsonProperty("symbol_name")
        String symbolName,

        @JsonProperty("symbol_type")
        String symbolType,

        String language,

        String source,

        List<String> sources,

        double score,

        @JsonProperty("bm25_score")
        double bm25Score,

        @JsonProperty("vector_score")
        double vectorScore,

        @JsonProperty("graph_score")
        double graphScore,

        String snippet,

        Map<String, Object> metadata
) {
}
