package com.repolens.qa.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public class QACreateRequest {

    @NotBlank
    @Size(max = 1000)
    private String question;

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

    public String getQuestion() {
        return question;
    }

    public void setQuestion(String question) {
        this.question = question;
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
}
