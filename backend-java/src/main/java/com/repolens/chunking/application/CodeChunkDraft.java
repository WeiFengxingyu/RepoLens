package com.repolens.chunking.application;

import com.repolens.chunking.domain.ChunkType;

import java.util.Map;

public record CodeChunkDraft(
        String filePath,
        String language,
        String symbolName,
        ChunkType chunkType,
        int startLine,
        int endLine,
        String content,
        String contentHash,
        int tokenEstimate,
        Map<String, Object> metadata
) {
}
