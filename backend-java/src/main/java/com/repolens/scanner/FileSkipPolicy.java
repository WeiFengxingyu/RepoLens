package com.repolens.scanner;

import com.repolens.config.RepoLensProperties;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.attribute.BasicFileAttributes;
import java.util.Locale;
import java.util.Set;
import java.util.regex.Pattern;

@Component
public class FileSkipPolicy {

    private static final Set<String> IGNORED_DIRECTORIES = Set.of(
            ".git",
            ".hg",
            ".svn",
            ".idea",
            ".vscode",
            ".gradle",
            ".mvn/wrapper",
            "node_modules",
            "dist",
            "build",
            "target",
            "out",
            "coverage",
            ".next",
            ".venv",
            "venv",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            "vendor"
    );

    private static final Pattern IGNORED_FILE_PATTERN = Pattern.compile(
            "^(\\.env(\\..*)?|.*\\.(pem|key|crt|p12|pfx|log|zip|tar|gz|tgz|rar|7z|png|jpg|jpeg|gif|webp|ico|pdf|sqlite|sqlite3|db|class|jar|war|ear|exe|dll|so|dylib))$",
            Pattern.CASE_INSENSITIVE
    );

    private final RepoLensProperties properties;

    public FileSkipPolicy(RepoLensProperties properties) {
        this.properties = properties;
    }

    public SkipReason directorySkipReason(Path directory, Path root) {
        String relativePath = relativePath(directory, root);
        if (Files.isSymbolicLink(directory)) {
            return SkipReason.SYMLINK_DIRECTORY;
        }
        String normalized = relativePath.toLowerCase(Locale.ROOT);
        if (IGNORED_DIRECTORIES.contains(normalized)
                || IGNORED_DIRECTORIES.contains(directory.getFileName().toString().toLowerCase(Locale.ROOT))) {
            return SkipReason.IGNORED_DIRECTORY;
        }
        return null;
    }

    public SkipReason fileSkipReason(Path file, Path root, BasicFileAttributes attributes) {
        if (Files.isSymbolicLink(file)) {
            return SkipReason.SYMLINK_FILE;
        }

        String relativePath = relativePath(file, root);
        if (escapesRoot(relativePath)) {
            return SkipReason.PATH_ESCAPES_ROOT;
        }

        String fileName = file.getFileName().toString();
        if (IGNORED_FILE_PATTERN.matcher(fileName).matches()) {
            return SkipReason.IGNORED_FILE;
        }

        if (attributes.size() > properties.getScanner().getMaxFileSizeBytes()) {
            return SkipReason.FILE_TOO_LARGE;
        }

        if (looksBinary(file)) {
            return SkipReason.BINARY_FILE;
        }

        return null;
    }

    public String relativePath(Path path, Path root) {
        try {
            return root.relativize(path.toRealPath()).toString().replace('\\', '/');
        } catch (IOException | IllegalArgumentException exception) {
            return root.relativize(path.toAbsolutePath().normalize()).toString().replace('\\', '/');
        }
    }

    private boolean looksBinary(Path file) {
        byte[] buffer = new byte[4096];
        try (InputStream input = Files.newInputStream(file)) {
            int read = input.read(buffer);
            if (read <= 0) {
                return false;
            }
            for (int index = 0; index < read; index++) {
                if (buffer[index] == 0) {
                    return true;
                }
            }
            return false;
        } catch (IOException exception) {
            return true;
        }
    }

    private boolean escapesRoot(String relativePath) {
        return relativePath.equals("..") || relativePath.startsWith("../");
    }
}
