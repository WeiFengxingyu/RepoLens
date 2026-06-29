package com.repolens.evaluation.application;

import com.repolens.evaluation.api.dto.EvaluationMetricResponse;
import com.repolens.evaluation.domain.EvaluationResultEntity;
import org.springframework.stereotype.Component;

import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Component
public class EvaluationMetricCalculator {

    public List<EvaluationMetricResponse> calculate(List<EvaluationResultEntity> results) {
        Map<String, List<EvaluationResultEntity>> byStrategy = results.stream()
                .collect(Collectors.groupingBy(EvaluationResultEntity::getStrategy, java.util.LinkedHashMap::new, Collectors.toList()));
        return byStrategy.entrySet().stream()
                .map(entry -> metric(entry.getKey(), entry.getValue()))
                .toList();
    }

    private EvaluationMetricResponse metric(String strategy, List<EvaluationResultEntity> results) {
        int sampleCount = results.size();
        if (sampleCount == 0) {
            return new EvaluationMetricResponse(strategy, 0, 0.0D, 0.0D, 0.0D, 0.0D, 0.0D, 0.0D, 0.0D, true, 0, 0);
        }
        int errorCount = (int) results.stream().filter(result -> result.getErrorMessage() != null).count();
        int tokenEstimatedCount = (int) results.stream().filter(EvaluationResultEntity::isTokenEstimated).count();
        List<Long> latencies = results.stream().map(EvaluationResultEntity::getLatencyMs).sorted().toList();
        return new EvaluationMetricResponse(
                strategy,
                sampleCount,
                average(results.stream().map(result -> result.isHitAt5() ? 1.0D : 0.0D).toList()),
                average(results.stream().map(EvaluationResultEntity::getMrr).toList()),
                average(results.stream().map(EvaluationResultEntity::getCitationCoverage).toList()),
                average(results.stream().map(result -> (double) result.getLatencyMs()).toList()),
                percentile(latencies, 0.50D),
                percentile(latencies, 0.95D),
                average(results.stream().map(result -> (double) result.getTokenCount()).toList()),
                tokenEstimatedCount > 0,
                tokenEstimatedCount,
                errorCount
        );
    }

    private double average(List<Double> values) {
        return values.stream().mapToDouble(Double::doubleValue).average().orElse(0.0D);
    }

    private double percentile(List<Long> sortedValues, double percentile) {
        if (sortedValues.isEmpty()) {
            return 0.0D;
        }
        List<Long> values = sortedValues.stream().sorted(Comparator.naturalOrder()).toList();
        int index = (int) Math.ceil(percentile * values.size()) - 1;
        return values.get(Math.max(0, Math.min(values.size() - 1, index)));
    }
}
