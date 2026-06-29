package com.repolens.evaluation.application;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.repolens.common.error.ResourceNotFoundException;
import com.repolens.common.id.IdGenerator;
import com.repolens.evaluation.api.dto.EvaluationCreateRequest;
import com.repolens.evaluation.api.dto.EvaluationMetricResponse;
import com.repolens.evaluation.api.dto.EvaluationResultResponse;
import com.repolens.evaluation.api.dto.EvaluationRunResponse;
import com.repolens.evaluation.api.dto.EvaluationRunSummaryResponse;
import com.repolens.evaluation.domain.EvaluationResultEntity;
import com.repolens.evaluation.domain.EvaluationRunEntity;
import com.repolens.evaluation.infrastructure.EvaluationResultJpaRepository;
import com.repolens.evaluation.infrastructure.EvaluationRunJpaRepository;
import com.repolens.repository.infrastructure.RepositoryJpaRepository;
import com.repolens.retrieval.api.dto.EvidenceResponse;
import com.repolens.retrieval.api.dto.RetrievalRequest;
import com.repolens.retrieval.api.dto.RetrievalResponse;
import com.repolens.retrieval.application.RetrievalService;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

@Service
public class EvaluationService {

    private final EvaluationRunJpaRepository runJpaRepository;
    private final EvaluationResultJpaRepository resultJpaRepository;
    private final RepositoryJpaRepository repositoryJpaRepository;
    private final EvaluationDatasetReader datasetReader;
    private final EvaluationMetricCalculator metricCalculator;
    private final RetrievalService retrievalService;
    private final IdGenerator idGenerator;
    private final ObjectMapper objectMapper;
    private final Clock clock;

    public EvaluationService(
            EvaluationRunJpaRepository runJpaRepository,
            EvaluationResultJpaRepository resultJpaRepository,
            RepositoryJpaRepository repositoryJpaRepository,
            EvaluationDatasetReader datasetReader,
            EvaluationMetricCalculator metricCalculator,
            RetrievalService retrievalService,
            IdGenerator idGenerator,
            ObjectMapper objectMapper,
            Clock clock
    ) {
        this.runJpaRepository = runJpaRepository;
        this.resultJpaRepository = resultJpaRepository;
        this.repositoryJpaRepository = repositoryJpaRepository;
        this.datasetReader = datasetReader;
        this.metricCalculator = metricCalculator;
        this.retrievalService = retrievalService;
        this.idGenerator = idGenerator;
        this.objectMapper = objectMapper;
        this.clock = clock;
    }

    @Transactional
    public EvaluationRunResponse create(EvaluationCreateRequest request) {
        List<EvaluationSample> samples = datasetReader.read(request.getDatasetPath());
        List<EvaluationStrategy> strategies = EvaluationStrategy.expand(request.getStrategy());
        validateRepositoryMap(samples, request.getRepositoryMap());

        Instant now = Instant.now(clock);
        EvaluationRunEntity run = new EvaluationRunEntity(
                idGenerator.newId("eval"),
                normalizeName(request),
                request.getDatasetPath(),
                request.getStrategy(),
                samples.size(),
                toJson(request.getRepositoryMap()),
                now
        );
        runJpaRepository.saveAndFlush(run);

        List<String> warnings = new java.util.ArrayList<>();
        List<EvaluationResultEntity> results = new java.util.ArrayList<>();
        try {
            for (EvaluationStrategy strategy : strategies) {
                for (EvaluationSample sample : samples) {
                    results.add(evaluate(run.getId(), sample, strategy, request.getRepositoryMap(), request.getTopK()));
                }
            }
            resultJpaRepository.saveAll(results);
            List<EvaluationMetricResponse> metrics = metricCalculator.calculate(results);
            run.setMetrics(toJson(metrics));
            run.setWarnings(toJson(warnings));
            run.setStatus("completed");
            run.setCompletedAt(Instant.now(clock));
            runJpaRepository.save(run);
            return toResponse(run);
        } catch (RuntimeException exception) {
            run.setStatus("failed");
            run.setErrorMessage(exception.getMessage());
            run.setWarnings(toJson(warnings));
            run.setCompletedAt(Instant.now(clock));
            runJpaRepository.save(run);
            throw exception;
        }
    }

    @Transactional(readOnly = true)
    public List<EvaluationRunSummaryResponse> list() {
        return runJpaRepository.findAllByOrderByCreatedAtDesc()
                .stream()
                .map(run -> EvaluationRunSummaryResponse.from(run, objectMapper))
                .toList();
    }

    @Transactional(readOnly = true)
    public EvaluationRunResponse get(String runId) {
        EvaluationRunEntity run = runJpaRepository.findById(runId)
                .orElseThrow(() -> new ResourceNotFoundException("Evaluation run not found"));
        return toResponse(run);
    }

    private EvaluationResultEntity evaluate(
            String runId,
            EvaluationSample sample,
            EvaluationStrategy strategy,
            Map<String, String> repositoryMap,
            Integer topK
    ) {
        Instant startedAt = Instant.now(clock);
        String repositoryId = repositoryMap.get(sample.repositoryKey());
        try {
            RetrievalRequest retrievalRequest = new RetrievalRequest();
            retrievalRequest.setQuery(sample.query());
            retrievalRequest.setTopK(topK == null ? 5 : Math.max(1, Math.min(20, topK)));
            retrievalRequest.setUseBm25(strategy.useBm25());
            retrievalRequest.setUseVector(strategy.useVector());
            retrievalRequest.setUseGraph(strategy.useGraph());
            RetrievalResponse retrieval = retrievalService.retrieve(repositoryId, retrievalRequest);
            long latencyMs = Duration.between(startedAt, Instant.now(clock)).toMillis();
            List<EvidenceResponse> evidences = retrieval.evidences();
            List<String> matchedFiles = matchedFiles(sample, evidences);
            List<String> matchedSymbols = matchedSymbols(sample, evidences);
            return new EvaluationResultEntity(
                    idGenerator.newId("eval_result"),
                    runId,
                    sample.id(),
                    sample.sampleType() == null || sample.sampleType().isBlank() ? "unknown" : sample.sampleType(),
                    sample.repositoryKey(),
                    strategy.value(),
                    hitAtFive(sample, evidences),
                    reciprocalRank(sample, evidences),
                    citationCoverage(sample, evidences),
                    latencyMs,
                    tokenEstimate(evidences),
                    true,
                    toJson(matchedFiles),
                    toJson(matchedSymbols),
                    toJson(citations(evidences)),
                    null,
                    Instant.now(clock)
            );
        } catch (RuntimeException exception) {
            long latencyMs = Duration.between(startedAt, Instant.now(clock)).toMillis();
            return new EvaluationResultEntity(
                    idGenerator.newId("eval_result"),
                    runId,
                    sample.id(),
                    sample.sampleType() == null || sample.sampleType().isBlank() ? "unknown" : sample.sampleType(),
                    sample.repositoryKey(),
                    strategy.value(),
                    false,
                    0.0D,
                    0.0D,
                    latencyMs,
                    0,
                    true,
                    toJson(List.of()),
                    toJson(List.of()),
                    toJson(List.of()),
                    exception.getMessage(),
                    Instant.now(clock)
            );
        }
    }

    private void validateRepositoryMap(List<EvaluationSample> samples, Map<String, String> repositoryMap) {
        if (repositoryMap == null || repositoryMap.isEmpty()) {
            throw new IllegalArgumentException("repository_map is required");
        }
        Set<String> keys = samples.stream().map(EvaluationSample::repositoryKey).collect(java.util.stream.Collectors.toCollection(LinkedHashSet::new));
        for (String key : keys) {
            String repositoryId = repositoryMap.get(key);
            if (repositoryId == null || repositoryId.isBlank()) {
                throw new IllegalArgumentException("Missing repository mapping for key: " + key);
            }
            if (!repositoryJpaRepository.existsById(repositoryId)) {
                throw new IllegalArgumentException("Mapped repository does not exist for key: " + key);
            }
        }
    }

    private boolean hitAtFive(EvaluationSample sample, List<EvidenceResponse> evidences) {
        return evidences.stream().limit(5).anyMatch(evidence -> sample.expectedFiles().contains(evidence.filePath()));
    }

    private double reciprocalRank(EvaluationSample sample, List<EvidenceResponse> evidences) {
        for (int index = 0; index < evidences.size(); index++) {
            if (sample.expectedFiles().contains(evidences.get(index).filePath())) {
                return 1.0D / (index + 1);
            }
        }
        return 0.0D;
    }

    private double citationCoverage(EvaluationSample sample, List<EvidenceResponse> evidences) {
        int expectedCount = sample.expectedFiles().size() + sample.expectedSymbols().size();
        if (expectedCount == 0) {
            return evidences.isEmpty() ? 0.0D : 1.0D;
        }
        Set<String> evidenceFiles = evidences.stream().map(EvidenceResponse::filePath).collect(java.util.stream.Collectors.toSet());
        Set<String> evidenceSymbols = evidences.stream().map(EvidenceResponse::symbolName).collect(java.util.stream.Collectors.toSet());
        int covered = 0;
        for (String expectedFile : sample.expectedFiles()) {
            if (evidenceFiles.contains(expectedFile)) {
                covered++;
            }
        }
        for (String expectedSymbol : sample.expectedSymbols()) {
            if (evidenceSymbols.contains(expectedSymbol)) {
                covered++;
            }
        }
        return (double) covered / expectedCount;
    }

    private List<String> matchedFiles(EvaluationSample sample, List<EvidenceResponse> evidences) {
        return evidences.stream()
                .map(EvidenceResponse::filePath)
                .filter(sample.expectedFiles()::contains)
                .distinct()
                .toList();
    }

    private List<String> matchedSymbols(EvaluationSample sample, List<EvidenceResponse> evidences) {
        return evidences.stream()
                .map(EvidenceResponse::symbolName)
                .filter(sample.expectedSymbols()::contains)
                .distinct()
                .toList();
    }

    private List<Map<String, Object>> citations(List<EvidenceResponse> evidences) {
        return evidences.stream()
                .limit(5)
                .map(evidence -> Map.<String, Object>of(
                        "evidence_id", evidence.evidenceId(),
                        "file_path", evidence.filePath(),
                        "start_line", evidence.startLine(),
                        "end_line", evidence.endLine(),
                        "symbol_name", evidence.symbolName(),
                        "source", evidence.source(),
                        "score", evidence.score()
                ))
                .toList();
    }

    private int tokenEstimate(List<EvidenceResponse> evidences) {
        return evidences.stream()
                .map(EvidenceResponse::snippet)
                .filter(snippet -> snippet != null && !snippet.isBlank())
                .mapToInt(snippet -> snippet.split("\\s+").length)
                .sum();
    }

    private EvaluationRunResponse toResponse(EvaluationRunEntity run) {
        List<EvaluationResultResponse> results = resultJpaRepository.findByRunIdOrderByStrategyAscSampleIdAsc(run.getId())
                .stream()
                .map(result -> EvaluationResultResponse.from(result, objectMapper))
                .toList();
        return EvaluationRunResponse.from(run, results, objectMapper);
    }

    private String normalizeName(EvaluationCreateRequest request) {
        if (request.getName() != null && !request.getName().isBlank()) {
            return request.getName().trim();
        }
        return "Evaluation " + Instant.now(clock);
    }

    private String toJson(Object value) {
        try {
            return objectMapper.writeValueAsString(value);
        } catch (JsonProcessingException exception) {
            throw new IllegalStateException("Failed to serialize evaluation payload", exception);
        }
    }
}
