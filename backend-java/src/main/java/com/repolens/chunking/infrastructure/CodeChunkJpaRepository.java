package com.repolens.chunking.infrastructure;

import com.repolens.chunking.domain.CodeChunkEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface CodeChunkJpaRepository extends JpaRepository<CodeChunkEntity, String> {

    List<CodeChunkEntity> findByRepositoryId(String repositoryId);

    List<CodeChunkEntity> findByRepositoryIdAndIdIn(String repositoryId, List<String> ids);

    List<CodeChunkEntity> findByRepositoryIdAndSymbolNameIn(String repositoryId, List<String> symbolNames);

    void deleteByRepositoryId(String repositoryId);
}
