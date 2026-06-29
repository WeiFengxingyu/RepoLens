package com.repolens.scanner;

import java.nio.file.Path;
import java.util.List;
import java.util.Map;

public record ScanResult(
        Path rootPath,
        List<ScannedFile> files,
        List<SkippedFile> skippedFiles,
        Map<Language, Integer> languageSummary
) {
    public int fileCount() {
        return files.size();
    }

    public int skippedFileCount() {
        return skippedFiles.size();
    }
}
