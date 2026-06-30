package com.repolens.change.application;

import org.springframework.stereotype.Component;

import java.util.List;

@Component
public class ChangeRequestProviderRegistry {

    private final List<ChangeRequestProvider> providers;

    public ChangeRequestProviderRegistry(List<ChangeRequestProvider> providers) {
        this.providers = providers;
    }

    public ChangeRequestProvider resolve(ChangeRequestRef ref) {
        return providers.stream()
                .filter(provider -> provider.supports(ref))
                .findFirst()
                .orElseThrow(() -> new IllegalArgumentException("No provider configured for " + ref.platform()));
    }
}
