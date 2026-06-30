package com.repolens.job.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.time.Instant;

@Entity
@Table(name = "dead_letter_jobs")
public class DeadLetterJobEntity {

    @Id
    @Column(name = "job_id", length = 64)
    private String jobId;

    @Column(nullable = false, length = 128)
    private String reason;

    @Column(name = "final_error", columnDefinition = "text")
    private String finalError;

    @Column(name = "attempt_count", nullable = false)
    private int attemptCount;

    @Column(name = "payload_json", columnDefinition = "text")
    private String payloadJson;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    protected DeadLetterJobEntity() {
    }

    public DeadLetterJobEntity(String jobId, String reason, String finalError, int attemptCount, String payloadJson, Instant createdAt) {
        this.jobId = jobId;
        this.reason = reason;
        this.finalError = finalError;
        this.attemptCount = attemptCount;
        this.payloadJson = payloadJson;
        this.createdAt = createdAt;
    }

    public String getJobId() {
        return jobId;
    }

    public String getReason() {
        return reason;
    }

    public String getFinalError() {
        return finalError;
    }

    public int getAttemptCount() {
        return attemptCount;
    }

    public String getPayloadJson() {
        return payloadJson;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }
}
