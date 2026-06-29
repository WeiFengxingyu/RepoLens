package com.repolens.retrieval.application;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.repolens.chunking.domain.CodeChunkEntity;
import com.repolens.chunking.infrastructure.CodeChunkJpaRepository;
import com.repolens.common.error.ResourceNotFoundException;
import com.repolens.config.RepoLensProperties;
import com.repolens.graph.domain.CodeRelationEntity;
import com.repolens.graph.domain.CodeSymbolEntity;
import com.repolens.graph.infrastructure.CodeRelationJpaRepository;
import com.repolens.graph.infrastructure.CodeSymbolJpaRepository;
import com.repolens.indexing.lexical.LexicalSearchHit;
import com.repolens.indexing.lexical.LuceneIndexService;
import com.repolens.repository.domain.RepositoryEntity;
import com.repolens.repository.domain.RepositoryStatus;
import com.repolens.repository.infrastructure.RepositoryJpaRepository;
import com.repolens.retrieval.api.dto.EvidenceResponse;
import com.repolens.retrieval.api.dto.RetrievalDebugResponse;
import com.repolens.retrieval.api.dto.RetrievalRequest;
import com.repolens.retrieval.api.dto.RetrievalResponse;
import com.repolens.retrieval.vector.VectorSearchHit;
import com.repolens.retrieval.vector.VectorSearchService;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Collections;
import java.util.Comparator;
import java.util.LinkedHashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.stream.Collectors;

@Service
public class RetrievalService {

    private static final TypeReference<Map<String, Object>> METADATA_TYPE = new TypeReference<>() {
    };
    private static final String BM25_SOURCE = "BM25";
    private static final String VECTOR_SOURCE = "VECTOR";
    private static final String GRAPH_SOURCE = "GRAPH";

    private final RepositoryJpaRepository repositoryJpaRepository;
    private final CodeChunkJpaRepository codeChunkJpaRepository;
    private final LuceneIndexService luceneIndexService;
    private final VectorSearchService vectorSearchService;
    private final CodeSymbolJpaRepository codeSymbolJpaRepository;
    private final CodeRelationJpaRepository codeRelationJpaRepository;
    private final EvidenceIdFactory evidenceIdFactory;
    private final SnippetBuilder snippetBuilder;
    private final ObjectMapper objectMapper;
    private final RepoLensProperties properties;

    public RetrievalService(
            RepositoryJpaRepository repositoryJpaRepository,
            CodeChunkJpaRepository codeChunkJpaRepository,
            LuceneIndexService luceneIndexService,
            VectorSearchService vectorSearchService,
            CodeSymbolJpaRepository codeSymbolJpaRepository,
            CodeRelationJpaRepository codeRelationJpaRepository,
            EvidenceIdFactory evidenceIdFactory,
            SnippetBuilder snippetBuilder,
            ObjectMapper objectMapper,
            RepoLensProperties properties
    ) {
        this.repositoryJpaRepository = repositoryJpaRepository;
        this.codeChunkJpaRepository = codeChunkJpaRepository;
        this.luceneIndexService = luceneIndexService;
        this.vectorSearchService = vectorSearchService;
        this.codeSymbolJpaRepository = codeSymbolJpaRepository;
        this.codeRelationJpaRepository = codeRelationJpaRepository;
        this.evidenceIdFactory = evidenceIdFactory;
        this.snippetBuilder = snippetBuilder;
        this.objectMapper = objectMapper;
        this.properties = properties;
    }

    @Transactional(readOnly = true)
    public RetrievalResponse retrieve(String repositoryId, RetrievalRequest request) {
        RepositoryEntity repository = repositoryJpaRepository.findById(repositoryId)
                .orElseThrow(() -> new ResourceNotFoundException("Repository not found"));
        if (repository.getStatus() != RepositoryStatus.READY) {
            throw new IllegalArgumentException("Repository must be ready before retrieval");
        }

        int topK = normalizeTopK(request.getTopK());
        boolean useBm25 = request.getUseBm25() == null || request.getUseBm25();
        boolean requestedVector = request.getUseVector() != null && request.getUseVector();
        boolean requestedGraph = request.getUseGraph() != null && request.getUseGraph();
        boolean useVector = requestedVector && properties.getRetrieval().isVectorEnabled();
        boolean useGraph = requestedGraph && properties.getRetrieval().isGraphEnabled();

        List<LexicalSearchHit> bm25Hits = useBm25
                ? luceneIndexService.search(repositoryId, request.getQuery(), topK)
                : List.of();
        List<VectorSearchHit> vectorHits = useVector
                ? vectorSearchService.search(repositoryId, request.getQuery(), topK)
                : List.of();

        Map<String, MergedHit> mergedHits = mergeHits(bm25Hits, vectorHits);
        int graphCount = useGraph ? expandGraph(repositoryId, mergedHits, topK) : 0;
        List<EvidenceResponse> evidences = buildEvidences(repositoryId, mergedHits, topK);

        RetrievalDebugResponse debug = new RetrievalDebugResponse(
                bm25Hits.size(),
                vectorHits.size(),
                graphCount,
                mergedHits.size(),
                evidences.size(),
                requestedVector && !useVector ? "Vector retrieval is disabled by configuration" : null,
                false
        );

        return new RetrievalResponse(repositoryId, request.getQuery(), evidences, debug);
    }

    private int normalizeTopK(Integer topK) {
        if (topK == null) {
            return properties.getRetrieval().getDefaultTopK();
        }
        return Math.max(1, Math.min(50, topK));
    }

    private Map<String, MergedHit> mergeHits(List<LexicalSearchHit> bm25Hits, List<VectorSearchHit> vectorHits) {
        Map<String, MergedHit> merged = new LinkedHashMap<>();
        double maxBm25 = bm25Hits.stream().mapToDouble(LexicalSearchHit::score).max().orElse(0.0D);
        for (LexicalSearchHit hit : bm25Hits) {
            MergedHit mergedHit = merged.computeIfAbsent(hit.chunkId(), MergedHit::new);
            mergedHit.sources.add(BM25_SOURCE);
            mergedHit.bm25Score = hit.score();
            mergedHit.normalizedBm25Score = maxBm25 <= 0.0D ? 0.0D : hit.score() / maxBm25;
        }
        for (VectorSearchHit hit : vectorHits) {
            MergedHit mergedHit = merged.computeIfAbsent(hit.chunkId(), MergedHit::new);
            mergedHit.sources.add(VECTOR_SOURCE);
            mergedHit.vectorScore = hit.score();
        }
        return merged;
    }

    private int expandGraph(String repositoryId, Map<String, MergedHit> mergedHits, int topK) {
        if (mergedHits.isEmpty()) {
            return 0;
        }
        List<String> seedChunkIds = mergedHits.values().stream()
                .sorted(Comparator.comparingDouble(MergedHit::score).reversed())
                .limit(topK)
                .map(hit -> hit.chunkId)
                .toList();
        Map<String, CodeChunkEntity> seedChunks = codeChunkJpaRepository.findByRepositoryIdAndIdIn(repositoryId, seedChunkIds)
                .stream()
                .collect(Collectors.toMap(CodeChunkEntity::getId, chunk -> chunk));
        List<CodeSymbolEntity> allSymbols = codeSymbolJpaRepository.findByRepositoryId(repositoryId);
        Map<String, CodeSymbolEntity> symbolsById = allSymbols.stream()
                .collect(Collectors.toMap(CodeSymbolEntity::getId, symbol -> symbol));
        Map<String, CodeSymbolEntity> symbolsByQualifiedName = allSymbols.stream()
                .collect(Collectors.toMap(CodeSymbolEntity::getQualifiedName, symbol -> symbol, (left, right) -> left));

        Set<String> relatedSymbolNames = new LinkedHashSet<>();
        for (String chunkId : seedChunkIds) {
            CodeChunkEntity chunk = seedChunks.get(chunkId);
            if (chunk == null || chunk.getSymbolName() == null || chunk.getSymbolName().isBlank()) {
                continue;
            }
            CodeSymbolEntity symbol = symbolsByQualifiedName.get(chunk.getSymbolName());
            if (symbol == null) {
                continue;
            }
            for (CodeRelationEntity relation : codeRelationJpaRepository.findByRepositoryIdAndSourceSymbolIdOrRepositoryIdAndTargetSymbolId(
                    repositoryId,
                    symbol.getId(),
                    repositoryId,
                    symbol.getId()
            )) {
                String relatedId = Objects.equals(relation.getSourceSymbolId(), symbol.getId())
                        ? relation.getTargetSymbolId()
                        : relation.getSourceSymbolId();
                CodeSymbolEntity related = relatedId == null ? null : symbolsById.get(relatedId);
                if (related != null) {
                    relatedSymbolNames.add(related.getQualifiedName());
                }
            }
        }
        if (relatedSymbolNames.isEmpty()) {
            return 0;
        }
        List<CodeChunkEntity> relatedChunks = codeChunkJpaRepository.findByRepositoryIdAndSymbolNameIn(repositoryId, List.copyOf(relatedSymbolNames));
        for (CodeChunkEntity chunk : relatedChunks) {
            MergedHit mergedHit = mergedHits.computeIfAbsent(chunk.getId(), MergedHit::new);
            mergedHit.sources.add(GRAPH_SOURCE);
            mergedHit.graphScore = Math.max(mergedHit.graphScore, 0.25D);
        }
        return relatedChunks.size();
    }

    private List<EvidenceResponse> buildEvidences(String repositoryId, Map<String, MergedHit> mergedHits, int topK) {
        if (mergedHits.isEmpty()) {
            return List.of();
        }
        List<MergedHit> rankedHits = mergedHits.values().stream()
                .sorted(Comparator.comparingDouble(MergedHit::score).reversed())
                .limit(topK)
                .toList();
        List<String> chunkIds = rankedHits.stream().map(hit -> hit.chunkId).toList();
        Map<String, CodeChunkEntity> chunksById = new LinkedHashMap<>();
        for (CodeChunkEntity chunk : codeChunkJpaRepository.findByRepositoryIdAndIdIn(repositoryId, chunkIds)) {
            chunksById.put(chunk.getId(), chunk);
        }

        java.util.concurrent.atomic.AtomicInteger rank = new java.util.concurrent.atomic.AtomicInteger(1);
        return rankedHits.stream()
                .map(hit -> toEvidence(repositoryId, hit, chunksById.get(hit.chunkId), rank.getAndIncrement()))
                .filter(java.util.Objects::nonNull)
                .toList();
    }

    private EvidenceResponse toEvidence(String repositoryId, MergedHit hit, CodeChunkEntity chunk, int rank) {
        if (chunk == null) {
            return null;
        }
        String source = hit.primarySource();
        return new EvidenceResponse(
                evidenceIdFactory.create(repositoryId, chunk.getId(), source, rank),
                chunk.getId(),
                repositoryId,
                chunk.getFilePath(),
                chunk.getStartLine(),
                chunk.getEndLine(),
                chunk.getSymbolName() == null ? "" : chunk.getSymbolName(),
                chunk.getSymbolType().name(),
                chunk.getLanguage(),
                source,
                List.copyOf(hit.sources),
                hit.score(),
                hit.bm25Score,
                hit.vectorScore,
                hit.graphScore,
                snippetBuilder.build(chunk.getContent()),
                parseMetadata(chunk.getMetadata())
        );
    }

    private Map<String, Object> parseMetadata(String metadata) {
        if (metadata == null || metadata.isBlank()) {
            return Collections.emptyMap();
        }
        try {
            return objectMapper.readValue(metadata, METADATA_TYPE);
        } catch (Exception ignored) {
            return Collections.emptyMap();
        }
    }

    private static class MergedHit {
        private final String chunkId;
        private final Set<String> sources = new LinkedHashSet<>();
        private double bm25Score;
        private double normalizedBm25Score;
        private double vectorScore;
        private double graphScore;

        private MergedHit(String chunkId) {
            this.chunkId = chunkId;
        }

        private double score() {
            return (0.55D * normalizedBm25Score) + (0.35D * vectorScore) + (0.10D * graphScore);
        }

        private String primarySource() {
            if (normalizedBm25Score >= vectorScore && normalizedBm25Score >= graphScore && sources.contains(BM25_SOURCE)) {
                return BM25_SOURCE;
            }
            if (vectorScore >= graphScore && sources.contains(VECTOR_SOURCE)) {
                return VECTOR_SOURCE;
            }
            if (sources.contains(GRAPH_SOURCE)) {
                return GRAPH_SOURCE;
            }
            return sources.stream().findFirst().orElse(BM25_SOURCE);
        }
    }
}
