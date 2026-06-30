package com.repolens.reviewhub.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.time.Instant;

@Entity
@Table(name = "repository_bindings")
public class RepositoryBindingEntity {

    @Id
    @Column(length = 64)
    private String id;

    @Column(name = "project_id", nullable = false, length = 64)
    private String projectId;

    @Column(name = "repository_id", nullable = false, length = 64)
    private String repositoryId;

    @Column(nullable = false, length = 64)
    private String provider;

    @Column(name = "external_repo_id", nullable = false, length = 512)
    private String externalRepoId;

    @Column(name = "webhook_secret_hash", length = 128)
    private String webhookSecretHash;

    @Column(nullable = false)
    private boolean enabled;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    protected RepositoryBindingEntity() {
    }

    public RepositoryBindingEntity(
            String id,
            String projectId,
            String repositoryId,
            String provider,
            String externalRepoId,
            String webhookSecretHash,
            Instant now
    ) {
        this.id = id;
        this.projectId = projectId;
        this.repositoryId = repositoryId;
        this.provider = provider;
        this.externalRepoId = externalRepoId;
        this.webhookSecretHash = webhookSecretHash;
        this.enabled = true;
        this.createdAt = now;
        this.updatedAt = now;
    }

    public String getId() {
        return id;
    }

    public String getProjectId() {
        return projectId;
    }

    public String getRepositoryId() {
        return repositoryId;
    }

    public String getProvider() {
        return provider;
    }

    public String getExternalRepoId() {
        return externalRepoId;
    }

    public String getWebhookSecretHash() {
        return webhookSecretHash;
    }

    public boolean isEnabled() {
        return enabled;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }

    public Instant getUpdatedAt() {
        return updatedAt;
    }
}
