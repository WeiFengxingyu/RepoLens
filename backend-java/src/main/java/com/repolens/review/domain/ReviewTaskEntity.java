package com.repolens.review.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.time.Instant;

@Entity
@Table(name = "review_tasks")
public class ReviewTaskEntity {

    @Id
    @Column(length = 64)
    private String id;

    @Column(name = "repository_id", nullable = false, length = 64)
    private String repositoryId;

    @Column(nullable = false, length = 32)
    private String status;

    @Column(name = "diff_text", nullable = false, columnDefinition = "text")
    private String diffText;

    @Column(columnDefinition = "text")
    private String summary;

    @Column(name = "risk_level", length = 32)
    private String riskLevel;

    @Column(columnDefinition = "text")
    private String risks;

    @Column(name = "impacted_symbols", columnDefinition = "text")
    private String impactedSymbols;

    @Column(name = "suggested_tests", columnDefinition = "text")
    private String suggestedTests;

    @Column(columnDefinition = "text")
    private String citations;

    @Column(columnDefinition = "text")
    private String markdown;

    @Column(name = "error_message", columnDefinition = "text")
    private String errorMessage;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "completed_at")
    private Instant completedAt;

    protected ReviewTaskEntity() {
    }

    public ReviewTaskEntity(String id, String repositoryId, String diffText, Instant createdAt) {
        this.id = id;
        this.repositoryId = repositoryId;
        this.diffText = diffText;
        this.status = "running";
        this.createdAt = createdAt;
    }

    public String getId() {
        return id;
    }

    public String getRepositoryId() {
        return repositoryId;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public String getDiffText() {
        return diffText;
    }

    public String getSummary() {
        return summary;
    }

    public void setSummary(String summary) {
        this.summary = summary;
    }

    public String getRiskLevel() {
        return riskLevel;
    }

    public void setRiskLevel(String riskLevel) {
        this.riskLevel = riskLevel;
    }

    public String getRisks() {
        return risks;
    }

    public void setRisks(String risks) {
        this.risks = risks;
    }

    public String getImpactedSymbols() {
        return impactedSymbols;
    }

    public void setImpactedSymbols(String impactedSymbols) {
        this.impactedSymbols = impactedSymbols;
    }

    public String getSuggestedTests() {
        return suggestedTests;
    }

    public void setSuggestedTests(String suggestedTests) {
        this.suggestedTests = suggestedTests;
    }

    public String getCitations() {
        return citations;
    }

    public void setCitations(String citations) {
        this.citations = citations;
    }

    public String getMarkdown() {
        return markdown;
    }

    public void setMarkdown(String markdown) {
        this.markdown = markdown;
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

    public Instant getCompletedAt() {
        return completedAt;
    }

    public void setCompletedAt(Instant completedAt) {
        this.completedAt = completedAt;
    }
}
