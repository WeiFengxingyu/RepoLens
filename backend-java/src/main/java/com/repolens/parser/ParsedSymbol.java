package com.repolens.parser;

import java.util.List;
import java.util.Map;

public record ParsedSymbol(
        String symbolName,
        String qualifiedName,
        SymbolType symbolType,
        String parentSymbolName,
        int startLine,
        int endLine,
        List<String> annotations,
        List<String> modifiers,
        String signature,
        Map<String, Object> metadata
) {
}
