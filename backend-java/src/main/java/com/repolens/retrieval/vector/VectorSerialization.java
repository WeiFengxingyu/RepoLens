package com.repolens.retrieval.vector;

import java.util.Arrays;

final class VectorSerialization {

    private VectorSerialization() {
    }

    static String serialize(double[] vector) {
        return Arrays.toString(vector);
    }

    static double[] deserialize(String value) {
        if (value == null || value.isBlank()) {
            return new double[0];
        }
        String trimmed = value.trim();
        if (trimmed.startsWith("[") && trimmed.endsWith("]")) {
            trimmed = trimmed.substring(1, trimmed.length() - 1);
        }
        if (trimmed.isBlank()) {
            return new double[0];
        }
        String[] parts = trimmed.split(",");
        double[] vector = new double[parts.length];
        for (int index = 0; index < parts.length; index++) {
            vector[index] = Double.parseDouble(parts[index].trim());
        }
        return vector;
    }
}
