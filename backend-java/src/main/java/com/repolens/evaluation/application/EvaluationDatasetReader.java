package com.repolens.evaluation.application;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

@Component
public class EvaluationDatasetReader {

    private final ObjectMapper objectMapper;

    public EvaluationDatasetReader(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
    }

    public List<EvaluationSample> read(String datasetPath) {
        Path path = Path.of(datasetPath).toAbsolutePath().normalize();
        if (!Files.exists(path) || !Files.isRegularFile(path)) {
            throw new IllegalArgumentException("Evaluation dataset not found: " + datasetPath);
        }
        try {
            return Files.readAllLines(path).stream()
                    .map(String::trim)
                    .filter(line -> !line.isBlank())
                    .filter(line -> !line.startsWith("#"))
                    .map(this::readLine)
                    .toList();
        } catch (IOException exception) {
            throw new IllegalArgumentException("Unable to read evaluation dataset: " + datasetPath, exception);
        }
    }

    private EvaluationSample readLine(String line) {
        try {
            EvaluationSample sample = objectMapper.readValue(line, EvaluationSample.class);
            validate(sample);
            return sample;
        } catch (IOException exception) {
            throw new IllegalArgumentException("Invalid evaluation sample JSONL line", exception);
        }
    }

    private void validate(EvaluationSample sample) {
        if (sample.id() == null || sample.id().isBlank()) {
            throw new IllegalArgumentException("Evaluation sample id is required");
        }
        if (sample.repositoryKey() == null || sample.repositoryKey().isBlank()) {
            throw new IllegalArgumentException("Evaluation sample repository_key is required");
        }
        if (sample.query() == null || sample.query().isBlank()) {
            throw new IllegalArgumentException("Evaluation sample query is required");
        }
    }
}
