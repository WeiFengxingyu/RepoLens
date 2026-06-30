package com.repolens.job.application;

import com.repolens.job.domain.AnalysisJobEntity;
import com.repolens.job.domain.JobStatus;
import com.repolens.job.infrastructure.AnalysisJobJpaRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.support.TransactionSynchronization;
import org.springframework.transaction.support.TransactionSynchronizationManager;

import java.time.Clock;
import java.time.Duration;
import java.time.Instant;

@Service
public class JobDispatchService {

    private final AnalysisJobJpaRepository analysisJobJpaRepository;
    private final JobStateMachine jobStateMachine;
    private final JobEventService jobEventService;
    private final JobDispatcher jobDispatcher;
    private final ConcurrencyControlService concurrencyControlService;
    private final Clock clock;

    public JobDispatchService(
            AnalysisJobJpaRepository analysisJobJpaRepository,
            JobStateMachine jobStateMachine,
            JobEventService jobEventService,
            JobDispatcher jobDispatcher,
            ConcurrencyControlService concurrencyControlService,
            Clock clock
    ) {
        this.analysisJobJpaRepository = analysisJobJpaRepository;
        this.jobStateMachine = jobStateMachine;
        this.jobEventService = jobEventService;
        this.jobDispatcher = jobDispatcher;
        this.concurrencyControlService = concurrencyControlService;
        this.clock = clock;
    }

    @Transactional
    public AnalysisJobEntity dispatch(String jobId) {
        AnalysisJobEntity job = analysisJobJpaRepository.findById(jobId)
                .orElseThrow(() -> new com.repolens.common.error.ResourceNotFoundException("Job not found"));
        if (job.getStatus() == JobStatus.DEAD) {
            transition(job, JobStatus.QUEUED, "retry queued");
        } else if (job.getStatus() == JobStatus.RETRY_SCHEDULED) {
            transition(job, JobStatus.QUEUED, "retry scheduled job queued");
        } else {
            transition(job, JobStatus.QUEUED, "job queued");
        }
        analysisJobJpaRepository.saveAndFlush(job);
        dispatchAfterCommit(job.getId());
        return job;
    }

    private void transition(AnalysisJobEntity job, JobStatus to, String message) {
        jobStateMachine.validate(job.getStatus(), to);
        job.setStatus(to);
        job.setUpdatedAt(Instant.now(clock));
        concurrencyControlService.cacheJobStatus(job.getId(), to, Duration.ofMinutes(5));
        jobEventService.record(job.getId(), null, "STATUS_CHANGED", message, "{\"status\":\"" + to + "\"}");
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
