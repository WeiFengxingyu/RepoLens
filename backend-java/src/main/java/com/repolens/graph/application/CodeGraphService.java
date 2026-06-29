package com.repolens.graph.application;

import com.repolens.common.error.ResourceNotFoundException;
import com.repolens.graph.api.dto.CodeGraphNeighborsResponse;
import com.repolens.graph.api.dto.CodeGraphSummaryResponse;
import com.repolens.graph.api.dto.CodeRelationResponse;
import com.repolens.graph.api.dto.CodeSymbolResponse;
import com.repolens.graph.domain.CodeRelationEntity;
import com.repolens.graph.domain.CodeSymbolEntity;
import com.repolens.graph.infrastructure.CodeRelationJpaRepository;
import com.repolens.graph.infrastructure.CodeSymbolJpaRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Comparator;
import java.util.List;

@Service
public class CodeGraphService {

    private final CodeSymbolJpaRepository codeSymbolJpaRepository;
    private final CodeRelationJpaRepository codeRelationJpaRepository;

    public CodeGraphService(
            CodeSymbolJpaRepository codeSymbolJpaRepository,
            CodeRelationJpaRepository codeRelationJpaRepository
    ) {
        this.codeSymbolJpaRepository = codeSymbolJpaRepository;
        this.codeRelationJpaRepository = codeRelationJpaRepository;
    }

    @Transactional(readOnly = true)
    public CodeGraphSummaryResponse summary(String repositoryId) {
        return new CodeGraphSummaryResponse(
                repositoryId,
                codeSymbolJpaRepository.countByRepositoryId(repositoryId),
                codeRelationJpaRepository.countByRepositoryId(repositoryId),
                codeRelationJpaRepository.countByRepositoryIdAndRelationType(repositoryId, "ROUTE")
        );
    }

    @Transactional(readOnly = true)
    public List<CodeSymbolResponse> searchSymbols(String repositoryId, String query) {
        String normalized = query == null || query.isBlank() ? "" : query.trim();
        List<CodeSymbolEntity> symbols = normalized.isBlank()
                ? codeSymbolJpaRepository.findByRepositoryId(repositoryId)
                : codeSymbolJpaRepository.findTop50ByRepositoryIdAndQualifiedNameContainingIgnoreCaseOrRepositoryIdAndSymbolNameContainingIgnoreCase(
                        repositoryId,
                        normalized,
                        repositoryId,
                        normalized
                );
        return symbols.stream()
                .sorted(Comparator.comparing(CodeSymbolEntity::getFilePath).thenComparingInt(CodeSymbolEntity::getStartLine))
                .map(CodeSymbolResponse::from)
                .toList();
    }

    @Transactional(readOnly = true)
    public CodeGraphNeighborsResponse neighbors(String repositoryId, String symbolId) {
        CodeSymbolEntity symbol = codeSymbolJpaRepository.findById(symbolId)
                .filter(value -> value.getRepositoryId().equals(repositoryId))
                .orElseThrow(() -> new ResourceNotFoundException("Code symbol not found"));
        List<CodeRelationResponse> relations = codeRelationJpaRepository.findByRepositoryIdAndSourceSymbolIdOrRepositoryIdAndTargetSymbolId(
                        repositoryId,
                        symbolId,
                        repositoryId,
                        symbolId
                )
                .stream()
                .map(CodeRelationResponse::from)
                .toList();
        return new CodeGraphNeighborsResponse(CodeSymbolResponse.from(symbol), relations);
    }

    @Transactional(readOnly = true)
    public List<CodeSymbolEntity> symbolsForFile(String repositoryId, String filePath) {
        return codeSymbolJpaRepository.findByRepositoryIdAndFilePath(repositoryId, filePath);
    }

    @Transactional(readOnly = true)
    public List<CodeRelationEntity> relationsForSymbol(String repositoryId, String symbolId) {
        return codeRelationJpaRepository.findByRepositoryIdAndSourceSymbolIdOrRepositoryIdAndTargetSymbolId(
                repositoryId,
                symbolId,
                repositoryId,
                symbolId
        );
    }
}
