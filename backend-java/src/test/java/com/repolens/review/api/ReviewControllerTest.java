package com.repolens.review.api;

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

import static org.hamcrest.Matchers.containsString;
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
class ReviewControllerTest {

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
    void reviewsDiffWithRisksCitationsMarkdownToolCallsAndTraces() throws Exception {
        Path repositoryPath = Files.createDirectory(tempDir.resolve("review-service"));
        write(repositoryPath, "src/main/java/com/demo/SecurityConfig.java", """
                package demo;

                class SecurityConfig {
                  void configure() {
                    requireAuth();
                  }
                }
                """);

        String importBody = mockMvc.perform(post("/api/repositories")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "source": "%s",
                                  "name": "review_service"
                                }
                                """.formatted(jsonEscapedPath(repositoryPath))))
                .andExpect(status().isCreated())
                .andReturn()
                .getResponse()
                .getContentAsString();
        String repositoryId = objectMapper.readTree(importBody).get("id").asText();

        String diff = """
                diff --git a/src/main/java/com/demo/SecurityConfig.java b/src/main/java/com/demo/SecurityConfig.java
                --- a/src/main/java/com/demo/SecurityConfig.java
                +++ b/src/main/java/com/demo/SecurityConfig.java
                @@ -2,6 +2,8 @@ package demo;
                 class SecurityConfig {
                   void configure() {
                -    requireAuth();
                +    permitAll();
                +    return null;
                   }
                 }
                """;

        String reviewBody = mockMvc.perform(post("/api/repositories/{repositoryId}/reviews", repositoryId)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "diff_text": %s,
                                  "top_k": 5,
                                  "use_bm25": true,
                                  "use_vector": true,
                                  "use_graph": true,
                                  "run_static_check": true
                                }
                                """.formatted(objectMapper.writeValueAsString(diff))))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.task_id", notNullValue()))
                .andExpect(jsonPath("$.repository_id", equalTo(repositoryId)))
                .andExpect(jsonPath("$.status", equalTo("completed")))
                .andExpect(jsonPath("$.risk_level", equalTo("high")))
                .andExpect(jsonPath("$.risks.length()", greaterThan(0)))
                .andExpect(jsonPath("$.risks[0].severity", equalTo("high")))
                .andExpect(jsonPath("$.impacted_symbols", hasItem("src/main/java/com/demo/SecurityConfig.java")))
                .andExpect(jsonPath("$.suggested_tests.length()", greaterThan(0)))
                .andExpect(jsonPath("$.citations.length()", greaterThan(0)))
                .andExpect(jsonPath("$.markdown", containsString("RepoLens Review")))
                .andExpect(jsonPath("$.tool_calls.length()", equalTo(3)))
                .andExpect(jsonPath("$.traces.length()", equalTo(4)))
                .andExpect(jsonPath("$.traces[*].step_name", hasItem("diff.parse")))
                .andExpect(jsonPath("$.traces[*].step_name", hasItem("code.search")))
                .andExpect(jsonPath("$.traces[*].step_name", hasItem("risk.rules")))
                .andExpect(jsonPath("$.traces[*].step_name", hasItem("final_report")))
                .andReturn()
                .getResponse()
                .getContentAsString();

        JsonNode review = objectMapper.readTree(reviewBody);
        String taskId = review.get("task_id").asText();

        mockMvc.perform(get("/api/reviews/{taskId}", taskId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.task_id", equalTo(taskId)))
                .andExpect(jsonPath("$.status", equalTo("completed")))
                .andExpect(jsonPath("$.markdown", containsString("Risk level: high")));
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
