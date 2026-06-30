package com.repolens.job.application;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.repolens.job.domain.AnalysisJobEntity;
import com.repolens.job.domain.JobType;
import org.springframework.stereotype.Component;

import java.util.Map;

@Component
public class NoopJobExecutor implements JobExecutor {

    private static final TypeReference<Map<String, Object>> MAP_TYPE = new TypeReference<>() {
    };

    private final ObjectMapper objectMapper;

    public NoopJobExecutor(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
    }

    @Override
    public JobType type() {
        return JobType.NOOP;
    }

    @Override
    public String execute(AnalysisJobEntity job) {
        Map<String, Object> payload = readPayload(job);
        if (Boolean.TRUE.equals(payload.get("fail"))) {
            boolean retryable = Boolean.TRUE.equals(payload.get("retryable"));
            throw new JobExecutionException("NOOP_FAILED", "Noop job failed by payload", retryable);
        }
        return "noop:" + job.getId();
    }

    private Map<String, Object> readPayload(AnalysisJobEntity job) {
        if (job.getPayloadJson() == null || job.getPayloadJson().isBlank()) {
            return Map.of();
        }
        try {
            return objectMapper.readValue(job.getPayloadJson(), MAP_TYPE);
        } catch (Exception exception) {
            throw new JobExecutionException("INVALID_PAYLOAD", "Invalid noop payload", false);
        }
    }
}
