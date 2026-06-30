package com.repolens.reviewhub.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.time.Instant;

@Entity
@Table(name = "audit_logs")
public class AuditLogEntity {

    @Id
    @Column(length = 64)
    private String id;

    @Column(length = 128)
    private String actor;

    @Column(nullable = false, length = 128)
    private String action;

    @Column(name = "scope_type", nullable = false, length = 64)
    private String scopeType;

    @Column(name = "scope_id", nullable = false, length = 64)
    private String scopeId;

    @Column(columnDefinition = "text")
    private String message;

    @Column(name = "payload_json", columnDefinition = "text")
    private String payloadJson;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    protected AuditLogEntity() {
    }

    public AuditLogEntity(
            String id,
            String actor,
            String action,
            String scopeType,
            String scopeId,
            String message,
            String payloadJson,
            Instant createdAt
    ) {
        this.id = id;
        this.actor = actor;
        this.action = action;
        this.scopeType = scopeType;
        this.scopeId = scopeId;
        this.message = message;
        this.payloadJson = payloadJson;
        this.createdAt = createdAt;
    }

    public String getId() {
        return id;
    }

    public String getActor() {
        return actor;
    }

    public String getAction() {
        return action;
    }

    public String getScopeType() {
        return scopeType;
    }

    public String getScopeId() {
        return scopeId;
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
