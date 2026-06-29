package com.repolens.evaluation.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.time.Instant;

@Entity
@Table(name = "evaluation_results")
public class EvaluationResultEntity {

    @Id
    @Column(length = 64)
    private String id;

    @Column(name = "run_id", nullable = false, length = 64)
    private String runId;

    @Column(name = "sample_id", nullable = false, length = 128)
    private String sampleId;

    @Column(name = "sample_type", nullable = false, length = 64)
    private String sampleType;

    @Column(name = "repository_key", nullable = false, length = 128)
    private String repositoryKey;

    @Column(nullable = false, length = 64)
    private String strategy;

    @Column(name = "hit_at_5", nullable = false)
    private boolean hitAt5;

    @Column(nullable = false)
    private double mrr;

    @Column(name = "citation_coverage", nullable = false)
    private double citationCoverage;

    @Column(name = "latency_ms", nullable = false)
    private long latencyMs;

    @Column(name = "token_count", nullable = false)
    private int tokenCount;

    @Column(name = "token_estimated", nullable = false)
    private boolean tokenEstimated;

    @Column(name = "matched_files", columnDefinition = "text")
    private String matchedFiles;

    @Column(name = "matched_symbols", columnDefinition = "text")
    private String matchedSymbols;

    @Column(columnDefinition = "text")
    private String citations;

    @Column(name = "error_message", columnDefinition = "text")
    private String errorMessage;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    protected EvaluationResultEntity() {
    }

    public EvaluationResultEntity(
            String id,
            String runId,
            String sampleId,
            String sampleType,
            String repositoryKey,
            String strategy,
            boolean hitAt5,
            double mrr,
            double citationCoverage,
            long latencyMs,
            int tokenCount,
            boolean tokenEstimated,
            String matchedFiles,
            String matchedSymbols,
            String citations,
            String errorMessage,
            Instant createdAt
    ) {
        this.id = id;
        this.runId = runId;
        this.sampleId = sampleId;
        this.sampleType = sampleType;
        this.repositoryKey = repositoryKey;
        this.strategy = strategy;
        this.hitAt5 = hitAt5;
        this.mrr = mrr;
        this.citationCoverage = citationCoverage;
        this.latencyMs = latencyMs;
        this.tokenCount = tokenCount;
        this.tokenEstimated = tokenEstimated;
        this.matchedFiles = matchedFiles;
        this.matchedSymbols = matchedSymbols;
        this.citations = citations;
        this.errorMessage = errorMessage;
        this.createdAt = createdAt;
    }

    public String getId() {
        return id;
    }

    public String getRunId() {
        return runId;
    }

    public String getSampleId() {
        return sampleId;
    }

    public String getSampleType() {
        return sampleType;
    }

    public String getRepositoryKey() {
        return repositoryKey;
    }

    public String getStrategy() {
        return strategy;
    }

    public boolean isHitAt5() {
        return hitAt5;
    }

    public double getMrr() {
        return mrr;
    }

    public double getCitationCoverage() {
        return citationCoverage;
    }

    public long getLatencyMs() {
        return latencyMs;
    }

    public int getTokenCount() {
        return tokenCount;
    }

    public boolean isTokenEstimated() {
        return tokenEstimated;
    }

    public String getMatchedFiles() {
        return matchedFiles;
    }

    public String getMatchedSymbols() {
        return matchedSymbols;
    }

    public String getCitations() {
        return citations;
    }

    public String getErrorMessage() {
        return errorMessage;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }
}
