package com.repolens.mcp.application;

import com.repolens.mcp.api.dto.McpToolCallAuditResponse;
import com.repolens.mcp.api.dto.McpToolCallRequest;
import com.repolens.mcp.api.dto.McpToolCallResponse;
import com.repolens.mcp.api.dto.McpToolInfoResponse;
import org.springframework.stereotype.Service;

import java.time.Clock;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Service
public class McpToolService {

    private final McpToolRegistry toolRegistry;
    private final McpAuditService auditService;
    private final Clock clock;

    public McpToolService(
            McpToolRegistry toolRegistry,
            McpAuditService auditService,
            Clock clock
    ) {
        this.toolRegistry = toolRegistry;
        this.auditService = auditService;
        this.clock = clock;
    }

    public List<McpToolInfoResponse> listTools() {
        return toolRegistry.definitions().stream()
                .map(definition -> new McpToolInfoResponse(
                        definition.name(),
                        definition.description(),
                        definition.inputSchema(),
                        definition.permissionPolicy(),
                        definition.enabled()
                ))
                .toList();
    }

    public McpToolCallResponse call(McpToolCallRequest request) {
        Instant startedAt = Instant.now(clock);
        String toolName = request.getName();
        Map<String, Object> arguments = request.getArguments();
        Map<String, Object> input = new LinkedHashMap<>();
        input.put("name", toolName);
        input.put("arguments", arguments);
        input.put("client_name", request.getClientName());
        input.put("client_session_id", request.getClientSessionId());
        String repositoryId = repositoryId(arguments);

        return toolRegistry.find(toolName)
                .map(tool -> callRegisteredTool(request, tool, input, repositoryId, startedAt))
                .orElseGet(() -> deniedUnknownTool(request, input, repositoryId, startedAt));
    }

    public List<McpToolCallAuditResponse> listAudits(int limit) {
        return auditService.listRecent(limit);
    }

    private McpToolCallResponse callRegisteredTool(
            McpToolCallRequest request,
            McpRegisteredTool tool,
            Object input,
            String repositoryId,
            Instant startedAt
    ) {
        McpToolDefinition definition = tool.definition();
        if (!definition.enabled()) {
            String message = "Tool is disabled by policy";
            McpToolCallAuditResponse audit = auditService.record(
                    repositoryId,
                    definition.name(),
                    "disabled",
                    "disabled",
                    definition.permissionPolicy(),
                    request.getClientName(),
                    request.getClientSessionId(),
                    input,
                    Map.of("message", message),
                    startedAt,
                    message
            );
            return new McpToolCallResponse(audit.id(), definition.name(), "disabled", "disabled", null, message, audit);
        }

        try {
            Object result = tool.handler().execute(new McpToolExecutionContext(definition, request.getArguments()));
            McpToolCallAuditResponse audit = auditService.record(
                    repositoryId(result, repositoryId),
                    definition.name(),
                    "completed",
                    "allow",
                    definition.permissionPolicy(),
                    request.getClientName(),
                    request.getClientSessionId(),
                    input,
                    result,
                    startedAt,
                    null
            );
            return new McpToolCallResponse(audit.id(), definition.name(), "completed", "allow", result, null, audit);
        } catch (McpPermissionException exception) {
            String decision = exception.getDecision() == null ? "deny" : exception.getDecision();
            McpToolCallAuditResponse audit = auditService.record(
                    repositoryId,
                    definition.name(),
                    "disabled".equals(decision) ? "disabled" : "denied",
                    decision,
                    definition.permissionPolicy(),
                    request.getClientName(),
                    request.getClientSessionId(),
                    input,
                    Map.of("error", exception.getMessage()),
                    startedAt,
                    exception.getMessage()
            );
            return new McpToolCallResponse(audit.id(), definition.name(), audit.status(), decision, null, exception.getMessage(), audit);
        } catch (RuntimeException exception) {
            String message = exception.getMessage() == null ? "MCP tool execution failed" : exception.getMessage();
            McpToolCallAuditResponse audit = auditService.record(
                    repositoryId,
                    definition.name(),
                    "failed",
                    "allow",
                    definition.permissionPolicy(),
                    request.getClientName(),
                    request.getClientSessionId(),
                    input,
                    Map.of("error", message),
                    startedAt,
                    message
            );
            return new McpToolCallResponse(audit.id(), definition.name(), "failed", "allow", null, message, audit);
        }
    }

    private McpToolCallResponse deniedUnknownTool(
            McpToolCallRequest request,
            Object input,
            String repositoryId,
            Instant startedAt
    ) {
        String message = "Unknown MCP tool: " + request.getName();
        McpToolCallAuditResponse audit = auditService.record(
                repositoryId,
                request.getName(),
                "denied",
                "deny",
                null,
                request.getClientName(),
                request.getClientSessionId(),
                input,
                Map.of("error", message),
                startedAt,
                message
        );
        return new McpToolCallResponse(audit.id(), request.getName(), "denied", "deny", null, message, audit);
    }

    private String repositoryId(Map<String, Object> arguments) {
        Object value = arguments.get("repository_id");
        if (value instanceof String text && !text.isBlank()) {
            return text.trim();
        }
        return null;
    }

    private String repositoryId(Object result, String fallback) {
        if (result instanceof com.repolens.retrieval.api.dto.RetrievalResponse response) {
            return response.repositoryId();
        }
        if (result instanceof com.repolens.review.api.dto.ReviewTaskResponse response) {
            return response.repositoryId();
        }
        return fallback;
    }
}
