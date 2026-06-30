package com.repolens.reviewhub.application;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.repolens.common.error.ResourceNotFoundException;
import com.repolens.common.id.IdGenerator;
import com.repolens.config.RepoLensProperties;
import com.repolens.repository.infrastructure.RepositoryJpaRepository;
import com.repolens.reviewhub.api.dto.AuditLogResponse;
import com.repolens.reviewhub.api.dto.OrganizationCreateRequest;
import com.repolens.reviewhub.api.dto.OrganizationResponse;
import com.repolens.reviewhub.api.dto.ProjectCreateRequest;
import com.repolens.reviewhub.api.dto.ProjectResponse;
import com.repolens.reviewhub.api.dto.QuotaBucketResponse;
import com.repolens.reviewhub.api.dto.RepositoryBindingCreateRequest;
import com.repolens.reviewhub.api.dto.RepositoryBindingResponse;
import com.repolens.reviewhub.api.dto.ReviewRulesetCreateRequest;
import com.repolens.reviewhub.api.dto.ReviewRulesetResponse;
import com.repolens.reviewhub.domain.AuditLogEntity;
import com.repolens.reviewhub.domain.OrganizationEntity;
import com.repolens.reviewhub.domain.ProjectEntity;
import com.repolens.reviewhub.domain.QuotaBucketEntity;
import com.repolens.reviewhub.domain.RepositoryBindingEntity;
import com.repolens.reviewhub.domain.ReviewRulesetEntity;
import com.repolens.reviewhub.domain.TeamMemberEntity;
import com.repolens.reviewhub.infrastructure.AuditLogJpaRepository;
import com.repolens.reviewhub.infrastructure.OrganizationJpaRepository;
import com.repolens.reviewhub.infrastructure.ProjectJpaRepository;
import com.repolens.reviewhub.infrastructure.QuotaBucketJpaRepository;
import com.repolens.reviewhub.infrastructure.RepositoryBindingJpaRepository;
import com.repolens.reviewhub.infrastructure.ReviewRulesetJpaRepository;
import com.repolens.reviewhub.infrastructure.TeamMemberJpaRepository;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@Service
public class ReviewHubService {

    public static final String QUOTA_WEBHOOK_REVIEW = "webhook_review";

    private final OrganizationJpaRepository organizationJpaRepository;
    private final ProjectJpaRepository projectJpaRepository;
    private final TeamMemberJpaRepository teamMemberJpaRepository;
    private final RepositoryBindingJpaRepository repositoryBindingJpaRepository;
    private final ReviewRulesetJpaRepository reviewRulesetJpaRepository;
    private final QuotaBucketJpaRepository quotaBucketJpaRepository;
    private final AuditLogJpaRepository auditLogJpaRepository;
    private final RepositoryJpaRepository repositoryJpaRepository;
    private final RepoLensProperties properties;
    private final IdGenerator idGenerator;
    private final ObjectMapper objectMapper;
    private final Clock clock;

    public ReviewHubService(
            OrganizationJpaRepository organizationJpaRepository,
            ProjectJpaRepository projectJpaRepository,
            TeamMemberJpaRepository teamMemberJpaRepository,
            RepositoryBindingJpaRepository repositoryBindingJpaRepository,
            ReviewRulesetJpaRepository reviewRulesetJpaRepository,
            QuotaBucketJpaRepository quotaBucketJpaRepository,
            AuditLogJpaRepository auditLogJpaRepository,
            RepositoryJpaRepository repositoryJpaRepository,
            RepoLensProperties properties,
            IdGenerator idGenerator,
            ObjectMapper objectMapper,
            Clock clock
    ) {
        this.organizationJpaRepository = organizationJpaRepository;
        this.projectJpaRepository = projectJpaRepository;
        this.teamMemberJpaRepository = teamMemberJpaRepository;
        this.repositoryBindingJpaRepository = repositoryBindingJpaRepository;
        this.reviewRulesetJpaRepository = reviewRulesetJpaRepository;
        this.quotaBucketJpaRepository = quotaBucketJpaRepository;
        this.auditLogJpaRepository = auditLogJpaRepository;
        this.repositoryJpaRepository = repositoryJpaRepository;
        this.properties = properties;
        this.idGenerator = idGenerator;
        this.objectMapper = objectMapper;
        this.clock = clock;
    }

    @Transactional
    public OrganizationResponse createOrganization(OrganizationCreateRequest request) {
        Instant now = Instant.now(clock);
        String ownerUserId = normalize(request.getOwnerUserId(), "local-owner");
        OrganizationEntity organization = new OrganizationEntity(
                idGenerator.newId("org"),
                request.getName().trim(),
                normalize(request.getPlanName(), "free"),
                "ACTIVE",
                now
        );
        organizationJpaRepository.saveAndFlush(organization);
        teamMemberJpaRepository.save(new TeamMemberEntity(
                idGenerator.newId("mem"),
                organization.getId(),
                ownerUserId,
                "OWNER",
                now
        ));
        audit(ownerUserId, "ORGANIZATION_CREATED", "organization", organization.getId(), "organization created", Map.of(
                "name", organization.getName(),
                "plan_name", organization.getPlanName()
        ));
        return OrganizationResponse.from(organization);
    }

    @Transactional(readOnly = true)
    public List<OrganizationResponse> listOrganizations(int limit) {
        int bounded = Math.max(1, Math.min(100, limit));
        return organizationJpaRepository.findByOrderByCreatedAtDesc(PageRequest.of(0, bounded)).stream()
                .map(OrganizationResponse::from)
                .toList();
    }

    @Transactional
    public ProjectResponse createProject(String organizationId, ProjectCreateRequest request) {
        OrganizationEntity organization = organizationJpaRepository.findById(organizationId)
                .orElseThrow(() -> new ResourceNotFoundException("Organization not found"));
        Instant now = Instant.now(clock);
        ProjectEntity project = new ProjectEntity(idGenerator.newId("proj"), organization.getId(), request.getName().trim(), "ACTIVE", now);
        projectJpaRepository.saveAndFlush(project);
        audit("local-owner", "PROJECT_CREATED", "project", project.getId(), "project created", Map.of(
                "organization_id", organization.getId(),
                "name", project.getName()
        ));
        return ProjectResponse.from(project);
    }

    @Transactional(readOnly = true)
    public List<ProjectResponse> listProjects(String organizationId) {
        if (!organizationJpaRepository.existsById(organizationId)) {
            throw new ResourceNotFoundException("Organization not found");
        }
        return projectJpaRepository.findByOrganizationIdOrderByCreatedAtDesc(organizationId).stream()
                .map(ProjectResponse::from)
                .toList();
    }

    @Transactional
    public RepositoryBindingResponse bindRepository(String projectId, String repositoryId, RepositoryBindingCreateRequest request) {
        ProjectEntity project = projectJpaRepository.findById(projectId)
                .orElseThrow(() -> new ResourceNotFoundException("Project not found"));
        if (!repositoryJpaRepository.existsById(repositoryId)) {
            throw new ResourceNotFoundException("Repository not found");
        }
        Instant now = Instant.now(clock);
        RepositoryBindingEntity binding = new RepositoryBindingEntity(
                idGenerator.newId("bind"),
                project.getId(),
                repositoryId,
                normalizeProvider(request.getProvider()),
                request.getExternalRepoId().trim(),
                hashNullable(request.getWebhookSecret()),
                now
        );
        repositoryBindingJpaRepository.saveAndFlush(binding);
        audit("local-owner", "REPOSITORY_BOUND", "project", project.getId(), "repository bound", Map.of(
                "repository_id", repositoryId,
                "provider", binding.getProvider(),
                "external_repo_id", binding.getExternalRepoId()
        ));
        return RepositoryBindingResponse.from(binding);
    }

    @Transactional(readOnly = true)
    public List<RepositoryBindingResponse> listBindings(String projectId) {
        if (!projectJpaRepository.existsById(projectId)) {
            throw new ResourceNotFoundException("Project not found");
        }
        return repositoryBindingJpaRepository.findByProjectIdOrderByCreatedAtDesc(projectId).stream()
                .map(RepositoryBindingResponse::from)
                .toList();
    }

    @Transactional
    public ReviewRulesetResponse createRuleset(String projectId, ReviewRulesetCreateRequest request) {
        ProjectEntity project = projectJpaRepository.findById(projectId)
                .orElseThrow(() -> new ResourceNotFoundException("Project not found"));
        Instant now = Instant.now(clock);
        ReviewRulesetEntity ruleset = new ReviewRulesetEntity(
                idGenerator.newId("rule"),
                project.getId(),
                request.getName().trim(),
                toJson(request.getRules()),
                request.getEnabled() == null || request.getEnabled(),
                now
        );
        reviewRulesetJpaRepository.saveAndFlush(ruleset);
        audit("local-owner", "REVIEW_RULESET_CREATED", "project", project.getId(), "review ruleset created", Map.of(
                "ruleset_id", ruleset.getId(),
                "name", ruleset.getName(),
                "enabled", ruleset.isEnabled()
        ));
        return ReviewRulesetResponse.from(ruleset, objectMapper);
    }

    @Transactional(readOnly = true)
    public List<ReviewRulesetResponse> listRulesets(String projectId) {
        if (!projectJpaRepository.existsById(projectId)) {
            throw new ResourceNotFoundException("Project not found");
        }
        return reviewRulesetJpaRepository.findByProjectIdOrderByCreatedAtDesc(projectId).stream()
                .map(entity -> ReviewRulesetResponse.from(entity, objectMapper))
                .toList();
    }

    @Transactional(readOnly = true)
    public Optional<ReviewRulesetEntity> findLatestEnabledRuleset(String projectId) {
        return reviewRulesetJpaRepository.findFirstByProjectIdAndEnabledTrueOrderByCreatedAtDesc(projectId);
    }

    @Transactional
    public QuotaBucketEntity consumeProjectQuota(String projectId, String quotaType, String actor, Map<String, Object> payload) {
        if (!projectJpaRepository.existsById(projectId)) {
            throw new ResourceNotFoundException("Project not found");
        }
        Instant now = Instant.now(clock);
        Duration window = Duration.ofMinutes(properties.getV2Lite().getReviewHub().getQuotaWindowMinutes());
        Instant windowStart = windowStart(now, window);
        Instant windowEnd = windowStart.plus(window);
        QuotaBucketEntity bucket = quotaBucketJpaRepository
                .findByScopeTypeAndScopeIdAndQuotaTypeAndWindowStart("project", projectId, quotaType, windowStart)
                .orElseGet(() -> new QuotaBucketEntity(
                        idGenerator.newId("quota"),
                        "project",
                        projectId,
                        quotaType,
                        properties.getV2Lite().getReviewHub().getDefaultQuotaLimit(),
                        windowStart,
                        windowEnd,
                        now
                ));
        if (bucket.getUsedCount() >= bucket.getLimitCount()) {
            throw new IllegalStateException("Project quota exceeded for " + quotaType);
        }
        bucket.consume(now);
        quotaBucketJpaRepository.saveAndFlush(bucket);
        audit(actor, "QUOTA_CONSUMED", "project", projectId, "project quota consumed", Map.of(
                "quota_type", quotaType,
                "used_count", bucket.getUsedCount(),
                "limit_count", bucket.getLimitCount(),
                "trigger", payload
        ));
        return bucket;
    }

    @Transactional(readOnly = true)
    public List<QuotaBucketResponse> listProjectQuota(String projectId) {
        if (!projectJpaRepository.existsById(projectId)) {
            throw new ResourceNotFoundException("Project not found");
        }
        return quotaBucketJpaRepository.findByScopeTypeAndScopeIdOrderByWindowStartDesc("project", projectId).stream()
                .map(QuotaBucketResponse::from)
                .toList();
    }

    @Transactional(readOnly = true)
    public RepositoryBindingEntity resolveBinding(String provider, String externalRepoId) {
        RepositoryBindingEntity binding = repositoryBindingJpaRepository
                .findByProviderAndExternalRepoId(normalizeProvider(provider), externalRepoId.trim())
                .orElseThrow(() -> new ResourceNotFoundException("Repository binding not found"));
        if (!binding.isEnabled()) {
            throw new IllegalStateException("Repository binding is disabled");
        }
        return binding;
    }

    @Transactional(readOnly = true)
    public void validateWebhookSecret(RepositoryBindingEntity binding, String providedSecret) {
        if (!properties.getV2Lite().getWebhook().isRequireSecret()) {
            return;
        }
        String expected = binding.getWebhookSecretHash();
        if (expected == null || !expected.equals(hashNullable(providedSecret))) {
            throw new IllegalStateException("Invalid webhook secret");
        }
    }

    @Transactional(readOnly = true)
    public List<AuditLogResponse> listAuditLogs(int limit) {
        int bounded = Math.max(1, Math.min(100, limit));
        return auditLogJpaRepository.findByOrderByCreatedAtDesc(PageRequest.of(0, bounded)).stream()
                .map(entity -> AuditLogResponse.from(entity, objectMapper))
                .toList();
    }

    private void audit(String actor, String action, String scopeType, String scopeId, String message, Map<String, Object> payload) {
        auditLogJpaRepository.save(new AuditLogEntity(
                idGenerator.newId("aud"),
                normalize(actor, "system"),
                action,
                scopeType,
                scopeId,
                message,
                toJson(payload),
                Instant.now(clock)
        ));
    }

    private Instant windowStart(Instant now, Duration window) {
        long seconds = window.getSeconds();
        return Instant.ofEpochSecond((now.getEpochSecond() / seconds) * seconds);
    }

    private String normalizeProvider(String value) {
        return normalize(value, null).toLowerCase();
    }

    private String normalize(String value, String fallback) {
        if (value == null || value.isBlank()) {
            return fallback;
        }
        return value.trim();
    }

    private String hashNullable(String value) {
        if (value == null || value.isBlank()) {
            return null;
        }
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            return HexFormat.of().formatHex(digest.digest(value.trim().getBytes(StandardCharsets.UTF_8)));
        } catch (NoSuchAlgorithmException exception) {
            throw new IllegalStateException("SHA-256 is not available", exception);
        }
    }

    private String toJson(Object value) {
        try {
            return objectMapper.writeValueAsString(value == null ? Map.of() : value);
        } catch (JsonProcessingException exception) {
            throw new IllegalStateException("Failed to serialize ReviewHub payload", exception);
        }
    }
}
