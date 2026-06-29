package com.repolens.qa.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.repolens.retrieval.api.dto.EvidenceResponse;

import java.util.List;

public record QACitationResponse(
        @JsonProperty("evidence_id")
        String evidenceId,
        @JsonProperty("chunk_id")
        String chunkId,
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
        double score,
        List<String> sources,
        String snippet
) {
    public static QACitationResponse from(EvidenceResponse evidence) {
        return new QACitationResponse(
                evidence.evidenceId(),
                evidence.chunkId(),
                evidence.filePath(),
                evidence.startLine(),
                evidence.endLine(),
                evidence.symbolName(),
                evidence.symbolType(),
                evidence.language(),
                evidence.score(),
                evidence.sources(),
                evidence.snippet()
        );
    }
}
