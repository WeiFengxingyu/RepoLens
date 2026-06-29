package com.repolens.graph.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.repolens.graph.domain.CodeRelationEntity;

public record CodeRelationResponse(
        String id,
        @JsonProperty("relation_type")
        String relationType,
        @JsonProperty("source_symbol_id")
        String sourceSymbolId,
        @JsonProperty("target_symbol_id")
        String targetSymbolId,
        @JsonProperty("source_name")
        String sourceName,
        @JsonProperty("target_name")
        String targetName,
        @JsonProperty("file_path")
        String filePath
) {
    public static CodeRelationResponse from(CodeRelationEntity entity) {
        return new CodeRelationResponse(
                entity.getId(),
                entity.getRelationType(),
                entity.getSourceSymbolId(),
                entity.getTargetSymbolId(),
                entity.getSourceName(),
                entity.getTargetName(),
                entity.getFilePath()
        );
    }
}
