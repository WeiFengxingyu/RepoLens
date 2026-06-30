package com.repolens.reviewhub.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.time.Instant;

@Entity
@Table(name = "quota_buckets")
public class QuotaBucketEntity {

    @Id
    @Column(length = 64)
    private String id;

    @Column(name = "scope_type", nullable = false, length = 64)
    private String scopeType;

    @Column(name = "scope_id", nullable = false, length = 64)
    private String scopeId;

    @Column(name = "quota_type", nullable = false, length = 64)
    private String quotaType;

    @Column(name = "used_count", nullable = false)
    private int usedCount;

    @Column(name = "limit_count", nullable = false)
    private int limitCount;

    @Column(name = "window_start", nullable = false)
    private Instant windowStart;

    @Column(name = "window_end", nullable = false)
    private Instant windowEnd;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    protected QuotaBucketEntity() {
    }

    public QuotaBucketEntity(
            String id,
            String scopeType,
            String scopeId,
            String quotaType,
            int limitCount,
            Instant windowStart,
            Instant windowEnd,
            Instant now
    ) {
        this.id = id;
        this.scopeType = scopeType;
        this.scopeId = scopeId;
        this.quotaType = quotaType;
        this.usedCount = 0;
        this.limitCount = limitCount;
        this.windowStart = windowStart;
        this.windowEnd = windowEnd;
        this.createdAt = now;
        this.updatedAt = now;
    }

    public void consume(Instant now) {
        usedCount += 1;
        updatedAt = now;
    }

    public String getId() {
        return id;
    }

    public String getScopeType() {
        return scopeType;
    }

    public String getScopeId() {
        return scopeId;
    }

    public String getQuotaType() {
        return quotaType;
    }

    public int getUsedCount() {
        return usedCount;
    }

    public int getLimitCount() {
        return limitCount;
    }

    public Instant getWindowStart() {
        return windowStart;
    }

    public Instant getWindowEnd() {
        return windowEnd;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }

    public Instant getUpdatedAt() {
        return updatedAt;
    }
}
