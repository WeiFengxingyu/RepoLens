package com.repolens.review.api;

import com.repolens.review.api.dto.ReviewCreateRequest;
import com.repolens.review.api.dto.ReviewTaskResponse;
import com.repolens.review.application.ReviewService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class ReviewController {

    private final ReviewService reviewService;

    public ReviewController(ReviewService reviewService) {
        this.reviewService = reviewService;
    }

    @PostMapping("/api/repositories/{repositoryId}/reviews")
    public ReviewTaskResponse review(
            @PathVariable String repositoryId,
            @Valid @RequestBody ReviewCreateRequest request
    ) {
        return reviewService.review(repositoryId, request);
    }

    @GetMapping("/api/reviews/{taskId}")
    public ReviewTaskResponse getReview(@PathVariable String taskId) {
        return reviewService.getReview(taskId);
    }
}
