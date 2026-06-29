package com.repolens.review.infrastructure;

import com.repolens.review.domain.ReviewToolCallEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface ReviewToolCallJpaRepository extends JpaRepository<ReviewToolCallEntity, String> {

    List<ReviewToolCallEntity> findByTaskIdOrderByCreatedAtAsc(String taskId);
}
