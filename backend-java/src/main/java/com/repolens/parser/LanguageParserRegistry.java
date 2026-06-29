package com.repolens.parser;

import com.repolens.scanner.Language;
import org.springframework.stereotype.Component;

import java.nio.file.Path;
import java.util.List;

@Component
public class LanguageParserRegistry {

    private final List<CodeParser> parsers;

    public LanguageParserRegistry(List<CodeParser> parsers) {
        this.parsers = parsers;
    }

    public ParsedFile parse(Path file, String relativePath, Language language) {
        return parsers.stream()
                .filter(parser -> parser.supports(language))
                .findFirst()
                .map(parser -> parser.parse(file, relativePath))
                .orElseGet(() -> parseWholeFile(file, relativePath, language));
    }

    private ParsedFile parseWholeFile(Path file, String relativePath, Language language) {
        try {
            String content = java.nio.file.Files.readString(file);
            int lineCount = Math.max(1, content.split("\\R", -1).length);
            return new ParsedFile(relativePath, language, content, lineCount, "", List.of(), List.of(), List.of());
        } catch (java.io.IOException exception) {
            return new ParsedFile(
                    relativePath,
                    language,
                    "",
                    1,
                    "",
                    List.of(),
                    List.of(),
                    List.of(new ParseError("Unable to read file for chunking", 0, 0))
            );
        }
    }
}
