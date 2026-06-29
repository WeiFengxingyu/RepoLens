package com.repolens.indexing.application;

import com.repolens.indexing.domain.IndexTaskEntity;
import com.repolens.indexing.domain.IndexTaskEventEntity;
import com.repolens.indexing.domain.IndexTaskEventStatus;
import com.repolens.indexing.domain.IndexTaskStatus;
import com.repolens.indexing.infrastructure.IndexTaskEventJpaRepository;
import com.repolens.indexing.infrastructure.IndexTaskJpaRepository;
import com.repolens.common.id.IdGenerator;

import java.time.Clock;
import java.time.Instant;

public class RepositoryIndexContext {

    private final IndexTaskEntity task;
    private final IndexTaskJpaRepository indexTaskJpaRepository;
    private final IndexTaskEventJpaRepository indexTaskEventJpaRepository;
    private final IdGenerator idGenerator;
    private final Clock clock;

    private int fileCount;
    private int parsedFileCount;
    private int chunkCount;
    private int symbolCount;
    private int relationCount;

    public RepositoryIndexContext(
            IndexTaskEntity task,
            IndexTaskJpaRepository indexTaskJpaRepository,
            IndexTaskEventJpaRepository indexTaskEventJpaRepository,
            IdGenerator idGenerator,
            Clock clock
    ) {
        this.task = task;
        this.indexTaskJpaRepository = indexTaskJpaRepository;
        this.indexTaskEventJpaRepository = indexTaskEventJpaRepository;
        this.idGenerator = idGenerator;
        this.clock = clock;
    }

    public void start(IndexTaskStatus stage, int progressPercent) {
        updateTask(stage, progressPercent, null);
        writeEvent(stage, IndexTaskEventStatus.STARTED, null);
    }

    public void succeed(IndexTaskStatus stage, String message) {
        writeEvent(stage, IndexTaskEventStatus.SUCCEEDED, message);
    }

    public void fail(IndexTaskStatus stage, String message) {
        updateTask(IndexTaskStatus.FAILED, task.getProgressPercent(), message);
        writeEvent(stage, IndexTaskEventStatus.FAILED, message);
    }

    public void markReady() {
        Instant now = Instant.now(clock);
        task.setStatus(IndexTaskStatus.READY);
        task.setProgressPercent(100);
        task.setLastError(null);
        task.setFinishedAt(now);
        task.setUpdatedAt(now);
        indexTaskJpaRepository.saveAndFlush(task);
        writeEvent(IndexTaskStatus.READY, IndexTaskEventStatus.SUCCEEDED, "Index task completed");
    }

    public void setCounts(int fileCount, int parsedFileCount, int chunkCount, int symbolCount, int relationCount) {
        this.fileCount = fileCount;
        this.parsedFileCount = parsedFileCount;
        this.chunkCount = chunkCount;
        this.symbolCount = symbolCount;
        this.relationCount = relationCount;
    }

    private void updateTask(IndexTaskStatus stage, int progressPercent, String error) {
        Instant now = Instant.now(clock);
        task.setStatus(stage);
        task.setProgressPercent(progressPercent);
        task.setLastError(error);
        if (task.getStartedAt() == null) {
            task.setStartedAt(now);
        }
        task.setUpdatedAt(now);
        indexTaskJpaRepository.saveAndFlush(task);
    }

    private void writeEvent(IndexTaskStatus stage, IndexTaskEventStatus status, String message) {
        IndexTaskEventEntity event = new IndexTaskEventEntity(
                idGenerator.newId("evt"),
                task.getId(),
                task.getRepositoryId(),
                stage,
                status,
                Instant.now(clock)
        );
        event.setMessage(message);
        event.setFileCount(fileCount);
        event.setParsedFileCount(parsedFileCount);
        event.setChunkCount(chunkCount);
        event.setSymbolCount(symbolCount);
        event.setRelationCount(relationCount);
        indexTaskEventJpaRepository.save(event);
    }
}
