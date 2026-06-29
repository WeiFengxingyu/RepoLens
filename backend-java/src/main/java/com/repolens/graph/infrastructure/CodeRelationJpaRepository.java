package com.repolens.graph.infrastructure;

import com.repolens.graph.domain.CodeRelationEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface CodeRelationJpaRepository extends JpaRepository<CodeRelationEntity, String> {

    List<CodeRelationEntity> findByRepositoryId(String repositoryId);

    List<CodeRelationEntity> findByRepositoryIdAndSourceSymbolIdOrRepositoryIdAndTargetSymbolId(
            String repositoryIdForSource,
            String sourceSymbolId,
            String repositoryIdForTarget,
            String targetSymbolId
    );

    List<CodeRelationEntity> findByRepositoryIdAndRelationType(String repositoryId, String relationType);

    long countByRepositoryId(String repositoryId);

    long countByRepositoryIdAndRelationType(String repositoryId, String relationType);

    void deleteByRepositoryId(String repositoryId);
}
