package com.repolens.mcp.application;

import com.repolens.graph.application.CodeGraphService;
import com.repolens.repository.domain.RepositoryEntity;
import com.repolens.retrieval.api.dto.RetrievalRequest;
import com.repolens.retrieval.application.RetrievalService;
import com.repolens.review.api.dto.ReviewCreateRequest;
import com.repolens.review.application.ReviewService;
import org.springframework.stereotype.Component;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@Component
public class McpToolRegistry {

    private final McpPermissionGuard permissionGuard;
    private final RetrievalService retrievalService;
    private final CodeGraphService codeGraphService;
    private final ReviewService reviewService;
    private final Map<String, McpRegisteredTool> tools;

    public McpToolRegistry(
            McpPermissionGuard permissionGuard,
            RetrievalService retrievalService,
            CodeGraphService codeGraphService,
            ReviewService reviewService
    ) {
        this.permissionGuard = permissionGuard;
        this.retrievalService = retrievalService;
        this.codeGraphService = codeGraphService;
        this.reviewService = reviewService;
        this.tools = buildTools();
    }

    public List<McpToolDefinition> definitions() {
        return tools.values().stream().map(McpRegisteredTool::definition).toList();
    }

    public Optional<McpRegisteredTool> find(String name) {
        return Optional.ofNullable(tools.get(name));
    }

    private Map<String, McpRegisteredTool> buildTools() {
        Map<String, McpRegisteredTool> registered = new LinkedHashMap<>();
        register(registered, definition(
                "repolens.search",
                "Search repository code with BM25, vector, and graph expansion.",
                "read_only:repository",
                true,
                Map.of(
                        "repository_id", "string",
                        "query", "string",
                        "top_k", "integer<=20",
                        "use_bm25", "boolean",
                        "use_vector", "boolean",
                        "use_graph", "boolean"
                )
        ), this::search);
        register(registered, definition(
                "repolens.read_file",
                "Read a bounded line slice from a scanned repository file.",
                "read_only:repository_file",
                true,
                Map.of(
                        "repository_id", "string",
                        "file_path", "relative string",
                        "start_line", "integer",
                        "end_line", "integer"
                )
        ), this::readFile);
        register(registered, definition(
                "repolens.find_symbol",
                "Find symbols in the persisted code graph.",
                "read_only:code_graph",
                true,
                Map.of(
                        "repository_id", "string",
                        "query", "string"
                )
        ), this::findSymbol);
        register(registered, definition(
                "repolens.graph_neighbors",
                "Return incoming and outgoing graph relations for one symbol.",
                "read_only:code_graph",
                true,
                Map.of(
                        "repository_id", "string",
                        "symbol_id", "string"
                )
        ), this::graphNeighbors);
        register(registered, definition(
                "repolens.review_diff",
                "Run deterministic repository-aware diff review.",
                "read_only:analysis",
                true,
                Map.of(
                        "repository_id", "string",
                        "diff_text", "string<=20000",
                        "top_k", "integer<=20",
                        "use_bm25", "boolean",
                        "use_vector", "boolean",
                        "use_graph", "boolean"
                )
        ), this::reviewDiff);
        register(registered, definition(
                "repolens.safe_static_check",
                "Reserved execution-class tool. Disabled until sandbox policy is introduced.",
                "disabled:execution_class",
                false,
                Map.of("repository_id", "string")
        ), context -> Map.of());
        return Collections.unmodifiableMap(new LinkedHashMap<>(registered));
    }

    private Object search(McpToolExecutionContext context) {
        Map<String, Object> arguments = context.arguments();
        RepositoryEntity repository = permissionGuard.requireRepository(arguments);
        RetrievalRequest request = new RetrievalRequest();
        request.setQuery(permissionGuard.requiredString(arguments, "query"));
        request.setTopK(permissionGuard.boundedTopK(arguments));
        request.setUseBm25(permissionGuard.optionalBoolean(arguments, "use_bm25", true));
        request.setUseVector(permissionGuard.optionalBoolean(arguments, "use_vector", true));
        request.setUseGraph(permissionGuard.optionalBoolean(arguments, "use_graph", true));
        return retrievalService.retrieve(repository.getId(), request);
    }

    private Object readFile(McpToolExecutionContext context) {
        Map<String, Object> arguments = context.arguments();
        RepositoryEntity repository = permissionGuard.requireRepository(arguments);
        String relativePath = permissionGuard.validateRelativeFilePath(repository, arguments);
        int startLine = permissionGuard.boundedStartLine(arguments);
        int endLine = permissionGuard.boundedEndLine(arguments, startLine);
        Path file = Path.of(repository.getLocalPath()).toAbsolutePath().normalize().resolve(relativePath).normalize();
        if (!Files.exists(file) || !Files.isRegularFile(file)) {
            throw new McpPermissionException("deny", "File is not available in repository");
        }
        try {
            List<String> lines = Files.readAllLines(file, StandardCharsets.UTF_8);
            int fromIndex = Math.max(0, startLine - 1);
            int toIndex = Math.min(lines.size(), endLine);
            List<String> selected = fromIndex >= lines.size() ? List.of() : lines.subList(fromIndex, toIndex);
            return Map.of(
                    "repository_id", repository.getId(),
                    "file_path", relativePath,
                    "start_line", startLine,
                    "end_line", startLine + selected.size() - 1,
                    "line_count", selected.size(),
                    "content", String.join(System.lineSeparator(), selected)
            );
        } catch (java.io.IOException exception) {
            throw new IllegalStateException("Failed to read repository file", exception);
        }
    }

    private Object findSymbol(McpToolExecutionContext context) {
        Map<String, Object> arguments = context.arguments();
        RepositoryEntity repository = permissionGuard.requireRepository(arguments);
        String query = permissionGuard.requiredString(arguments, "query");
        return codeGraphService.searchSymbols(repository.getId(), query);
    }

    private Object graphNeighbors(McpToolExecutionContext context) {
        Map<String, Object> arguments = context.arguments();
        RepositoryEntity repository = permissionGuard.requireRepository(arguments);
        String symbolId = permissionGuard.requiredString(arguments, "symbol_id");
        return codeGraphService.neighbors(repository.getId(), symbolId);
    }

    private Object reviewDiff(McpToolExecutionContext context) {
        Map<String, Object> arguments = context.arguments();
        RepositoryEntity repository = permissionGuard.requireRepository(arguments);
        permissionGuard.validateDiffLength(arguments);
        ReviewCreateRequest request = new ReviewCreateRequest();
        request.setDiffText(permissionGuard.requiredString(arguments, "diff_text"));
        request.setTopK(permissionGuard.boundedTopK(arguments));
        request.setUseBm25(permissionGuard.optionalBoolean(arguments, "use_bm25", true));
        request.setUseVector(permissionGuard.optionalBoolean(arguments, "use_vector", true));
        request.setUseGraph(permissionGuard.optionalBoolean(arguments, "use_graph", true));
        request.setRunStaticCheck(false);
        return reviewService.review(repository.getId(), request);
    }

    private void register(Map<String, McpRegisteredTool> registered, McpToolDefinition definition, McpToolHandler handler) {
        registered.put(definition.name(), new McpRegisteredTool(definition, handler));
    }

    private McpToolDefinition definition(
            String name,
            String description,
            String permissionPolicy,
            boolean enabled,
            Map<String, Object> properties
    ) {
        Map<String, Object> schema = new LinkedHashMap<>();
        schema.put("type", "object");
        schema.put("properties", properties);
        schema.put("required", List.of("repository_id"));
        return new McpToolDefinition(name, description, schema, permissionPolicy, enabled);
    }
}
