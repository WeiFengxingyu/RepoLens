package com.repolens.job.application;

import com.repolens.config.RepoLensProperties;
import com.repolens.indexing.application.RepositoryIndexingService;
import com.repolens.indexing.domain.IndexTaskEntity;
import com.repolens.job.domain.AnalysisJobEntity;
import com.repolens.job.domain.JobType;
import org.springframework.stereotype.Component;

import java.time.Duration;

@Component
public class IndexRepositoryJobExecutor implements JobExecutor {

    private final RepositoryIndexingService repositoryIndexingService;
    private final ConcurrencyControlService concurrencyControlService;
    private final RepoLensProperties properties;

    public IndexRepositoryJobExecutor(
            RepositoryIndexingService repositoryIndexingService,
            ConcurrencyControlService concurrencyControlService,
            RepoLensProperties properties
    ) {
        this.repositoryIndexingService = repositoryIndexingService;
        this.concurrencyControlService = concurrencyControlService;
        this.properties = properties;
    }

    @Override
    public JobType type() {
        return JobType.INDEX_REPOSITORY;
    }

    @Override
    public String execute(AnalysisJobEntity job) {
        if (job.getRepositoryId() == null || job.getRepositoryId().isBlank()) {
            throw new JobExecutionException("REPOSITORY_REQUIRED", "repository_id is required for index job", false);
        }
        LockHandle lock = concurrencyControlService
                .tryAcquireLock("lock:repo:" + job.getRepositoryId() + ":index", Duration.ofSeconds(properties.getV2Lite().getConcurrency().getLockTtlSeconds()))
                .orElseThrow(() -> new JobExecutionException("REPOSITORY_INDEX_LOCKED", "Repository index job is already running", true));
        try {
            IndexTaskEntity indexTask = repositoryIndexingService.startIndex(job.getRepositoryId());
            return "index_task:" + indexTask.getId();
        } finally {
            concurrencyControlService.releaseLock(lock);
        }
    }
}
