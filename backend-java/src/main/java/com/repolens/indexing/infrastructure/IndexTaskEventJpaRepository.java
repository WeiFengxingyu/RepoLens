package com.repolens.indexing.infrastructure;

import com.repolens.indexing.domain.IndexTaskEventEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface IndexTaskEventJpaRepository extends JpaRepository<IndexTaskEventEntity, String> {

    List<IndexTaskEventEntity> findByTaskIdOrderByCreatedAtAsc(String taskId);
}
