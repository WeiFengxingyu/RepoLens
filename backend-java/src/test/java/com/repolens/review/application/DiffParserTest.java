package com.repolens.review.application;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class DiffParserTest {

    private final DiffParser parser = new DiffParser();

    @Test
    void parsesUnifiedDiffFilesHunksAndAddedLines() {
        ParsedDiff diff = parser.parse("""
                diff --git a/src/AuthConfig.java b/src/AuthConfig.java
                --- a/src/AuthConfig.java
                +++ b/src/AuthConfig.java
                @@ -10,6 +10,8 @@ class AuthConfig {
                   void configure() {
                -    requireAuth();
                +    permitAll();
                +    return null;
                   }
                """);

        assertThat(diff.files()).hasSize(1);
        ChangedFile file = diff.files().getFirst();
        assertThat(file.displayPath()).isEqualTo("src/AuthConfig.java");
        assertThat(file.hunks()).hasSize(1);
        assertThat(file.hunks().getFirst().lines())
                .filteredOn(line -> line.type() == DiffLineType.ADDED)
                .extracting(DiffLine::content)
                .containsExactly("    permitAll();", "    return null;");
        assertThat(diff.addedLineCount()).isEqualTo(2);
    }
}
