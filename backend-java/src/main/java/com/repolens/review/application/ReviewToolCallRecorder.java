package com.repolens.review.application;

import com.repolens.common.id.IdGenerator;
import com.repolens.review.domain.ReviewToolCallEntity;
import com.repolens.review.infrastructure.ReviewToolCallJpaRepository;
import org.springframework.stereotype.Component;

import java.time.Clock;
import java.time.Duration;
import java.time.Instant;

@Component
public class ReviewToolCallRecorder {

    private final ReviewToolCallJpaRepository reviewToolCallJpaRepository;
    private final IdGenerator idGenerator;
    private final Clock clock;

    public ReviewToolCallRecorder(
            ReviewToolCallJpaRepository reviewToolCallJpaRepository,
            IdGenerator idGenerator,
            Clock clock
    ) {
        this.reviewToolCallJpaRepository = reviewToolCallJpaRepository;
        this.idGenerator = idGenerator;
        this.clock = clock;
    }

    public ReviewToolCallEntity record(
            String taskId,
            String repositoryId,
            String toolName,
            String inputSummary,
            String outputSummary,
            Instant startedAt
    ) {
        Instant completedAt = Instant.now(clock);
        ReviewToolCallEntity entity = new ReviewToolCallEntity(idGenerator.newId("tool"), taskId, repositoryId, toolName, startedAt);
        entity.setInputSummary(inputSummary);
        entity.setOutputSummary(outputSummary);
        entity.setLatencyMs(Duration.between(startedAt, completedAt).toMillis());
        return reviewToolCallJpaRepository.save(entity);
    }
}
