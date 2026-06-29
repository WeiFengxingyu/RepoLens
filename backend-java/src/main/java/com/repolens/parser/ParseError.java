package com.repolens.parser;

public record ParseError(
        String message,
        int line,
        int column
) {
}
