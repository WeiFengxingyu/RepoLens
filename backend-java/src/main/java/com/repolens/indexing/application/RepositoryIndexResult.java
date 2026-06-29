package com.repolens.indexing.application;

public record RepositoryIndexResult(
        int fileCount,
        int parsedFileCount,
        int skippedFileCount,
        int chunkCount,
        int symbolCount,
        int relationCount,
        int vectorCount
) {
}
