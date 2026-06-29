package com.repolens.graph.infrastructure;

import com.repolens.graph.domain.CodeSymbolEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface CodeSymbolJpaRepository extends JpaRepository<CodeSymbolEntity, String> {

    List<CodeSymbolEntity> findByRepositoryId(String repositoryId);

    List<CodeSymbolEntity> findTop50ByRepositoryIdAndQualifiedNameContainingIgnoreCaseOrRepositoryIdAndSymbolNameContainingIgnoreCase(
            String repositoryIdForQualifiedName,
            String qualifiedName,
            String repositoryIdForSymbolName,
            String symbolName
    );

    List<CodeSymbolEntity> findByRepositoryIdAndQualifiedName(String repositoryId, String qualifiedName);

    List<CodeSymbolEntity> findByRepositoryIdAndFilePath(String repositoryId, String filePath);

    long countByRepositoryId(String repositoryId);

    void deleteByRepositoryId(String repositoryId);
}
