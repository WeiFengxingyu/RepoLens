package com.repolens.reviewhub.infrastructure;

import com.repolens.reviewhub.domain.RepositoryBindingEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface RepositoryBindingJpaRepository extends JpaRepository<RepositoryBindingEntity, String> {
    Optional<RepositoryBindingEntity> findByProviderAndExternalRepoId(String provider, String externalRepoId);

    List<RepositoryBindingEntity> findByProjectIdOrderByCreatedAtDesc(String projectId);
}
