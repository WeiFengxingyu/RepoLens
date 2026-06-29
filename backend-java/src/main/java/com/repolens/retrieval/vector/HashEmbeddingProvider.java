package com.repolens.retrieval.vector;

import com.repolens.config.RepoLensProperties;
import org.springframework.stereotype.Component;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;

@Component
public class HashEmbeddingProvider implements EmbeddingProvider {

    private final int dimensions;

    public HashEmbeddingProvider(RepoLensProperties properties) {
        this.dimensions = properties.getRetrieval().getVectorDimensions();
    }

    @Override
    public String modelName() {
        return "hash-embedding-v1";
    }

    @Override
    public int dimensions() {
        return dimensions;
    }

    @Override
    public double[] embed(String text) {
        double[] vector = new double[dimensions];
        if (text == null || text.isBlank()) {
            return vector;
        }
        for (String token : text.toLowerCase(java.util.Locale.ROOT).split("[^a-z0-9_./:-]+")) {
            if (token.isBlank()) {
                continue;
            }
            byte[] hash = sha256(token);
            int bucket = Byte.toUnsignedInt(hash[0]) % dimensions;
            int sign = (hash[1] & 1) == 0 ? 1 : -1;
            vector[bucket] += sign * (1.0D + Math.min(token.length(), 24) / 24.0D);
        }
        normalize(vector);
        return vector;
    }

    private byte[] sha256(String value) {
        try {
            return MessageDigest.getInstance("SHA-256").digest(value.getBytes(StandardCharsets.UTF_8));
        } catch (NoSuchAlgorithmException exception) {
            throw new IllegalStateException("SHA-256 is not available", exception);
        }
    }

    private void normalize(double[] vector) {
        double sum = 0.0D;
        for (double value : vector) {
            sum += value * value;
        }
        if (sum == 0.0D) {
            return;
        }
        double norm = Math.sqrt(sum);
        for (int index = 0; index < vector.length; index++) {
            vector[index] = vector[index] / norm;
        }
    }
}
