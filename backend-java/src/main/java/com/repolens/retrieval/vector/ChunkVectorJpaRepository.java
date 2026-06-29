package com.repolens.retrieval.vector;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface ChunkVectorJpaRepository extends JpaRepository<ChunkVectorEntity, String> {

    List<ChunkVectorEntity> findByRepositoryId(String repositoryId);

    long countByRepositoryId(String repositoryId);

    void deleteByRepositoryId(String repositoryId);
}
