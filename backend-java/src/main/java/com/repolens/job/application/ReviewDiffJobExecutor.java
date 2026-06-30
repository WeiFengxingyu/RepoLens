package com.repolens.job.application;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.repolens.job.domain.AnalysisJobEntity;
import com.repolens.job.domain.JobType;
import com.repolens.review.api.dto.ReviewCreateRequest;
import com.repolens.review.api.dto.ReviewTaskResponse;
import com.repolens.review.application.ReviewService;
import org.springframework.stereotype.Component;

import java.util.Map;

@Component
public class ReviewDiffJobExecutor implements JobExecutor {

    private static final TypeReference<Map<String, Object>> MAP_TYPE = new TypeReference<>() {
    };

    private final ReviewService reviewService;
    private final ObjectMapper objectMapper;

    public ReviewDiffJobExecutor(ReviewService reviewService, ObjectMapper objectMapper) {
        this.reviewService = reviewService;
        this.objectMapper = objectMapper;
    }

    @Override
    public JobType type() {
        return JobType.REVIEW_DIFF;
    }

    @Override
    public String execute(AnalysisJobEntity job) {
        if (job.getRepositoryId() == null || job.getRepositoryId().isBlank()) {
            throw new JobExecutionException("REPOSITORY_REQUIRED", "repository_id is required for review job", false);
        }
        Map<String, Object> payload = readPayload(job);
        Object diffText = payload.get("diff_text");
        if (!(diffText instanceof String diff) || diff.isBlank()) {
            throw new JobExecutionException("DIFF_REQUIRED", "diff_text is required for review job", false);
        }
        ReviewCreateRequest request = new ReviewCreateRequest();
        request.setDiffText(diff);
        request.setTopK(intValue(payload.get("top_k"), 8));
        request.setUseBm25(booleanValue(payload.get("use_bm25"), true));
        request.setUseVector(booleanValue(payload.get("use_vector"), true));
        request.setUseGraph(booleanValue(payload.get("use_graph"), true));
        request.setRunStaticCheck(booleanValue(payload.get("run_static_check"), true));
        ReviewTaskResponse response = reviewService.review(job.getRepositoryId(), request, "V2-Lite async job.");
        return "review_task:" + response.taskId();
    }

    private Map<String, Object> readPayload(AnalysisJobEntity job) {
        if (job.getPayloadJson() == null || job.getPayloadJson().isBlank()) {
            return Map.of();
        }
        try {
            return objectMapper.readValue(job.getPayloadJson(), MAP_TYPE);
        } catch (Exception exception) {
            throw new JobExecutionException("INVALID_PAYLOAD", "Invalid review job payload", false);
        }
    }

    private int intValue(Object value, int fallback) {
        if (value instanceof Number number) {
            return number.intValue();
        }
        return fallback;
    }

    private boolean booleanValue(Object value, boolean fallback) {
        if (value instanceof Boolean bool) {
            return bool;
        }
        return fallback;
    }
}
