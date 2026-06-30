package com.repolens.webhook.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public class WebhookReviewRequest {

    @NotBlank
    @Size(max = 512)
    @JsonProperty("external_repo_id")
    private String externalRepoId;

    @NotBlank
    @Size(max = 2048)
    @JsonProperty("change_url")
    private String changeUrl;

    @Size(max = 64)
    private String event = "pull_request";

    @Size(max = 64)
    private String action = "opened";

    @Size(max = 128)
    @JsonProperty("commit_sha")
    private String commitSha;

    @Size(max = 128)
    private String sender = "webhook";

    @JsonProperty("top_k")
    @Min(1)
    @Max(20)
    private Integer topK = 8;

    @JsonProperty("use_bm25")
    private Boolean useBm25 = true;

    @JsonProperty("use_vector")
    private Boolean useVector = true;

    @JsonProperty("use_graph")
    private Boolean useGraph = true;

    @JsonProperty("run_static_check")
    private Boolean runStaticCheck = true;

    public String getExternalRepoId() {
        return externalRepoId;
    }

    public void setExternalRepoId(String externalRepoId) {
        this.externalRepoId = externalRepoId;
    }

    public String getChangeUrl() {
        return changeUrl;
    }

    public void setChangeUrl(String changeUrl) {
        this.changeUrl = changeUrl;
    }

    public String getEvent() {
        return event;
    }

    public void setEvent(String event) {
        this.event = event;
    }

    public String getAction() {
        return action;
    }

    public void setAction(String action) {
        this.action = action;
    }

    public String getCommitSha() {
        return commitSha;
    }

    public void setCommitSha(String commitSha) {
        this.commitSha = commitSha;
    }

    public String getSender() {
        return sender;
    }

    public void setSender(String sender) {
        this.sender = sender;
    }

    public Integer getTopK() {
        return topK;
    }

    public void setTopK(Integer topK) {
        this.topK = topK;
    }

    public Boolean getUseBm25() {
        return useBm25;
    }

    public void setUseBm25(Boolean useBm25) {
        this.useBm25 = useBm25;
    }

    public Boolean getUseVector() {
        return useVector;
    }

    public void setUseVector(Boolean useVector) {
        this.useVector = useVector;
    }

    public Boolean getUseGraph() {
        return useGraph;
    }

    public void setUseGraph(Boolean useGraph) {
        this.useGraph = useGraph;
    }

    public Boolean getRunStaticCheck() {
        return runStaticCheck;
    }

    public void setRunStaticCheck(Boolean runStaticCheck) {
        this.runStaticCheck = runStaticCheck;
    }
}
