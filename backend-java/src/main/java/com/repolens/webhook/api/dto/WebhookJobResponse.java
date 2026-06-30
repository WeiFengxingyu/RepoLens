package com.repolens.webhook.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.repolens.job.api.dto.JobResponse;
import com.repolens.reviewhub.api.dto.QuotaBucketResponse;

public record WebhookJobResponse(
        String provider,
        @JsonProperty("external_repo_id")
        String externalRepoId,
        @JsonProperty("project_id")
        String projectId,
        @JsonProperty("repository_id")
        String repositoryId,
        @JsonProperty("ruleset_id")
        String rulesetId,
        @JsonProperty("idempotency_key")
        String idempotencyKey,
        @JsonProperty("idempotent_replay")
        boolean idempotentReplay,
        QuotaBucketResponse quota,
        JobResponse job
) {
}
