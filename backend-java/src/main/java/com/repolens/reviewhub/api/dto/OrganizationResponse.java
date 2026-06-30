package com.repolens.reviewhub.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.repolens.reviewhub.domain.OrganizationEntity;

import java.time.Instant;

public record OrganizationResponse(
        String id,
        String name,
        @JsonProperty("plan_name")
        String planName,
        String status,
        @JsonProperty("created_at")
        Instant createdAt,
        @JsonProperty("updated_at")
        Instant updatedAt
) {
    public static OrganizationResponse from(OrganizationEntity entity) {
        return new OrganizationResponse(
                entity.getId(),
                entity.getName(),
                entity.getPlanName(),
                entity.getStatus(),
                entity.getCreatedAt(),
                entity.getUpdatedAt()
        );
    }
}
