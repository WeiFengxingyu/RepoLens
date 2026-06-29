package com.repolens.mcp.application;

public class McpPermissionException extends RuntimeException {

    private final String decision;

    public McpPermissionException(String decision, String message) {
        super(message);
        this.decision = decision;
    }

    public String getDecision() {
        return decision;
    }
}
