package com.repolens.retrieval.vector;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Comparator;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;

@Service
public class VectorSearchService {

    private final ChunkVectorJpaRepository chunkVectorJpaRepository;
    private final EmbeddingProvider embeddingProvider;

    public VectorSearchService(
            ChunkVectorJpaRepository chunkVectorJpaRepository,
            EmbeddingProvider embeddingProvider
    ) {
        this.chunkVectorJpaRepository = chunkVectorJpaRepository;
        this.embeddingProvider = embeddingProvider;
    }

    @Transactional(readOnly = true)
    public List<VectorSearchHit> search(String repositoryId, String query, int topK) {
        double[] queryVector = embeddingProvider.embed(query);
        AtomicInteger rank = new AtomicInteger(1);
        return chunkVectorJpaRepository.findByRepositoryId(repositoryId).stream()
                .map(vector -> new ScoredVector(vector.getChunkId(), VectorMath.cosine(queryVector, VectorSerialization.deserialize(vector.getEmbedding()))))
                .filter(vector -> vector.score() > 0.0D)
                .sorted(Comparator.comparingDouble(ScoredVector::score).reversed())
                .limit(topK)
                .map(vector -> new VectorSearchHit(vector.chunkId(), vector.score(), rank.getAndIncrement()))
                .toList();
    }

    private record ScoredVector(String chunkId, double score) {
    }
}
