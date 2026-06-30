package com.repolens.job.application;

import com.repolens.job.domain.AnalysisJobEntity;
import com.repolens.job.domain.JobType;

public interface JobExecutor {

    JobType type();

    String execute(AnalysisJobEntity job);
}
