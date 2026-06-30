package com.repolens.job.application;

public record RateLimitDecision(
        boolean allowed,
        int limit,
        int used,
        long retryAfterSeconds
) {
}
