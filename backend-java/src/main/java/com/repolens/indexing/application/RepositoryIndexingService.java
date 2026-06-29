package com.repolens.indexing.application;

import com.repolens.common.error.ResourceNotFoundException;
import com.repolens.common.id.IdGenerator;
import com.repolens.indexing.api.dto.IndexTaskEventResponse;
import com.repolens.indexing.api.dto.IndexTaskResponse;
import com.repolens.indexing.domain.IndexTaskEntity;
import com.repolens.indexing.domain.IndexTaskStatus;
import com.repolens.indexing.infrastructure.IndexTaskEventJpaRepository;
import com.repolens.indexing.infrastructure.IndexTaskJpaRepository;
import com.repolens.repository.domain.RepositoryEntity;
import com.repolens.repository.domain.RepositoryStatus;
import com.repolens.repository.infrastructure.RepositoryJpaRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Clock;
import java.time.Instant;
import java.util.List;

@Service
public class RepositoryIndexingService {

    private static final List<IndexTaskStatus> ACTIVE_STATUSES = List.of(
            IndexTaskStatus.CREATED,
            IndexTaskStatus.VALIDATING,
            IndexTaskStatus.SCANNING,
            IndexTaskStatus.PARSING,
            IndexTaskStatus.CHUNKING,
            IndexTaskStatus.BM25_INDEXING,
            IndexTaskStatus.VECTOR_INDEXING,
            IndexTaskStatus.GRAPH_BUILDING
    );

    private final RepositoryJpaRepository repositoryJpaRepository;
    private final IndexTaskJpaRepository indexTaskJpaRepository;
    private final IndexTaskEventJpaRepository indexTaskEventJpaRepository;
    private final RepositoryIndexPipeline repositoryIndexPipeline;
    private final RepositoryIndexLock repositoryIndexLock;
    private final IdGenerator idGenerator;
    private final Clock clock;

    public RepositoryIndexingService(
            RepositoryJpaRepository repositoryJpaRepository,
            IndexTaskJpaRepository indexTaskJpaRepository,
            IndexTaskEventJpaRepository indexTaskEventJpaRepository,
            RepositoryIndexPipeline repositoryIndexPipeline,
            RepositoryIndexLock repositoryIndexLock,
            IdGenerator idGenerator,
            Clock clock
    ) {
        this.repositoryJpaRepository = repositoryJpaRepository;
        this.indexTaskJpaRepository = indexTaskJpaRepository;
        this.indexTaskEventJpaRepository = indexTaskEventJpaRepository;
        this.repositoryIndexPipeline = repositoryIndexPipeline;
        this.repositoryIndexLock = repositoryIndexLock;
        this.idGenerator = idGenerator;
        this.clock = clock;
    }

    @Transactional
    public IndexTaskEntity startIndex(String repositoryId) {
        RepositoryEntity repository = repositoryJpaRepository.findById(repositoryId)
                .orElseThrow(() -> new ResourceNotFoundException("Repository not found"));
        if (!repositoryIndexLock.tryLock(repositoryId)) {
            throw new IllegalStateException("Repository index task is already running");
        }
        IndexTaskEntity task = new IndexTaskEntity(idGenerator.newId("task"), repositoryId, Instant.now(clock));
        indexTaskJpaRepository.saveAndFlush(task);
        try {
            RepositoryIndexContext context = new RepositoryIndexContext(
                    task,
                    indexTaskJpaRepository,
                    indexTaskEventJpaRepository,
                    idGenerator,
                    clock
            );
            repositoryIndexPipeline.rebuild(repository, context);
            context.markReady();
            return task;
        } catch (RuntimeException exception) {
            Instant now = Instant.now(clock);
            task.setStatus(IndexTaskStatus.FAILED);
            task.setLastError(exception.getMessage());
            task.setFinishedAt(now);
            task.setUpdatedAt(now);
            indexTaskJpaRepository.save(task);
            repository.setStatus(RepositoryStatus.FAILED);
            repository.setLastError(exception.getMessage());
            repository.setUpdatedAt(now);
            return task;
        } finally {
            repositoryIndexLock.unlock(repositoryId);
        }
    }

    @Transactional
    public IndexTaskResponse retry(String taskId) {
        IndexTaskEntity task = indexTaskJpaRepository.findById(taskId)
                .orElseThrow(() -> new ResourceNotFoundException("Index task not found"));
        if (task.getStatus() != IndexTaskStatus.FAILED) {
            throw new IllegalArgumentException("Only failed index tasks can be retried");
        }
        IndexTaskEntity retried = startIndex(task.getRepositoryId());
        return toResponse(retried);
    }

    @Transactional(readOnly = true)
    public IndexTaskResponse getTask(String taskId) {
        return toResponse(indexTaskJpaRepository.findById(taskId)
                .orElseThrow(() -> new ResourceNotFoundException("Index task not found")));
    }

    @Transactional(readOnly = true)
    public IndexTaskResponse getLatestTask(String repositoryId) {
        return toResponse(indexTaskJpaRepository.findFirstByRepositoryIdOrderByCreatedAtDesc(repositoryId)
                .orElseThrow(() -> new ResourceNotFoundException("Index task not found")));
    }

    @Transactional(readOnly = true)
    public boolean hasActiveTask(String repositoryId) {
        return !indexTaskJpaRepository.findByRepositoryIdAndStatusIn(repositoryId, ACTIVE_STATUSES).isEmpty();
    }

    private IndexTaskResponse toResponse(IndexTaskEntity task) {
        return IndexTaskResponse.from(
                task,
                indexTaskEventJpaRepository.findByTaskIdOrderByCreatedAtAsc(task.getId()).stream()
                        .map(IndexTaskEventResponse::from)
                        .toList()
        );
    }
}
