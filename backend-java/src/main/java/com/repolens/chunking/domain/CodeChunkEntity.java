package com.repolens.chunking.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.time.Instant;

@Entity
@Table(name = "code_chunks")
public class CodeChunkEntity {

    @Id
    @Column(length = 64)
    private String id;

    @Column(name = "repository_id", nullable = false, length = 64)
    private String repositoryId;

    @Column(name = "file_id", nullable = false, length = 64)
    private String fileId;

    @Column(name = "file_path", nullable = false, length = 1024)
    private String filePath;

    @Column(nullable = false, length = 64)
    private String language;

    @Column(name = "symbol_name", length = 512)
    private String symbolName;

    @Enumerated(EnumType.STRING)
    @Column(name = "symbol_type", nullable = false, length = 64)
    private ChunkType symbolType;

    @Column(name = "start_line", nullable = false)
    private int startLine;

    @Column(name = "end_line", nullable = false)
    private int endLine;

    @Column(name = "content_hash", length = 128)
    private String contentHash;

    @Column(nullable = false, columnDefinition = "text")
    private String content;

    @Column(name = "token_estimate", nullable = false)
    private int tokenEstimate;

    @Column(columnDefinition = "text")
    private String metadata;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    protected CodeChunkEntity() {
    }

    public CodeChunkEntity(
            String id,
            String repositoryId,
            String fileId,
            String filePath,
            String language,
            ChunkType symbolType,
            int startLine,
            int endLine,
            String content,
            Instant createdAt
    ) {
        this.id = id;
        this.repositoryId = repositoryId;
        this.fileId = fileId;
        this.filePath = filePath;
        this.language = language;
        this.symbolType = symbolType;
        this.startLine = startLine;
        this.endLine = endLine;
        this.content = content;
        this.createdAt = createdAt;
    }

    public String getId() {
        return id;
    }

    public String getRepositoryId() {
        return repositoryId;
    }

    public String getFileId() {
        return fileId;
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

    public void setSymbolName(String symbolName) {
        this.symbolName = symbolName;
    }

    public ChunkType getSymbolType() {
        return symbolType;
    }

    public int getStartLine() {
        return startLine;
    }

    public int getEndLine() {
        return endLine;
    }

    public String getContentHash() {
        return contentHash;
    }

    public void setContentHash(String contentHash) {
        this.contentHash = contentHash;
    }

    public String getContent() {
        return content;
    }

    public int getTokenEstimate() {
        return tokenEstimate;
    }

    public void setTokenEstimate(int tokenEstimate) {
        this.tokenEstimate = tokenEstimate;
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
