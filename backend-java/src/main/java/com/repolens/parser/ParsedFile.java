package com.repolens.parser;

import com.repolens.scanner.Language;

import java.util.List;

public record ParsedFile(
        String relativePath,
        Language language,
        String content,
        int lineCount,
        String packageName,
        List<String> imports,
        List<ParsedSymbol> symbols,
        List<ParseError> errors
) {
}
