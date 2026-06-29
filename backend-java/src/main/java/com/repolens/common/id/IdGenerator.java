package com.repolens.common.id;

import org.springframework.stereotype.Component;

import java.util.Locale;
import java.util.UUID;

@Component
public class IdGenerator {

    public String newId(String prefix) {
        String normalizedPrefix = prefix == null ? "" : prefix.trim().toLowerCase(Locale.ROOT);
        if (normalizedPrefix.isBlank()) {
            throw new IllegalArgumentException("ID prefix must not be blank");
        }
        return normalizedPrefix + "_" + UUID.randomUUID().toString().replace("-", "");
    }
}
