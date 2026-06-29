package com.repolens.indexing.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.time.Instant;

@Entity
@Table(name = "index_task_events")
public class IndexTaskEventEntity {

    @Id
    @Column(length = 64)
    private String id;

    @Column(name = "task_id", nullable = false, length = 64)
    private String taskId;

    @Column(name = "repository_id", nullable = false, length = 64)
    private String repositoryId;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 64)
    private IndexTaskStatus stage;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 32)
    private IndexTaskEventStatus status;

    @Column(columnDefinition = "text")
    private String message;

    @Column(name = "file_count", nullable = false)
    private int fileCount;

    @Column(name = "parsed_file_count", nullable = false)
    private int parsedFileCount;

    @Column(name = "chunk_count", nullable = false)
    private int chunkCount;

    @Column(name = "symbol_count", nullable = false)
    private int symbolCount;

    @Column(name = "relation_count", nullable = false)
    private int relationCount;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    protected IndexTaskEventEntity() {
    }

    public IndexTaskEventEntity(
            String id,
            String taskId,
            String repositoryId,
            IndexTaskStatus stage,
            IndexTaskEventStatus status,
            Instant createdAt
    ) {
        this.id = id;
        this.taskId = taskId;
        this.repositoryId = repositoryId;
        this.stage = stage;
        this.status = status;
        this.createdAt = createdAt;
    }

    public String getId() {
        return id;
    }

    public String getTaskId() {
        return taskId;
    }

    public String getRepositoryId() {
        return repositoryId;
    }

    public IndexTaskStatus getStage() {
        return stage;
    }

    public IndexTaskEventStatus getStatus() {
        return status;
    }

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
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

    public int getSymbolCount() {
        return symbolCount;
    }

    public void setSymbolCount(int symbolCount) {
        this.symbolCount = symbolCount;
    }

    public int getRelationCount() {
        return relationCount;
    }

    public void setRelationCount(int relationCount) {
        this.relationCount = relationCount;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }
}
