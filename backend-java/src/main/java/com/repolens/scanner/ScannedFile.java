package com.repolens.scanner;

import java.nio.file.Path;

public record ScannedFile(
        Path path,
        String relativePath,
        Language language,
        long sizeBytes,
        String contentHash
) {
}
