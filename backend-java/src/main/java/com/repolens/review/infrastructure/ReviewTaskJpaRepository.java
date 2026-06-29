package com.repolens.review.infrastructure;

import com.repolens.review.domain.ReviewTaskEntity;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ReviewTaskJpaRepository extends JpaRepository<ReviewTaskEntity, String> {
}
