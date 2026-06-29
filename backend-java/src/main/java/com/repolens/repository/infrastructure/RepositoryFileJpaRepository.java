package com.repolens.repository.infrastructure;

import com.repolens.repository.domain.RepositoryFileEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface RepositoryFileJpaRepository extends JpaRepository<RepositoryFileEntity, String> {

    List<RepositoryFileEntity> findByRepositoryId(String repositoryId);

    List<RepositoryFileEntity> findByRepositoryIdAndSkippedFalseOrderByRelativePathAsc(String repositoryId);

    void deleteByRepositoryId(String repositoryId);
}
