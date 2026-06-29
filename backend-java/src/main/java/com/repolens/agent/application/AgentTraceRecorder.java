package com.repolens.agent.application;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.repolens.agent.domain.AgentTraceEntity;
import com.repolens.agent.infrastructure.AgentTraceJpaRepository;
import com.repolens.common.id.IdGenerator;
import org.springframework.stereotype.Component;

import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;

@Component
public class AgentTraceRecorder {

    private final AgentTraceJpaRepository agentTraceJpaRepository;
    private final IdGenerator idGenerator;
    private final ObjectMapper objectMapper;
    private final Clock clock;

    public AgentTraceRecorder(
            AgentTraceJpaRepository agentTraceJpaRepository,
            IdGenerator idGenerator,
            ObjectMapper objectMapper,
            Clock clock
    ) {
        this.agentTraceJpaRepository = agentTraceJpaRepository;
        this.idGenerator = idGenerator;
        this.objectMapper = objectMapper;
        this.clock = clock;
    }

    public AgentTraceEntity record(
            String taskId,
            String repositoryId,
            String stepName,
            int stepOrder,
            String inputSummary,
            String outputSummary,
            List<String> evidenceIds,
            List<Map<String, Object>> toolCalls,
            Instant startedAt
    ) {
        Instant completedAt = Instant.now(clock);
        AgentTraceEntity trace = new AgentTraceEntity(
                idGenerator.newId("trace"),
                taskId,
                repositoryId,
                stepName,
                stepOrder,
                startedAt
        );
        trace.setInputSummary(inputSummary);
        trace.setOutputSummary(outputSummary);
        trace.setEvidenceIds(toJson(evidenceIds));
        trace.setToolCalls(toJson(toolCalls));
        trace.setTokenUsage("{}");
        trace.setLatencyMs(Duration.between(startedAt, completedAt).toMillis());
        trace.setCompletedAt(completedAt);
        return agentTraceJpaRepository.save(trace);
    }

    private String toJson(Object value) {
        try {
            return objectMapper.writeValueAsString(value);
        } catch (JsonProcessingException exception) {
            throw new IllegalStateException("Failed to serialize agent trace payload", exception);
        }
    }
}
