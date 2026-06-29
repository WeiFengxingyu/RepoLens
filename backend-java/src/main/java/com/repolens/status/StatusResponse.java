package com.repolens.status;

public record StatusResponse(
        String service,
        String version,
        String status,
        StorageStatus storage
) {
    public record StorageStatus(
            String database,
            String workspaceRoot,
            String indexRoot
    ) {
    }
}
