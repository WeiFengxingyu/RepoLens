package com.repolens.evaluation.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.time.Instant;

@Entity
@Table(name = "evaluation_runs")
public class EvaluationRunEntity {

    @Id
    @Column(length = 64)
    private String id;

    @Column(nullable = false, length = 256)
    private String name;

    @Column(name = "dataset_path", nullable = false, length = 1024)
    private String datasetPath;

    @Column(nullable = false, length = 64)
    private String strategy;

    @Column(nullable = false, length = 32)
    private String status;

    @Column(name = "sample_count", nullable = false)
    private int sampleCount;

    @Column(name = "repository_map", nullable = false, columnDefinition = "text")
    private String repositoryMap;

    @Column(columnDefinition = "text")
    private String metrics;

    @Column(columnDefinition = "text")
    private String warnings;

    @Column(name = "error_message", columnDefinition = "text")
    private String errorMessage;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "started_at")
    private Instant startedAt;

    @Column(name = "completed_at")
    private Instant completedAt;

    protected EvaluationRunEntity() {
    }

    public EvaluationRunEntity(
            String id,
            String name,
            String datasetPath,
            String strategy,
            int sampleCount,
            String repositoryMap,
            Instant createdAt
    ) {
        this.id = id;
        this.name = name;
        this.datasetPath = datasetPath;
        this.strategy = strategy;
        this.status = "running";
        this.sampleCount = sampleCount;
        this.repositoryMap = repositoryMap;
        this.createdAt = createdAt;
        this.startedAt = createdAt;
    }

    public String getId() {
        return id;
    }

    public String getName() {
        return name;
    }

    public String getDatasetPath() {
        return datasetPath;
    }

    public String getStrategy() {
        return strategy;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public int getSampleCount() {
        return sampleCount;
    }

    public String getRepositoryMap() {
        return repositoryMap;
    }

    public String getMetrics() {
        return metrics;
    }

    public void setMetrics(String metrics) {
        this.metrics = metrics;
    }

    public String getWarnings() {
        return warnings;
    }

    public void setWarnings(String warnings) {
        this.warnings = warnings;
    }

    public String getErrorMessage() {
        return errorMessage;
    }

    public void setErrorMessage(String errorMessage) {
        this.errorMessage = errorMessage;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }

    public Instant getStartedAt() {
        return startedAt;
    }

    public Instant getCompletedAt() {
        return completedAt;
    }

    public void setCompletedAt(Instant completedAt) {
        this.completedAt = completedAt;
    }
}
