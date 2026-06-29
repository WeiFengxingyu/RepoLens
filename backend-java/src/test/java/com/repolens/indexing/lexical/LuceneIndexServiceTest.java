package com.repolens.indexing.lexical;

import com.repolens.chunking.domain.ChunkType;
import com.repolens.chunking.domain.CodeChunkEntity;
import com.repolens.config.RepoLensProperties;
import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

class LuceneIndexServiceTest {

    @Test
    void indexesAndSearchesChunksBySymbolPathMetadataAndTopK() throws IOException {
        LuceneIndexService service = newService(Files.createTempDirectory(Path.of("target"), "lucene-test-"));
        String repositoryId = "repo_lucene";
        CodeChunkEntity controller = chunk(
                "chunk_controller",
                repositoryId,
                "src/main/java/com/demo/UserController.java",
                ChunkType.METHOD,
                "UserController#getUser",
                "GetMapping get user by id\nreturn userService.findUser(id);",
                "{\"annotations\":[\"GetMapping\"],\"route\":\"/users/{id}\"}"
        );
        CodeChunkEntity serviceChunk = chunk(
                "chunk_service",
                repositoryId,
                "src/main/java/com/demo/UserService.java",
                ChunkType.METHOD,
                "UserService#findUser",
                "find user from repository by id",
                "{\"annotations\":[]}"
        );
        CodeChunkEntity config = chunk(
                "chunk_config",
                repositoryId,
                "src/main/resources/application.yml",
                ChunkType.CONFIG,
                "src/main/resources/application.yml",
                "server:\n  port: 8080",
                "{\"kind\":\"config\"}"
        );

        service.rebuildIndex(repositoryId, List.of(controller, serviceChunk, config));

        assertThat(service.search(repositoryId, "getUser", 5))
                .extracting(LexicalSearchHit::chunkId)
                .first()
                .isEqualTo("chunk_controller");
        assertThat(service.search(repositoryId, "UserService.java", 5))
                .extracting(LexicalSearchHit::chunkId)
                .contains("chunk_service");
        assertThat(service.search(repositoryId, "GetMapping", 5))
                .extracting(LexicalSearchHit::chunkId)
                .contains("chunk_controller");
        assertThat(service.search(repositoryId, "user", 1))
                .hasSize(1);
    }

    private LuceneIndexService newService(Path tempDir) {
        RepoLensProperties properties = new RepoLensProperties();
        properties.setIndexRoot(tempDir.resolve("indexes").toString());
        LuceneIndexPathResolver pathResolver = new LuceneIndexPathResolver(properties);
        return new LuceneIndexService(pathResolver, new LuceneDocumentMapper());
    }

    private CodeChunkEntity chunk(
            String id,
            String repositoryId,
            String filePath,
            ChunkType chunkType,
            String symbolName,
            String content,
            String metadata
    ) {
        CodeChunkEntity chunk = new CodeChunkEntity(
                id,
                repositoryId,
                "file_" + id,
                filePath,
                "JAVA",
                chunkType,
                1,
                20,
                content,
                Instant.parse("2026-01-01T00:00:00Z")
        );
        chunk.setSymbolName(symbolName);
        chunk.setMetadata(metadata);
        chunk.setTokenEstimate(10);
        chunk.setContentHash("hash_" + id);
        return chunk;
    }
}
