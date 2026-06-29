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
public class SimplePythonParser implements CodeParser {

    private static final Pattern IMPORT_PATTERN = Pattern.compile("^\\s*(?:from\\s+([\\w.]+)\\s+import\\s+(.+)|import\\s+(.+))\\s*$");
    private static final Pattern CLASS_PATTERN = Pattern.compile("^(\\s*)class\\s+([A-Za-z_][\\w]*)\\s*(?:\\([^)]*\\))?\\s*:");
    private static final Pattern FUNCTION_PATTERN = Pattern.compile("^(\\s*)(?:async\\s+)?def\\s+([A-Za-z_][\\w]*)\\s*\\(([^)]*)\\)\\s*(?:->\\s*[^:]+)?\\s*:");
    private static final Pattern DECORATOR_PATTERN = Pattern.compile("^\\s*@([A-Za-z_][\\w.]*)");

    @Override
    public ParsedFile parse(Path file, String relativePath) {
        String content = readContent(file);
        List<String> lines = content.lines().toList();
        List<String> imports = new ArrayList<>();
        List<ParsedSymbol> symbols = new ArrayList<>();
        List<String> pendingDecorators = new ArrayList<>();
        List<PythonScope> scopes = new ArrayList<>();

        for (int index = 0; index < lines.size(); index++) {
            String line = lines.get(index);
            int lineNumber = index + 1;

            Matcher importMatcher = IMPORT_PATTERN.matcher(line);
            if (importMatcher.matches()) {
                imports.add(line.trim());
                continue;
            }

            Matcher decoratorMatcher = DECORATOR_PATTERN.matcher(line);
            if (decoratorMatcher.find()) {
                pendingDecorators.add(decoratorMatcher.group(1));
                continue;
            }

            Matcher classMatcher = CLASS_PATTERN.matcher(line);
            if (classMatcher.find()) {
                int indent = classMatcher.group(1).length();
                trimScopes(scopes, indent);
                String name = classMatcher.group(2);
                String qualifiedName = qualify(scopes, name);
                symbols.add(symbol(name, qualifiedName, SymbolType.CLASS, parent(scopes), lineNumber, findBlockEnd(lines, index, indent), pendingDecorators, line.trim()));
                scopes.add(new PythonScope(indent, qualifiedName));
                pendingDecorators = new ArrayList<>();
                continue;
            }

            Matcher functionMatcher = FUNCTION_PATTERN.matcher(line);
            if (functionMatcher.find()) {
                int indent = functionMatcher.group(1).length();
                trimScopes(scopes, indent);
                String name = functionMatcher.group(2);
                String qualifiedName = qualify(scopes, name);
                symbols.add(symbol(name, qualifiedName, SymbolType.FUNCTION, parent(scopes), lineNumber, findBlockEnd(lines, index, indent), pendingDecorators, line.trim()));
                pendingDecorators = new ArrayList<>();
            } else if (!line.isBlank()) {
                pendingDecorators = new ArrayList<>();
            }
        }

        return new ParsedFile(relativePath, Language.PYTHON, content, Math.max(1, lines.size()), "", List.copyOf(imports), List.copyOf(symbols), List.of());
    }

    @Override
    public boolean supports(Language language) {
        return language == Language.PYTHON;
    }

    private ParsedSymbol symbol(
            String name,
            String qualifiedName,
            SymbolType type,
            String parent,
            int startLine,
            int endLine,
            List<String> decorators,
            String signature
    ) {
        return new ParsedSymbol(
                name,
                qualifiedName,
                type,
                parent,
                startLine,
                endLine,
                List.copyOf(decorators),
                List.of(),
                signature,
                Map.of("parser", "simple-python")
        );
    }

    private void trimScopes(List<PythonScope> scopes, int indent) {
        while (!scopes.isEmpty() && scopes.getLast().indent() >= indent) {
            scopes.removeLast();
        }
    }

    private String parent(List<PythonScope> scopes) {
        return scopes.isEmpty() ? null : scopes.getLast().qualifiedName();
    }

    private String qualify(List<PythonScope> scopes, String name) {
        String parent = parent(scopes);
        return parent == null ? name : parent + "." + name;
    }

    private int findBlockEnd(List<String> lines, int startIndex, int indent) {
        for (int index = startIndex + 1; index < lines.size(); index++) {
            String line = lines.get(index);
            if (line.isBlank()) {
                continue;
            }
            int currentIndent = leadingSpaces(line);
            if (currentIndent <= indent) {
                return index;
            }
        }
        return Math.max(1, lines.size());
    }

    private int leadingSpaces(String value) {
        int count = 0;
        while (count < value.length() && value.charAt(count) == ' ') {
            count++;
        }
        return count;
    }

    private String readContent(Path file) {
        try {
            return Files.readString(file);
        } catch (IOException exception) {
            throw new IllegalArgumentException("Unable to read Python source file: " + file, exception);
        }
    }

    private record PythonScope(int indent, String qualifiedName) {
    }
}
