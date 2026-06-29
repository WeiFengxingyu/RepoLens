package com.repolens.persistence;

import com.repolens.chunking.domain.ChunkType;
import com.repolens.chunking.domain.CodeChunkEntity;
import com.repolens.chunking.infrastructure.CodeChunkJpaRepository;
import com.repolens.repository.domain.RepositoryEntity;
import com.repolens.repository.domain.RepositoryFileEntity;
import com.repolens.repository.domain.RepositorySourceType;
import com.repolens.repository.domain.RepositoryStatus;
import com.repolens.repository.infrastructure.RepositoryFileJpaRepository;
import com.repolens.repository.infrastructure.RepositoryJpaRepository;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import java.time.Instant;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest
class V0SchemaIntegrationTest {

    @Autowired
    private RepositoryJpaRepository repositoryJpaRepository;

    @Autowired
    private RepositoryFileJpaRepository repositoryFileJpaRepository;

    @Autowired
    private CodeChunkJpaRepository codeChunkJpaRepository;

    @Test
    void savesRepositoryFileAndChunk() {
        Instant now = Instant.parse("2026-06-28T09:00:00Z");

        RepositoryEntity repository = new RepositoryEntity(
                "repo_test",
                "java_service",
                RepositorySourceType.LOCAL,
                RepositoryStatus.CREATED,
                now
        );
        repository.setLocalPath("F:/demo/java_service");
        repository.setFileCount(1);
        repository.setChunkCount(1);
        repository.setLanguageSummary("{\"JAVA\":1}");
        repositoryJpaRepository.save(repository);

        RepositoryFileEntity file = new RepositoryFileEntity(
                "file_test",
                repository.getId(),
                "src/main/java/com/demo/UserService.java",
                "JAVA",
                1200,
                now
        );
        file.setContentHash("abc123");
        repositoryFileJpaRepository.save(file);

        CodeChunkEntity chunk = new CodeChunkEntity(
                "chunk_test",
                repository.getId(),
                file.getId(),
                file.getRelativePath(),
                "JAVA",
                ChunkType.METHOD,
                10,
                24,
                "public User getUser(Long id) { return repository.findById(id); }",
                now
        );
        chunk.setSymbolName("UserService#getUser");
        chunk.setContentHash("def456");
        chunk.setTokenEstimate(16);
        chunk.setMetadata("{\"annotations\":[]}");
        codeChunkJpaRepository.save(chunk);

        assertThat(repositoryJpaRepository.findById("repo_test")).isPresent();
        assertThat(repositoryFileJpaRepository.findByRepositoryId("repo_test"))
                .extracting(RepositoryFileEntity::getRelativePath)
                .containsExactly("src/main/java/com/demo/UserService.java");
        assertThat(codeChunkJpaRepository.findByRepositoryId("repo_test"))
                .singleElement()
                .satisfies(saved -> {
                    assertThat(saved.getSymbolName()).isEqualTo("UserService#getUser");
                    assertThat(saved.getSymbolType()).isEqualTo(ChunkType.METHOD);
                    assertThat(saved.getStartLine()).isEqualTo(10);
                    assertThat(saved.getEndLine()).isEqualTo(24);
                });
    }
}
