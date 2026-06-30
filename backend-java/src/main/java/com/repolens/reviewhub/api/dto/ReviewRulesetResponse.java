package com.repolens.reviewhub.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.repolens.reviewhub.domain.ReviewRulesetEntity;

import java.time.Instant;
import java.util.Map;

public record ReviewRulesetResponse(
        String id,
        @JsonProperty("project_id")
        String projectId,
        String name,
        Map<String, Object> rules,
        boolean enabled,
        @JsonProperty("created_at")
        Instant createdAt,
        @JsonProperty("updated_at")
        Instant updatedAt
) {
    private static final TypeReference<Map<String, Object>> MAP_TYPE = new TypeReference<>() {
    };

    public static ReviewRulesetResponse from(ReviewRulesetEntity entity, ObjectMapper objectMapper) {
        return new ReviewRulesetResponse(
                entity.getId(),
                entity.getProjectId(),
                entity.getName(),
                readRules(entity.getRulesJson(), objectMapper),
                entity.isEnabled(),
                entity.getCreatedAt(),
                entity.getUpdatedAt()
        );
    }

    private static Map<String, Object> readRules(String rulesJson, ObjectMapper objectMapper) {
        try {
            return objectMapper.readValue(rulesJson, MAP_TYPE);
        } catch (Exception exception) {
            return Map.of("parse_error", "rules unavailable");
        }
    }
}
