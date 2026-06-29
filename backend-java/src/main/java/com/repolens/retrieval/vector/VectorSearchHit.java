package com.repolens.retrieval.vector;

public record VectorSearchHit(
        String chunkId,
        double score,
        int rank
) {
}
