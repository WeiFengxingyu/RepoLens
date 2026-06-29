package com.repolens.retrieval.api;

import com.repolens.retrieval.api.dto.RetrievalRequest;
import com.repolens.retrieval.api.dto.RetrievalResponse;
import com.repolens.retrieval.application.RetrievalService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/repositories/{repositoryId}/retrieve")
public class RetrievalController {

    private final RetrievalService retrievalService;

    public RetrievalController(RetrievalService retrievalService) {
        this.retrievalService = retrievalService;
    }

    @PostMapping
    public RetrievalResponse retrieve(
            @PathVariable String repositoryId,
            @Valid @RequestBody RetrievalRequest request
    ) {
        return retrievalService.retrieve(repositoryId, request);
    }
}
