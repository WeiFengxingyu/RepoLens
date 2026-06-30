package com.repolens.reviewhub.infrastructure;

import com.repolens.reviewhub.domain.QuotaBucketEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

public interface QuotaBucketJpaRepository extends JpaRepository<QuotaBucketEntity, String> {
    Optional<QuotaBucketEntity> findByScopeTypeAndScopeIdAndQuotaTypeAndWindowStart(
            String scopeType,
            String scopeId,
            String quotaType,
            Instant windowStart
    );

    List<QuotaBucketEntity> findByScopeTypeAndScopeIdOrderByWindowStartDesc(String scopeType, String scopeId);
}
