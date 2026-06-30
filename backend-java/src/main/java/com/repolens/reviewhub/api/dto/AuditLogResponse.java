package com.repolens.reviewhub.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.repolens.reviewhub.domain.AuditLogEntity;

import java.time.Instant;
import java.util.Map;

public record AuditLogResponse(
        String id,
        String actor,
        String action,
        @JsonProperty("scope_type")
        String scopeType,
        @JsonProperty("scope_id")
        String scopeId,
        String message,
        @JsonProperty("payload")
        Map<String, Object> payload,
        @JsonProperty("created_at")
        Instant createdAt
) {
    private static final TypeReference<Map<String, Object>> MAP_TYPE = new TypeReference<>() {
    };

    public static AuditLogResponse from(AuditLogEntity entity, ObjectMapper objectMapper) {
        return new AuditLogResponse(
                entity.getId(),
                entity.getActor(),
                entity.getAction(),
                entity.getScopeType(),
                entity.getScopeId(),
                entity.getMessage(),
                readPayload(entity.getPayloadJson(), objectMapper),
                entity.getCreatedAt()
        );
    }

    private static Map<String, Object> readPayload(String payloadJson, ObjectMapper objectMapper) {
        if (payloadJson == null || payloadJson.isBlank()) {
            return Map.of();
        }
        try {
            return objectMapper.readValue(payloadJson, MAP_TYPE);
        } catch (Exception exception) {
            return Map.of("parse_error", "payload unavailable");
        }
    }
}
