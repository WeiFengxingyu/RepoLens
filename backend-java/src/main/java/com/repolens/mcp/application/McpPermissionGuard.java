package com.repolens.mcp.application;

import com.repolens.repository.domain.RepositoryEntity;
import com.repolens.repository.domain.RepositoryStatus;
import com.repolens.repository.infrastructure.RepositoryJpaRepository;
import org.springframework.stereotype.Component;

import java.nio.file.Path;
import java.util.Locale;
import java.util.Map;
import java.util.Set;

@Component
public class McpPermissionGuard {

    public static final int MAX_FILE_LINES = 200;
    public static final int MAX_TOP_K = 20;
    public static final int MAX_DIFF_CHARS = 20_000;

    private static final Set<String> SENSITIVE_FILENAMES = Set.of(
            ".env",
            ".env.local",
            ".env.production",
            "id_rsa",
            "id_dsa",
            "known_hosts",
            "credentials",
            "credentials.json"
    );

    private static final Set<String> SENSITIVE_EXTENSIONS = Set.of(
            ".pem",
            ".key",
            ".p12",
            ".pfx",
            ".jks",
            ".keystore"
    );

    private final RepositoryJpaRepository repositoryJpaRepository;

    public McpPermissionGuard(RepositoryJpaRepository repositoryJpaRepository) {
        this.repositoryJpaRepository = repositoryJpaRepository;
    }

    public RepositoryEntity requireRepository(Map<String, Object> arguments) {
        String repositoryId = requiredString(arguments, "repository_id");
        RepositoryEntity repository = repositoryJpaRepository.findById(repositoryId)
                .orElseThrow(() -> new McpPermissionException("deny", "Repository not found"));
        if (repository.getStatus() != RepositoryStatus.READY) {
            throw new McpPermissionException("deny", "Repository must be ready before MCP tool execution");
        }
        return repository;
    }

    public String validateRelativeFilePath(RepositoryEntity repository, Map<String, Object> arguments) {
        String rawPath = requiredString(arguments, "file_path");
        Path relative = Path.of(rawPath);
        if (relative.isAbsolute()) {
            throw new McpPermissionException("deny", "Absolute paths are not allowed");
        }
        Path normalized = relative.normalize();
        if (normalized.startsWith("..") || normalized.toString().contains(".." + java.io.File.separator)) {
            throw new McpPermissionException("deny", "Path traversal is not allowed");
        }
        String normalizedPath = normalized.toString().replace('\\', '/');
        if (normalizedPath.isBlank() || normalizedPath.startsWith("../") || normalizedPath.contains("/../")) {
            throw new McpPermissionException("deny", "Path traversal is not allowed");
        }
        denySensitivePath(normalizedPath);
        Path root = Path.of(repository.getLocalPath()).toAbsolutePath().normalize();
        Path resolved = root.resolve(normalizedPath).toAbsolutePath().normalize();
        if (!resolved.startsWith(root)) {
            throw new McpPermissionException("deny", "Resolved path escapes repository root");
        }
        return normalizedPath;
    }

    public int boundedTopK(Map<String, Object> arguments) {
        return boundedInt(arguments, "top_k", 8, 1, MAX_TOP_K);
    }

    public int boundedStartLine(Map<String, Object> arguments) {
        return boundedInt(arguments, "start_line", 1, 1, Integer.MAX_VALUE);
    }

    public int boundedEndLine(Map<String, Object> arguments, int startLine) {
        int requested = boundedInt(arguments, "end_line", startLine + MAX_FILE_LINES - 1, startLine, Integer.MAX_VALUE);
        return Math.min(requested, startLine + MAX_FILE_LINES - 1);
    }

    public void validateDiffLength(Map<String, Object> arguments) {
        String diffText = requiredString(arguments, "diff_text");
        if (diffText.length() > MAX_DIFF_CHARS) {
            throw new McpPermissionException("deny", "Diff text exceeds MCP limit of " + MAX_DIFF_CHARS + " characters");
        }
    }

    public String requiredString(Map<String, Object> arguments, String key) {
        Object value = arguments.get(key);
        if (!(value instanceof String text) || text.isBlank()) {
            throw new McpPermissionException("deny", key + " is required");
        }
        return text.trim();
    }

    public boolean optionalBoolean(Map<String, Object> arguments, String key, boolean fallback) {
        Object value = arguments.get(key);
        if (value == null) {
            return fallback;
        }
        if (value instanceof Boolean bool) {
            return bool;
        }
        if (value instanceof String text && !text.isBlank()) {
            return Boolean.parseBoolean(text);
        }
        return fallback;
    }

    private int boundedInt(Map<String, Object> arguments, String key, int fallback, int min, int max) {
        Object value = arguments.get(key);
        int parsed = fallback;
        if (value instanceof Number number) {
            parsed = number.intValue();
        } else if (value instanceof String text && !text.isBlank()) {
            try {
                parsed = Integer.parseInt(text);
            } catch (NumberFormatException ignored) {
                parsed = fallback;
            }
        }
        return Math.max(min, Math.min(max, parsed));
    }

    private void denySensitivePath(String normalizedPath) {
        String fileName = Path.of(normalizedPath).getFileName().toString().toLowerCase(Locale.ROOT);
        if (SENSITIVE_FILENAMES.contains(fileName)) {
            throw new McpPermissionException("deny", "Sensitive files are not readable through MCP tools");
        }
        for (String extension : SENSITIVE_EXTENSIONS) {
            if (fileName.endsWith(extension)) {
                throw new McpPermissionException("deny", "Sensitive files are not readable through MCP tools");
            }
        }
        String lowered = normalizedPath.toLowerCase(Locale.ROOT);
        if (lowered.contains("secret") || lowered.contains("private_key")) {
            throw new McpPermissionException("deny", "Sensitive files are not readable through MCP tools");
        }
    }
}
