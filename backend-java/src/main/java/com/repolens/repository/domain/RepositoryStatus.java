package com.repolens.repository.domain;

public enum RepositoryStatus {
    CREATED,
    SCANNING,
    PARSING,
    CHUNKING,
    INDEXING,
    READY,
    FAILED
}
