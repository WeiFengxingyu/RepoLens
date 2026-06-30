package com.repolens.job.application;

import com.repolens.common.error.ResourceNotFoundException;
import com.repolens.common.id.IdGenerator;
import com.repolens.config.RepoLensProperties;
import com.repolens.job.domain.AnalysisJobEntity;
import com.repolens.job.domain.DeadLetterJobEntity;
import com.repolens.job.domain.JobAttemptEntity;
import com.repolens.job.domain.JobAttemptStatus;
import com.repolens.job.domain.JobStatus;
import com.repolens.job.infrastructure.AnalysisJobJpaRepository;
import com.repolens.job.infrastructure.DeadLetterJobJpaRepository;
import com.repolens.job.infrastructure.JobAttemptJpaRepository;
import org.springframework.context.annotation.Lazy;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.support.TransactionSynchronization;
import org.springframework.transaction.support.TransactionSynchronizationManager;

import java.time.Clock;
import java.time.Duration;
import java.time.Instant;

@Service
public class JobWorkerService {

    private final AnalysisJobJpaRepository analysisJobJpaRepository;
    private final JobAttemptJpaRepository jobAttemptJpaRepository;
    private final DeadLetterJobJpaRepository deadLetterJobJpaRepository;
    private final JobExecutorRegistry jobExecutorRegistry;
    private final JobStateMachine jobStateMachine;
    private final JobEventService jobEventService;
    private final JobDispatcher jobDispatcher;
    private final ConcurrencyControlService concurrencyControlService;
    private final RepoLensProperties properties;
    private final WorkerRegistry workerRegistry;
    private final IdGenerator idGenerator;
    private final Clock clock;

    public JobWorkerService(
            AnalysisJobJpaRepository analysisJobJpaRepository,
            JobAttemptJpaRepository jobAttemptJpaRepository,
            DeadLetterJobJpaRepository deadLetterJobJpaRepository,
            JobExecutorRegistry jobExecutorRegistry,
            JobStateMachine jobStateMachine,
            JobEventService jobEventService,
            @Lazy JobDispatcher jobDispatcher,
            ConcurrencyControlService concurrencyControlService,
            RepoLensProperties properties,
            WorkerRegistry workerRegistry,
            IdGenerator idGenerator,
            Clock clock
    ) {
        this.analysisJobJpaRepository = analysisJobJpaRepository;
        this.jobAttemptJpaRepository = jobAttemptJpaRepository;
        this.deadLetterJobJpaRepository = deadLetterJobJpaRepository;
        this.jobExecutorRegistry = jobExecutorRegistry;
        this.jobStateMachine = jobStateMachine;
        this.jobEventService = jobEventService;
        this.jobDispatcher = jobDispatcher;
        this.concurrencyControlService = concurrencyControlService;
        this.properties = properties;
        this.workerRegistry = workerRegistry;
        this.idGenerator = idGenerator;
        this.clock = clock;
    }

    @Transactional
    public void process(String jobId, String workerId) {
        workerRegistry.markRunning(workerId, jobId);
        JobAttemptEntity attempt = null;
        try {
            AnalysisJobEntity job = analysisJobJpaRepository.findById(jobId)
                    .orElseThrow(() -> new ResourceNotFoundException("Job not found"));
            if (job.getStatus() != JobStatus.QUEUED && job.getStatus() != JobStatus.RETRY_SCHEDULED) {
                jobEventService.record(jobId, null, "SKIPPED", "job is not queued", "{\"status\":\"" + job.getStatus() + "\"}");
                return;
            }

            Instant now = Instant.now(clock);
            transition(job, JobStatus.RUNNING, null, "job running");
            job.setStartedAt(job.getStartedAt() == null ? now : job.getStartedAt());
            attempt = new JobAttemptEntity(
                    idGenerator.newId("att"),
                    job.getId(),
                    (int) jobAttemptJpaRepository.countByJobId(job.getId()) + 1,
                    workerId,
                    now
            );
            jobAttemptJpaRepository.saveAndFlush(attempt);
            jobEventService.record(job.getId(), attempt.getId(), "ATTEMPT_STARTED", "attempt started", "{\"worker_id\":\"" + workerId + "\"}");

            String resultRef = jobExecutorRegistry.require(job.getJobType()).execute(job);
            Instant finishedAt = Instant.now(clock);
            attempt.setStatus(JobAttemptStatus.SUCCEEDED);
            attempt.setFinishedAt(finishedAt);
            attempt.setHeartbeatAt(finishedAt);
            jobAttemptJpaRepository.save(attempt);
            job.setResultRef(resultRef);
            job.setFinishedAt(finishedAt);
            job.setLastErrorCode(null);
            job.setLastErrorMessage(null);
            transition(job, JobStatus.SUCCEEDED, attempt.getId(), "job succeeded");
            analysisJobJpaRepository.save(job);
        } catch (RuntimeException exception) {
            fail(jobId, attempt, exception);
        } finally {
            workerRegistry.markIdle(workerId);
        }
    }

    private void fail(String jobId, JobAttemptEntity attempt, RuntimeException exception) {
        AnalysisJobEntity job = analysisJobJpaRepository.findById(jobId)
                .orElseThrow(() -> new ResourceNotFoundException("Job not found"));
        Instant now = Instant.now(clock);
        int attemptNo = attempt == null ? (int) jobAttemptJpaRepository.countByJobId(jobId) + 1 : attempt.getAttemptNo();
        if (attempt != null) {
            attempt.setStatus(JobAttemptStatus.FAILED);
            attempt.setFinishedAt(now);
            attempt.setHeartbeatAt(now);
            attempt.setErrorCode(errorCode(exception));
            attempt.setErrorMessage(exception.getMessage());
            jobAttemptJpaRepository.save(attempt);
        }
        job.setLastErrorCode(errorCode(exception));
        job.setLastErrorMessage(exception.getMessage());
        boolean retryable = isRetryable(exception) && attemptNo < properties.getV2Lite().getWorker().getMaxAttempts();
        if (retryable) {
            transition(job, JobStatus.FAILED_RETRYABLE, attempt == null ? null : attempt.getId(), "job failed retryable");
            transition(job, JobStatus.RETRY_SCHEDULED, attempt == null ? null : attempt.getId(), "job retry scheduled");
            job.setNextRunAt(now.plusSeconds(properties.getV2Lite().getWorker().getRetryBackoffSeconds() * (long) attemptNo));
            analysisJobJpaRepository.saveAndFlush(job);
            transition(job, JobStatus.QUEUED, attempt == null ? null : attempt.getId(), "retry queued by local dispatcher");
            analysisJobJpaRepository.save(job);
            dispatchAfterCommit(job.getId());
        } else {
            transition(job, JobStatus.DEAD, attempt == null ? null : attempt.getId(), "job moved to dead letter");
            job.setFinishedAt(now);
            analysisJobJpaRepository.save(job);
            deadLetterJobJpaRepository.save(new DeadLetterJobEntity(
                    job.getId(),
                    errorCode(exception),
                    exception.getMessage(),
                    attemptNo,
                    job.getPayloadJson(),
                    now
            ));
        }
    }

    private void transition(AnalysisJobEntity job, JobStatus to, String attemptId, String message) {
        jobStateMachine.validate(job.getStatus(), to);
        job.setStatus(to);
        job.setUpdatedAt(Instant.now(clock));
        concurrencyControlService.cacheJobStatus(job.getId(), to, Duration.ofSeconds(properties.getV2Lite().getConcurrency().getStatusCacheTtlSeconds()));
        jobEventService.record(job.getId(), attemptId, "STATUS_CHANGED", message, "{\"status\":\"" + to + "\"}");
    }

    private boolean isRetryable(RuntimeException exception) {
        return exception instanceof JobExecutionException jobExecutionException && jobExecutionException.isRetryable();
    }

    private String errorCode(RuntimeException exception) {
        if (exception instanceof JobExecutionException jobExecutionException) {
            return jobExecutionException.getErrorCode();
        }
        return "JOB_EXECUTION_FAILED";
    }

    private void dispatchAfterCommit(String jobId) {
        if (!TransactionSynchronizationManager.isSynchronizationActive()) {
            jobDispatcher.dispatch(jobId);
            return;
        }
        TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
            @Override
            public void afterCommit() {
                jobDispatcher.dispatch(jobId);
            }
        });
    }
}
