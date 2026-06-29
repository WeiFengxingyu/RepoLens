package com.repolens.agent.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.time.Instant;

@Entity
@Table(name = "agent_traces")
public class AgentTraceEntity {

    @Id
    @Column(length = 64)
    private String id;

    @Column(name = "task_id", nullable = false, length = 64)
    private String taskId;

    @Column(name = "repository_id", nullable = false, length = 64)
    private String repositoryId;

    @Column(name = "step_name", nullable = false, length = 128)
    private String stepName;

    @Column(name = "step_order", nullable = false)
    private int stepOrder;

    @Column(nullable = false, length = 32)
    private String status;

    @Column(name = "input_summary", columnDefinition = "text")
    private String inputSummary;

    @Column(name = "output_summary", columnDefinition = "text")
    private String outputSummary;

    @Column(name = "evidence_ids", columnDefinition = "text")
    private String evidenceIds;

    @Column(name = "tool_calls", columnDefinition = "text")
    private String toolCalls;

    @Column(name = "token_usage", columnDefinition = "text")
    private String tokenUsage;

    @Column(name = "latency_ms")
    private Long latencyMs;

    @Column(name = "error_message", columnDefinition = "text")
    private String errorMessage;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "completed_at")
    private Instant completedAt;

    protected AgentTraceEntity() {
    }

    public AgentTraceEntity(String id, String taskId, String repositoryId, String stepName, int stepOrder, Instant createdAt) {
        this.id = id;
        this.taskId = taskId;
        this.repositoryId = repositoryId;
        this.stepName = stepName;
        this.stepOrder = stepOrder;
        this.status = "completed";
        this.createdAt = createdAt;
        this.completedAt = createdAt;
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

    public String getStepName() {
        return stepName;
    }

    public int getStepOrder() {
        return stepOrder;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public String getInputSummary() {
        return inputSummary;
    }

    public void setInputSummary(String inputSummary) {
        this.inputSummary = inputSummary;
    }

    public String getOutputSummary() {
        return outputSummary;
    }

    public void setOutputSummary(String outputSummary) {
        this.outputSummary = outputSummary;
    }

    public String getEvidenceIds() {
        return evidenceIds;
    }

    public void setEvidenceIds(String evidenceIds) {
        this.evidenceIds = evidenceIds;
    }

    public String getToolCalls() {
        return toolCalls;
    }

    public void setToolCalls(String toolCalls) {
        this.toolCalls = toolCalls;
    }

    public String getTokenUsage() {
        return tokenUsage;
    }

    public void setTokenUsage(String tokenUsage) {
        this.tokenUsage = tokenUsage;
    }

    public Long getLatencyMs() {
        return latencyMs;
    }

    public void setLatencyMs(Long latencyMs) {
        this.latencyMs = latencyMs;
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
