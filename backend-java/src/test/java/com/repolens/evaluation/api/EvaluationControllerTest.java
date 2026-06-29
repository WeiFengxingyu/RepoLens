package com.repolens.evaluation.api;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.repolens.evaluation.infrastructure.EvaluationRunJpaRepository;
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
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
class EvaluationControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private RepositoryJpaRepository repositoryJpaRepository;

    @Autowired
    private EvaluationRunJpaRepository evaluationRunJpaRepository;

    @TempDir
    private Path tempDir;

    @BeforeEach
    void setUp() {
        evaluationRunJpaRepository.deleteAll();
        repositoryJpaRepository.deleteAll();
    }

    @Test
    void runsAllStrategiesAndPersistsEvaluationResults() throws Exception {
        Path repositoryPath = Files.createDirectory(tempDir.resolve("evaluation-service"));
        write(repositoryPath, "src/main/java/com/demo/SecurityConfig.java", """
                package demo;

                class SecurityConfig {
                  void configure() {
                    requireAuth();
                  }
                }
                """);
        Path dataset = tempDir.resolve("eval.jsonl");
        Files.writeString(dataset, """
                {"id":"security-001","repository_key":"java_demo","sample_type":"location","query":"SecurityConfig requireAuth configure","expected_files":["src/main/java/com/demo/SecurityConfig.java"],"expected_symbols":["demo.SecurityConfig#void configure()"]}
                """);

        String importBody = mockMvc.perform(post("/api/repositories")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "source": "%s",
                                  "name": "evaluation_service"
                                }
                                """.formatted(jsonEscapedPath(repositoryPath))))
                .andExpect(status().isCreated())
                .andReturn()
                .getResponse()
                .getContentAsString();
        String repositoryId = objectMapper.readTree(importBody).get("id").asText();

        String runBody = mockMvc.perform(post("/api/evaluations")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "name": "p7-smoke",
                                  "dataset_path": "%s",
                                  "strategy": "all",
                                  "repository_map": {
                                    "java_demo": "%s"
                                  },
                                  "top_k": 5
                                }
                                """.formatted(jsonEscapedPath(dataset), repositoryId)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.run_id", notNullValue()))
                .andExpect(jsonPath("$.status", equalTo("completed")))
                .andExpect(jsonPath("$.sample_count", equalTo(1)))
                .andExpect(jsonPath("$.metrics.length()", equalTo(3)))
                .andExpect(jsonPath("$.metrics[*].strategy", hasItem("vector_only")))
                .andExpect(jsonPath("$.metrics[*].strategy", hasItem("bm25_vector")))
                .andExpect(jsonPath("$.metrics[*].strategy", hasItem("bm25_vector_graph")))
                .andExpect(jsonPath("$.results.length()", equalTo(3)))
                .andExpect(jsonPath("$.results[?(@.strategy=='bm25_vector')].hit_at_5", hasItem(true)))
                .andExpect(jsonPath("$.results[?(@.strategy=='bm25_vector')].mrr", hasItem(greaterThan(0.0))))
                .andExpect(jsonPath("$.results[?(@.strategy=='bm25_vector')].citation_coverage", hasItem(greaterThan(0.0))))
                .andReturn()
                .getResponse()
                .getContentAsString();
        JsonNode run = objectMapper.readTree(runBody);
        String runId = run.get("run_id").asText();

        mockMvc.perform(get("/api/evaluations"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].run_id", equalTo(runId)))
                .andExpect(jsonPath("$[0].metrics.length()", equalTo(3)));

        mockMvc.perform(get("/api/evaluations/{runId}", runId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.run_id", equalTo(runId)))
                .andExpect(jsonPath("$.results.length()", equalTo(3)));
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
