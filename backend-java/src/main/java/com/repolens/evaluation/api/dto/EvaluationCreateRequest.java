package com.repolens.evaluation.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;

import java.util.Map;

public class EvaluationCreateRequest {

    private String name;

    @NotBlank
    @JsonProperty("dataset_path")
    private String datasetPath;

    @NotBlank
    private String strategy = "all";

    @NotEmpty
    @JsonProperty("repository_map")
    private Map<String, String> repositoryMap;

    @JsonProperty("top_k")
    @Min(1)
    @Max(20)
    private Integer topK = 5;

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getDatasetPath() {
        return datasetPath;
    }

    public void setDatasetPath(String datasetPath) {
        this.datasetPath = datasetPath;
    }

    public String getStrategy() {
        return strategy;
    }

    public void setStrategy(String strategy) {
        this.strategy = strategy;
    }

    public Map<String, String> getRepositoryMap() {
        return repositoryMap;
    }

    public void setRepositoryMap(Map<String, String> repositoryMap) {
        this.repositoryMap = repositoryMap;
    }

    public Integer getTopK() {
        return topK;
    }

    public void setTopK(Integer topK) {
        this.topK = topK;
    }
}
