package com.repolens.change.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.repolens.review.api.dto.ReviewTaskResponse;

public record ChangeRequestReviewResponse(
        @JsonProperty("change_request")
        ChangeRequestMetadataResponse changeRequest,
        ReviewTaskResponse review
) {
}
