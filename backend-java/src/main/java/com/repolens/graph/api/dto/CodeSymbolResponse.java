package com.repolens.graph.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.repolens.graph.domain.CodeSymbolEntity;

public record CodeSymbolResponse(
        String id,
        @JsonProperty("repository_id")
        String repositoryId,
        @JsonProperty("file_path")
        String filePath,
        String language,
        @JsonProperty("symbol_name")
        String symbolName,
        @JsonProperty("qualified_name")
        String qualifiedName,
        @JsonProperty("symbol_type")
        String symbolType,
        @JsonProperty("parent_symbol_name")
        String parentSymbolName,
        @JsonProperty("start_line")
        int startLine,
        @JsonProperty("end_line")
        int endLine,
        String signature
) {
    public static CodeSymbolResponse from(CodeSymbolEntity entity) {
        return new CodeSymbolResponse(
                entity.getId(),
                entity.getRepositoryId(),
                entity.getFilePath(),
                entity.getLanguage(),
                entity.getSymbolName(),
                entity.getQualifiedName(),
                entity.getSymbolType(),
                entity.getParentSymbolName(),
                entity.getStartLine(),
                entity.getEndLine(),
                entity.getSignature()
        );
    }
}
