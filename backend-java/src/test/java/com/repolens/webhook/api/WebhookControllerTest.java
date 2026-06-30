package com.repolens.webhook.api;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.repolens.agent.infrastructure.AgentTraceJpaRepository;
import com.repolens.change.infrastructure.ChangeRequestJpaRepository;
import com.repolens.indexing.infrastructure.IndexTaskEventJpaRepository;
import com.repolens.indexing.infrastructure.IndexTaskJpaRepository;
import com.repolens.job.application.JobWorkerService;
import com.repolens.job.domain.JobStatus;
import com.repolens.job.infrastructure.AnalysisJobJpaRepository;
import com.repolens.job.infrastructure.DeadLetterJobJpaRepository;
import com.repolens.job.infrastructure.JobAttemptJpaRepository;
import com.repolens.job.infrastructure.JobEventJpaRepository;
import com.repolens.review.infrastructure.ReviewTaskJpaRepository;
import com.repolens.review.infrastructure.ReviewToolCallJpaRepository;
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
import java.time.Duration;

import static org.assertj.core.api.Assertions.assertThat;
import static org.awaitility.Awaitility.await;
import static org.hamcrest.Matchers.containsString;
import static org.hamcrest.Matchers.equalTo;
import static org.hamcrest.Matchers.greaterThanOrEqualTo;
import static org.hamcrest.Matchers.hasItem;
import static org.hamcrest.Matchers.notNullValue;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest(properties = "repolens.v2-lite.worker.local-enabled=false")
@AutoConfigureMockMvc
class WebhookControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private AnalysisJobJpaRepository analysisJobJpaRepository;

    @Autowired
    private JobWorkerService jobWorkerService;

    @Autowired
    private DeadLetterJobJpaRepository deadLetterJobJpaRepository;

    @Autowired
    private JobAttemptJpaRepository jobAttemptJpaRepository;

    @Autowired
    private JobEventJpaRepository jobEventJpaRepository;

    @Autowired
    private ChangeRequestJpaRepository changeRequestJpaRepository;

    @Autowired
    private ReviewToolCallJpaRepository reviewToolCallJpaRepository;

    @Autowired
    private ReviewTaskJpaRepository reviewTaskJpaRepository;

    @Autowired
    private AgentTraceJpaRepository agentTraceJpaRepository;

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

    @Autowired
    private IndexTaskEventJpaRepository indexTaskEventJpaRepository;

    @Autowired
    private IndexTaskJpaRepository indexTaskJpaRepository;

    @Autowired
    private RepositoryJpaRepository repositoryJpaRepository;

    @TempDir
    private Path tempDir;

    @BeforeEach
    void setUp() {
        deadLetterJobJpaRepository.deleteAll();
        jobEventJpaRepository.deleteAll();
        jobAttemptJpaRepository.deleteAll();
        analysisJobJpaRepository.deleteAll();
        changeRequestJpaRepository.deleteAll();
        reviewToolCallJpaRepository.deleteAll();
        reviewTaskJpaRepository.deleteAll();
        agentTraceJpaRepository.deleteAll();
        auditLogJpaRepository.deleteAll();
        quotaBucketJpaRepository.deleteAll();
        reviewRulesetJpaRepository.deleteAll();
        repositoryBindingJpaRepository.deleteAll();
        teamMemberJpaRepository.deleteAll();
        projectJpaRepository.deleteAll();
        organizationJpaRepository.deleteAll();
        indexTaskEventJpaRepository.deleteAll();
        indexTaskJpaRepository.deleteAll();
        repositoryJpaRepository.deleteAll();
    }

    @Test
    void fixtureWebhookCreatesIdempotentAsyncChangeRequestReviewJob() throws Exception {
        String repositoryId = importRepository("webhook-service");
        String organizationId = createOrganization();
        String projectId = createProject(organizationId);
        bindRepository(projectId, repositoryId);
        String rulesetId = createRuleset(projectId);

        String webhookBody = mockMvc.perform(post("/api/webhooks/fixture-github")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "external_repo_id": "fixture/repolens-java",
                                  "change_url": "fixture://github/repolens-java/1",
                                  "event": "pull_request",
                                  "action": "opened",
                                  "commit_sha": "demo-sha",
                                  "sender": "demo-user",
                                  "top_k": 5,
                                  "use_bm25": true,
                                  "use_vector": true,
                                  "use_graph": true,
                                  "run_static_check": true
                                }
                                """))
                .andExpect(status().isAccepted())
                .andExpect(jsonPath("$.project_id", equalTo(projectId)))
                .andExpect(jsonPath("$.repository_id", equalTo(repositoryId)))
                .andExpect(jsonPath("$.ruleset_id", equalTo(rulesetId)))
                .andExpect(jsonPath("$.idempotent_replay", equalTo(false)))
                .andExpect(jsonPath("$.quota.used_count", equalTo(1)))
                .andExpect(jsonPath("$.job.id", notNullValue()))
                .andExpect(jsonPath("$.job.job_type", equalTo("REVIEW_CHANGE_REQUEST")))
                .andReturn()
                .getResponse()
                .getContentAsString();
        String jobId = objectMapper.readTree(webhookBody).get("job").get("id").asText();

        jobWorkerService.process(jobId, "test-worker-webhook");

        await().atMost(Duration.ofSeconds(8)).untilAsserted(() -> {
            assertThat(analysisJobJpaRepository.findById(jobId).orElseThrow().getStatus())
                    .isEqualTo(JobStatus.SUCCEEDED);
            assertThat(analysisJobJpaRepository.findById(jobId).orElseThrow().getResultRef())
                    .contains("change_request:", "review_task:");
            assertThat(changeRequestJpaRepository.count()).isEqualTo(1);
            assertThat(reviewTaskJpaRepository.count()).isEqualTo(1);
        });

        mockMvc.perform(post("/api/webhooks/fixture-github")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "external_repo_id": "fixture/repolens-java",
                                  "change_url": "fixture://github/repolens-java/1",
                                  "event": "pull_request",
                                  "action": "opened",
                                  "commit_sha": "demo-sha",
                                  "sender": "demo-user"
                                }
                                """))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.idempotent_replay", equalTo(true)))
                .andExpect(jsonPath("$.quota").doesNotExist())
                .andExpect(jsonPath("$.job.id", equalTo(jobId)));

        mockMvc.perform(get("/api/jobs/{jobId}", jobId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status", equalTo("SUCCEEDED")))
                .andExpect(jsonPath("$.result_ref", containsString("review_task:")))
                .andExpect(jsonPath("$.events[*].event_type", hasItem("RULESET_ATTACHED")));

        mockMvc.perform(get("/api/projects/{projectId}/quota", projectId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].quota_type", equalTo("webhook_review")))
                .andExpect(jsonPath("$[0].used_count", equalTo(1)));

        mockMvc.perform(get("/api/audit-logs"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.length()", greaterThanOrEqualTo(5)))
                .andExpect(jsonPath("$[*].action", hasItem("QUOTA_CONSUMED")));
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

    private String createOrganization() throws Exception {
        String body = mockMvc.perform(post("/api/organizations")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "name": "Webhook Demo Org",
                                  "plan_name": "team",
                                  "owner_user_id": "owner-1"
                                }
                                """))
                .andExpect(status().isCreated())
                .andReturn()
                .getResponse()
                .getContentAsString();
        return objectMapper.readTree(body).get("id").asText();
    }

    private String createProject(String organizationId) throws Exception {
        String body = mockMvc.perform(post("/api/organizations/{organizationId}/projects", organizationId)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "name": "Webhook Project"
                                }
                                """))
                .andExpect(status().isCreated())
                .andReturn()
                .getResponse()
                .getContentAsString();
        return objectMapper.readTree(body).get("id").asText();
    }

    private void bindRepository(String projectId, String repositoryId) throws Exception {
        mockMvc.perform(post("/api/projects/{projectId}/repositories/{repositoryId}/bind", projectId, repositoryId)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "provider": "fixture-github",
                                  "external_repo_id": "fixture/repolens-java"
                                }
                                """))
                .andExpect(status().isCreated());
    }

    private String createRuleset(String projectId) throws Exception {
        String body = mockMvc.perform(post("/api/projects/{projectId}/rulesets", projectId)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "name": "Webhook Security Rules",
                                  "enabled": true,
                                  "rules": {
                                    "block_permit_all": true
                                  }
                                }
                                """))
                .andExpect(status().isCreated())
                .andReturn()
                .getResponse()
                .getContentAsString();
        return objectMapper.readTree(body).get("id").asText();
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
