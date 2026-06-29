package com.repolens.evaluation.infrastructure;

import com.repolens.evaluation.domain.EvaluationRunEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface EvaluationRunJpaRepository extends JpaRepository<EvaluationRunEntity, String> {

    List<EvaluationRunEntity> findAllByOrderByCreatedAtDesc();
}
