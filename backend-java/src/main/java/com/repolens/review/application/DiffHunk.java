package com.repolens.review.application;

import java.util.List;

public record DiffHunk(
        int oldStart,
        int oldCount,
        int newStart,
        int newCount,
        List<DiffLine> lines
) {
    public int addedLineCount() {
        return (int) lines.stream().filter(line -> line.type() == DiffLineType.ADDED).count();
    }
}
