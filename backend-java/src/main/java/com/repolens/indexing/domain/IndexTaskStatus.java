package com.repolens.indexing.domain;

public enum IndexTaskStatus {
    CREATED,
    VALIDATING,
    SCANNING,
    PARSING,
    CHUNKING,
    BM25_INDEXING,
    VECTOR_INDEXING,
    GRAPH_BUILDING,
    READY,
    FAILED
}
