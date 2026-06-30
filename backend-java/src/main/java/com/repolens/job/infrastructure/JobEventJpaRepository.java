package com.repolens.job.infrastructure;

import com.repolens.job.domain.JobEventEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface JobEventJpaRepository extends JpaRepository<JobEventEntity, String> {

    List<JobEventEntity> findByJobIdOrderByCreatedAtAsc(String jobId);
}
