package com.repolens.job.api;

import com.repolens.job.api.dto.JobAttemptResponse;
import com.repolens.job.api.dto.JobCreateRequest;
import com.repolens.job.api.dto.JobEventResponse;
import com.repolens.job.api.dto.JobResponse;
import com.repolens.job.api.dto.WorkerResponse;
import com.repolens.job.application.JobService;
import com.repolens.job.application.WorkerRegistry;
import com.repolens.job.domain.AnalysisJobEntity;
import com.repolens.job.infrastructure.JobAttemptJpaRepository;
import com.repolens.job.infrastructure.JobEventJpaRepository;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
public class JobController {

    private final JobService jobService;
    private final JobAttemptJpaRepository jobAttemptJpaRepository;
    private final JobEventJpaRepository jobEventJpaRepository;
    private final WorkerRegistry workerRegistry;

    public JobController(
            JobService jobService,
            JobAttemptJpaRepository jobAttemptJpaRepository,
            JobEventJpaRepository jobEventJpaRepository,
            WorkerRegistry workerRegistry
    ) {
        this.jobService = jobService;
        this.jobAttemptJpaRepository = jobAttemptJpaRepository;
        this.jobEventJpaRepository = jobEventJpaRepository;
        this.workerRegistry = workerRegistry;
    }

    @PostMapping("/api/jobs")
    @ResponseStatus(HttpStatus.CREATED)
    public JobResponse create(@Valid @RequestBody JobCreateRequest request) {
        return toResponse(jobService.create(request.toCommand()));
    }

    @GetMapping("/api/jobs")
    public List<JobResponse> list(@RequestParam(defaultValue = "50") int limit) {
        return jobService.list(limit).stream()
                .map(job -> JobResponse.from(job, List.of(), List.of()))
                .toList();
    }

    @GetMapping("/api/jobs/{jobId}")
    public JobResponse get(@PathVariable String jobId) {
        return toResponse(jobService.get(jobId));
    }

    @GetMapping("/api/jobs/{jobId}/events")
    public List<JobEventResponse> events(@PathVariable String jobId) {
        jobService.get(jobId);
        return jobEventJpaRepository.findByJobIdOrderByCreatedAtAsc(jobId).stream()
                .map(JobEventResponse::from)
                .toList();
    }

    @PostMapping("/api/jobs/{jobId}/retry")
    public JobResponse retry(@PathVariable String jobId) {
        return toResponse(jobService.retry(jobId));
    }

    @PostMapping("/api/jobs/{jobId}/cancel")
    public JobResponse cancel(@PathVariable String jobId) {
        return toResponse(jobService.cancel(jobId));
    }

    @GetMapping("/api/workers")
    public List<WorkerResponse> workers() {
        return workerRegistry.snapshots().stream()
                .map(WorkerResponse::from)
                .toList();
    }

    private JobResponse toResponse(AnalysisJobEntity job) {
        return JobResponse.from(
                job,
                jobAttemptJpaRepository.findByJobIdOrderByAttemptNoAsc(job.getId()).stream()
                        .map(JobAttemptResponse::from)
                        .toList(),
                jobEventJpaRepository.findByJobIdOrderByCreatedAtAsc(job.getId()).stream()
                        .map(JobEventResponse::from)
                        .toList()
        );
    }
}
