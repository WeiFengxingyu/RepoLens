package com.repolens.repository.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public record RepositoryStatusResponse(
        String id,
        String status,
        RepositoryProgressResponse progress,
        @JsonProperty("error_message")
        String errorMessage
) {
}
