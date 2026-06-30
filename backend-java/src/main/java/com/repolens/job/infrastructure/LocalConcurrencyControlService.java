package com.repolens.job.infrastructure;

import com.repolens.job.application.ConcurrencyControlService;
import com.repolens.job.application.LockHandle;
import com.repolens.job.application.RateLimitDecision;
import com.repolens.job.domain.JobStatus;
import org.springframework.stereotype.Service;

import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

@Service
public class LocalConcurrencyControlService implements ConcurrencyControlService {

    private final Clock clock;
    private final Map<String, ExpiringValue<String>> locks = new HashMap<>();
    private final Map<String, ExpiringValue<String>> idempotency = new HashMap<>();
    private final Map<String, ExpiringValue<JobStatus>> statuses = new HashMap<>();
    private final Map<String, RateWindow> rateWindows = new HashMap<>();

    public LocalConcurrencyControlService(Clock clock) {
        this.clock = clock;
    }

    @Override
    public synchronized Optional<LockHandle> tryAcquireLock(String key, Duration ttl) {
        purgeExpired(locks);
        if (locks.containsKey(key)) {
            return Optional.empty();
        }
        String owner = UUID.randomUUID().toString().replace("-", "");
        locks.put(key, new ExpiringValue<>(owner, Instant.now(clock).plus(ttl)));
        return Optional.of(new LockHandle(key, owner));
    }

    @Override
    public synchronized void releaseLock(LockHandle handle) {
        ExpiringValue<String> value = locks.get(handle.key());
        if (value != null && value.value().equals(handle.ownerToken())) {
            locks.remove(handle.key());
        }
    }

    @Override
    public synchronized Optional<String> findIdempotency(String key) {
        purgeExpired(idempotency);
        return Optional.ofNullable(idempotency.get(key)).map(ExpiringValue::value);
    }

    @Override
    public synchronized boolean rememberIdempotency(String key, String value, Duration ttl) {
        purgeExpired(idempotency);
        if (idempotency.containsKey(key)) {
            return false;
        }
        idempotency.put(key, new ExpiringValue<>(value, Instant.now(clock).plus(ttl)));
        return true;
    }

    @Override
    public synchronized RateLimitDecision checkRateLimit(String key, int limit, Duration window) {
        Instant now = Instant.now(clock);
        RateWindow current = rateWindows.get(key);
        if (current == null || !current.windowEnd().isAfter(now)) {
            current = new RateWindow(now.plus(window), 0);
        }
        int used = current.used() + 1;
        rateWindows.put(key, new RateWindow(current.windowEnd(), used));
        boolean allowed = used <= limit;
        long retryAfter = allowed ? 0 : Math.max(1, Duration.between(now, current.windowEnd()).toSeconds());
        return new RateLimitDecision(allowed, limit, used, retryAfter);
    }

    @Override
    public synchronized void cacheJobStatus(String jobId, JobStatus status, Duration ttl) {
        statuses.put(jobId, new ExpiringValue<>(status, Instant.now(clock).plus(ttl)));
    }

    @Override
    public synchronized Optional<JobStatus> getCachedJobStatus(String jobId) {
        purgeExpired(statuses);
        return Optional.ofNullable(statuses.get(jobId)).map(ExpiringValue::value);
    }

    private <T> void purgeExpired(Map<String, ExpiringValue<T>> values) {
        Instant now = Instant.now(clock);
        values.entrySet().removeIf(entry -> !entry.getValue().expiresAt().isAfter(now));
    }

    private record ExpiringValue<T>(T value, Instant expiresAt) {
    }

    private record RateWindow(Instant windowEnd, int used) {
    }
}
