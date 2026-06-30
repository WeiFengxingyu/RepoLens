package com.repolens.job.application;

import com.repolens.common.error.ResourceNotFoundException;
import com.repolens.common.id.IdGenerator;
import com.repolens.config.RepoLensProperties;
import com.repolens.job.domain.AnalysisJobEntity;
import com.repolens.job.domain.JobStatus;
import com.repolens.job.domain.JobType;
import com.repolens.job.infrastructure.AnalysisJobJpaRepository;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Optional;

@Service
public class JobService {

    private final AnalysisJobJpaRepository analysisJobJpaRepository;
    private final JobDispatchService jobDispatchService;
    private final JobStateMachine jobStateMachine;
    private final JobEventService jobEventService;
    private final ConcurrencyControlService concurrencyControlService;
    private final RepoLensProperties properties;
    private final IdGenerator idGenerator;
    private final Clock clock;

    public JobService(
            AnalysisJobJpaRepository analysisJobJpaRepository,
            JobDispatchService jobDispatchService,
            JobStateMachine jobStateMachine,
            JobEventService jobEventService,
            ConcurrencyControlService concurrencyControlService,
            RepoLensProperties properties,
            IdGenerator idGenerator,
            Clock clock
    ) {
        this.analysisJobJpaRepository = analysisJobJpaRepository;
        this.jobDispatchService = jobDispatchService;
        this.jobStateMachine = jobStateMachine;
        this.jobEventService = jobEventService;
        this.concurrencyControlService = concurrencyControlService;
        this.properties = properties;
        this.idGenerator = idGenerator;
        this.clock = clock;
    }

    @Transactional
    public AnalysisJobEntity create(JobCreateCommand command) {
        if (!properties.getV2Lite().isEnabled()) {
            throw new IllegalStateException("V2-Lite job API is disabled");
        }
        if (command.jobType() == null) {
            throw new IllegalArgumentException("job_type is required");
        }

        String idempotencyKey = normalize(command.idempotencyKey());
        if (idempotencyKey != null) {
            String cachedJobId = concurrencyControlService.findIdempotency(idempotencyKey).orElse(null);
            if (cachedJobId != null) {
                return analysisJobJpaRepository.findById(cachedJobId)
                        .orElseThrow(() -> new ResourceNotFoundException("Idempotent job not found"));
            }
            AnalysisJobEntity existing = analysisJobJpaRepository.findByIdempotencyKey(idempotencyKey).orElse(null);
            if (existing != null) {
                remember(idempotencyKey, existing.getId());
                return existing;
            }
        }

        enforceRateLimit(command);

        Instant now = Instant.now(clock);
        AnalysisJobEntity job = new AnalysisJobEntity(idGenerator.newId("job"), command.jobType(), now);
        job.setRepositoryId(normalize(command.repositoryId()));
        job.setProjectId(normalize(command.projectId()));
        job.setIdempotencyKey(idempotencyKey);
        job.setPayloadJson(normalize(command.payloadJson()));
        job.setCreatedBy(normalize(command.createdBy()));
        job.setPriority(command.priority() == null ? 5 : Math.max(0, Math.min(10, command.priority())));
        analysisJobJpaRepository.saveAndFlush(job);
        jobEventService.record(job.getId(), null, "JOB_CREATED", "job created", "{\"job_type\":\"" + job.getJobType() + "\"}");
        if (idempotencyKey != null) {
            remember(idempotencyKey, job.getId());
        }
        if (command.dispatch()) {
            return jobDispatchService.dispatch(job.getId());
        }
        return job;
    }

    @Transactional(readOnly = true)
    public AnalysisJobEntity get(String jobId) {
        return analysisJobJpaRepository.findById(jobId)
                .orElseThrow(() -> new ResourceNotFoundException("Job not found"));
    }

    @Transactional(readOnly = true)
    public Optional<AnalysisJobEntity> findByIdempotencyKey(String idempotencyKey) {
        String normalized = normalize(idempotencyKey);
        if (normalized == null) {
            return Optional.empty();
        }
        Optional<String> cachedJobId = concurrencyControlService.findIdempotency(normalized);
        if (cachedJobId.isPresent()) {
            Optional<AnalysisJobEntity> cached = analysisJobJpaRepository.findById(cachedJobId.get());
            if (cached.isPresent()) {
                return cached;
            }
        }
        return analysisJobJpaRepository.findByIdempotencyKey(normalized);
    }

    @Transactional(readOnly = true)
    public List<AnalysisJobEntity> list(int limit) {
        int bounded = Math.max(1, Math.min(100, limit));
        return analysisJobJpaRepository.findByOrderByCreatedAtDesc(PageRequest.of(0, bounded));
    }

    @Transactional
    public AnalysisJobEntity cancel(String jobId) {
        AnalysisJobEntity job = get(jobId);
        transition(job, JobStatus.CANCELED, "job canceled");
        return analysisJobJpaRepository.save(job);
    }

    @Transactional
    public AnalysisJobEntity retry(String jobId) {
        AnalysisJobEntity job = get(jobId);
        if (job.getStatus() != JobStatus.DEAD && job.getStatus() != JobStatus.FAILED_RETRYABLE) {
            throw new IllegalArgumentException("Only failed or dead jobs can be retried");
        }
        if (job.getStatus() == JobStatus.FAILED_RETRYABLE) {
            transition(job, JobStatus.RETRY_SCHEDULED, "manual retry scheduled");
            analysisJobJpaRepository.saveAndFlush(job);
        }
        return jobDispatchService.dispatch(job.getId());
    }

    private void transition(AnalysisJobEntity job, JobStatus to, String message) {
        jobStateMachine.validate(job.getStatus(), to);
        job.setStatus(to);
        job.setUpdatedAt(Instant.now(clock));
        concurrencyControlService.cacheJobStatus(job.getId(), to, Duration.ofSeconds(properties.getV2Lite().getConcurrency().getStatusCacheTtlSeconds()));
        jobEventService.record(job.getId(), null, "STATUS_CHANGED", message, "{\"status\":\"" + to + "\"}");
    }

    private void enforceRateLimit(JobCreateCommand command) {
        if (command.jobType() != JobType.REVIEW_DIFF) {
            return;
        }
        String owner = normalize(command.createdBy());
        String repository = normalize(command.repositoryId());
        String key = "rate:review:" + (owner == null ? "anonymous" : owner) + ":" + (repository == null ? "none" : repository);
        RateLimitDecision decision = concurrencyControlService.checkRateLimit(
                key,
                properties.getV2Lite().getConcurrency().getReviewRateLimitPerMinute(),
                Duration.ofMinutes(1)
        );
        if (!decision.allowed()) {
            throw new IllegalStateException("Review job rate limit exceeded; retry after " + decision.retryAfterSeconds() + "s");
        }
    }

    private void remember(String idempotencyKey, String jobId) {
        concurrencyControlService.rememberIdempotency(
                idempotencyKey,
                jobId,
                Duration.ofSeconds(properties.getV2Lite().getConcurrency().getIdempotencyTtlSeconds())
        );
    }

    private String normalize(String value) {
        if (value == null || value.isBlank()) {
            return null;
        }
        return value.trim();
    }
}
