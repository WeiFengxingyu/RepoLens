package com.repolens.job.api;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.repolens.job.domain.JobStatus;
import com.repolens.job.infrastructure.AnalysisJobJpaRepository;
import com.repolens.job.infrastructure.DeadLetterJobJpaRepository;
import com.repolens.job.infrastructure.JobAttemptJpaRepository;
import com.repolens.job.infrastructure.JobEventJpaRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import java.time.Duration;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;
import static org.awaitility.Awaitility.await;
import static org.hamcrest.Matchers.equalTo;
import static org.hamcrest.Matchers.greaterThan;
import static org.hamcrest.Matchers.notNullValue;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
class JobControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private AnalysisJobJpaRepository analysisJobJpaRepository;

    @Autowired
    private JobAttemptJpaRepository jobAttemptJpaRepository;

    @Autowired
    private JobEventJpaRepository jobEventJpaRepository;

    @Autowired
    private DeadLetterJobJpaRepository deadLetterJobJpaRepository;

    @BeforeEach
    void setUp() {
        deadLetterJobJpaRepository.deleteAll();
        jobEventJpaRepository.deleteAll();
        jobAttemptJpaRepository.deleteAll();
        analysisJobJpaRepository.deleteAll();
    }

    @Test
    void createsIdempotentNoopJobAndCompletesAsync() throws Exception {
        String body = mockMvc.perform(post("/api/jobs")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "job_type": "NOOP",
                                  "idempotency_key": "idem-noop-1",
                                  "payload_json": "{}",
                                  "created_by": "tester"
                                }
                                """))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.id", notNullValue()))
                .andExpect(jsonPath("$.job_type", equalTo("NOOP")))
                .andReturn()
                .getResponse()
                .getContentAsString();
        String jobId = objectMapper.readTree(body).get("id").asText();

        await().atMost(Duration.ofSeconds(5)).untilAsserted(() ->
                assertThat(analysisJobJpaRepository.findById(jobId).orElseThrow().getStatus())
                        .isEqualTo(JobStatus.SUCCEEDED)
        );

        mockMvc.perform(post("/api/jobs")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "job_type": "NOOP",
                                  "idempotency_key": "idem-noop-1",
                                  "payload_json": "{}"
                                }
                                """))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.id", equalTo(jobId)));

        mockMvc.perform(get("/api/jobs/{jobId}", jobId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status", equalTo("SUCCEEDED")))
                .andExpect(jsonPath("$.attempts.length()", equalTo(1)))
                .andExpect(jsonPath("$.events.length()", greaterThan(0)))
                .andExpect(jsonPath("$.result_ref", equalTo("noop:" + jobId)));
    }

    @Test
    void failedNoopJobMovesToDeadLetterAndCanBeListed() throws Exception {
        String payload = objectMapper.writeValueAsString(Map.of("fail", true));
        String body = mockMvc.perform(post("/api/jobs")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "job_type": "NOOP",
                                  "payload_json": %s
                                }
                                """.formatted(objectMapper.writeValueAsString(payload))))
                .andExpect(status().isCreated())
                .andReturn()
                .getResponse()
                .getContentAsString();
        String jobId = objectMapper.readTree(body).get("id").asText();

        await().atMost(Duration.ofSeconds(5)).untilAsserted(() -> {
            assertThat(analysisJobJpaRepository.findById(jobId).orElseThrow().getStatus()).isEqualTo(JobStatus.DEAD);
            assertThat(deadLetterJobJpaRepository.findById(jobId)).isPresent();
        });

        mockMvc.perform(get("/api/jobs/{jobId}/events", jobId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.length()", greaterThan(0)));
    }

    @Test
    void retryableNoopJobRetriesUntilDeadLetter() throws Exception {
        String payload = objectMapper.writeValueAsString(Map.of("fail", true, "retryable", true));
        String body = mockMvc.perform(post("/api/jobs")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "job_type": "NOOP",
                                  "payload_json": %s
                                }
                                """.formatted(objectMapper.writeValueAsString(payload))))
                .andExpect(status().isCreated())
                .andReturn()
                .getResponse()
                .getContentAsString();
        String jobId = objectMapper.readTree(body).get("id").asText();

        await().atMost(Duration.ofSeconds(8)).untilAsserted(() -> {
            assertThat(analysisJobJpaRepository.findById(jobId).orElseThrow().getStatus()).isEqualTo(JobStatus.DEAD);
            assertThat(jobAttemptJpaRepository.countByJobId(jobId)).isEqualTo(3);
            assertThat(deadLetterJobJpaRepository.findById(jobId)).isPresent();
        });
    }
}
