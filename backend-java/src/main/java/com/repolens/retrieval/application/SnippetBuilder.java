package com.repolens.retrieval.application;

import org.springframework.stereotype.Component;

@Component
public class SnippetBuilder {

    private static final int DEFAULT_MAX_CHARS = 600;

    public String build(String content) {
        if (content == null || content.isBlank()) {
            return "";
        }
        String normalized = content.stripTrailing();
        if (normalized.length() <= DEFAULT_MAX_CHARS) {
            return normalized;
        }
        return normalized.substring(0, DEFAULT_MAX_CHARS).stripTrailing() + "\n...";
    }
}
