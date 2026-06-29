package com.repolens.indexing.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.time.Instant;

@Entity
@Table(name = "index_tasks")
public class IndexTaskEntity {

    @Id
    @Column(length = 64)
    private String id;

    @Column(name = "repository_id", nullable = false, length = 64)
    private String repositoryId;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 64)
    private IndexTaskStatus status;

    @Column(name = "current_stage", nullable = false, length = 64)
    private String currentStage;

    @Column(name = "progress_percent", nullable = false)
    private int progressPercent;

    @Column(name = "last_error", columnDefinition = "text")
    private String lastError;

    @Column(name = "started_at")
    private Instant startedAt;

    @Column(name = "finished_at")
    private Instant finishedAt;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    protected IndexTaskEntity() {
    }

    public IndexTaskEntity(String id, String repositoryId, Instant now) {
        this.id = id;
        this.repositoryId = repositoryId;
        this.status = IndexTaskStatus.CREATED;
        this.currentStage = IndexTaskStatus.CREATED.name();
        this.createdAt = now;
        this.updatedAt = now;
    }

    public String getId() {
        return id;
    }

    public String getRepositoryId() {
        return repositoryId;
    }

    public IndexTaskStatus getStatus() {
        return status;
    }

    public void setStatus(IndexTaskStatus status) {
        this.status = status;
        this.currentStage = status.name();
    }

    public String getCurrentStage() {
        return currentStage;
    }

    public int getProgressPercent() {
        return progressPercent;
    }

    public void setProgressPercent(int progressPercent) {
        this.progressPercent = progressPercent;
    }

    public String getLastError() {
        return lastError;
    }

    public void setLastError(String lastError) {
        this.lastError = lastError;
    }

    public Instant getStartedAt() {
        return startedAt;
    }

    public void setStartedAt(Instant startedAt) {
        this.startedAt = startedAt;
    }

    public Instant getFinishedAt() {
        return finishedAt;
    }

    public void setFinishedAt(Instant finishedAt) {
        this.finishedAt = finishedAt;
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
}
