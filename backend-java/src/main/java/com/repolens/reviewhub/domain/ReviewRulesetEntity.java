package com.repolens.reviewhub.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.time.Instant;

@Entity
@Table(name = "review_rulesets")
public class ReviewRulesetEntity {

    @Id
    @Column(length = 64)
    private String id;

    @Column(name = "project_id", nullable = false, length = 64)
    private String projectId;

    @Column(nullable = false)
    private String name;

    @Column(name = "rules_json", nullable = false, columnDefinition = "text")
    private String rulesJson;

    @Column(nullable = false)
    private boolean enabled;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    protected ReviewRulesetEntity() {
    }

    public ReviewRulesetEntity(String id, String projectId, String name, String rulesJson, boolean enabled, Instant now) {
        this.id = id;
        this.projectId = projectId;
        this.name = name;
        this.rulesJson = rulesJson;
        this.enabled = enabled;
        this.createdAt = now;
        this.updatedAt = now;
    }

    public String getId() {
        return id;
    }

    public String getProjectId() {
        return projectId;
    }

    public String getName() {
        return name;
    }

    public String getRulesJson() {
        return rulesJson;
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
