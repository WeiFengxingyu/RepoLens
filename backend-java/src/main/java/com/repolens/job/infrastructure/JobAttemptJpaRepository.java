package com.repolens.job.infrastructure;

import com.repolens.job.domain.JobAttemptEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface JobAttemptJpaRepository extends JpaRepository<JobAttemptEntity, String> {

    List<JobAttemptEntity> findByJobIdOrderByAttemptNoAsc(String jobId);

    long countByJobId(String jobId);
}
