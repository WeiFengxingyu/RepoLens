package com.repolens.repository.application;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.repolens.repository.api.dto.RepositoryDetailResponse;
import com.repolens.repository.api.dto.RepositoryProgressResponse;
import com.repolens.repository.api.dto.RepositoryStatusResponse;
import com.repolens.repository.api.dto.RepositorySummaryResponse;
import com.repolens.repository.domain.RepositoryEntity;
import com.repolens.repository.domain.RepositoryStatus;
import org.springframework.stereotype.Component;

import java.util.Collections;
import java.util.Map;

@Component
public class RepositoryMapper {

    private static final TypeReference<Map<String, Integer>> LANGUAGE_SUMMARY_TYPE = new TypeReference<>() {
    };

    private final ObjectMapper objectMapper;

    public RepositoryMapper(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
    }

    public RepositorySummaryResponse toSummary(RepositoryEntity repository) {
        return new RepositorySummaryResponse(
                repository.getId(),
                repository.getName(),
                repository.getSourceType().name().toLowerCase(),
                toApiStatus(repository.getStatus()),
                repository.getFileCount(),
                repository.getChunkCount(),
                repository.getRelationCount(),
                repository.getUpdatedAt()
        );
    }

    public RepositoryDetailResponse toDetail(RepositoryEntity repository) {
        return new RepositoryDetailResponse(
                repository.getId(),
                repository.getName(),
                repository.getSourceType().name().toLowerCase(),
                repository.getSourceUrl(),
                repository.getLocalPath(),
                repository.getBranchName(),
                repository.getCommitHash(),
                toApiStatus(repository.getStatus()),
                parseLanguageSummary(repository.getLanguageSummary()),
                repository.getFileCount(),
                repository.getParsedFileCount(),
                repository.getSkippedFileCount(),
                repository.getChunkCount(),
                repository.getRelationCount(),
                repository.getLastError(),
                repository.getCreatedAt(),
                repository.getUpdatedAt(),
                repository.getIndexedAt()
        );
    }

    public RepositoryStatusResponse toStatus(RepositoryEntity repository) {
        return new RepositoryStatusResponse(
                repository.getId(),
                toApiStatus(repository.getStatus()),
                new RepositoryProgressResponse(
                        toApiStatus(repository.getStatus()),
                        repository.getFileCount(),
                        repository.getParsedFileCount(),
                        repository.getChunkCount(),
                        repository.getRelationCount()
                ),
                repository.getLastError()
        );
    }

    private Map<String, Integer> parseLanguageSummary(String value) {
        if (value == null || value.isBlank()) {
            return Collections.emptyMap();
        }
        try {
            return objectMapper.readValue(value, LANGUAGE_SUMMARY_TYPE);
        } catch (Exception ignored) {
            return Collections.emptyMap();
        }
    }

    private String toApiStatus(RepositoryStatus status) {
        return switch (status) {
            case CREATED -> "pending";
            case SCANNING -> "scanning";
            case PARSING -> "parsing";
            case CHUNKING -> "chunking";
            case INDEXING -> "indexing";
            case READY -> "ready";
            case FAILED -> "failed";
        };
    }
}
