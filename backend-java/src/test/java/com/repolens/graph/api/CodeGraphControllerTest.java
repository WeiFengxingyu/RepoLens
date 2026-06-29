package com.repolens.graph.api;

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
import static org.hamcrest.Matchers.notNullValue;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
class CodeGraphControllerTest {

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
    void exposesGraphSummarySymbolSearchAndNeighbors() throws Exception {
        Path repositoryPath = Files.createDirectory(tempDir.resolve("graph-service"));
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
                                  "name": "graph_service"
                                }
                                """.formatted(jsonEscapedPath(repositoryPath))))
                .andExpect(status().isCreated())
                .andReturn()
                .getResponse()
                .getContentAsString();
        String repositoryId = objectMapper.readTree(importBody).get("id").asText();

        mockMvc.perform(get("/api/repositories/{repositoryId}/graph/summary", repositoryId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.repository_id", equalTo(repositoryId)))
                .andExpect(jsonPath("$.symbol_count", greaterThan(0)))
                .andExpect(jsonPath("$.relation_count", greaterThan(0)))
                .andExpect(jsonPath("$.route_count", greaterThan(0)));

        String symbolsBody = mockMvc.perform(get("/api/repositories/{repositoryId}/symbols?query=getUser", repositoryId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].id", notNullValue()))
                .andExpect(jsonPath("$[0].symbol_name", equalTo("getUser")))
                .andExpect(jsonPath("$[0].symbol_type", equalTo("METHOD")))
                .andReturn()
                .getResponse()
                .getContentAsString();
        JsonNode symbols = objectMapper.readTree(symbolsBody);
        String symbolId = symbols.get(0).get("id").asText();

        mockMvc.perform(get("/api/repositories/{repositoryId}/symbols/{symbolId}/neighbors", repositoryId, symbolId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.symbol.id", equalTo(symbolId)))
                .andExpect(jsonPath("$.relations.length()", greaterThan(0)));
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
