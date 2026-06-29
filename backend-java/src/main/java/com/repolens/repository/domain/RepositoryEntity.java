package com.repolens.repository.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.time.Instant;

@Entity
@Table(name = "repositories")
public class RepositoryEntity {

    @Id
    @Column(length = 64)
    private String id;

    @Column(nullable = false)
    private String name;

    @Enumerated(EnumType.STRING)
    @Column(name = "source_type", nullable = false, length = 32)
    private RepositorySourceType sourceType;

    @Column(name = "source_url", length = 1024)
    private String sourceUrl;

    @Column(name = "local_path", length = 1024)
    private String localPath;

    @Column(name = "branch_name")
    private String branchName;

    @Column(name = "commit_hash")
    private String commitHash;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 64)
    private RepositoryStatus status;

    @Column(name = "file_count", nullable = false)
    private int fileCount;

    @Column(name = "parsed_file_count", nullable = false)
    private int parsedFileCount;

    @Column(name = "chunk_count", nullable = false)
    private int chunkCount;

    @Column(name = "relation_count", nullable = false)
    private int relationCount;

    @Column(name = "skipped_file_count", nullable = false)
    private int skippedFileCount;

    @Column(name = "language_summary", columnDefinition = "text")
    private String languageSummary;

    @Column(name = "last_error", columnDefinition = "text")
    private String lastError;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    @Column(name = "indexed_at")
    private Instant indexedAt;

    protected RepositoryEntity() {
    }

    public RepositoryEntity(String id, String name, RepositorySourceType sourceType, RepositoryStatus status, Instant now) {
        this.id = id;
        this.name = name;
        this.sourceType = sourceType;
        this.status = status;
        this.createdAt = now;
        this.updatedAt = now;
    }

    public String getId() {
        return id;
    }

    public String getName() {
        return name;
    }

    public RepositorySourceType getSourceType() {
        return sourceType;
    }

    public String getSourceUrl() {
        return sourceUrl;
    }

    public void setSourceUrl(String sourceUrl) {
        this.sourceUrl = sourceUrl;
    }

    public String getLocalPath() {
        return localPath;
    }

    public void setLocalPath(String localPath) {
        this.localPath = localPath;
    }

    public String getBranchName() {
        return branchName;
    }

    public void setBranchName(String branchName) {
        this.branchName = branchName;
    }

    public String getCommitHash() {
        return commitHash;
    }

    public void setCommitHash(String commitHash) {
        this.commitHash = commitHash;
    }

    public RepositoryStatus getStatus() {
        return status;
    }

    public void setStatus(RepositoryStatus status) {
        this.status = status;
    }

    public int getFileCount() {
        return fileCount;
    }

    public void setFileCount(int fileCount) {
        this.fileCount = fileCount;
    }

    public int getParsedFileCount() {
        return parsedFileCount;
    }

    public void setParsedFileCount(int parsedFileCount) {
        this.parsedFileCount = parsedFileCount;
    }

    public int getChunkCount() {
        return chunkCount;
    }

    public void setChunkCount(int chunkCount) {
        this.chunkCount = chunkCount;
    }

    public int getRelationCount() {
        return relationCount;
    }

    public void setRelationCount(int relationCount) {
        this.relationCount = relationCount;
    }

    public int getSkippedFileCount() {
        return skippedFileCount;
    }

    public void setSkippedFileCount(int skippedFileCount) {
        this.skippedFileCount = skippedFileCount;
    }

    public String getLanguageSummary() {
        return languageSummary;
    }

    public void setLanguageSummary(String languageSummary) {
        this.languageSummary = languageSummary;
    }

    public String getLastError() {
        return lastError;
    }

    public void setLastError(String lastError) {
        this.lastError = lastError;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }

    public Instant getUpdatedAt() {
        return updatedAt;
    }

    public void setUpdatedAt(Instant updatedAt) {
        this.updatedAt = updatedAt;
    }

    public Instant getIndexedAt() {
        return indexedAt;
    }

    public void setIndexedAt(Instant indexedAt) {
        this.indexedAt = indexedAt;
    }
}
