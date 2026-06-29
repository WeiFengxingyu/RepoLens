package com.repolens.repository.api;

import com.repolens.chunking.domain.ChunkType;
import com.repolens.chunking.infrastructure.CodeChunkJpaRepository;
import com.repolens.graph.infrastructure.CodeRelationJpaRepository;
import com.repolens.graph.infrastructure.CodeSymbolJpaRepository;
import com.repolens.indexing.infrastructure.IndexTaskEventJpaRepository;
import com.repolens.indexing.infrastructure.IndexTaskJpaRepository;
import com.repolens.repository.infrastructure.RepositoryJpaRepository;
import com.repolens.retrieval.vector.ChunkVectorJpaRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import java.nio.file.Files;
import java.nio.file.Path;

import static org.assertj.core.api.Assertions.assertThat;
import static org.hamcrest.Matchers.equalTo;
import static org.hamcrest.Matchers.greaterThan;
import static org.hamcrest.Matchers.notNullValue;
import static org.hamcrest.Matchers.nullValue;
import static org.hamcrest.Matchers.startsWith;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
class RepositoryControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private RepositoryJpaRepository repositoryJpaRepository;

    @Autowired
    private CodeChunkJpaRepository codeChunkJpaRepository;

    @Autowired
    private CodeSymbolJpaRepository codeSymbolJpaRepository;

    @Autowired
    private CodeRelationJpaRepository codeRelationJpaRepository;

    @Autowired
    private ChunkVectorJpaRepository chunkVectorJpaRepository;

    @Autowired
    private IndexTaskJpaRepository indexTaskJpaRepository;

    @Autowired
    private IndexTaskEventJpaRepository indexTaskEventJpaRepository;

    @TempDir
    private Path tempDir;

    @BeforeEach
    void setUp() {
        repositoryJpaRepository.deleteAll();
    }

    @Test
    void importsLocalRepositoryWithLegacyFrontendRequest() throws Exception {
        Path repositoryPath = Files.createDirectory(tempDir.resolve("java-service"));
        write(repositoryPath, "src/main/java/com/demo/UserService.java", "package demo;\nclass UserService {\n  String name() { return \"demo\"; }\n}\n");
        write(repositoryPath, "README.md", "# Demo\n");
        write(repositoryPath, ".env", "SECRET=value\n");

        mockMvc.perform(post("/api/repositories")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "source": "%s",
                                  "name": "java_service",
                                  "branch": "main"
                                }
                                """.formatted(jsonEscapedPath(repositoryPath))))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.id", startsWith("repo_")))
                .andExpect(jsonPath("$.name", equalTo("java_service")))
                .andExpect(jsonPath("$.source_type", equalTo("local")))
                .andExpect(jsonPath("$.local_path", equalTo(repositoryPath.toAbsolutePath().normalize().toString())))
                .andExpect(jsonPath("$.branch", equalTo("main")))
                .andExpect(jsonPath("$.status", equalTo("ready")))
                .andExpect(jsonPath("$.language_summary.JAVA", equalTo(1)))
                .andExpect(jsonPath("$.language_summary.MARKDOWN", equalTo(1)))
                .andExpect(jsonPath("$.file_count", equalTo(2)))
                .andExpect(jsonPath("$.parsed_file_count", equalTo(2)))
                .andExpect(jsonPath("$.skipped_file_count", equalTo(1)))
                .andExpect(jsonPath("$.chunk_count", equalTo(3)))
                .andExpect(jsonPath("$.relation_count", greaterThan(0)))
                .andExpect(jsonPath("$.error_message", nullValue()));
    }

    @Test
    void importsLocalRepositoryWithJavaPlanRequestAndExposesListDetailAndStatus() throws Exception {
        Path repositoryPath = Files.createDirectory(tempDir.resolve("java-plan-service"));
        write(repositoryPath, "src/main/java/com/demo/App.java", "package demo;\nclass App {\n  String name() { return \"demo\"; }\n}\n");
        write(repositoryPath, "src/main/resources/application.yml", "server:\n  port: 8080\n");
        write(repositoryPath, "target/classes/App.class", "compiled");

        String response = mockMvc.perform(post("/api/repositories")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "sourceType": "LOCAL",
                                  "localPath": "%s",
                                  "name": "java_plan_service"
                                }
                                """.formatted(jsonEscapedPath(repositoryPath))))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.id", startsWith("repo_")))
                .andExpect(jsonPath("$.name", equalTo("java_plan_service")))
                .andReturn()
                .getResponse()
                .getContentAsString();

        String repositoryId = response.replaceAll(".*\\\"id\\\":\\\"([^\\\"]+)\\\".*", "$1");

        mockMvc.perform(get("/api/repositories"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].id", equalTo(repositoryId)))
                .andExpect(jsonPath("$[0].source_type", equalTo("local")))
                .andExpect(jsonPath("$[0].status", equalTo("ready")))
                .andExpect(jsonPath("$[0].file_count", equalTo(2)))
                .andExpect(jsonPath("$[0].chunk_count", equalTo(3)))
                .andExpect(jsonPath("$[0].relation_count", greaterThan(0)));

        mockMvc.perform(get("/api/repositories/{repositoryId}", repositoryId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id", equalTo(repositoryId)))
                .andExpect(jsonPath("$.local_path", equalTo(repositoryPath.toAbsolutePath().normalize().toString())))
                .andExpect(jsonPath("$.language_summary.JAVA", equalTo(1)))
                .andExpect(jsonPath("$.language_summary.YAML", equalTo(1)))
                .andExpect(jsonPath("$.skipped_file_count", equalTo(1)))
                .andExpect(jsonPath("$.parsed_file_count", equalTo(2)))
                .andExpect(jsonPath("$.chunk_count", equalTo(3)))
                .andExpect(jsonPath("$.indexed_at", notNullValue()));

        mockMvc.perform(get("/api/repositories/{repositoryId}/status", repositoryId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id", equalTo(repositoryId)))
                .andExpect(jsonPath("$.status", equalTo("ready")))
                .andExpect(jsonPath("$.progress.current_step", equalTo("ready")))
                .andExpect(jsonPath("$.progress.file_count", equalTo(2)))
                .andExpect(jsonPath("$.progress.parsed_file_count", equalTo(2)))
                .andExpect(jsonPath("$.progress.chunk_count", equalTo(3)))
                .andExpect(jsonPath("$.progress.relation_count", greaterThan(0)))
                .andExpect(jsonPath("$.error_message", nullValue()));

        assertThat(codeChunkJpaRepository.findByRepositoryId(repositoryId))
                .extracting(chunk -> chunk.getSymbolType())
                .contains(ChunkType.CLASS, ChunkType.METHOD, ChunkType.CONFIG);
        assertThat(codeSymbolJpaRepository.countByRepositoryId(repositoryId)).isGreaterThan(0);
        assertThat(codeRelationJpaRepository.countByRepositoryId(repositoryId)).isGreaterThan(0);
        assertThat(chunkVectorJpaRepository.countByRepositoryId(repositoryId)).isEqualTo(3);
        String taskId = indexTaskJpaRepository.findFirstByRepositoryIdOrderByCreatedAtDesc(repositoryId)
                .orElseThrow()
                .getId();
        assertThat(indexTaskEventJpaRepository.findByTaskIdOrderByCreatedAtAsc(taskId))
                .extracting(event -> event.getStage().name())
                .contains("SCANNING", "PARSING", "GRAPH_BUILDING", "BM25_INDEXING", "VECTOR_INDEXING", "READY");

        mockMvc.perform(get("/api/repositories/{repositoryId}/index-tasks/latest", repositoryId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id", equalTo(taskId)))
                .andExpect(jsonPath("$.status", equalTo("READY")))
                .andExpect(jsonPath("$.progress_percent", equalTo(100)))
                .andExpect(jsonPath("$.events.length()", greaterThan(0)));

        mockMvc.perform(get("/api/index-tasks/{taskId}", taskId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.repository_id", equalTo(repositoryId)))
                .andExpect(jsonPath("$.current_stage", equalTo("READY")));
    }

    @Test
    void rejectsMissingLocalPath() throws Exception {
        Path missingPath = tempDir.resolve("missing");

        mockMvc.perform(post("/api/repositories")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "source": "%s",
                                  "name": "missing"
                                }
                                """.formatted(jsonEscapedPath(missingPath))))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.code", equalTo("BAD_REQUEST")))
                .andExpect(jsonPath("$.message", equalTo("Repository local path does not exist")));
    }

    @Test
    void rejectsFilePath() throws Exception {
        Path filePath = Files.writeString(tempDir.resolve("README.md"), "demo");

        mockMvc.perform(post("/api/repositories")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "source": "%s"
                                }
                                """.formatted(jsonEscapedPath(filePath))))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.message", equalTo("Repository local path must be a directory")));
    }

    @Test
    void rejectsGitSourceInV0() throws Exception {
        mockMvc.perform(post("/api/repositories")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "sourceType": "GIT",
                                  "source": "https://example.com/demo.git"
                                }
                                """))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.message", equalTo("Only local repository import is supported in V0")));
    }

    @Test
    void rejectsFilesystemRootDirectory() throws Exception {
        Path rootPath = tempDir.toAbsolutePath().normalize().getRoot();

        mockMvc.perform(post("/api/repositories")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "source": "%s"
                                }
                                """.formatted(jsonEscapedPath(rootPath))))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.message", equalTo("Refusing to import a filesystem root directory")));
    }

    @Test
    void rejectsUserHomeDirectory() throws Exception {
        Path userHome = Path.of(System.getProperty("user.home"));

        mockMvc.perform(post("/api/repositories")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "source": "%s"
                                }
                                """.formatted(jsonEscapedPath(userHome))))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.message", equalTo("Refusing to import the whole user home directory")));
    }

    @Test
    void returnsNotFoundForUnknownRepository() throws Exception {
        mockMvc.perform(get("/api/repositories/repo_missing"))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.code", equalTo("NOT_FOUND")))
                .andExpect(jsonPath("$.message", equalTo("Repository not found")));
    }

    private String jsonEscapedPath(Path path) {
        return path.toAbsolutePath().normalize().toString().replace("\\", "\\\\");
    }

    private void write(Path root, String relativePath, String content) throws Exception {
        Path file = root.resolve(relativePath);
        Files.createDirectories(file.getParent());
        Files.writeString(file, content);
    }
}
