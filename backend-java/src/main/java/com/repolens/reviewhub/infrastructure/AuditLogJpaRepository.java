package com.repolens.reviewhub.infrastructure;

import com.repolens.reviewhub.domain.AuditLogEntity;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface AuditLogJpaRepository extends JpaRepository<AuditLogEntity, String> {
    List<AuditLogEntity> findByOrderByCreatedAtDesc(Pageable pageable);
}
