package com.repolens.review.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.time.Instant;

@Entity
@Table(name = "review_tool_calls")
public class ReviewToolCallEntity {

    @Id
    @Column(length = 64)
    private String id;

    @Column(name = "task_id", nullable = false, length = 64)
    private String taskId;

    @Column(name = "repository_id", nullable = false, length = 64)
    private String repositoryId;

    @Column(name = "tool_name", nullable = false, length = 128)
    private String toolName;

    @Column(nullable = false, length = 32)
    private String status;

    @Column(name = "permission_decision", nullable = false, length = 32)
    private String permissionDecision;

    @Column(name = "input_summary", columnDefinition = "text")
    private String inputSummary;

    @Column(name = "output_summary", columnDefinition = "text")
    private String outputSummary;

    @Column(name = "latency_ms")
    private Long latencyMs;

    @Column(name = "error_message", columnDefinition = "text")
    private String errorMessage;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "completed_at")
    private Instant completedAt;

    protected ReviewToolCallEntity() {
    }

    public ReviewToolCallEntity(String id, String taskId, String repositoryId, String toolName, Instant createdAt) {
        this.id = id;
        this.taskId = taskId;
        this.repositoryId = repositoryId;
        this.toolName = toolName;
        this.status = "completed";
        this.permissionDecision = "allow";
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

    public String getToolName() {
        return toolName;
    }

    public String getStatus() {
        return status;
    }

    public String getPermissionDecision() {
        return permissionDecision;
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

    public Long getLatencyMs() {
        return latencyMs;
    }

    public void setLatencyMs(Long latencyMs) {
        this.latencyMs = latencyMs;
    }

    public String getErrorMessage() {
        return errorMessage;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }

    public Instant getCompletedAt() {
        return completedAt;
    }
}
