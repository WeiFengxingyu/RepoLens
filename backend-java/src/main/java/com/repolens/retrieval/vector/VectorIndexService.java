package com.repolens.retrieval.vector;

import com.repolens.chunking.domain.CodeChunkEntity;
import com.repolens.common.id.IdGenerator;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Clock;
import java.time.Instant;
import java.util.List;

@Service
public class VectorIndexService {

    private final ChunkVectorJpaRepository chunkVectorJpaRepository;
    private final EmbeddingProvider embeddingProvider;
    private final IdGenerator idGenerator;
    private final Clock clock;

    public VectorIndexService(
            ChunkVectorJpaRepository chunkVectorJpaRepository,
            EmbeddingProvider embeddingProvider,
            IdGenerator idGenerator,
            Clock clock
    ) {
        this.chunkVectorJpaRepository = chunkVectorJpaRepository;
        this.embeddingProvider = embeddingProvider;
        this.idGenerator = idGenerator;
        this.clock = clock;
    }

    @Transactional
    public int rebuild(String repositoryId, List<CodeChunkEntity> chunks) {
        chunkVectorJpaRepository.deleteByRepositoryId(repositoryId);
        Instant now = Instant.now(clock);
        List<ChunkVectorEntity> vectors = chunks.stream()
                .map(chunk -> toVector(repositoryId, chunk, now))
                .toList();
        chunkVectorJpaRepository.saveAll(vectors);
        return vectors.size();
    }

    private ChunkVectorEntity toVector(String repositoryId, CodeChunkEntity chunk, Instant now) {
        double[] embedding = embeddingProvider.embed(chunk.getContent());
        ChunkVectorEntity entity = new ChunkVectorEntity(
                idGenerator.newId("vec"),
                repositoryId,
                chunk.getId(),
                embeddingProvider.modelName(),
                embeddingProvider.dimensions(),
                VectorSerialization.serialize(embedding),
                now
        );
        entity.setContentHash(chunk.getContentHash());
        return entity;
    }
}
