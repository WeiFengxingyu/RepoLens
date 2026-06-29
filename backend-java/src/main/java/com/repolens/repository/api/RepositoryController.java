package com.repolens.repository.api;

import com.repolens.repository.api.dto.CreateRepositoryRequest;
import com.repolens.repository.api.dto.RepositoryDetailResponse;
import com.repolens.repository.api.dto.RepositoryStatusResponse;
import com.repolens.repository.api.dto.RepositorySummaryResponse;
import com.repolens.repository.application.RepositoryApplicationService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/repositories")
public class RepositoryController {

    private final RepositoryApplicationService repositoryApplicationService;

    public RepositoryController(RepositoryApplicationService repositoryApplicationService) {
        this.repositoryApplicationService = repositoryApplicationService;
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public RepositoryDetailResponse importRepository(@Valid @RequestBody CreateRepositoryRequest request) {
        return repositoryApplicationService.importRepository(request);
    }

    @GetMapping
    public List<RepositorySummaryResponse> listRepositories() {
        return repositoryApplicationService.listRepositories();
    }

    @GetMapping("/{repositoryId}")
    public RepositoryDetailResponse getRepository(@PathVariable String repositoryId) {
        return repositoryApplicationService.getRepository(repositoryId);
    }

    @GetMapping("/{repositoryId}/status")
    public RepositoryStatusResponse getRepositoryStatus(@PathVariable String repositoryId) {
        return repositoryApplicationService.getStatus(repositoryId);
    }
}
