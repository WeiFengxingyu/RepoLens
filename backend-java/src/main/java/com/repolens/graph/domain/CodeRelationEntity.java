package com.repolens.graph.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.time.Instant;

@Entity
@Table(name = "code_relations")
public class CodeRelationEntity {

    @Id
    @Column(length = 64)
    private String id;

    @Column(name = "repository_id", nullable = false, length = 64)
    private String repositoryId;

    @Column(name = "relation_type", nullable = false, length = 64)
    private String relationType;

    @Column(name = "source_symbol_id", length = 64)
    private String sourceSymbolId;

    @Column(name = "target_symbol_id", length = 64)
    private String targetSymbolId;

    @Column(name = "source_name", length = 1024)
    private String sourceName;

    @Column(name = "target_name", length = 1024)
    private String targetName;

    @Column(name = "file_path", length = 1024)
    private String filePath;

    @Column(columnDefinition = "text")
    private String metadata;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    protected CodeRelationEntity() {
    }

    public CodeRelationEntity(String id, String repositoryId, String relationType, Instant createdAt) {
        this.id = id;
        this.repositoryId = repositoryId;
        this.relationType = relationType;
        this.createdAt = createdAt;
    }

    public String getId() {
        return id;
    }

    public String getRepositoryId() {
        return repositoryId;
    }

    public String getRelationType() {
        return relationType;
    }

    public String getSourceSymbolId() {
        return sourceSymbolId;
    }

    public void setSourceSymbolId(String sourceSymbolId) {
        this.sourceSymbolId = sourceSymbolId;
    }

    public String getTargetSymbolId() {
        return targetSymbolId;
    }

    public void setTargetSymbolId(String targetSymbolId) {
        this.targetSymbolId = targetSymbolId;
    }

    public String getSourceName() {
        return sourceName;
    }

    public void setSourceName(String sourceName) {
        this.sourceName = sourceName;
    }

    public String getTargetName() {
        return targetName;
    }

    public void setTargetName(String targetName) {
        this.targetName = targetName;
    }

    public String getFilePath() {
        return filePath;
    }

    public void setFilePath(String filePath) {
        this.filePath = filePath;
    }

    public String getMetadata() {
        return metadata;
    }

    public void setMetadata(String metadata) {
        this.metadata = metadata;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }
}
