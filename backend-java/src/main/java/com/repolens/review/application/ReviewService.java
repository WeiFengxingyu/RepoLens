package com.repolens.review.application;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.repolens.agent.api.dto.AgentTraceResponse;
import com.repolens.agent.application.AgentTraceRecorder;
import com.repolens.agent.infrastructure.AgentTraceJpaRepository;
import com.repolens.common.error.ResourceNotFoundException;
import com.repolens.common.id.IdGenerator;
import com.repolens.repository.domain.RepositoryEntity;
import com.repolens.repository.domain.RepositoryStatus;
import com.repolens.repository.infrastructure.RepositoryJpaRepository;
import com.repolens.retrieval.api.dto.EvidenceResponse;
import com.repolens.retrieval.api.dto.RetrievalRequest;
import com.repolens.retrieval.api.dto.RetrievalResponse;
import com.repolens.retrieval.application.RetrievalService;
import com.repolens.review.api.dto.ReviewCreateRequest;
import com.repolens.review.api.dto.ReviewTaskResponse;
import com.repolens.review.api.dto.ReviewToolCallResponse;
import com.repolens.review.domain.ReviewTaskEntity;
import com.repolens.review.infrastructure.ReviewTaskJpaRepository;
import com.repolens.review.infrastructure.ReviewToolCallJpaRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Clock;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
public class ReviewService {

    private static final TypeReference<List<Map<String, Object>>> MAP_LIST = new TypeReference<>() {
    };

    private final ReviewTaskJpaRepository reviewTaskJpaRepository;
    private final ReviewToolCallJpaRepository reviewToolCallJpaRepository;
    private final RepositoryJpaRepository repositoryJpaRepository;
    private final DiffParser diffParser;
    private final ReviewRiskRuleEngine riskRuleEngine;
    private final RetrievalService retrievalService;
    private final ReviewToolCallRecorder toolCallRecorder;
    private final AgentTraceRecorder agentTraceRecorder;
    private final AgentTraceJpaRepository agentTraceJpaRepository;
    private final IdGenerator idGenerator;
    private final ObjectMapper objectMapper;
    private final Clock clock;

    public ReviewService(
            ReviewTaskJpaRepository reviewTaskJpaRepository,
            ReviewToolCallJpaRepository reviewToolCallJpaRepository,
            RepositoryJpaRepository repositoryJpaRepository,
            DiffParser diffParser,
            ReviewRiskRuleEngine riskRuleEngine,
            RetrievalService retrievalService,
            ReviewToolCallRecorder toolCallRecorder,
            AgentTraceRecorder agentTraceRecorder,
            AgentTraceJpaRepository agentTraceJpaRepository,
            IdGenerator idGenerator,
            ObjectMapper objectMapper,
            Clock clock
    ) {
        this.reviewTaskJpaRepository = reviewTaskJpaRepository;
        this.reviewToolCallJpaRepository = reviewToolCallJpaRepository;
        this.repositoryJpaRepository = repositoryJpaRepository;
        this.diffParser = diffParser;
        this.riskRuleEngine = riskRuleEngine;
        this.retrievalService = retrievalService;
        this.toolCallRecorder = toolCallRecorder;
        this.agentTraceRecorder = agentTraceRecorder;
        this.agentTraceJpaRepository = agentTraceJpaRepository;
        this.idGenerator = idGenerator;
        this.objectMapper = objectMapper;
        this.clock = clock;
    }

    @Transactional
    public ReviewTaskResponse review(String repositoryId, ReviewCreateRequest request) {
        return review(repositoryId, request, null);
    }

    @Transactional
    public ReviewTaskResponse review(String repositoryId, ReviewCreateRequest request, String originSummary) {
        RepositoryEntity repository = repositoryJpaRepository.findById(repositoryId)
                .orElseThrow(() -> new ResourceNotFoundException("Repository not found"));
        if (repository.getStatus() != RepositoryStatus.READY) {
            throw new IllegalArgumentException("Repository must be ready before review");
        }

        ReviewTaskEntity task = new ReviewTaskEntity(idGenerator.newId("review"), repositoryId, request.getDiffText(), Instant.now(clock));
        reviewTaskJpaRepository.saveAndFlush(task);

        try {
            Instant parseStart = Instant.now(clock);
            ParsedDiff parsedDiff = diffParser.parse(request.getDiffText());
            toolCallRecorder.record(task.getId(), repositoryId, "diff.parse", "diff length=" + request.getDiffText().length(), "files=" + parsedDiff.changedFileCount(), parseStart);
            trace(task, "diff.parse", 1, "parse unified diff", "Parsed " + parsedDiff.changedFileCount() + " files", List.of(), List.of());

            String query = buildSearchQuery(parsedDiff);
            Instant searchStart = Instant.now(clock);
            RetrievalResponse retrieval = retrieve(repositoryId, request, query);
            List<EvidenceResponse> evidences = retrieval.evidences();
            List<String> evidenceIds = evidences.stream().map(EvidenceResponse::evidenceId).toList();
            toolCallRecorder.record(task.getId(), repositoryId, "code.search", query, "evidences=" + evidences.size(), searchStart);
            trace(task, "code.search", 2, query, "Retrieved " + evidences.size() + " evidences", evidenceIds, List.of(Map.of(
                    "tool_name", "code.search",
                    "status", "completed",
                    "bm25_count", retrieval.debug().bm25Count(),
                    "vector_count", retrieval.debug().vectorCount(),
                    "graph_count", retrieval.debug().graphCount()
            )));

            Instant ruleStart = Instant.now(clock);
            List<Map<String, Object>> citations = evidences.stream().map(this::citation).toList();
            List<Map<String, Object>> risks = riskRuleEngine.evaluate(parsedDiff, evidenceIds);
            toolCallRecorder.record(task.getId(), repositoryId, "risk.rules", "added_lines=" + parsedDiff.addedLineCount(), "risks=" + risks.size(), ruleStart);
            trace(task, "risk.rules", 3, "evaluate deterministic rules", "Generated " + risks.size() + " risks", evidenceIds, List.of());

            List<String> impactedSymbols = impactedSymbols(parsedDiff, evidences);
            List<Map<String, Object>> suggestedTests = suggestedTests(parsedDiff, risks);
            String riskLevel = riskLevel(risks);
            String summaryPrefix = originSummary == null || originSummary.isBlank() ? "" : originSummary + " ";
            String summary = summaryPrefix + "Review completed for " + parsedDiff.changedFileCount() + " changed files, " + risks.size() + " findings.";
            String markdown = markdown(summary, riskLevel, risks, suggestedTests, citations);

            task.setSummary(summary);
            task.setRiskLevel(riskLevel);
            task.setRisks(toJson(risks));
            task.setImpactedSymbols(toJson(impactedSymbols));
            task.setSuggestedTests(toJson(suggestedTests));
            task.setCitations(toJson(citations));
            task.setMarkdown(markdown);
            task.setStatus("completed");
            task.setCompletedAt(Instant.now(clock));
            reviewTaskJpaRepository.save(task);
            trace(task, "final_report", 4, "compose markdown", "Review report completed", evidenceIds, List.of());
            return toResponse(task);
        } catch (RuntimeException exception) {
            task.setStatus("failed");
            task.setErrorMessage(exception.getMessage());
            task.setCompletedAt(Instant.now(clock));
            reviewTaskJpaRepository.save(task);
            throw exception;
        }
    }

    @Transactional(readOnly = true)
    public ReviewTaskResponse getReview(String taskId) {
        ReviewTaskEntity task = reviewTaskJpaRepository.findById(taskId)
                .orElseThrow(() -> new ResourceNotFoundException("Review task not found"));
        return toResponse(task);
    }

    private RetrievalResponse retrieve(String repositoryId, ReviewCreateRequest request, String query) {
        RetrievalRequest retrievalRequest = new RetrievalRequest();
        retrievalRequest.setQuery(query.isBlank() ? "changed code review risk" : query);
        retrievalRequest.setTopK(request.getTopK());
        retrievalRequest.setUseBm25(request.getUseBm25());
        retrievalRequest.setUseVector(request.getUseVector());
        retrievalRequest.setUseGraph(request.getUseGraph());
        return retrievalService.retrieve(repositoryId, retrievalRequest);
    }

    private String buildSearchQuery(ParsedDiff diff) {
        String changedPaths = diff.files().stream().map(ChangedFile::displayPath).collect(Collectors.joining(" "));
        String added = diff.files().stream()
                .flatMap(file -> file.hunks().stream())
                .flatMap(hunk -> hunk.lines().stream())
                .filter(line -> line.type() == DiffLineType.ADDED)
                .map(DiffLine::content)
                .limit(12)
                .collect(Collectors.joining(" "));
        return (changedPaths + " " + added).trim();
    }

    private Map<String, Object> citation(EvidenceResponse evidence) {
        Map<String, Object> citation = new LinkedHashMap<>();
        citation.put("evidence_id", evidence.evidenceId());
        citation.put("chunk_id", evidence.chunkId());
        citation.put("file_path", evidence.filePath());
        citation.put("start_line", evidence.startLine());
        citation.put("end_line", evidence.endLine());
        citation.put("symbol_name", evidence.symbolName());
        citation.put("score", evidence.score());
        citation.put("sources", evidence.sources());
        citation.put("snippet", evidence.snippet());
        return citation;
    }

    private List<String> impactedSymbols(ParsedDiff diff, List<EvidenceResponse> evidences) {
        java.util.LinkedHashSet<String> impacted = new java.util.LinkedHashSet<>();
        diff.files().stream().map(ChangedFile::displayPath).forEach(impacted::add);
        evidences.stream()
                .map(EvidenceResponse::symbolName)
                .filter(value -> value != null && !value.isBlank())
                .limit(8)
                .forEach(impacted::add);
        return List.copyOf(impacted);
    }

    private List<Map<String, Object>> suggestedTests(ParsedDiff diff, List<Map<String, Object>> risks) {
        String target = diff.files().isEmpty() ? "changed module" : diff.files().getFirst().displayPath();
        List<Map<String, Object>> tests = new java.util.ArrayList<>();
        tests.add(Map.of(
                "target", target,
                "reason", "覆盖本次 diff 影响的主路径和回归场景。",
                "test_type", "regression",
                "related_risk_titles", risks.stream().map(risk -> String.valueOf(risk.get("title"))).toList(),
                "file_path", target
        ));
        if (risks.stream().anyMatch(risk -> "high".equalsIgnoreCase(String.valueOf(risk.get("severity"))))) {
            tests.add(Map.of(
                    "target", target,
                    "reason", "高风险变更需要补充安全或异常路径测试。",
                    "test_type", "security",
                    "related_risk_titles", risks.stream().filter(risk -> "high".equalsIgnoreCase(String.valueOf(risk.get("severity")))).map(risk -> String.valueOf(risk.get("title"))).toList(),
                    "file_path", target
            ));
        }
        return tests;
    }

    private String riskLevel(List<Map<String, Object>> risks) {
        if (risks.stream().anyMatch(risk -> "high".equalsIgnoreCase(String.valueOf(risk.get("severity"))))) {
            return "high";
        }
        if (risks.stream().anyMatch(risk -> "medium".equalsIgnoreCase(String.valueOf(risk.get("severity"))))) {
            return "medium";
        }
        return "low";
    }

    private String markdown(String summary, String riskLevel, List<Map<String, Object>> risks, List<Map<String, Object>> tests, List<Map<String, Object>> citations) {
        StringBuilder builder = new StringBuilder();
        builder.append("# RepoLens Review").append(System.lineSeparator()).append(System.lineSeparator());
        builder.append("Risk level: ").append(riskLevel).append(System.lineSeparator()).append(System.lineSeparator());
        builder.append(summary).append(System.lineSeparator()).append(System.lineSeparator());
        builder.append("## Findings").append(System.lineSeparator());
        for (Map<String, Object> risk : risks) {
            builder.append("- [").append(risk.get("severity")).append("] ").append(risk.get("title")).append(": ").append(risk.get("reason")).append(System.lineSeparator());
        }
        builder.append(System.lineSeparator()).append("## Suggested Tests").append(System.lineSeparator());
        for (Map<String, Object> test : tests) {
            builder.append("- ").append(test.get("test_type")).append(" test for `").append(test.get("target")).append("`: ").append(test.get("reason")).append(System.lineSeparator());
        }
        builder.append(System.lineSeparator()).append("## Evidence").append(System.lineSeparator());
        for (Map<String, Object> citation : citations.stream().limit(5).toList()) {
            builder.append("- ").append(citation.get("file_path")).append(":").append(citation.get("start_line")).append("-").append(citation.get("end_line")).append(" `").append(citation.get("symbol_name")).append("`").append(System.lineSeparator());
        }
        return builder.toString();
    }

    private void trace(
            ReviewTaskEntity task,
            String stepName,
            int stepOrder,
            String input,
            String output,
            List<String> evidenceIds,
            List<Map<String, Object>> toolCalls
    ) {
        agentTraceRecorder.record(task.getId(), task.getRepositoryId(), stepName, stepOrder, input, output, evidenceIds, toolCalls, Instant.now(clock));
    }

    private ReviewTaskResponse toResponse(ReviewTaskEntity task) {
        List<ReviewToolCallResponse> toolCalls = reviewToolCallJpaRepository.findByTaskIdOrderByCreatedAtAsc(task.getId())
                .stream()
                .map(ReviewToolCallResponse::from)
                .toList();
        List<AgentTraceResponse> traces = agentTraceJpaRepository.findByTaskIdOrderByStepOrderAsc(task.getId()).stream()
                .map(trace -> AgentTraceResponse.from(trace, objectMapper))
                .toList();
        return ReviewTaskResponse.from(task, toolCalls, traces, objectMapper);
    }

    private String toJson(Object value) {
        try {
            return objectMapper.writeValueAsString(value);
        } catch (JsonProcessingException exception) {
            throw new IllegalStateException("Failed to serialize review payload", exception);
        }
    }
}
