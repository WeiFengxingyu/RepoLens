package com.repolens.change.application;

import org.springframework.stereotype.Component;

@Component
public class SensitiveTextRedactor {

    public String redact(String value) {
        if (value == null) {
            return null;
        }
        return value
                .replaceAll("(?i)authorization\\s*[:=]\\s*bearer\\s+[^\\s,;]+", "Authorization: Bearer [redacted]")
                .replaceAll("(?i)bearer\\s+[^\\s,;]+", "Bearer [redacted]")
                .replaceAll("(?i)(token|access_token|private_token|api_key)\\s*[:=]\\s*[^\\s,;]+", "$1=[redacted]");
    }
}
