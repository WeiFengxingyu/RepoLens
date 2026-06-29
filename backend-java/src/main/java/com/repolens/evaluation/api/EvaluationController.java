package com.repolens.evaluation.api;

import com.repolens.evaluation.api.dto.EvaluationCreateRequest;
import com.repolens.evaluation.api.dto.EvaluationRunResponse;
import com.repolens.evaluation.api.dto.EvaluationRunSummaryResponse;
import com.repolens.evaluation.application.EvaluationService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/evaluations")
public class EvaluationController {

    private final EvaluationService evaluationService;

    public EvaluationController(EvaluationService evaluationService) {
        this.evaluationService = evaluationService;
    }

    @PostMapping
    public EvaluationRunResponse create(@Valid @RequestBody EvaluationCreateRequest request) {
        return evaluationService.create(request);
    }

    @GetMapping
    public List<EvaluationRunSummaryResponse> list() {
        return evaluationService.list();
    }

    @GetMapping("/{runId}")
    public EvaluationRunResponse get(@PathVariable String runId) {
        return evaluationService.get(runId);
    }
}
