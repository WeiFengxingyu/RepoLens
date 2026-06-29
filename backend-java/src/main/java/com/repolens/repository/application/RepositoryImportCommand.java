package com.repolens.repository.application;

import com.repolens.repository.domain.RepositorySourceType;

import java.nio.file.Path;

public record RepositoryImportCommand(
        RepositorySourceType sourceType,
        Path localPath,
        String name,
        String branch
) {
}
