package com.repolens.parser;

import com.repolens.scanner.Language;

import java.nio.file.Path;

public interface CodeParser {

    ParsedFile parse(Path file, String relativePath);

    boolean supports(Language language);
}
