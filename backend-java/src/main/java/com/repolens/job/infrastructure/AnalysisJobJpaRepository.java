package com.repolens.job.infrastructure;

import com.repolens.job.domain.AnalysisJobEntity;
import com.repolens.job.domain.JobStatus;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface AnalysisJobJpaRepository extends JpaRepository<AnalysisJobEntity, String> {

    Optional<AnalysisJobEntity> findByIdempotencyKey(String idempotencyKey);

    List<AnalysisJobEntity> findByStatusOrderByCreatedAtAsc(JobStatus status);

    List<AnalysisJobEntity> findByOrderByCreatedAtDesc(Pageable pageable);
}
