package com.repolens.reviewhub.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.repolens.reviewhub.domain.QuotaBucketEntity;

import java.time.Instant;

public record QuotaBucketResponse(
        String id,
        @JsonProperty("scope_type")
        String scopeType,
        @JsonProperty("scope_id")
        String scopeId,
        @JsonProperty("quota_type")
        String quotaType,
        @JsonProperty("used_count")
        int usedCount,
        @JsonProperty("limit_count")
        int limitCount,
        @JsonProperty("window_start")
        Instant windowStart,
        @JsonProperty("window_end")
        Instant windowEnd,
        @JsonProperty("created_at")
        Instant createdAt,
        @JsonProperty("updated_at")
        Instant updatedAt
) {
    public static QuotaBucketResponse from(QuotaBucketEntity entity) {
        return new QuotaBucketResponse(
                entity.getId(),
                entity.getScopeType(),
                entity.getScopeId(),
                entity.getQuotaType(),
                entity.getUsedCount(),
                entity.getLimitCount(),
                entity.getWindowStart(),
                entity.getWindowEnd(),
                entity.getCreatedAt(),
                entity.getUpdatedAt()
        );
    }
}
