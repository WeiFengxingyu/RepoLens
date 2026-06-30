package com.repolens.change.api;

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
import static org.hamcrest.Matchers.notNullValue;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
class ChangeRequestControllerTest {

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
    void reviewsFixtureChangeRequestAndLinksMetadataToReviewTask() throws Exception {
        Path repositoryPath = Files.createDirectory(tempDir.resolve("change-request-service"));
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
                                  "name": "change_request_service"
                                }
                                """.formatted(jsonEscapedPath(repositoryPath))))
                .andExpect(status().isCreated())
                .andReturn()
                .getResponse()
                .getContentAsString();
        String repositoryId = objectMapper.readTree(importBody).get("id").asText();

        String responseBody = mockMvc.perform(post("/api/repositories/{repositoryId}/change-requests/reviews", repositoryId)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "url": "fixture://github/repolens-java/1",
                                  "top_k": 5,
                                  "use_bm25": true,
                                  "use_vector": true,
                                  "use_graph": true,
                                  "run_static_check": true
                                }
                                """))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.change_request.id", notNullValue()))
                .andExpect(jsonPath("$.change_request.repository_id", equalTo(repositoryId)))
                .andExpect(jsonPath("$.change_request.task_id", notNullValue()))
                .andExpect(jsonPath("$.change_request.platform", equalTo("fixture-github")))
                .andExpect(jsonPath("$.change_request.provider_status", equalTo("reviewed")))
                .andExpect(jsonPath("$.change_request.diff_hash", notNullValue()))
                .andExpect(jsonPath("$.change_request.changed_file_count", equalTo(1)))
                .andExpect(jsonPath("$.review.status", equalTo("completed")))
                .andExpect(jsonPath("$.review.summary", containsString("Change request fixture-github")))
                .andExpect(jsonPath("$.review.risks.length()", greaterThan(0)))
                .andReturn()
                .getResponse()
                .getContentAsString();

        JsonNode root = objectMapper.readTree(responseBody);
        String changeRequestId = root.get("change_request").get("id").asText();
        String taskId = root.get("review").get("task_id").asText();

        mockMvc.perform(get("/api/change-requests/{changeRequestId}", changeRequestId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id", equalTo(changeRequestId)))
                .andExpect(jsonPath("$.task_id", equalTo(taskId)));

        mockMvc.perform(get("/api/change-requests/tasks/{taskId}", taskId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id", equalTo(changeRequestId)))
                .andExpect(jsonPath("$.metadata.warnings.length()", equalTo(1)));
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
