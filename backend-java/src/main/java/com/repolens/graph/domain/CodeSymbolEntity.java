package com.repolens.graph.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.time.Instant;

@Entity
@Table(name = "code_symbols")
public class CodeSymbolEntity {

    @Id
    @Column(length = 64)
    private String id;

    @Column(name = "repository_id", nullable = false, length = 64)
    private String repositoryId;

    @Column(name = "file_path", nullable = false, length = 1024)
    private String filePath;

    @Column(nullable = false, length = 64)
    private String language;

    @Column(name = "symbol_name", nullable = false, length = 512)
    private String symbolName;

    @Column(name = "qualified_name", nullable = false, length = 1024)
    private String qualifiedName;

    @Column(name = "symbol_type", nullable = false, length = 64)
    private String symbolType;

    @Column(name = "parent_symbol_name", length = 1024)
    private String parentSymbolName;

    @Column(name = "start_line", nullable = false)
    private int startLine;

    @Column(name = "end_line", nullable = false)
    private int endLine;

    @Column(columnDefinition = "text")
    private String signature;

    @Column(columnDefinition = "text")
    private String metadata;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    protected CodeSymbolEntity() {
    }

    public CodeSymbolEntity(
            String id,
            String repositoryId,
            String filePath,
            String language,
            String symbolName,
            String qualifiedName,
            String symbolType,
            int startLine,
            int endLine,
            Instant createdAt
    ) {
        this.id = id;
        this.repositoryId = repositoryId;
        this.filePath = filePath;
        this.language = language;
        this.symbolName = symbolName;
        this.qualifiedName = qualifiedName;
        this.symbolType = symbolType;
        this.startLine = startLine;
        this.endLine = endLine;
        this.createdAt = createdAt;
    }

    public String getId() {
        return id;
    }

    public String getRepositoryId() {
        return repositoryId;
    }

    public String getFilePath() {
        return filePath;
    }

    public String getLanguage() {
        return language;
    }

    public String getSymbolName() {
        return symbolName;
    }

    public String getQualifiedName() {
        return qualifiedName;
    }

    public String getSymbolType() {
        return symbolType;
    }

    public String getParentSymbolName() {
        return parentSymbolName;
    }

    public void setParentSymbolName(String parentSymbolName) {
        this.parentSymbolName = parentSymbolName;
    }

    public int getStartLine() {
        return startLine;
    }

    public int getEndLine() {
        return endLine;
    }

    public String getSignature() {
        return signature;
    }

    public void setSignature(String signature) {
        this.signature = signature;
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
