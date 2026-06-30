package com.repolens.job.application;

import com.repolens.job.domain.JobStatus;

import java.time.Duration;
import java.util.Optional;

public interface ConcurrencyControlService {

    Optional<LockHandle> tryAcquireLock(String key, Duration ttl);

    void releaseLock(LockHandle handle);

    Optional<String> findIdempotency(String key);

    boolean rememberIdempotency(String key, String value, Duration ttl);

    RateLimitDecision checkRateLimit(String key, int limit, Duration window);

    void cacheJobStatus(String jobId, JobStatus status, Duration ttl);

    Optional<JobStatus> getCachedJobStatus(String jobId);
}
