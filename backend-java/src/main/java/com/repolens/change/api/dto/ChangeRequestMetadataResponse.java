package com.repolens.change.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.repolens.change.domain.ChangeRequestEntity;

import java.time.Instant;
import java.util.Map;

public record ChangeRequestMetadataResponse(
        String id,
        @JsonProperty("repository_id")
        String repositoryId,
        @JsonProperty("task_id")
        String taskId,
        String platform,
        @JsonProperty("change_type")
        String changeType,
        String owner,
        String repo,
        String number,
        String url,
        String title,
        String author,
        @JsonProperty("source_branch")
        String sourceBranch,
        @JsonProperty("target_branch")
        String targetBranch,
        String state,
        @JsonProperty("changed_file_count")
        int changedFileCount,
        @JsonProperty("addition_count")
        int additionCount,
        @JsonProperty("deletion_count")
        int deletionCount,
        @JsonProperty("commit_count")
        int commitCount,
        @JsonProperty("provider_status")
        String providerStatus,
        @JsonProperty("diff_hash")
        String diffHash,
        @JsonProperty("metadata")
        Map<String, Object> metadata,
        @JsonProperty("error_message")
        String errorMessage,
        @JsonProperty("created_at")
        Instant createdAt,
        @JsonProperty("updated_at")
        Instant updatedAt
) {
    private static final TypeReference<Map<String, Object>> MAP = new TypeReference<>() {
    };

    public static ChangeRequestMetadataResponse from(ChangeRequestEntity entity, ObjectMapper objectMapper) {
        return new ChangeRequestMetadataResponse(
                entity.getId(),
                entity.getRepositoryId(),
                entity.getReviewTaskId(),
                entity.getPlatform(),
                entity.getChangeType(),
                entity.getOwnerName(),
                entity.getRepositoryName(),
                entity.getChangeNumber(),
                entity.getUrl(),
                entity.getTitle(),
                entity.getAuthor(),
                entity.getSourceBranch(),
                entity.getTargetBranch(),
                entity.getState(),
                entity.getChangedFileCount(),
                entity.getAdditionCount(),
                entity.getDeletionCount(),
                entity.getCommitCount(),
                entity.getProviderStatus(),
                entity.getDiffHash(),
                readMetadata(entity.getMetadataJson(), objectMapper),
                entity.getErrorMessage(),
                entity.getCreatedAt(),
                entity.getUpdatedAt()
        );
    }

    private static Map<String, Object> readMetadata(String value, ObjectMapper objectMapper) {
        if (value == null || value.isBlank()) {
            return Map.of();
        }
        try {
            return objectMapper.readValue(value, MAP);
        } catch (Exception exception) {
            return Map.of("parse_error", "metadata unavailable");
        }
    }
}
