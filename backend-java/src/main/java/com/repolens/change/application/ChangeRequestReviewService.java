package com.repolens.change.application;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.repolens.change.api.dto.ChangeRequestMetadataResponse;
import com.repolens.change.api.dto.ChangeRequestReviewCreateRequest;
import com.repolens.change.api.dto.ChangeRequestReviewResponse;
import com.repolens.change.domain.ChangeRequestEntity;
import com.repolens.change.infrastructure.ChangeRequestJpaRepository;
import com.repolens.common.error.ResourceNotFoundException;
import com.repolens.common.id.IdGenerator;
import com.repolens.review.api.dto.ReviewCreateRequest;
import com.repolens.review.api.dto.ReviewTaskResponse;
import com.repolens.review.application.ReviewService;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Clock;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.Map;

@Service
public class ChangeRequestReviewService {

    private final ChangeRequestUrlParser urlParser;
    private final ChangeRequestProviderRegistry providerRegistry;
    private final ChangeRequestJpaRepository changeRequestJpaRepository;
    private final ReviewService reviewService;
    private final IdGenerator idGenerator;
    private final ObjectMapper objectMapper;
    private final DiffHashService diffHashService;
    private final SensitiveTextRedactor redactor;
    private final Clock clock;

    public ChangeRequestReviewService(
            ChangeRequestUrlParser urlParser,
            ChangeRequestProviderRegistry providerRegistry,
            ChangeRequestJpaRepository changeRequestJpaRepository,
            ReviewService reviewService,
            IdGenerator idGenerator,
            ObjectMapper objectMapper,
            DiffHashService diffHashService,
            SensitiveTextRedactor redactor,
            Clock clock
    ) {
        this.urlParser = urlParser;
        this.providerRegistry = providerRegistry;
        this.changeRequestJpaRepository = changeRequestJpaRepository;
        this.reviewService = reviewService;
        this.idGenerator = idGenerator;
        this.objectMapper = objectMapper;
        this.diffHashService = diffHashService;
        this.redactor = redactor;
        this.clock = clock;
    }

    @Transactional
    public ChangeRequestReviewResponse review(String repositoryId, ChangeRequestReviewCreateRequest request) {
        ChangeRequestRef ref = urlParser.parse(request.getUrl());
        FetchedChangeRequest fetched = providerRegistry.resolve(ref).fetch(ref);
        if (fetched.diffText() == null || fetched.diffText().isBlank()) {
            throw new IllegalArgumentException("Provider returned empty diff");
        }

        ChangeRequestEntity entity = toEntity(repositoryId, fetched);
        changeRequestJpaRepository.saveAndFlush(entity);

        ReviewTaskResponse review = reviewService.review(repositoryId, toReviewRequest(request, fetched.diffText()), originSummary(fetched));
        entity.setReviewTaskId(review.taskId());
        entity.setProviderStatus("reviewed");
        entity.setUpdatedAt(Instant.now(clock));
        changeRequestJpaRepository.save(entity);

        return new ChangeRequestReviewResponse(ChangeRequestMetadataResponse.from(entity, objectMapper), review);
    }

    @Transactional(readOnly = true)
    public ChangeRequestMetadataResponse getChangeRequest(String changeRequestId) {
        ChangeRequestEntity entity = changeRequestJpaRepository.findById(changeRequestId)
                .orElseThrow(() -> new ResourceNotFoundException("Change request not found"));
        return ChangeRequestMetadataResponse.from(entity, objectMapper);
    }

    @Transactional(readOnly = true)
    public ChangeRequestMetadataResponse getChangeRequestByTask(String taskId) {
        ChangeRequestEntity entity = changeRequestJpaRepository.findByReviewTaskId(taskId)
                .orElseThrow(() -> new ResourceNotFoundException("Change request not found"));
        return ChangeRequestMetadataResponse.from(entity, objectMapper);
    }

    private ChangeRequestEntity toEntity(String repositoryId, FetchedChangeRequest fetched) {
        ChangeRequestRef ref = fetched.ref();
        Instant now = Instant.now(clock);
        ChangeRequestEntity entity = new ChangeRequestEntity(
                idGenerator.newId("cr"),
                repositoryId,
                ref.platform(),
                ref.changeType(),
                ref.owner(),
                ref.repo(),
                ref.number(),
                ref.url(),
                redactor.redact(fetched.title()),
                now
        );
        entity.setAuthor(redactor.redact(fetched.author()));
        entity.setSourceBranch(redactor.redact(fetched.sourceBranch()));
        entity.setTargetBranch(redactor.redact(fetched.targetBranch()));
        entity.setState(redactor.redact(fetched.state()));
        entity.setCommitCount(fetched.commitCount());
        entity.setChangedFileCount(fetched.changedFiles().size());
        entity.setAdditionCount(fetched.additionCount());
        entity.setDeletionCount(fetched.deletionCount());
        entity.setDiffHash(diffHashService.sha256(fetched.diffText()));
        entity.setMetadataJson(metadataJson(fetched));
        return entity;
    }

    private String metadataJson(FetchedChangeRequest fetched) {
        Map<String, Object> metadata = new LinkedHashMap<>();
        metadata.put("provider_metadata", fetched.metadata());
        metadata.put("changed_files", fetched.changedFiles());
        metadata.put("warnings", fetched.warnings());
        try {
            return redactor.redact(objectMapper.writeValueAsString(metadata));
        } catch (JsonProcessingException exception) {
            throw new IllegalStateException("Failed to serialize change request metadata", exception);
        }
    }

    private ReviewCreateRequest toReviewRequest(ChangeRequestReviewCreateRequest request, String diffText) {
        ReviewCreateRequest reviewRequest = new ReviewCreateRequest();
        reviewRequest.setDiffText(diffText);
        reviewRequest.setTopK(request.getTopK());
        reviewRequest.setUseBm25(request.getUseBm25());
        reviewRequest.setUseVector(request.getUseVector());
        reviewRequest.setUseGraph(request.getUseGraph());
        reviewRequest.setRunStaticCheck(request.getRunStaticCheck());
        return reviewRequest;
    }

    private String originSummary(FetchedChangeRequest fetched) {
        ChangeRequestRef ref = fetched.ref();
        return "Change request " + ref.platform() + " " + ref.owner() + "/" + ref.repo() + "#" + ref.number() + " fetched.";
    }
}
