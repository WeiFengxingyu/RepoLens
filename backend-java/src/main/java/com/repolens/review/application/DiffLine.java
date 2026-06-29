package com.repolens.review.application;

public record DiffLine(
        DiffLineType type,
        int oldLine,
        int newLine,
        String content
) {
}
