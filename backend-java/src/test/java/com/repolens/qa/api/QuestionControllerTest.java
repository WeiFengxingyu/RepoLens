package com.repolens.qa.api;

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
class QuestionControllerTest {

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
    void answersQuestionWithCitationsAndTrace() throws Exception {
        Path repositoryPath = Files.createDirectory(tempDir.resolve("qa-service"));
        write(repositoryPath, "src/main/java/com/demo/AuthController.java", """
                package demo;

                import org.springframework.web.bind.annotation.GetMapping;
                import org.springframework.web.bind.annotation.RequestMapping;
                import org.springframework.web.bind.annotation.RestController;

                @RestController
                @RequestMapping("/auth")
                class AuthController {
                  @GetMapping("/me")
                  String currentUser() {
                    return "user";
                  }
                }
                """);

        String importBody = mockMvc.perform(post("/api/repositories")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "source": "%s",
                                  "name": "qa_service"
                                }
                                """.formatted(jsonEscapedPath(repositoryPath))))
                .andExpect(status().isCreated())
                .andReturn()
                .getResponse()
                .getContentAsString();
        String repositoryId = objectMapper.readTree(importBody).get("id").asText();

        String qaBody = mockMvc.perform(post("/api/repositories/{repositoryId}/questions", repositoryId)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "question": "auth current user endpoint 在哪里？",
                                  "top_k": 5,
                                  "use_bm25": true,
                                  "use_vector": true,
                                  "use_graph": true
                                }
                                """))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.task_id", notNullValue()))
                .andExpect(jsonPath("$.repository_id", equalTo(repositoryId)))
                .andExpect(jsonPath("$.status", equalTo("completed")))
                .andExpect(jsonPath("$.answer", containsString("AuthController.java")))
                .andExpect(jsonPath("$.citations.length()", greaterThan(0)))
                .andExpect(jsonPath("$.citations[0].file_path", equalTo("src/main/java/com/demo/AuthController.java")))
                .andExpect(jsonPath("$.traces.length()", equalTo(4)))
                .andExpect(jsonPath("$.traces[*].step_name", hasItem("planner")))
                .andExpect(jsonPath("$.traces[*].step_name", hasItem("code.search")))
                .andExpect(jsonPath("$.traces[*].step_name", hasItem("verifier")))
                .andExpect(jsonPath("$.traces[*].step_name", hasItem("final_answer")))
                .andReturn()
                .getResponse()
                .getContentAsString();

        JsonNode qa = objectMapper.readTree(qaBody);
        String taskId = qa.get("task_id").asText();

        mockMvc.perform(get("/api/questions/{taskId}", taskId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.task_id", equalTo(taskId)))
                .andExpect(jsonPath("$.status", equalTo("completed")))
                .andExpect(jsonPath("$.traces.length()", equalTo(4)));
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
