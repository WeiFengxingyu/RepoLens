package com.repolens.graph.application;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.repolens.common.id.IdGenerator;
import com.repolens.graph.domain.CodeRelationEntity;
import com.repolens.graph.domain.CodeSymbolEntity;
import com.repolens.graph.infrastructure.CodeRelationJpaRepository;
import com.repolens.graph.infrastructure.CodeSymbolJpaRepository;
import com.repolens.parser.ParsedFile;
import com.repolens.parser.ParsedSymbol;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Clock;
import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.stream.Collectors;

@Service
public class CodeGraphBuilder {

    private final CodeSymbolJpaRepository codeSymbolJpaRepository;
    private final CodeRelationJpaRepository codeRelationJpaRepository;
    private final IdGenerator idGenerator;
    private final ObjectMapper objectMapper;
    private final Clock clock;

    public CodeGraphBuilder(
            CodeSymbolJpaRepository codeSymbolJpaRepository,
            CodeRelationJpaRepository codeRelationJpaRepository,
            IdGenerator idGenerator,
            ObjectMapper objectMapper,
            Clock clock
    ) {
        this.codeSymbolJpaRepository = codeSymbolJpaRepository;
        this.codeRelationJpaRepository = codeRelationJpaRepository;
        this.idGenerator = idGenerator;
        this.objectMapper = objectMapper;
        this.clock = clock;
    }

    @Transactional
    public CodeGraphBuildResult rebuild(String repositoryId, List<ParsedFile> parsedFiles) {
        codeRelationJpaRepository.deleteByRepositoryId(repositoryId);
        codeSymbolJpaRepository.deleteByRepositoryId(repositoryId);

        Instant now = Instant.now(clock);
        List<CodeSymbolEntity> symbols = new ArrayList<>();
        for (ParsedFile parsedFile : parsedFiles) {
            for (ParsedSymbol parsedSymbol : parsedFile.symbols()) {
                symbols.add(toEntity(repositoryId, parsedFile, parsedSymbol, now));
            }
        }
        codeSymbolJpaRepository.saveAll(symbols);

        Map<String, CodeSymbolEntity> byQualifiedName = symbols.stream()
                .collect(Collectors.toMap(CodeSymbolEntity::getQualifiedName, symbol -> symbol, (left, right) -> left, LinkedHashMap::new));

        List<CodeRelationEntity> relations = new ArrayList<>();
        for (ParsedFile parsedFile : parsedFiles) {
            for (String imported : parsedFile.imports()) {
                relations.add(importRelation(repositoryId, parsedFile.relativePath(), imported, now));
            }
            for (ParsedSymbol parsedSymbol : parsedFile.symbols()) {
                CodeSymbolEntity current = byQualifiedName.get(parsedSymbol.qualifiedName());
                if (current == null) {
                    continue;
                }
                if (parsedSymbol.parentSymbolName() != null && !parsedSymbol.parentSymbolName().isBlank()) {
                    CodeSymbolEntity parent = byQualifiedName.get(parsedSymbol.parentSymbolName());
                    if (parent != null) {
                        relations.add(containsRelation(repositoryId, parent, current, parsedFile.relativePath(), now));
                    }
                }
                routePath(parsedSymbol).ifPresent(route -> relations.add(routeRelation(repositoryId, current, route, parsedFile.relativePath(), now)));
            }
        }

        codeRelationJpaRepository.saveAll(relations);
        return new CodeGraphBuildResult(symbols.size(), relations.size());
    }

    private CodeSymbolEntity toEntity(String repositoryId, ParsedFile parsedFile, ParsedSymbol parsedSymbol, Instant now) {
        CodeSymbolEntity entity = new CodeSymbolEntity(
                idGenerator.newId("sym"),
                repositoryId,
                parsedFile.relativePath(),
                parsedFile.language().name(),
                parsedSymbol.symbolName(),
                parsedSymbol.qualifiedName(),
                parsedSymbol.symbolType().name(),
                parsedSymbol.startLine(),
                parsedSymbol.endLine(),
                now
        );
        entity.setParentSymbolName(parsedSymbol.parentSymbolName());
        entity.setSignature(parsedSymbol.signature());
        entity.setMetadata(toJson(parsedSymbol.metadata()));
        return entity;
    }

    private CodeRelationEntity importRelation(String repositoryId, String filePath, String imported, Instant now) {
        CodeRelationEntity relation = new CodeRelationEntity(idGenerator.newId("rel"), repositoryId, "IMPORTS", now);
        relation.setTargetName(imported);
        relation.setFilePath(filePath);
        return relation;
    }

    private CodeRelationEntity containsRelation(String repositoryId, CodeSymbolEntity parent, CodeSymbolEntity child, String filePath, Instant now) {
        CodeRelationEntity relation = new CodeRelationEntity(idGenerator.newId("rel"), repositoryId, "CONTAINS", now);
        relation.setSourceSymbolId(parent.getId());
        relation.setTargetSymbolId(child.getId());
        relation.setSourceName(parent.getQualifiedName());
        relation.setTargetName(child.getQualifiedName());
        relation.setFilePath(filePath);
        return relation;
    }

    private CodeRelationEntity routeRelation(String repositoryId, CodeSymbolEntity symbol, String route, String filePath, Instant now) {
        CodeRelationEntity relation = new CodeRelationEntity(idGenerator.newId("rel"), repositoryId, "ROUTE", now);
        relation.setSourceSymbolId(symbol.getId());
        relation.setSourceName(symbol.getQualifiedName());
        relation.setTargetName(route);
        relation.setFilePath(filePath);
        relation.setMetadata(toJson(Map.of("path", route)));
        return relation;
    }

    @SuppressWarnings("unchecked")
    private Optional<String> routePath(ParsedSymbol parsedSymbol) {
        Object route = parsedSymbol.metadata().get("route");
        if (route instanceof Map<?, ?> routeMap) {
            Object path = routeMap.get("path");
            if (path != null && !path.toString().isBlank()) {
                return Optional.of(path.toString());
            }
        }
        return Optional.empty();
    }

    private String toJson(Object value) {
        try {
            return objectMapper.writeValueAsString(value);
        } catch (JsonProcessingException exception) {
            throw new IllegalStateException("Failed to serialize code graph metadata", exception);
        }
    }
}
