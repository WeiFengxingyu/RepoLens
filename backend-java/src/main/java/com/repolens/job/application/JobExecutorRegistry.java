package com.repolens.job.application;

import com.repolens.job.domain.JobType;
import org.springframework.stereotype.Component;

import java.util.EnumMap;
import java.util.List;
import java.util.Map;

@Component
public class JobExecutorRegistry {

    private final Map<JobType, JobExecutor> executors = new EnumMap<>(JobType.class);

    public JobExecutorRegistry(List<JobExecutor> executors) {
        for (JobExecutor executor : executors) {
            this.executors.put(executor.type(), executor);
        }
    }

    public JobExecutor require(JobType jobType) {
        JobExecutor executor = executors.get(jobType);
        if (executor == null) {
            throw new JobExecutionException("EXECUTOR_NOT_FOUND", "No executor registered for " + jobType, false);
        }
        return executor;
    }
}
