package com.repolens.job.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.time.Instant;

@Entity
@Table(name = "job_attempts")
public class JobAttemptEntity {

    @Id
    @Column(length = 64)
    private String id;

    @Column(name = "job_id", nullable = false, length = 64)
    private String jobId;

    @Column(name = "attempt_no", nullable = false)
    private int attemptNo;

    @Column(name = "worker_id", nullable = false, length = 128)
    private String workerId;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 64)
    private JobAttemptStatus status;

    @Column(name = "started_at", nullable = false)
    private Instant startedAt;

    @Column(name = "heartbeat_at")
    private Instant heartbeatAt;

    @Column(name = "finished_at")
    private Instant finishedAt;

    @Column(name = "error_code", length = 128)
    private String errorCode;

    @Column(name = "error_message", columnDefinition = "text")
    private String errorMessage;

    protected JobAttemptEntity() {
    }

    public JobAttemptEntity(String id, String jobId, int attemptNo, String workerId, Instant now) {
        this.id = id;
        this.jobId = jobId;
        this.attemptNo = attemptNo;
        this.workerId = workerId;
        this.status = JobAttemptStatus.RUNNING;
        this.startedAt = now;
        this.heartbeatAt = now;
    }

    public String getId() {
        return id;
    }

    public String getJobId() {
        return jobId;
    }

    public int getAttemptNo() {
        return attemptNo;
    }

    public String getWorkerId() {
        return workerId;
    }

    public JobAttemptStatus getStatus() {
        return status;
    }

    public void setStatus(JobAttemptStatus status) {
        this.status = status;
    }

    public Instant getStartedAt() {
        return startedAt;
    }

    public Instant getHeartbeatAt() {
        return heartbeatAt;
    }

    public void setHeartbeatAt(Instant heartbeatAt) {
        this.heartbeatAt = heartbeatAt;
    }

    public Instant getFinishedAt() {
        return finishedAt;
    }

    public void setFinishedAt(Instant finishedAt) {
        this.finishedAt = finishedAt;
    }

    public String getErrorCode() {
        return errorCode;
    }

    public void setErrorCode(String errorCode) {
        this.errorCode = errorCode;
    }

    public String getErrorMessage() {
        return errorMessage;
    }

    public void setErrorMessage(String errorMessage) {
        this.errorMessage = errorMessage;
    }
}
