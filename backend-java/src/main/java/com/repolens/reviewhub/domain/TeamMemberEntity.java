package com.repolens.reviewhub.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.time.Instant;

@Entity
@Table(name = "team_members")
public class TeamMemberEntity {

    @Id
    @Column(length = 64)
    private String id;

    @Column(name = "organization_id", nullable = false, length = 64)
    private String organizationId;

    @Column(name = "user_id", nullable = false, length = 128)
    private String userId;

    @Column(name = "role_name", nullable = false, length = 64)
    private String roleName;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    protected TeamMemberEntity() {
    }

    public TeamMemberEntity(String id, String organizationId, String userId, String roleName, Instant createdAt) {
        this.id = id;
        this.organizationId = organizationId;
        this.userId = userId;
        this.roleName = roleName;
        this.createdAt = createdAt;
    }

    public String getId() {
        return id;
    }
}
