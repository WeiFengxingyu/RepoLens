package com.repolens.indexing.api;

import com.repolens.indexing.api.dto.IndexTaskResponse;
import com.repolens.indexing.application.RepositoryIndexingService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class IndexTaskController {

    private final RepositoryIndexingService repositoryIndexingService;

    public IndexTaskController(RepositoryIndexingService repositoryIndexingService) {
        this.repositoryIndexingService = repositoryIndexingService;
    }

    @PostMapping("/api/repositories/{repositoryId}/index")
    public IndexTaskResponse startIndex(@PathVariable String repositoryId) {
        return repositoryIndexingService.getTask(repositoryIndexingService.startIndex(repositoryId).getId());
    }

    @GetMapping("/api/repositories/{repositoryId}/index-tasks/latest")
    public IndexTaskResponse latest(@PathVariable String repositoryId) {
        return repositoryIndexingService.getLatestTask(repositoryId);
    }

    @GetMapping("/api/index-tasks/{taskId}")
    public IndexTaskResponse getTask(@PathVariable String taskId) {
        return repositoryIndexingService.getTask(taskId);
    }

    @PostMapping("/api/index-tasks/{taskId}/retry")
    public IndexTaskResponse retry(@PathVariable String taskId) {
        return repositoryIndexingService.retry(taskId);
    }
}
