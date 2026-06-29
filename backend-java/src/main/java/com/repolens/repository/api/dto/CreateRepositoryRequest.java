package com.repolens.repository.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.Size;

public class CreateRepositoryRequest {

    @Size(max = 1024)
    private String source;

    @JsonProperty("sourceType")
    @Size(max = 32)
    private String sourceType;

    @JsonProperty("localPath")
    @Size(max = 1024)
    private String localPath;

    @Size(max = 255)
    private String name;

    @Size(max = 255)
    private String branch;

    public String getSource() {
        return source;
    }

    public void setSource(String source) {
        this.source = source;
    }

    public String getSourceType() {
        return sourceType;
    }

    public void setSourceType(String sourceType) {
        this.sourceType = sourceType;
    }

    public String getLocalPath() {
        return localPath;
    }

    public void setLocalPath(String localPath) {
        this.localPath = localPath;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getBranch() {
        return branch;
    }

    public void setBranch(String branch) {
        this.branch = branch;
    }
}
