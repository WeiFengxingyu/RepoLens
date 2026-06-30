package com.repolens.reviewhub.api;

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
import com.repolens.reviewhub.application.ReviewHubService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
public class ReviewHubController {

    private final ReviewHubService reviewHubService;

    public ReviewHubController(ReviewHubService reviewHubService) {
        this.reviewHubService = reviewHubService;
    }

    @PostMapping("/api/organizations")
    @ResponseStatus(HttpStatus.CREATED)
    public OrganizationResponse createOrganization(@Valid @RequestBody OrganizationCreateRequest request) {
        return reviewHubService.createOrganization(request);
    }

    @GetMapping("/api/organizations")
    public List<OrganizationResponse> listOrganizations(@RequestParam(defaultValue = "20") int limit) {
        return reviewHubService.listOrganizations(limit);
    }

    @PostMapping("/api/organizations/{organizationId}/projects")
    @ResponseStatus(HttpStatus.CREATED)
    public ProjectResponse createProject(
            @PathVariable String organizationId,
            @Valid @RequestBody ProjectCreateRequest request
    ) {
        return reviewHubService.createProject(organizationId, request);
    }

    @GetMapping("/api/organizations/{organizationId}/projects")
    public List<ProjectResponse> listProjects(@PathVariable String organizationId) {
        return reviewHubService.listProjects(organizationId);
    }

    @PostMapping("/api/projects/{projectId}/repositories/{repositoryId}/bind")
    @ResponseStatus(HttpStatus.CREATED)
    public RepositoryBindingResponse bindRepository(
            @PathVariable String projectId,
            @PathVariable String repositoryId,
            @Valid @RequestBody RepositoryBindingCreateRequest request
    ) {
        return reviewHubService.bindRepository(projectId, repositoryId, request);
    }

    @GetMapping("/api/projects/{projectId}/repositories")
    public List<RepositoryBindingResponse> listBindings(@PathVariable String projectId) {
        return reviewHubService.listBindings(projectId);
    }

    @PostMapping("/api/projects/{projectId}/rulesets")
    @ResponseStatus(HttpStatus.CREATED)
    public ReviewRulesetResponse createRuleset(
            @PathVariable String projectId,
            @Valid @RequestBody ReviewRulesetCreateRequest request
    ) {
        return reviewHubService.createRuleset(projectId, request);
    }

    @GetMapping("/api/projects/{projectId}/rulesets")
    public List<ReviewRulesetResponse> listRulesets(@PathVariable String projectId) {
        return reviewHubService.listRulesets(projectId);
    }

    @GetMapping("/api/projects/{projectId}/quota")
    public List<QuotaBucketResponse> listProjectQuota(@PathVariable String projectId) {
        return reviewHubService.listProjectQuota(projectId);
    }

    @GetMapping("/api/audit-logs")
    public List<AuditLogResponse> listAuditLogs(@RequestParam(defaultValue = "50") int limit) {
        return reviewHubService.listAuditLogs(limit);
    }
}
