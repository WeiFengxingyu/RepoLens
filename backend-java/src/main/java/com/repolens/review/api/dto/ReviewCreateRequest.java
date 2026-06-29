package com.repolens.review.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;

public class ReviewCreateRequest {

    @NotBlank
    @JsonProperty("diff_text")
    private String diffText;

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

    public String getDiffText() {
        return diffText;
    }

    public void setDiffText(String diffText) {
        this.diffText = diffText;
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
