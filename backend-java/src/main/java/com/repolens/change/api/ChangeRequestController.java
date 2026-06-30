package com.repolens.change.api;

import com.repolens.change.api.dto.ChangeRequestMetadataResponse;
import com.repolens.change.api.dto.ChangeRequestReviewCreateRequest;
import com.repolens.change.api.dto.ChangeRequestReviewResponse;
import com.repolens.change.application.ChangeRequestReviewService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class ChangeRequestController {

    private final ChangeRequestReviewService changeRequestReviewService;

    public ChangeRequestController(ChangeRequestReviewService changeRequestReviewService) {
        this.changeRequestReviewService = changeRequestReviewService;
    }

    @PostMapping("/api/repositories/{repositoryId}/change-requests/reviews")
    public ChangeRequestReviewResponse review(
            @PathVariable String repositoryId,
            @Valid @RequestBody ChangeRequestReviewCreateRequest request
    ) {
        return changeRequestReviewService.review(repositoryId, request);
    }

    @GetMapping("/api/change-requests/{changeRequestId}")
    public ChangeRequestMetadataResponse getChangeRequest(@PathVariable String changeRequestId) {
        return changeRequestReviewService.getChangeRequest(changeRequestId);
    }

    @GetMapping("/api/change-requests/tasks/{taskId}")
    public ChangeRequestMetadataResponse getChangeRequestByTask(@PathVariable String taskId) {
        return changeRequestReviewService.getChangeRequestByTask(taskId);
    }
}
