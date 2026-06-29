package com.repolens.review.application;

import java.util.List;

public record ParsedDiff(List<ChangedFile> files) {

    public int changedFileCount() {
        return files.size();
    }

    public int addedLineCount() {
        return files.stream().mapToInt(ChangedFile::addedLineCount).sum();
    }
}
