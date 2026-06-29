package com.repolens.repository.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.time.Instant;

@Entity
@Table(name = "repository_files")
public class RepositoryFileEntity {

    @Id
    @Column(length = 64)
    private String id;

    @Column(name = "repository_id", nullable = false, length = 64)
    private String repositoryId;

    @Column(name = "relative_path", nullable = false, length = 1024)
    private String relativePath;

    @Column(nullable = false, length = 64)
    private String language;

    @Column(name = "size_bytes", nullable = false)
    private long sizeBytes;

    @Column(name = "content_hash", length = 128)
    private String contentHash;

    @Column(nullable = false)
    private boolean skipped;

    @Column(name = "skip_reason")
    private String skipReason;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    protected RepositoryFileEntity() {
    }

    public RepositoryFileEntity(
            String id,
            String repositoryId,
            String relativePath,
            String language,
            long sizeBytes,
            Instant createdAt
    ) {
        this.id = id;
        this.repositoryId = repositoryId;
        this.relativePath = relativePath;
        this.language = language;
        this.sizeBytes = sizeBytes;
        this.createdAt = createdAt;
    }

    public String getId() {
        return id;
    }

    public String getRepositoryId() {
        return repositoryId;
    }

    public String getRelativePath() {
        return relativePath;
    }

    public String getLanguage() {
        return language;
    }

    public long getSizeBytes() {
        return sizeBytes;
    }

    public String getContentHash() {
        return contentHash;
    }

    public void setContentHash(String contentHash) {
        this.contentHash = contentHash;
    }

    public boolean isSkipped() {
        return skipped;
    }

    public void setSkipped(boolean skipped) {
        this.skipped = skipped;
    }

    public String getSkipReason() {
        return skipReason;
    }

    public void setSkipReason(String skipReason) {
        this.skipReason = skipReason;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }
}
