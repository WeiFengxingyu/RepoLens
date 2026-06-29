package com.repolens.mcp.api;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.repolens.mcp.infrastructure.McpToolCallAuditJpaRepository;
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
class McpControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private RepositoryJpaRepository repositoryJpaRepository;

    @Autowired
    private McpToolCallAuditJpaRepository auditJpaRepository;

    @TempDir
    private Path tempDir;

    @BeforeEach
    void setUp() {
        auditJpaRepository.deleteAll();
        repositoryJpaRepository.deleteAll();
    }

    @Test
    void listsCallsAndAuditsMcpTools() throws Exception {
        Path repositoryPath = Files.createDirectory(tempDir.resolve("mcp-service"));
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
                                  "name": "mcp_service"
                                }
                                """.formatted(jsonEscapedPath(repositoryPath))))
                .andExpect(status().isCreated())
                .andReturn()
                .getResponse()
                .getContentAsString();
        String repositoryId = objectMapper.readTree(importBody).get("id").asText();

        mockMvc.perform(get("/api/mcp/tools"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.length()", greaterThan(4)))
                .andExpect(jsonPath("$[*].name", hasItem("repolens.search")))
                .andExpect(jsonPath("$[*].name", hasItem("repolens.read_file")))
                .andExpect(jsonPath("$[*].name", hasItem("repolens.safe_static_check")));

        mockMvc.perform(post("/api/mcp/tools/call")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "name": "repolens.search",
                                  "arguments": {
                                    "repository_id": "%s",
                                    "query": "requireAuth security",
                                    "top_k": 5,
                                    "use_bm25": true,
                                    "use_vector": true,
                                    "use_graph": true
                                  },
                                  "client_name": "junit",
                                  "client_session_id": "p6"
                                }
                                """.formatted(repositoryId)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status", equalTo("completed")))
                .andExpect(jsonPath("$.permission_decision", equalTo("allow")))
                .andExpect(jsonPath("$.audit.input_hash", notNullValue()))
                .andExpect(jsonPath("$.audit.output_hash", notNullValue()))
                .andExpect(jsonPath("$.result.repository_id", equalTo(repositoryId)))
                .andExpect(jsonPath("$.result.evidences.length()", greaterThan(0)));

        mockMvc.perform(post("/api/mcp/tools/call")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "name": "repolens.read_file",
                                  "arguments": {
                                    "repository_id": "%s",
                                    "file_path": "src/main/java/com/demo/SecurityConfig.java",
                                    "start_line": 1,
                                    "end_line": 20
                                  },
                                  "client_name": "junit",
                                  "client_session_id": "p6"
                                }
                                """.formatted(repositoryId)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status", equalTo("completed")))
                .andExpect(jsonPath("$.result.content", containsString("requireAuth")));

        mockMvc.perform(post("/api/mcp/tools/call")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "name": "repolens.read_file",
                                  "arguments": {
                                    "repository_id": "%s",
                                    "file_path": "../secret.txt"
                                  },
                                  "client_name": "junit",
                                  "client_session_id": "p6"
                                }
                                """.formatted(repositoryId)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status", equalTo("denied")))
                .andExpect(jsonPath("$.permission_decision", equalTo("deny")))
                .andExpect(jsonPath("$.error_message", containsString("Path traversal")));

        mockMvc.perform(post("/api/mcp/tools/call")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "name": "repolens.safe_static_check",
                                  "arguments": {
                                    "repository_id": "%s"
                                  },
                                  "client_name": "junit",
                                  "client_session_id": "p6"
                                }
                                """.formatted(repositoryId)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status", equalTo("disabled")))
                .andExpect(jsonPath("$.permission_decision", equalTo("disabled")));

        JsonNode audits = objectMapper.readTree(mockMvc.perform(get("/api/mcp/tool-calls?limit=10"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.length()", equalTo(4)))
                .andExpect(jsonPath("$[*].status", hasItem("completed")))
                .andExpect(jsonPath("$[*].status", hasItem("denied")))
                .andExpect(jsonPath("$[*].status", hasItem("disabled")))
                .andExpect(jsonPath("$[*].client_name", hasItem("junit")))
                .andReturn()
                .getResponse()
                .getContentAsString());

        org.assertj.core.api.Assertions.assertThat(audits)
                .allMatch(audit -> audit.hasNonNull("input_hash"));
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
