package com.repolens.mcp.infrastructure;

import com.repolens.mcp.domain.McpToolCallAuditEntity;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface McpToolCallAuditJpaRepository extends JpaRepository<McpToolCallAuditEntity, String> {

    List<McpToolCallAuditEntity> findByOrderByCreatedAtDesc(Pageable pageable);
}
