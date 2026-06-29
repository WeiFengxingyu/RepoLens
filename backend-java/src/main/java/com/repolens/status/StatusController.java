package com.repolens.status;

import com.repolens.config.RepoLensProperties;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class StatusController {

    private final RepoLensProperties properties;

    public StatusController(RepoLensProperties properties) {
        this.properties = properties;
    }

    @GetMapping("/health")
    public HealthResponse health() {
        return new HealthResponse("ok");
    }

    @GetMapping("/api/status")
    public StatusResponse status() {
        return new StatusResponse(
                "repolens-java",
                properties.getVersion(),
                "ok",
                new StatusResponse.StorageStatus(
                        "not_configured",
                        properties.getWorkspaceRoot(),
                        properties.getIndexRoot()
                )
        );
    }
}
