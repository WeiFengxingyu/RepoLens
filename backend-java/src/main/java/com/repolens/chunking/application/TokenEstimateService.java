package com.repolens.chunking.application;

import org.springframework.stereotype.Component;

@Component
public class TokenEstimateService {

    public int estimate(String content) {
        if (content == null || content.isBlank()) {
            return 1;
        }
        return Math.max(1, content.length() / 4);
    }
}
