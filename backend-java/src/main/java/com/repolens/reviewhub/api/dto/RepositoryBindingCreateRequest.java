package com.repolens.reviewhub.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public class RepositoryBindingCreateRequest {

    @NotBlank
    @Size(max = 64)
    private String provider;

    @NotBlank
    @Size(max = 512)
    @JsonProperty("external_repo_id")
    private String externalRepoId;

    @Size(max = 256)
    @JsonProperty("webhook_secret")
    private String webhookSecret;

    public String getProvider() {
        return provider;
    }

    public void setProvider(String provider) {
        this.provider = provider;
    }

    public String getExternalRepoId() {
        return externalRepoId;
    }

    public void setExternalRepoId(String externalRepoId) {
        this.externalRepoId = externalRepoId;
    }

    public String getWebhookSecret() {
        return webhookSecret;
    }

    public void setWebhookSecret(String webhookSecret) {
        this.webhookSecret = webhookSecret;
    }
}
