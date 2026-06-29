package com.repolens.qa.api;

import com.repolens.qa.api.dto.QACreateRequest;
import com.repolens.qa.api.dto.QATaskResponse;
import com.repolens.qa.application.QuestionAnsweringService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class QuestionController {

    private final QuestionAnsweringService questionAnsweringService;

    public QuestionController(QuestionAnsweringService questionAnsweringService) {
        this.questionAnsweringService = questionAnsweringService;
    }

    @PostMapping("/api/repositories/{repositoryId}/questions")
    public QATaskResponse ask(
            @PathVariable String repositoryId,
            @Valid @RequestBody QACreateRequest request
    ) {
        return questionAnsweringService.ask(repositoryId, request);
    }

    @GetMapping("/api/questions/{taskId}")
    public QATaskResponse getTask(@PathVariable String taskId) {
        return questionAnsweringService.getTask(taskId);
    }
}
