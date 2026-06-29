package com.repolens.evaluation.infrastructure;

import com.repolens.evaluation.domain.EvaluationResultEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface EvaluationResultJpaRepository extends JpaRepository<EvaluationResultEntity, String> {

    List<EvaluationResultEntity> findByRunIdOrderByStrategyAscSampleIdAsc(String runId);

    void deleteByRunId(String runId);
}
