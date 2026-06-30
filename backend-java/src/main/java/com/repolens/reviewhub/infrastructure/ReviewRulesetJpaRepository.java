package com.repolens.reviewhub.infrastructure;

import com.repolens.reviewhub.domain.ReviewRulesetEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface ReviewRulesetJpaRepository extends JpaRepository<ReviewRulesetEntity, String> {
    List<ReviewRulesetEntity> findByProjectIdOrderByCreatedAtDesc(String projectId);

    Optional<ReviewRulesetEntity> findFirstByProjectIdAndEnabledTrueOrderByCreatedAtDesc(String projectId);
}
