package com.repolens.retrieval.api;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.repolens.repository.infrastructure.RepositoryJpaRepository;
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

import static org.hamcrest.Matchers.equalTo;
import static org.hamcrest.Matchers.greaterThan;
import static org.hamcrest.Matchers.hasItem;
import static org.hamcrest.Matchers.notNullValue;
import static org.hamcrest.Matchers.nullValue;
import static org.hamcrest.Matchers.startsWith;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
class RetrievalControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private RepositoryJpaRepository repositoryJpaRepository;

    @TempDir
    private Path tempDir;

    @BeforeEach
    void setUp() {
        repositoryJpaRepository.deleteAll();
    }

    @Test
    void retrievesBm25EvidenceAfterRepositoryImport() throws Exception {
        Path repositoryPath = Files.createDirectory(tempDir.resolve("retrieval-service"));
        write(repositoryPath, "src/main/java/com/demo/UserController.java", """
                package demo;

                import org.springframework.web.bind.annotation.GetMapping;
                import org.springframework.web.bind.annotation.RequestMapping;
                import org.springframework.web.bind.annotation.RestController;

                @RestController
                @RequestMapping("/users")
                class UserController {
                  @GetMapping("/{id}")
                  String getUser(String id) {
                    return "user-" + id;
                  }
                }
                """);

        String importBody = mockMvc.perform(post("/api/repositories")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "source": "%s",
                                  "name": "retrieval_service"
                                }
                                """.formatted(jsonEscapedPath(repositoryPath))))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.status", equalTo("ready")))
                .andExpect(jsonPath("$.indexed_at", notNullValue()))
                .andReturn()
                .getResponse()
                .getContentAsString();
        JsonNode imported = objectMapper.readTree(importBody);
        String repositoryId = imported.get("id").asText();

        mockMvc.perform(post("/api/repositories/{repositoryId}/retrieve", repositoryId)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "query": "GetMapping getUser",
                                  "top_k": 5,
                                  "use_bm25": true,
                                  "use_vector": true,
                                  "use_graph": true
                                }
                                """))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.repository_id", equalTo(repositoryId)))
                .andExpect(jsonPath("$.query", equalTo("GetMapping getUser")))
                .andExpect(jsonPath("$.evidences[0].evidence_id", startsWith("ev_")))
                .andExpect(jsonPath("$.evidences[0].chunk_id", startsWith("chunk_")))
                .andExpect(jsonPath("$.evidences[0].repository_id", equalTo(repositoryId)))
                .andExpect(jsonPath("$.evidences[0].file_path", equalTo("src/main/java/com/demo/UserController.java")))
                .andExpect(jsonPath("$.evidences[0].symbol_name", equalTo("demo.UserController#String getUser(String)")))
                .andExpect(jsonPath("$.evidences[0].symbol_type", equalTo("METHOD")))
                .andExpect(jsonPath("$.evidences[0].language", equalTo("JAVA")))
                .andExpect(jsonPath("$.evidences[0].source", equalTo("BM25")))
                .andExpect(jsonPath("$.evidences[0].sources", hasItem("BM25")))
                .andExpect(jsonPath("$.evidences[0].sources", hasItem("VECTOR")))
                .andExpect(jsonPath("$.evidences[0].sources", hasItem("GRAPH")))
                .andExpect(jsonPath("$.evidences[0].score", greaterThan(0.0)))
                .andExpect(jsonPath("$.evidences[0].bm25_score", greaterThan(0.0)))
                .andExpect(jsonPath("$.evidences[0].vector_score", greaterThan(0.0)))
                .andExpect(jsonPath("$.evidences[0].graph_score", greaterThan(0.0)))
                .andExpect(jsonPath("$.evidences[0].snippet", startsWith("// file: src/main/java/com/demo/UserController.java")))
                .andExpect(jsonPath("$.evidences[0].metadata.route.path", equalTo("/users/{id}")))
                .andExpect(jsonPath("$.debug.bm25_count", greaterThan(0)))
                .andExpect(jsonPath("$.debug.vector_count", greaterThan(0)))
                .andExpect(jsonPath("$.debug.graph_count", greaterThan(0)))
                .andExpect(jsonPath("$.debug.evidence_count", greaterThan(0)))
                .andExpect(jsonPath("$.debug.vector_disabled_reason", nullValue()))
                .andExpect(jsonPath("$.debug.context_truncated", equalTo(false)));
    }

    @Test
    void returnsNotFoundForUnknownRepository() throws Exception {
        mockMvc.perform(post("/api/repositories/repo_missing/retrieve")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "query": "anything"
                                }
                                """))
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
