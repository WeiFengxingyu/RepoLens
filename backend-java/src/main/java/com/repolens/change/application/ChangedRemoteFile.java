package com.repolens.change.application;

public record ChangedRemoteFile(
        String path,
        int additions,
        int deletions
) {
}
