package com.repolens.scanner;

import org.springframework.stereotype.Component;

import java.nio.file.Path;
import java.util.Locale;

@Component
public class FileLanguageDetector {

    public Language detect(Path path) {
        String fileName = path.getFileName().toString().toLowerCase(Locale.ROOT);
        if (fileName.equals("dockerfile")) {
            return Language.TEXT;
        }
        if (fileName.endsWith(".java")) {
            return Language.JAVA;
        }
        if (fileName.endsWith(".kt") || fileName.endsWith(".kts")) {
            return Language.KOTLIN;
        }
        if (fileName.endsWith(".py")) {
            return Language.PYTHON;
        }
        if (fileName.endsWith(".ts") || fileName.endsWith(".tsx")) {
            return Language.TYPESCRIPT;
        }
        if (fileName.endsWith(".js") || fileName.endsWith(".jsx") || fileName.endsWith(".mjs") || fileName.endsWith(".cjs")) {
            return Language.JAVASCRIPT;
        }
        if (fileName.endsWith(".xml") || fileName.endsWith(".pom")) {
            return Language.XML;
        }
        if (fileName.endsWith(".yml") || fileName.endsWith(".yaml")) {
            return Language.YAML;
        }
        if (fileName.endsWith(".json")) {
            return Language.JSON;
        }
        if (fileName.endsWith(".md") || fileName.endsWith(".markdown")) {
            return Language.MARKDOWN;
        }
        if (fileName.endsWith(".properties")) {
            return Language.PROPERTIES;
        }
        if (fileName.endsWith(".sql")) {
            return Language.SQL;
        }
        if (fileName.endsWith(".txt") || fileName.equals(".gitignore")) {
            return Language.TEXT;
        }
        return Language.UNKNOWN;
    }
}
