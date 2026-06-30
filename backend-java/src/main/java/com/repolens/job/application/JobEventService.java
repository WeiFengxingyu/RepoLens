package com.repolens.job.application;

import com.repolens.common.id.IdGenerator;
import com.repolens.job.domain.JobEventEntity;
import com.repolens.job.infrastructure.JobEventJpaRepository;
import org.springframework.stereotype.Service;

import java.time.Clock;
import java.time.Instant;

@Service
public class JobEventService {

    private final JobEventJpaRepository jobEventJpaRepository;
    private final IdGenerator idGenerator;
    private final Clock clock;

    public JobEventService(JobEventJpaRepository jobEventJpaRepository, IdGenerator idGenerator, Clock clock) {
        this.jobEventJpaRepository = jobEventJpaRepository;
        this.idGenerator = idGenerator;
        this.clock = clock;
    }

    public JobEventEntity record(String jobId, String attemptId, String eventType, String message, String payloadJson) {
        JobEventEntity event = new JobEventEntity(
                idGenerator.newId("evt"),
                jobId,
                attemptId,
                eventType,
                message,
                payloadJson,
                Instant.now(clock)
        );
        return jobEventJpaRepository.save(event);
    }
}
