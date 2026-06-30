package com.repolens.reviewhub.infrastructure;

import com.repolens.reviewhub.domain.TeamMemberEntity;
import org.springframework.data.jpa.repository.JpaRepository;

public interface TeamMemberJpaRepository extends JpaRepository<TeamMemberEntity, String> {
}
