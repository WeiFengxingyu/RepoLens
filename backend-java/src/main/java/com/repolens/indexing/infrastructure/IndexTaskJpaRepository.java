package com.repolens.indexing.infrastructure;

import com.repolens.indexing.domain.IndexTaskEntity;
import com.repolens.indexing.domain.IndexTaskStatus;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface IndexTaskJpaRepository extends JpaRepository<IndexTaskEntity, String> {

    Optional<IndexTaskEntity> findFirstByRepositoryIdOrderByCreatedAtDesc(String repositoryId);

    List<IndexTaskEntity> findByRepositoryIdAndStatusIn(String repositoryId, List<IndexTaskStatus> statuses);
}
