package com.repolens.reviewhub.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.repolens.reviewhub.domain.RepositoryBindingEntity;

import java.time.Instant;

public record RepositoryBindingResponse(
        String id,
        @JsonProperty("project_id")
        String projectId,
        @JsonProperty("repository_id")
        String repositoryId,
        String provider,
        @JsonProperty("external_repo_id")
        String externalRepoId,
        boolean enabled,
        @JsonProperty("created_at")
        Instant createdAt,
        @JsonProperty("updated_at")
        Instant updatedAt
) {
    public static RepositoryBindingResponse from(RepositoryBindingEntity entity) {
        return new RepositoryBindingResponse(
                entity.getId(),
                entity.getProjectId(),
                entity.getRepositoryId(),
                entity.getProvider(),
                entity.getExternalRepoId(),
                entity.isEnabled(),
                entity.getCreatedAt(),
                entity.getUpdatedAt()
        );
    }
}
