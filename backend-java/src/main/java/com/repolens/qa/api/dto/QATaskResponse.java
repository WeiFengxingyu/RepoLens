package com.repolens.qa.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.repolens.agent.api.dto.AgentTraceResponse;
import com.repolens.qa.domain.QATaskEntity;

import java.time.Instant;
import java.util.List;

public record QATaskResponse(
        @JsonProperty("task_id")
        String taskId,
        @JsonProperty("repository_id")
        String repositoryId,
        String status,
        String question,
        String answer,
        List<QACitationResponse> citations,
        Double confidence,
        List<String> warnings,
        @JsonProperty("error_message")
        String errorMessage,
        List<AgentTraceResponse> traces,
        @JsonProperty("created_at")
        Instant createdAt,
        @JsonProperty("completed_at")
        Instant completedAt
) {
    private static final TypeReference<List<String>> STRING_LIST = new TypeReference<>() {
    };

    public static QATaskResponse from(
            QATaskEntity task,
            List<QACitationResponse> citations,
            List<AgentTraceResponse> traces,
            ObjectMapper objectMapper
    ) {
        return new QATaskResponse(
                task.getId(),
                task.getRepositoryId(),
                task.getStatus(),
                task.getQuestion(),
                task.getAnswer(),
                citations,
                task.getConfidence(),
                readWarnings(task.getWarnings(), objectMapper),
                task.getErrorMessage(),
                traces,
                task.getCreatedAt(),
                task.getCompletedAt()
        );
    }

    private static List<String> readWarnings(String value, ObjectMapper objectMapper) {
        if (value == null || value.isBlank()) {
            return List.of();
        }
        try {
            return objectMapper.readValue(value, STRING_LIST);
        } catch (Exception ignored) {
            return List.of();
        }
    }
}
