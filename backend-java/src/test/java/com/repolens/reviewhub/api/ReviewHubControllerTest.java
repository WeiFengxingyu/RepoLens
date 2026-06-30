package com.repolens.reviewhub.api;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.repolens.reviewhub.infrastructure.AuditLogJpaRepository;
import com.repolens.reviewhub.infrastructure.OrganizationJpaRepository;
import com.repolens.reviewhub.infrastructure.ProjectJpaRepository;
import com.repolens.reviewhub.infrastructure.QuotaBucketJpaRepository;
import com.repolens.reviewhub.infrastructure.RepositoryBindingJpaRepository;
import com.repolens.reviewhub.infrastructure.ReviewRulesetJpaRepository;
import com.repolens.reviewhub.infrastructure.TeamMemberJpaRepository;
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
import static org.hamcrest.Matchers.greaterThanOrEqualTo;
import static org.hamcrest.Matchers.hasItem;
import static org.hamcrest.Matchers.notNullValue;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
class ReviewHubControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private RepositoryJpaRepository repositoryJpaRepository;

    @Autowired
    private AuditLogJpaRepository auditLogJpaRepository;

    @Autowired
    private QuotaBucketJpaRepository quotaBucketJpaRepository;

    @Autowired
    private ReviewRulesetJpaRepository reviewRulesetJpaRepository;

    @Autowired
    private RepositoryBindingJpaRepository repositoryBindingJpaRepository;

    @Autowired
    private TeamMemberJpaRepository teamMemberJpaRepository;

    @Autowired
    private ProjectJpaRepository projectJpaRepository;

    @Autowired
    private OrganizationJpaRepository organizationJpaRepository;

    @TempDir
    private Path tempDir;

    @BeforeEach
    void setUp() {
        auditLogJpaRepository.deleteAll();
        quotaBucketJpaRepository.deleteAll();
        reviewRulesetJpaRepository.deleteAll();
        repositoryBindingJpaRepository.deleteAll();
        teamMemberJpaRepository.deleteAll();
        projectJpaRepository.deleteAll();
        organizationJpaRepository.deleteAll();
        repositoryJpaRepository.deleteAll();
    }

    @Test
    void createsReviewHubGovernanceObjectsAndAuditTrail() throws Exception {
        String repositoryId = importRepository("reviewhub-service");

        String organizationBody = mockMvc.perform(post("/api/organizations")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "name": "RepoLens Demo Org",
                                  "plan_name": "team",
                                  "owner_user_id": "owner-1"
                                }
                                """))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.id", notNullValue()))
                .andExpect(jsonPath("$.plan_name", equalTo("team")))
                .andReturn()
                .getResponse()
                .getContentAsString();
        String organizationId = objectMapper.readTree(organizationBody).get("id").asText();

        String projectBody = mockMvc.perform(post("/api/organizations/{organizationId}/projects", organizationId)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "name": "RepoLens ReviewHub"
                                }
                                """))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.organization_id", equalTo(organizationId)))
                .andReturn()
                .getResponse()
                .getContentAsString();
        String projectId = objectMapper.readTree(projectBody).get("id").asText();

        mockMvc.perform(post("/api/projects/{projectId}/repositories/{repositoryId}/bind", projectId, repositoryId)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "provider": "fixture-github",
                                  "external_repo_id": "fixture/repolens-java"
                                }
                                """))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.project_id", equalTo(projectId)))
                .andExpect(jsonPath("$.repository_id", equalTo(repositoryId)))
                .andExpect(jsonPath("$.provider", equalTo("fixture-github")));

        mockMvc.perform(post("/api/projects/{projectId}/rulesets", projectId)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "name": "Strict Security Review",
                                  "enabled": true,
                                  "rules": {
                                    "block_permit_all": true,
                                    "min_severity": "medium"
                                  }
                                }
                                """))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.project_id", equalTo(projectId)))
                .andExpect(jsonPath("$.rules.block_permit_all", equalTo(true)));

        mockMvc.perform(get("/api/organizations"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[*].id", hasItem(organizationId)));

        mockMvc.perform(get("/api/organizations/{organizationId}/projects", organizationId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].id", equalTo(projectId)));

        mockMvc.perform(get("/api/projects/{projectId}/repositories", projectId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].external_repo_id", equalTo("fixture/repolens-java")));

        mockMvc.perform(get("/api/projects/{projectId}/rulesets", projectId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].name", equalTo("Strict Security Review")));

        mockMvc.perform(get("/api/projects/{projectId}/quota", projectId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.length()", equalTo(0)));

        mockMvc.perform(get("/api/audit-logs"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.length()", greaterThanOrEqualTo(4)))
                .andExpect(jsonPath("$[*].action", hasItem("ORGANIZATION_CREATED")))
                .andExpect(jsonPath("$[*].action", hasItem("PROJECT_CREATED")))
                .andExpect(jsonPath("$[*].action", hasItem("REPOSITORY_BOUND")))
                .andExpect(jsonPath("$[*].action", hasItem("REVIEW_RULESET_CREATED")));
    }

    private String importRepository(String directoryName) throws Exception {
        Path repositoryPath = Files.createDirectory(tempDir.resolve(directoryName));
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
                                  "name": "%s"
                                }
                                """.formatted(jsonEscapedPath(repositoryPath), directoryName)))
                .andExpect(status().isCreated())
                .andReturn()
                .getResponse()
                .getContentAsString();
        return objectMapper.readTree(importBody).get("id").asText();
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
