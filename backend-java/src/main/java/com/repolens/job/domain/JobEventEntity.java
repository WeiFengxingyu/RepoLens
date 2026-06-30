package com.repolens.job.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.time.Instant;

@Entity
@Table(name = "job_events")
public class JobEventEntity {

    @Id
    @Column(length = 64)
    private String id;

    @Column(name = "job_id", nullable = false, length = 64)
    private String jobId;

    @Column(name = "attempt_id", length = 64)
    private String attemptId;

    @Column(name = "event_type", nullable = false, length = 64)
    private String eventType;

    @Column(columnDefinition = "text")
    private String message;

    @Column(name = "payload_json", columnDefinition = "text")
    private String payloadJson;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    protected JobEventEntity() {
    }

    public JobEventEntity(String id, String jobId, String attemptId, String eventType, String message, String payloadJson, Instant createdAt) {
        this.id = id;
        this.jobId = jobId;
        this.attemptId = attemptId;
        this.eventType = eventType;
        this.message = message;
        this.payloadJson = payloadJson;
        this.createdAt = createdAt;
    }

    public String getId() {
        return id;
    }

    public String getJobId() {
        return jobId;
    }

    public String getAttemptId() {
        return attemptId;
    }

    public String getEventType() {
        return eventType;
    }

    public String getMessage() {
        return message;
    }

    public String getPayloadJson() {
        return payloadJson;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }
}
