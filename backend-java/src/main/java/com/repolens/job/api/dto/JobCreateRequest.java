package com.repolens.job.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.repolens.job.application.JobCreateCommand;
import com.repolens.job.domain.JobType;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;

public class JobCreateRequest {

    @NotNull
    @JsonProperty("job_type")
    private JobType jobType;

    @JsonProperty("repository_id")
    private String repositoryId;

    @JsonProperty("project_id")
    private String projectId;

    @JsonProperty("idempotency_key")
    private String idempotencyKey;

    @JsonProperty("payload_json")
    private String payloadJson;

    @JsonProperty("created_by")
    private String createdBy;

    @Min(0)
    @Max(10)
    private Integer priority = 5;

    private Boolean dispatch = true;

    public JobType getJobType() {
        return jobType;
    }

    public void setJobType(JobType jobType) {
        this.jobType = jobType;
    }

    public String getRepositoryId() {
        return repositoryId;
    }

    public void setRepositoryId(String repositoryId) {
        this.repositoryId = repositoryId;
    }

    public String getProjectId() {
        return projectId;
    }

    public void setProjectId(String projectId) {
        this.projectId = projectId;
    }

    public String getIdempotencyKey() {
        return idempotencyKey;
    }

    public void setIdempotencyKey(String idempotencyKey) {
        this.idempotencyKey = idempotencyKey;
    }

    public String getPayloadJson() {
        return payloadJson;
    }

    public void setPayloadJson(String payloadJson) {
        this.payloadJson = payloadJson;
    }

    public String getCreatedBy() {
        return createdBy;
    }

    public void setCreatedBy(String createdBy) {
        this.createdBy = createdBy;
    }

    public Integer getPriority() {
        return priority;
    }

    public void setPriority(Integer priority) {
        this.priority = priority;
    }

    public Boolean getDispatch() {
        return dispatch;
    }

    public void setDispatch(Boolean dispatch) {
        this.dispatch = dispatch;
    }

    public JobCreateCommand toCommand() {
        return new JobCreateCommand(
                jobType,
                repositoryId,
                projectId,
                idempotencyKey,
                payloadJson,
                createdBy,
                priority,
                dispatch == null || dispatch
        );
    }
}
