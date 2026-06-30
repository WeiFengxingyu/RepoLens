package com.repolens.change.application;

import java.util.List;
import java.util.Map;

public record FetchedChangeRequest(
        ChangeRequestRef ref,
        String title,
        String author,
        String sourceBranch,
        String targetBranch,
        String state,
        int commitCount,
        List<ChangedRemoteFile> changedFiles,
        String diffText,
        Map<String, Object> metadata,
        List<String> warnings
) {
    public int additionCount() {
        return changedFiles.stream().mapToInt(ChangedRemoteFile::additions).sum();
    }

    public int deletionCount() {
        return changedFiles.stream().mapToInt(ChangedRemoteFile::deletions).sum();
    }
}
