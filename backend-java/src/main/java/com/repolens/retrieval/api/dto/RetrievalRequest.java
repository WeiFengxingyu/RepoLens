package com.repolens.retrieval.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public class RetrievalRequest {

    @NotBlank
    @Size(max = 512)
    private String query;

    @JsonProperty("top_k")
    @Min(1)
    @Max(50)
    private Integer topK = 10;

    @JsonProperty("use_bm25")
    private Boolean useBm25 = true;

    @JsonProperty("use_vector")
    private Boolean useVector = false;

    @JsonProperty("use_graph")
    private Boolean useGraph = false;

    public String getQuery() {
        return query;
    }

    public void setQuery(String query) {
        this.query = query;
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
