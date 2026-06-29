package com.repolens.mcp.application;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.repolens.common.id.IdGenerator;
import com.repolens.mcp.api.dto.McpToolCallAuditResponse;
import com.repolens.mcp.domain.McpToolCallAuditEntity;
import com.repolens.mcp.infrastructure.McpToolCallAuditJpaRepository;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;

@Service
public class McpAuditService {

    private static final int SUMMARY_LIMIT = 300;

    private final McpToolCallAuditJpaRepository auditJpaRepository;
    private final IdGenerator idGenerator;
    private final ObjectMapper objectMapper;
    private final Clock clock;

    public McpAuditService(
            McpToolCallAuditJpaRepository auditJpaRepository,
            IdGenerator idGenerator,
            ObjectMapper objectMapper,
            Clock clock
    ) {
        this.auditJpaRepository = auditJpaRepository;
        this.idGenerator = idGenerator;
        this.objectMapper = objectMapper;
        this.clock = clock;
    }

    @Transactional
    public McpToolCallAuditResponse record(
            String repositoryId,
            String toolName,
            String status,
            String permissionDecision,
            String permissionPolicy,
            String clientName,
            String clientSessionId,
            Object input,
            Object output,
            Instant startedAt,
            String errorMessage
    ) {
        Instant completedAt = Instant.now(clock);
        McpToolCallAuditEntity entity = new McpToolCallAuditEntity(
                idGenerator.newId("mcp_call"),
                idGenerator.newId("mcp_task"),
                repositoryId,
                toolName,
                status,
                permissionDecision,
                permissionPolicy,
                clientName,
                clientSessionId,
                hash(input),
                output == null ? null : hash(output),
                summarize(input),
                output == null ? null : summarize(output),
                Duration.between(startedAt, completedAt).toMillis(),
                errorMessage,
                startedAt,
                completedAt
        );
        return McpToolCallAuditResponse.from(auditJpaRepository.save(entity));
    }

    @Transactional(readOnly = true)
    public List<McpToolCallAuditResponse> listRecent(int limit) {
        int boundedLimit = Math.max(1, Math.min(200, limit));
        return auditJpaRepository.findByOrderByCreatedAtDesc(PageRequest.of(0, boundedLimit))
                .stream()
                .map(McpToolCallAuditResponse::from)
                .toList();
    }

    private String hash(Object value) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] encoded = canonicalJson(value).getBytes(StandardCharsets.UTF_8);
            return HexFormat.of().formatHex(digest.digest(encoded));
        } catch (NoSuchAlgorithmException exception) {
            throw new IllegalStateException("SHA-256 is unavailable", exception);
        }
    }

    private String summarize(Object value) {
        String text;
        if (value instanceof Map<?, ?> map) {
            text = map.toString();
        } else {
            text = String.valueOf(value);
        }
        text = text.replaceAll("(?i)(authorization|token|password|secret)=([^,}\\s]+)", "$1=[redacted]");
        if (text.length() <= SUMMARY_LIMIT) {
            return text;
        }
        return text.substring(0, SUMMARY_LIMIT) + "...";
    }

    private String canonicalJson(Object value) {
        try {
            return objectMapper.writeValueAsString(value);
        } catch (JsonProcessingException exception) {
            return String.valueOf(value);
        }
    }
}
