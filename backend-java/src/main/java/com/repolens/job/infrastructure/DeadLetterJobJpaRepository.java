package com.repolens.job.infrastructure;

import com.repolens.job.domain.DeadLetterJobEntity;
import org.springframework.data.jpa.repository.JpaRepository;

public interface DeadLetterJobJpaRepository extends JpaRepository<DeadLetterJobEntity, String> {
}
