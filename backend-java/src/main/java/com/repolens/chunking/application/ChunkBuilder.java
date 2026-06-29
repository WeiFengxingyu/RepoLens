package com.repolens.chunking.application;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.repolens.chunking.domain.ChunkType;
import com.repolens.parser.ParseError;
import com.repolens.parser.ParsedFile;
import com.repolens.parser.ParsedSymbol;
import com.repolens.parser.SymbolType;
import com.repolens.scanner.Language;
import org.springframework.stereotype.Component;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Component
public class ChunkBuilder {

    private final LineSliceService lineSliceService;
    private final TokenEstimateService tokenEstimateService;
    private final ObjectMapper objectMapper;

    public ChunkBuilder(
            LineSliceService lineSliceService,
            TokenEstimateService tokenEstimateService,
            ObjectMapper objectMapper
    ) {
        this.lineSliceService = lineSliceService;
        this.tokenEstimateService = tokenEstimateService;
        this.objectMapper = objectMapper;
    }

    public List<CodeChunkDraft> buildChunks(ParsedFile parsedFile) {
        if (!parsedFile.symbols().isEmpty()) {
            return buildSymbolChunks(parsedFile);
        }
        Map<String, Object> metadata = parsedFile.language() == Language.JAVA || !parsedFile.errors().isEmpty()
                ? fallbackMetadata(parsedFile)
                : Map.of("source", "scanner");
        return List.of(buildWholeFileChunk(parsedFile, chunkTypeFor(parsedFile.language()), metadata));
    }

    private List<CodeChunkDraft> buildSymbolChunks(ParsedFile parsedFile) {
        List<ParsedSymbol> chunkSymbols = parsedFile.symbols().stream()
                .filter(this::isChunkSymbol)
                .sorted(Comparator
                        .comparingInt((ParsedSymbol symbol) -> symbol.symbolType() == SymbolType.METHOD || symbol.symbolType() == SymbolType.CONSTRUCTOR ? 0 : 1)
                        .thenComparingInt(ParsedSymbol::startLine)
                        .thenComparing(ParsedSymbol::qualifiedName))
                .toList();
        if (chunkSymbols.isEmpty()) {
            return List.of(buildWholeFileChunk(
                    parsedFile,
                    ChunkType.FILE,
                    fallbackMetadata(parsedFile)
            ));
        }

        List<CodeChunkDraft> chunks = new ArrayList<>();
        for (ParsedSymbol symbol : chunkSymbols) {
            ChunkType chunkType = toChunkType(symbol.symbolType());
            String slice = lineSliceService.slice(parsedFile.content(), symbol.startLine(), symbol.endLine());
            Map<String, Object> metadata = symbolMetadata(symbol);
            String content = withHeader(parsedFile.relativePath(), symbol, slice);
            chunks.add(new CodeChunkDraft(
                    parsedFile.relativePath(),
                    parsedFile.language().name(),
                    symbol.qualifiedName(),
                    chunkType,
                    symbol.startLine(),
                    symbol.endLine(),
                    content,
                    contentHash(parsedFile.language().name(), parsedFile.relativePath(), symbol.startLine(), symbol.endLine(), content),
                    tokenEstimateService.estimate(content),
                    metadata
            ));
        }
        return List.copyOf(chunks);
    }

    private CodeChunkDraft buildWholeFileChunk(ParsedFile parsedFile, ChunkType chunkType, Map<String, Object> metadata) {
        String content = withFileHeader(parsedFile.relativePath(), parsedFile.content());
        int lineCount = Math.max(1, parsedFile.lineCount());
        return new CodeChunkDraft(
                parsedFile.relativePath(),
                parsedFile.language().name(),
                parsedFile.relativePath(),
                chunkType,
                1,
                lineCount,
                content,
                contentHash(parsedFile.language().name(), parsedFile.relativePath(), 1, lineCount, content),
                tokenEstimateService.estimate(content),
                metadata
        );
    }

    private boolean isChunkSymbol(ParsedSymbol symbol) {
        return switch (symbol.symbolType()) {
            case CLASS, INTERFACE, ENUM, RECORD, METHOD, CONSTRUCTOR, FUNCTION -> true;
        };
    }

    private ChunkType toChunkType(SymbolType symbolType) {
        return switch (symbolType) {
            case METHOD, CONSTRUCTOR, FUNCTION -> ChunkType.METHOD;
            case CLASS, INTERFACE, ENUM, RECORD -> ChunkType.CLASS;
        };
    }

    private ChunkType chunkTypeFor(Language language) {
        return switch (language) {
            case XML, YAML, JSON, PROPERTIES, SQL -> ChunkType.CONFIG;
            case MARKDOWN, TEXT, UNKNOWN, KOTLIN, PYTHON, TYPESCRIPT, JAVASCRIPT -> ChunkType.TEXT;
            case JAVA -> ChunkType.FILE;
        };
    }

    private Map<String, Object> symbolMetadata(ParsedSymbol symbol) {
        Map<String, Object> metadata = new LinkedHashMap<>();
        metadata.put("source", "parser");
        metadata.put("symbolType", symbol.symbolType().name());
        if (symbol.parentSymbolName() != null) {
            metadata.put("parentSymbol", symbol.parentSymbolName());
        }
        metadata.put("annotations", symbol.annotations());
        metadata.put("modifiers", symbol.modifiers());
        metadata.put("signature", symbol.signature());
        metadata.putAll(symbol.metadata());
        return Map.copyOf(metadata);
    }

    private Map<String, Object> fallbackMetadata(ParsedFile parsedFile) {
        Map<String, Object> metadata = new LinkedHashMap<>();
        metadata.put("source", "parser");
        metadata.put("fallback", true);
        metadata.put("errors", parsedFile.errors().stream().map(ParseError::message).toList());
        return Map.copyOf(metadata);
    }

    private String withHeader(String filePath, ParsedSymbol symbol, String body) {
        List<String> header = new ArrayList<>();
        header.add("// file: " + filePath);
        header.add("// symbol: " + symbol.qualifiedName());
        header.add("// lines: " + symbol.startLine() + "-" + symbol.endLine());
        if (!symbol.annotations().isEmpty()) {
            header.add("// annotations: " + String.join(", ", symbol.annotations()));
        }
        Object route = symbol.metadata().get("route");
        if (route != null) {
            header.add("// route: " + compactJson(route));
        }
        header.add(body);
        return String.join(System.lineSeparator(), header);
    }

    private String withFileHeader(String filePath, String body) {
        return "// file: " + filePath + System.lineSeparator()
                + "// symbol: " + filePath + System.lineSeparator()
                + body;
    }

    private String compactJson(Object value) {
        try {
            return objectMapper.writeValueAsString(value);
        } catch (JsonProcessingException exception) {
            return String.valueOf(value);
        }
    }

    private String contentHash(String language, String filePath, int startLine, int endLine, String content) {
        String raw = language + filePath + startLine + endLine + content;
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            return HexFormat.of().formatHex(digest.digest(raw.getBytes(StandardCharsets.UTF_8)));
        } catch (NoSuchAlgorithmException exception) {
            throw new IllegalStateException("SHA-256 algorithm is not available", exception);
        }
    }
}
