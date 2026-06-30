package com.repolens.job.application;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.repolens.change.api.dto.ChangeRequestReviewCreateRequest;
import com.repolens.change.api.dto.ChangeRequestReviewResponse;
import com.repolens.change.application.ChangeRequestReviewService;
import com.repolens.job.domain.AnalysisJobEntity;
import com.repolens.job.domain.JobType;
import org.springframework.stereotype.Component;

import java.util.Map;

@Component
public class ReviewChangeRequestJobExecutor implements JobExecutor {

    private static final TypeReference<Map<String, Object>> MAP_TYPE = new TypeReference<>() {
    };

    private final ChangeRequestReviewService changeRequestReviewService;
    private final JobEventService jobEventService;
    private final ObjectMapper objectMapper;

    public ReviewChangeRequestJobExecutor(
            ChangeRequestReviewService changeRequestReviewService,
            JobEventService jobEventService,
            ObjectMapper objectMapper
    ) {
        this.changeRequestReviewService = changeRequestReviewService;
        this.jobEventService = jobEventService;
        this.objectMapper = objectMapper;
    }

    @Override
    public JobType type() {
        return JobType.REVIEW_CHANGE_REQUEST;
    }

    @Override
    public String execute(AnalysisJobEntity job) {
        if (job.getRepositoryId() == null || job.getRepositoryId().isBlank()) {
            throw new JobExecutionException("REPOSITORY_REQUIRED", "repository_id is required for change request review job", false);
        }
        Map<String, Object> payload = readPayload(job);
        String changeUrl = stringValue(payload.get("change_url"));
        if (changeUrl == null) {
            changeUrl = stringValue(payload.get("url"));
        }
        if (changeUrl == null) {
            throw new JobExecutionException("CHANGE_URL_REQUIRED", "change_url is required for change request review job", false);
        }
        String rulesetId = stringValue(payload.get("ruleset_id"));
        if (rulesetId != null) {
            jobEventService.record(job.getId(), null, "RULESET_ATTACHED", "review ruleset attached", "{\"ruleset_id\":\"" + rulesetId + "\"}");
        }

        ChangeRequestReviewCreateRequest request = new ChangeRequestReviewCreateRequest();
        request.setUrl(changeUrl);
        request.setTopK(intValue(payload.get("top_k"), 8));
        request.setUseBm25(booleanValue(payload.get("use_bm25"), true));
        request.setUseVector(booleanValue(payload.get("use_vector"), true));
        request.setUseGraph(booleanValue(payload.get("use_graph"), true));
        request.setRunStaticCheck(booleanValue(payload.get("run_static_check"), true));

        ChangeRequestReviewResponse response = changeRequestReviewService.review(job.getRepositoryId(), request);
        return "change_request:" + response.changeRequest().id() + ";review_task:" + response.review().taskId();
    }

    private Map<String, Object> readPayload(AnalysisJobEntity job) {
        if (job.getPayloadJson() == null || job.getPayloadJson().isBlank()) {
            return Map.of();
        }
        try {
            return objectMapper.readValue(job.getPayloadJson(), MAP_TYPE);
        } catch (Exception exception) {
            throw new JobExecutionException("INVALID_PAYLOAD", "Invalid change request review payload", false);
        }
    }

    private String stringValue(Object value) {
        if (value instanceof String text && !text.isBlank()) {
            return text.trim();
        }
        return null;
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
