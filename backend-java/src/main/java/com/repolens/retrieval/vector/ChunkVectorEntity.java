package com.repolens.retrieval.vector;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.time.Instant;

@Entity
@Table(name = "vector_chunks")
public class ChunkVectorEntity {

    @Id
    @Column(length = 64)
    private String id;

    @Column(name = "repository_id", nullable = false, length = 64)
    private String repositoryId;

    @Column(name = "chunk_id", nullable = false, length = 64)
    private String chunkId;

    @Column(name = "embedding_model", nullable = false, length = 128)
    private String embeddingModel;

    @Column(nullable = false)
    private int dimensions;

    @Column(nullable = false, columnDefinition = "text")
    private String embedding;

    @Column(name = "content_hash", length = 128)
    private String contentHash;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    protected ChunkVectorEntity() {
    }

    public ChunkVectorEntity(
            String id,
            String repositoryId,
            String chunkId,
            String embeddingModel,
            int dimensions,
            String embedding,
            Instant createdAt
    ) {
        this.id = id;
        this.repositoryId = repositoryId;
        this.chunkId = chunkId;
        this.embeddingModel = embeddingModel;
        this.dimensions = dimensions;
        this.embedding = embedding;
        this.createdAt = createdAt;
    }

    public String getId() {
        return id;
    }

    public String getRepositoryId() {
        return repositoryId;
    }

    public String getChunkId() {
        return chunkId;
    }

    public String getEmbeddingModel() {
        return embeddingModel;
    }

    public int getDimensions() {
        return dimensions;
    }

    public String getEmbedding() {
        return embedding;
    }

    public String getContentHash() {
        return contentHash;
    }

    public void setContentHash(String contentHash) {
        this.contentHash = contentHash;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }
}
