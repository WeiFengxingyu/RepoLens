package com.repolens.job.infrastructure;

import com.repolens.job.application.LockHandle;
import com.repolens.job.application.RateLimitDecision;
import com.repolens.job.domain.JobStatus;
import org.junit.jupiter.api.Test;

import java.time.Clock;
import java.time.Duration;

import static org.assertj.core.api.Assertions.assertThat;

class LocalConcurrencyControlServiceTest {

    private final LocalConcurrencyControlService service = new LocalConcurrencyControlService(Clock.systemUTC());

    @Test
    void lockRequiresMatchingOwnerTokenToRelease() {
        LockHandle first = service.tryAcquireLock("lock:repo:test", Duration.ofMinutes(1)).orElseThrow();

        assertThat(service.tryAcquireLock("lock:repo:test", Duration.ofMinutes(1))).isEmpty();

        service.releaseLock(new LockHandle(first.key(), "wrong-owner"));
        assertThat(service.tryAcquireLock("lock:repo:test", Duration.ofMinutes(1))).isEmpty();

        service.releaseLock(first);
        assertThat(service.tryAcquireLock("lock:repo:test", Duration.ofMinutes(1))).isPresent();
    }

    @Test
    void remembersIdempotencyAndCachesStatus() {
        assertThat(service.rememberIdempotency("idem:one", "job_1", Duration.ofMinutes(1))).isTrue();
        assertThat(service.rememberIdempotency("idem:one", "job_2", Duration.ofMinutes(1))).isFalse();
        assertThat(service.findIdempotency("idem:one")).contains("job_1");

        service.cacheJobStatus("job_1", JobStatus.QUEUED, Duration.ofMinutes(1));
        assertThat(service.getCachedJobStatus("job_1")).contains(JobStatus.QUEUED);
    }

    @Test
    void fixedWindowRateLimitRejectsAfterLimit() {
        RateLimitDecision first = service.checkRateLimit("rate:user:demo", 2, Duration.ofMinutes(1));
        RateLimitDecision second = service.checkRateLimit("rate:user:demo", 2, Duration.ofMinutes(1));
        RateLimitDecision third = service.checkRateLimit("rate:user:demo", 2, Duration.ofMinutes(1));

        assertThat(first.allowed()).isTrue();
        assertThat(second.allowed()).isTrue();
        assertThat(third.allowed()).isFalse();
        assertThat(third.retryAfterSeconds()).isGreaterThan(0);
    }
}
