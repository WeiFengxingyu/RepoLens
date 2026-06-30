package com.repolens.reviewhub.infrastructure;

import com.repolens.reviewhub.domain.OrganizationEntity;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface OrganizationJpaRepository extends JpaRepository<OrganizationEntity, String> {
    List<OrganizationEntity> findByOrderByCreatedAtDesc(Pageable pageable);
}
