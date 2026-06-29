package com.repolens.parser;

import com.repolens.scanner.Language;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Component
public class SimpleTypeScriptParser implements CodeParser {

    private static final Pattern IMPORT_PATTERN = Pattern.compile("^\\s*import\\s+.+");
    private static final Pattern CLASS_PATTERN = Pattern.compile("^\\s*(?:export\\s+)?(?:default\\s+)?class\\s+([A-Za-z_$][\\w$]*)");
    private static final Pattern FUNCTION_PATTERN = Pattern.compile("^\\s*(?:export\\s+)?(?:default\\s+)?(?:async\\s+)?function\\s+([A-Za-z_$][\\w$]*)\\s*\\(");
    private static final Pattern CONST_FUNCTION_PATTERN = Pattern.compile("^\\s*(?:export\\s+)?(?:const|let|var)\\s+([A-Za-z_$][\\w$]*)\\s*=\\s*(?:async\\s*)?\\([^)]*\\)\\s*=>");
    private static final Pattern METHOD_PATTERN = Pattern.compile("^\\s{2,}(?:async\\s+)?([A-Za-z_$][\\w$]*)\\s*\\([^)]*\\)\\s*[:{]");

    @Override
    public ParsedFile parse(Path file, String relativePath) {
        String content = readContent(file);
        List<String> lines = content.lines().toList();
        List<String> imports = new ArrayList<>();
        List<ParsedSymbol> symbols = new ArrayList<>();
        String currentClass = null;

        for (int index = 0; index < lines.size(); index++) {
            String line = lines.get(index);
            int lineNumber = index + 1;
            if (IMPORT_PATTERN.matcher(line).find()) {
                imports.add(line.trim());
            }

            Matcher classMatcher = CLASS_PATTERN.matcher(line);
            if (classMatcher.find()) {
                String name = classMatcher.group(1);
                currentClass = name;
                symbols.add(symbol(name, name, SymbolType.CLASS, null, lineNumber, findBraceBlockEnd(lines, index), line.trim(), "simple-typescript"));
                continue;
            }

            Matcher functionMatcher = FUNCTION_PATTERN.matcher(line);
            if (functionMatcher.find()) {
                String name = functionMatcher.group(1);
                symbols.add(symbol(name, name, SymbolType.FUNCTION, null, lineNumber, findBraceBlockEnd(lines, index), line.trim(), "simple-typescript"));
                continue;
            }

            Matcher constMatcher = CONST_FUNCTION_PATTERN.matcher(line);
            if (constMatcher.find()) {
                String name = constMatcher.group(1);
                symbols.add(symbol(name, name, SymbolType.FUNCTION, null, lineNumber, findBraceBlockEnd(lines, index), line.trim(), "simple-typescript"));
                continue;
            }

            Matcher methodMatcher = METHOD_PATTERN.matcher(line);
            if (currentClass != null && methodMatcher.find()) {
                String name = methodMatcher.group(1);
                symbols.add(symbol(name, currentClass + "#" + name, SymbolType.METHOD, currentClass, lineNumber, findBraceBlockEnd(lines, index), line.trim(), "simple-typescript"));
            }
        }

        return new ParsedFile(relativePath, languageFor(relativePath), content, Math.max(1, lines.size()), "", List.copyOf(imports), List.copyOf(symbols), List.of());
    }

    @Override
    public boolean supports(Language language) {
        return language == Language.TYPESCRIPT || language == Language.JAVASCRIPT;
    }

    private ParsedSymbol symbol(
            String name,
            String qualifiedName,
            SymbolType type,
            String parent,
            int startLine,
            int endLine,
            String signature,
            String parser
    ) {
        return new ParsedSymbol(
                name,
                qualifiedName,
                type,
                parent,
                startLine,
                endLine,
                List.of(),
                List.of(),
                signature,
                Map.of("parser", parser)
        );
    }

    private int findBraceBlockEnd(List<String> lines, int startIndex) {
        int depth = 0;
        boolean seenBrace = false;
        for (int index = startIndex; index < lines.size(); index++) {
            String line = lines.get(index);
            for (int charIndex = 0; charIndex < line.length(); charIndex++) {
                char current = line.charAt(charIndex);
                if (current == '{') {
                    depth++;
                    seenBrace = true;
                } else if (current == '}') {
                    depth--;
                    if (seenBrace && depth <= 0) {
                        return index + 1;
                    }
                }
            }
        }
        return Math.max(1, lines.size());
    }

    private Language languageFor(String relativePath) {
        String lower = relativePath.toLowerCase(java.util.Locale.ROOT);
        return lower.endsWith(".js") || lower.endsWith(".jsx") || lower.endsWith(".mjs") || lower.endsWith(".cjs")
                ? Language.JAVASCRIPT
                : Language.TYPESCRIPT;
    }

    private String readContent(Path file) {
        try {
            return Files.readString(file);
        } catch (IOException exception) {
            throw new IllegalArgumentException("Unable to read TypeScript/JavaScript source file: " + file, exception);
        }
    }
}
