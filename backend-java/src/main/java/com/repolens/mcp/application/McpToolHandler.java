package com.repolens.mcp.application;

@FunctionalInterface
public interface McpToolHandler {

    Object execute(McpToolExecutionContext context);
}
