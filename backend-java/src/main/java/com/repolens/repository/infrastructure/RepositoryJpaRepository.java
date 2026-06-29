package com.repolens.repository.infrastructure;

import com.repolens.repository.domain.RepositoryEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface RepositoryJpaRepository extends JpaRepository<RepositoryEntity, String> {
    List<RepositoryEntity> findAllByOrderByCreatedAtDesc();
}
