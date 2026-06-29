package com.repolens.retrieval.vector;

public interface EmbeddingProvider {

    String modelName();

    int dimensions();

    double[] embed(String text);
}
