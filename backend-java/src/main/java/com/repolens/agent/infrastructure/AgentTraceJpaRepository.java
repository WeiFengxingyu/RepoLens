package com.repolens.agent.infrastructure;

import com.repolens.agent.domain.AgentTraceEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface AgentTraceJpaRepository extends JpaRepository<AgentTraceEntity, String> {

    List<AgentTraceEntity> findByTaskIdOrderByStepOrderAsc(String taskId);
}
