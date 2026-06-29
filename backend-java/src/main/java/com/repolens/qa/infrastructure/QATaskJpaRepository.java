package com.repolens.qa.infrastructure;

import com.repolens.qa.domain.QATaskEntity;
import org.springframework.data.jpa.repository.JpaRepository;

public interface QATaskJpaRepository extends JpaRepository<QATaskEntity, String> {
}
