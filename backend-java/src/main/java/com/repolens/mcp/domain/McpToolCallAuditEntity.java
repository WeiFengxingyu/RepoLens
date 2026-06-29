package com.repolens.mcp.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.time.Instant;

@Entity
@Table(name = "mcp_tool_call_audits")
public class McpToolCallAuditEntity {

    @Id
    @Column(length = 64)
    private String id;

    @Column(name = "task_id", nullable = false, length = 64)
    private String taskId;

    @Column(name = "repository_id", length = 64)
    private String repositoryId;

    @Column(name = "tool_name", nullable = false, length = 128)
    private String toolName;

    @Column(nullable = false, length = 32)
    private String status;

    @Column(name = "permission_decision", nullable = false, length = 32)
    private String permissionDecision;

    @Column(name = "permission_policy", length = 128)
    private String permissionPolicy;

    @Column(name = "client_name", length = 128)
    private String clientName;

    @Column(name = "client_session_id", length = 128)
    private String clientSessionId;

    @Column(name = "input_hash", length = 128)
    private String inputHash;

    @Column(name = "output_hash", length = 128)
    private String outputHash;

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

    protected McpToolCallAuditEntity() {
    }

    public McpToolCallAuditEntity(
            String id,
            String taskId,
            String repositoryId,
            String toolName,
            String status,
            String permissionDecision,
            String permissionPolicy,
            String clientName,
            String clientSessionId,
            String inputHash,
            String outputHash,
            String inputSummary,
            String outputSummary,
            Long latencyMs,
            String errorMessage,
            Instant createdAt,
            Instant completedAt
    ) {
        this.id = id;
        this.taskId = taskId;
        this.repositoryId = repositoryId;
        this.toolName = toolName;
        this.status = status;
        this.permissionDecision = permissionDecision;
        this.permissionPolicy = permissionPolicy;
        this.clientName = clientName;
        this.clientSessionId = clientSessionId;
        this.inputHash = inputHash;
        this.outputHash = outputHash;
        this.inputSummary = inputSummary;
        this.outputSummary = outputSummary;
        this.latencyMs = latencyMs;
        this.errorMessage = errorMessage;
        this.createdAt = createdAt;
        this.completedAt = completedAt;
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

    public String getPermissionPolicy() {
        return permissionPolicy;
    }

    public String getClientName() {
        return clientName;
    }

    public String getClientSessionId() {
        return clientSessionId;
    }

    public String getInputHash() {
        return inputHash;
    }

    public String getOutputHash() {
        return outputHash;
    }

    public String getInputSummary() {
        return inputSummary;
    }

    public String getOutputSummary() {
        return outputSummary;
    }

    public Long getLatencyMs() {
        return latencyMs;
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
