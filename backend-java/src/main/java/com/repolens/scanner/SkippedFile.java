package com.repolens.scanner;

public record SkippedFile(
        String relativePath,
        SkipReason reason
) {
}
