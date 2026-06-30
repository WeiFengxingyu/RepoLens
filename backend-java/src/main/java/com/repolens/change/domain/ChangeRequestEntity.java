package com.repolens.change.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.time.Instant;

@Entity
@Table(name = "change_requests")
public class ChangeRequestEntity {

    @Id
    @Column(length = 64)
    private String id;

    @Column(name = "repository_id", nullable = false, length = 64)
    private String repositoryId;

    @Column(name = "review_task_id", length = 64)
    private String reviewTaskId;

    @Column(nullable = false, length = 32)
    private String platform;

    @Column(name = "change_type", nullable = false, length = 32)
    private String changeType;

    @Column(name = "owner_name", nullable = false, length = 512)
    private String ownerName;

    @Column(name = "repository_name", nullable = false, length = 256)
    private String repositoryName;

    @Column(name = "change_number", nullable = false, length = 64)
    private String changeNumber;

    @Column(nullable = false, length = 2048)
    private String url;

    @Column(nullable = false, columnDefinition = "text")
    private String title;

    @Column(length = 256)
    private String author;

    @Column(name = "source_branch", length = 512)
    private String sourceBranch;

    @Column(name = "target_branch", length = 512)
    private String targetBranch;

    @Column(length = 64)
    private String state;

    @Column(name = "changed_file_count", nullable = false)
    private int changedFileCount;

    @Column(name = "addition_count", nullable = false)
    private int additionCount;

    @Column(name = "deletion_count", nullable = false)
    private int deletionCount;

    @Column(name = "commit_count", nullable = false)
    private int commitCount;

    @Column(name = "provider_status", nullable = false, length = 32)
    private String providerStatus;

    @Column(name = "metadata_json", columnDefinition = "text")
    private String metadataJson;

    @Column(name = "diff_hash", length = 128)
    private String diffHash;

    @Column(name = "error_message", columnDefinition = "text")
    private String errorMessage;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    protected ChangeRequestEntity() {
    }

    public ChangeRequestEntity(
            String id,
            String repositoryId,
            String platform,
            String changeType,
            String ownerName,
            String repositoryName,
            String changeNumber,
            String url,
            String title,
            Instant now
    ) {
        this.id = id;
        this.repositoryId = repositoryId;
        this.platform = platform;
        this.changeType = changeType;
        this.ownerName = ownerName;
        this.repositoryName = repositoryName;
        this.changeNumber = changeNumber;
        this.url = url;
        this.title = title;
        this.providerStatus = "fetched";
        this.createdAt = now;
        this.updatedAt = now;
    }

    public String getId() {
        return id;
    }

    public String getRepositoryId() {
        return repositoryId;
    }

    public String getReviewTaskId() {
        return reviewTaskId;
    }

    public void setReviewTaskId(String reviewTaskId) {
        this.reviewTaskId = reviewTaskId;
    }

    public String getPlatform() {
        return platform;
    }

    public String getChangeType() {
        return changeType;
    }

    public String getOwnerName() {
        return ownerName;
    }

    public String getRepositoryName() {
        return repositoryName;
    }

    public String getChangeNumber() {
        return changeNumber;
    }

    public String getUrl() {
        return url;
    }

    public String getTitle() {
        return title;
    }

    public String getAuthor() {
        return author;
    }

    public void setAuthor(String author) {
        this.author = author;
    }

    public String getSourceBranch() {
        return sourceBranch;
    }

    public void setSourceBranch(String sourceBranch) {
        this.sourceBranch = sourceBranch;
    }

    public String getTargetBranch() {
        return targetBranch;
    }

    public void setTargetBranch(String targetBranch) {
        this.targetBranch = targetBranch;
    }

    public String getState() {
        return state;
    }

    public void setState(String state) {
        this.state = state;
    }

    public int getChangedFileCount() {
        return changedFileCount;
    }

    public void setChangedFileCount(int changedFileCount) {
        this.changedFileCount = changedFileCount;
    }

    public int getAdditionCount() {
        return additionCount;
    }

    public void setAdditionCount(int additionCount) {
        this.additionCount = additionCount;
    }

    public int getDeletionCount() {
        return deletionCount;
    }

    public void setDeletionCount(int deletionCount) {
        this.deletionCount = deletionCount;
    }

    public int getCommitCount() {
        return commitCount;
    }

    public void setCommitCount(int commitCount) {
        this.commitCount = commitCount;
    }

    public String getProviderStatus() {
        return providerStatus;
    }

    public void setProviderStatus(String providerStatus) {
        this.providerStatus = providerStatus;
    }

    public String getMetadataJson() {
        return metadataJson;
    }

    public void setMetadataJson(String metadataJson) {
        this.metadataJson = metadataJson;
    }

    public String getDiffHash() {
        return diffHash;
    }

    public void setDiffHash(String diffHash) {
        this.diffHash = diffHash;
    }

    public String getErrorMessage() {
        return errorMessage;
    }

    public void setErrorMessage(String errorMessage) {
        this.errorMessage = errorMessage;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }

    public Instant getUpdatedAt() {
        return updatedAt;
    }

    public void setUpdatedAt(Instant updatedAt) {
        this.updatedAt = updatedAt;
    }
}
