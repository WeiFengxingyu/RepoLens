package com.repolens.review.application;

import java.util.List;

public record ChangedFile(
        String oldPath,
        String newPath,
        List<DiffHunk> hunks
) {
    public String displayPath() {
        if (newPath != null && !newPath.equals("/dev/null")) {
            return stripPrefix(newPath);
        }
        return stripPrefix(oldPath);
    }

    public int addedLineCount() {
        return hunks.stream().mapToInt(DiffHunk::addedLineCount).sum();
    }

    private String stripPrefix(String value) {
        if (value == null) {
            return "";
        }
        if (value.startsWith("a/") || value.startsWith("b/")) {
            return value.substring(2);
        }
        return value;
    }
}
