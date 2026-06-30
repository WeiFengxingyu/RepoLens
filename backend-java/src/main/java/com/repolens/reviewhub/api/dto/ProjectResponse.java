package com.repolens.reviewhub.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.repolens.reviewhub.domain.ProjectEntity;

import java.time.Instant;

public record ProjectResponse(
        String id,
        @JsonProperty("organization_id")
        String organizationId,
        String name,
        String status,
        @JsonProperty("created_at")
        Instant createdAt,
        @JsonProperty("updated_at")
        Instant updatedAt
) {
    public static ProjectResponse from(ProjectEntity entity) {
        return new ProjectResponse(
                entity.getId(),
                entity.getOrganizationId(),
                entity.getName(),
                entity.getStatus(),
                entity.getCreatedAt(),
                entity.getUpdatedAt()
        );
    }
}
