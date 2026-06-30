package com.repolens.reviewhub.infrastructure;

import com.repolens.reviewhub.domain.ProjectEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface ProjectJpaRepository extends JpaRepository<ProjectEntity, String> {
    List<ProjectEntity> findByOrganizationIdOrderByCreatedAtDesc(String organizationId);
}
