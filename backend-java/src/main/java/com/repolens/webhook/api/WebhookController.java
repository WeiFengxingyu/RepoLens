package com.repolens.webhook.api;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.repolens.job.api.dto.JobResponse;
import com.repolens.job.application.JobCreateCommand;
import com.repolens.job.application.JobService;
import com.repolens.job.domain.AnalysisJobEntity;
import com.repolens.job.domain.JobType;
import com.repolens.reviewhub.api.dto.QuotaBucketResponse;
import com.repolens.reviewhub.application.ReviewHubService;
import com.repolens.reviewhub.domain.QuotaBucketEntity;
import com.repolens.reviewhub.domain.RepositoryBindingEntity;
import com.repolens.reviewhub.domain.ReviewRulesetEntity;
import com.repolens.webhook.api.dto.WebhookJobResponse;
import com.repolens.webhook.api.dto.WebhookReviewRequest;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RestController;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

@RestController
public class WebhookController {

    private final ReviewHubService reviewHubService;
    private final JobService jobService;
    private final ObjectMapper objectMapper;

    public WebhookController(ReviewHubService reviewHubService, JobService jobService, ObjectMapper objectMapper) {
        this.reviewHubService = reviewHubService;
        this.jobService = jobService;
        this.objectMapper = objectMapper;
    }

    @PostMapping("/api/webhooks/{provider}")
    public ResponseEntity<WebhookJobResponse> receive(
            @PathVariable String provider,
            @RequestHeader(value = "X-RepoLens-Webhook-Secret", required = false) String webhookSecret,
            @Valid @RequestBody WebhookReviewRequest request
    ) {
        String normalizedProvider = provider.trim().toLowerCase(Locale.ROOT);
        RepositoryBindingEntity binding = reviewHubService.resolveBinding(normalizedProvider, request.getExternalRepoId());
        reviewHubService.validateWebhookSecret(binding, webhookSecret);

        String idempotencyKey = idempotencyKey(normalizedProvider, request);
        AnalysisJobEntity existing = jobService.findByIdempotencyKey(idempotencyKey).orElse(null);
        String rulesetId = reviewHubService.findLatestEnabledRuleset(binding.getProjectId())
                .map(ReviewRulesetEntity::getId)
                .orElse(null);
        if (existing != null) {
            return ResponseEntity.ok(response(normalizedProvider, request, binding, rulesetId, idempotencyKey, true, null, existing));
        }

        QuotaBucketEntity quota = reviewHubService.consumeProjectQuota(
                binding.getProjectId(),
                ReviewHubService.QUOTA_WEBHOOK_REVIEW,
                defaultString(request.getSender(), "webhook"),
                Map.of(
                        "provider", normalizedProvider,
                        "external_repo_id", request.getExternalRepoId(),
                        "change_url", request.getChangeUrl(),
                        "commit_sha", defaultString(request.getCommitSha(), "none"),
                        "action", defaultString(request.getAction(), "opened")
                )
        );

        AnalysisJobEntity job = jobService.create(new JobCreateCommand(
                JobType.REVIEW_CHANGE_REQUEST,
                binding.getRepositoryId(),
                binding.getProjectId(),
                idempotencyKey,
                payloadJson(normalizedProvider, request, rulesetId),
                defaultString(request.getSender(), "webhook"),
                4,
                true
        ));
        return ResponseEntity.status(HttpStatus.ACCEPTED)
                .body(response(normalizedProvider, request, binding, rulesetId, idempotencyKey, false, quota, job));
    }

    private WebhookJobResponse response(
            String provider,
            WebhookReviewRequest request,
            RepositoryBindingEntity binding,
            String rulesetId,
            String idempotencyKey,
            boolean idempotentReplay,
            QuotaBucketEntity quota,
            AnalysisJobEntity job
    ) {
        return new WebhookJobResponse(
                provider,
                request.getExternalRepoId(),
                binding.getProjectId(),
                binding.getRepositoryId(),
                rulesetId,
                idempotencyKey,
                idempotentReplay,
                quota == null ? null : QuotaBucketResponse.from(quota),
                JobResponse.from(job, List.of(), List.of())
        );
    }

    private String idempotencyKey(String provider, WebhookReviewRequest request) {
        return "webhook:%s:%s:%s:%s:%s".formatted(
                provider,
                request.getExternalRepoId().trim(),
                request.getChangeUrl().trim(),
                defaultString(request.getCommitSha(), "no-sha"),
                defaultString(request.getAction(), "opened")
        );
    }

    private String payloadJson(String provider, WebhookReviewRequest request, String rulesetId) {
        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("source", "webhook");
        payload.put("provider", provider);
        payload.put("external_repo_id", request.getExternalRepoId());
        payload.put("change_url", request.getChangeUrl());
        payload.put("event", defaultString(request.getEvent(), "pull_request"));
        payload.put("action", defaultString(request.getAction(), "opened"));
        payload.put("commit_sha", defaultString(request.getCommitSha(), ""));
        payload.put("sender", defaultString(request.getSender(), "webhook"));
        payload.put("ruleset_id", rulesetId);
        payload.put("top_k", request.getTopK() == null ? 8 : request.getTopK());
        payload.put("use_bm25", request.getUseBm25() == null || request.getUseBm25());
        payload.put("use_vector", request.getUseVector() == null || request.getUseVector());
        payload.put("use_graph", request.getUseGraph() == null || request.getUseGraph());
        payload.put("run_static_check", request.getRunStaticCheck() == null || request.getRunStaticCheck());
        try {
            return objectMapper.writeValueAsString(payload);
        } catch (JsonProcessingException exception) {
            throw new IllegalStateException("Failed to serialize webhook job payload", exception);
        }
    }

    private String defaultString(String value, String fallback) {
        if (value == null || value.isBlank()) {
            return fallback;
        }
        return value.trim();
    }
}
