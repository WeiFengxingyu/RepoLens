package com.repolens.retrieval.vector;

import com.repolens.config.RepoLensProperties;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class HashEmbeddingProviderTest {

    @Test
    void createsDeterministicNormalizedEmbeddings() {
        HashEmbeddingProvider provider = new HashEmbeddingProvider(new RepoLensProperties());

        double[] first = provider.embed("JWT authentication token filter");
        double[] second = provider.embed("JWT authentication token filter");
        double norm = 0.0D;
        for (double value : first) {
            norm += value * value;
        }

        assertThat(provider.modelName()).isEqualTo("hash-embedding-v1");
        assertThat(first).hasSize(provider.dimensions());
        assertThat(first).containsExactly(second);
        assertThat(Math.sqrt(norm)).isCloseTo(1.0D, org.assertj.core.data.Offset.offset(0.000001D));
    }
}
