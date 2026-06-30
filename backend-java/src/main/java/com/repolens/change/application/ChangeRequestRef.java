package com.repolens.change.application;

public record ChangeRequestRef(
        String platform,
        String changeType,
        String owner,
        String repo,
        String number,
        String url
) {
}
