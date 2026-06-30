package com.repolens.change.infrastructure;

import com.repolens.change.domain.ChangeRequestEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface ChangeRequestJpaRepository extends JpaRepository<ChangeRequestEntity, String> {
    Optional<ChangeRequestEntity> findByReviewTaskId(String reviewTaskId);
}
