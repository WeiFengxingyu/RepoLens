package com.repolens.repository.application;

import org.springframework.stereotype.Component;

import java.nio.file.Files;
import java.nio.file.Path;

@Component
public class RepositoryPathValidator {

    public Path validateLocalRepositoryPath(String rawPath) {
        if (rawPath == null || rawPath.isBlank()) {
            throw new IllegalArgumentException("Repository local path must not be blank");
        }

        Path path = Path.of(rawPath).toAbsolutePath().normalize();
        if (!Files.exists(path)) {
            throw new IllegalArgumentException("Repository local path does not exist");
        }
        if (!Files.isDirectory(path)) {
            throw new IllegalArgumentException("Repository local path must be a directory");
        }
        if (!Files.isReadable(path)) {
            throw new IllegalArgumentException("Repository local path is not readable");
        }
        if (path.getParent() == null) {
            throw new IllegalArgumentException("Refusing to import a filesystem root directory");
        }

        Path userHome = Path.of(System.getProperty("user.home")).toAbsolutePath().normalize();
        if (path.equals(userHome)) {
            throw new IllegalArgumentException("Refusing to import the whole user home directory");
        }

        return path;
    }
}
