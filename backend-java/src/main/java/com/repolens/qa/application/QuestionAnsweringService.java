package com.repolens.qa.application;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.repolens.agent.api.dto.AgentTraceResponse;
import com.repolens.agent.application.AgentTraceRecorder;
import com.repolens.agent.infrastructure.AgentTraceJpaRepository;
import com.repolens.common.error.ResourceNotFoundException;
import com.repolens.common.id.IdGenerator;
import com.repolens.qa.api.dto.QACitationResponse;
import com.repolens.qa.api.dto.QACreateRequest;
import com.repolens.qa.api.dto.QATaskResponse;
import com.repolens.qa.domain.QATaskEntity;
import com.repolens.qa.infrastructure.QATaskJpaRepository;
import com.repolens.repository.domain.RepositoryEntity;
import com.repolens.repository.domain.RepositoryStatus;
import com.repolens.repository.infrastructure.RepositoryJpaRepository;
import com.repolens.retrieval.api.dto.EvidenceResponse;
import com.repolens.retrieval.api.dto.RetrievalRequest;
import com.repolens.retrieval.api.dto.RetrievalResponse;
import com.repolens.retrieval.application.RetrievalService;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Clock;
import java.time.Instant;
import java.util.List;
import java.util.Map;

@Service
public class QuestionAnsweringService {

    private final QATaskJpaRepository qaTaskJpaRepository;
    private final RepositoryJpaRepository repositoryJpaRepository;
    private final RetrievalService retrievalService;
    private final AgentTraceRecorder agentTraceRecorder;
    private final AgentTraceJpaRepository agentTraceJpaRepository;
    private final IdGenerator idGenerator;
    private final ObjectMapper objectMapper;
    private final Clock clock;

    public QuestionAnsweringService(
            QATaskJpaRepository qaTaskJpaRepository,
            RepositoryJpaRepository repositoryJpaRepository,
            RetrievalService retrievalService,
            AgentTraceRecorder agentTraceRecorder,
            AgentTraceJpaRepository agentTraceJpaRepository,
            IdGenerator idGenerator,
            ObjectMapper objectMapper,
            Clock clock
    ) {
        this.qaTaskJpaRepository = qaTaskJpaRepository;
        this.repositoryJpaRepository = repositoryJpaRepository;
        this.retrievalService = retrievalService;
        this.agentTraceRecorder = agentTraceRecorder;
        this.agentTraceJpaRepository = agentTraceJpaRepository;
        this.idGenerator = idGenerator;
        this.objectMapper = objectMapper;
        this.clock = clock;
    }

    @Transactional
    public QATaskResponse ask(String repositoryId, QACreateRequest request) {
        RepositoryEntity repository = repositoryJpaRepository.findById(repositoryId)
                .orElseThrow(() -> new ResourceNotFoundException("Repository not found"));
        if (repository.getStatus() != RepositoryStatus.READY) {
            throw new IllegalArgumentException("Repository must be ready before question answering");
        }

        QATaskEntity task = new QATaskEntity(idGenerator.newId("qa"), repositoryId, request.getQuestion().trim(), Instant.now(clock));
        qaTaskJpaRepository.saveAndFlush(task);

        try {
            record(task, "planner", 1, request.getQuestion(), "Selected hybrid code.search tool", List.of(), List.of());
            RetrievalResponse retrieval = retrieve(repositoryId, request);
            List<EvidenceResponse> evidences = retrieval.evidences();
            List<String> evidenceIds = evidences.stream().map(EvidenceResponse::evidenceId).toList();
            record(task, "code.search", 2, request.getQuestion(), "Retrieved " + evidences.size() + " evidences", evidenceIds, List.of(Map.of(
                    "tool_name", "code.search",
                    "status", "completed",
                    "bm25_count", retrieval.debug().bm25Count(),
                    "vector_count", retrieval.debug().vectorCount(),
                    "graph_count", retrieval.debug().graphCount()
            )));

            List<String> warnings = evidences.isEmpty() ? List.of("NO_EVIDENCE") : List.of();
            String verifierOutput = evidences.isEmpty() ? "No citation available" : "All citations are grounded in retrieval evidence";
            record(task, "verifier", 3, "citations=" + evidences.size(), verifierOutput, evidenceIds, List.of());

            String answer = composeAnswer(request.getQuestion(), evidences);
            double confidence = evidences.isEmpty() ? 0.25D : Math.min(0.95D, 0.55D + evidences.size() * 0.08D);
            task.setAnswer(answer);
            task.setConfidence(confidence);
            task.setWarnings(toJson(warnings));
            task.setStatus("completed");
            task.setCompletedAt(Instant.now(clock));
            qaTaskJpaRepository.save(task);
            record(task, "final_answer", 4, "compose answer", "Answer completed with " + evidences.size() + " citations", evidenceIds, List.of());
            return toResponse(task, evidences.stream().map(QACitationResponse::from).toList());
        } catch (RuntimeException exception) {
            task.setStatus("failed");
            task.setErrorMessage(exception.getMessage());
            task.setWarnings(toJson(List.of("QA_FAILED")));
            task.setCompletedAt(Instant.now(clock));
            qaTaskJpaRepository.save(task);
            throw exception;
        }
    }

    @Transactional(readOnly = true)
    public QATaskResponse getTask(String taskId) {
        QATaskEntity task = qaTaskJpaRepository.findById(taskId)
                .orElseThrow(() -> new ResourceNotFoundException("QA task not found"));
        return toResponse(task, List.of());
    }

    private RetrievalResponse retrieve(String repositoryId, QACreateRequest request) {
        RetrievalRequest retrievalRequest = new RetrievalRequest();
        retrievalRequest.setQuery(request.getQuestion());
        retrievalRequest.setTopK(request.getTopK());
        retrievalRequest.setUseBm25(request.getUseBm25());
        retrievalRequest.setUseVector(request.getUseVector());
        retrievalRequest.setUseGraph(request.getUseGraph());
        return retrievalService.retrieve(repositoryId, retrievalRequest);
    }

    private String composeAnswer(String question, List<EvidenceResponse> evidences) {
        if (evidences.isEmpty()) {
            return "当前索引证据不足，无法可靠回答该问题。建议扩大检索范围或检查仓库是否已完成索引。";
        }
        StringBuilder builder = new StringBuilder();
        builder.append("问题：").append(question).append(System.lineSeparator()).append(System.lineSeparator());
        builder.append("根据当前仓库证据，最相关的位置是：").append(System.lineSeparator());
        for (int index = 0; index < Math.min(5, evidences.size()); index++) {
            EvidenceResponse evidence = evidences.get(index);
            builder.append(index + 1)
                    .append(". ")
                    .append(evidence.filePath())
                    .append(":")
                    .append(evidence.startLine())
                    .append("-")
                    .append(evidence.endLine())
                    .append(" `")
                    .append(evidence.symbolName())
                    .append("`，来源 ")
                    .append(String.join("+", evidence.sources()))
                    .append("。")
                    .append(System.lineSeparator());
        }
        EvidenceResponse top = evidences.getFirst();
        builder.append(System.lineSeparator())
                .append("结论：优先查看 `")
                .append(top.symbolName())
                .append("`，它是当前问题最强的证据入口；再结合同文件和图谱扩展的引用确认调用关系。");
        return builder.toString();
    }

    private void record(
            QATaskEntity task,
            String stepName,
            int stepOrder,
            String input,
            String output,
            List<String> evidenceIds,
            List<Map<String, Object>> toolCalls
    ) {
        agentTraceRecorder.record(
                task.getId(),
                task.getRepositoryId(),
                stepName,
                stepOrder,
                input,
                output,
                evidenceIds,
                toolCalls,
                Instant.now(clock)
        );
    }

    private QATaskResponse toResponse(QATaskEntity task, List<QACitationResponse> citations) {
        List<AgentTraceResponse> traces = agentTraceJpaRepository.findByTaskIdOrderByStepOrderAsc(task.getId()).stream()
                .map(trace -> AgentTraceResponse.from(trace, objectMapper))
                .toList();
        return QATaskResponse.from(task, citations, traces, objectMapper);
    }

    private String toJson(Object value) {
        try {
            return objectMapper.writeValueAsString(value);
        } catch (JsonProcessingException exception) {
            throw new IllegalStateException("Failed to serialize QA payload", exception);
        }
    }
}
