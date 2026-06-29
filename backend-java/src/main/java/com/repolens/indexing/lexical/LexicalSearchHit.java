package com.repolens.indexing.lexical;

public record LexicalSearchHit(
        String chunkId,
        float score,
        int rank
) {
}
