package com.repolens.job.infrastructure;

import com.repolens.config.RepoLensProperties;
import com.repolens.job.application.JobDispatcher;
import com.repolens.job.application.JobWorkerService;
import jakarta.annotation.PreDestroy;
import org.springframework.stereotype.Component;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicInteger;

@Component
public class LocalJobDispatcher implements JobDispatcher {

    private final JobWorkerService jobWorkerService;
    private final RepoLensProperties properties;
    private final ExecutorService executorService;
    private final AtomicInteger workerSequence = new AtomicInteger();

    public LocalJobDispatcher(JobWorkerService jobWorkerService, RepoLensProperties properties) {
        this.jobWorkerService = jobWorkerService;
        this.properties = properties;
        this.executorService = Executors.newFixedThreadPool(properties.getV2Lite().getWorker().getPoolSize());
    }

    @Override
    public void dispatch(String jobId) {
        if (!properties.getV2Lite().getWorker().isLocalEnabled()) {
            return;
        }
        executorService.submit(() -> jobWorkerService.process(jobId, "local-worker-" + workerSequence.incrementAndGet()));
    }

    @PreDestroy
    public void shutdown() {
        executorService.shutdownNow();
    }
}
