package com.repolens.job.application;

public record LockHandle(
        String key,
        String ownerToken
) {
}
