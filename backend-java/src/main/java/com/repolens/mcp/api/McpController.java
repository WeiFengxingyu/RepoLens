package com.repolens.mcp.api;

import com.repolens.mcp.api.dto.McpToolCallAuditResponse;
import com.repolens.mcp.api.dto.McpToolCallRequest;
import com.repolens.mcp.api.dto.McpToolCallResponse;
import com.repolens.mcp.api.dto.McpToolInfoResponse;
import com.repolens.mcp.application.McpToolService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/mcp")
public class McpController {

    private final McpToolService mcpToolService;

    public McpController(McpToolService mcpToolService) {
        this.mcpToolService = mcpToolService;
    }

    @GetMapping("/tools")
    public List<McpToolInfoResponse> listTools() {
        return mcpToolService.listTools();
    }

    @PostMapping("/tools/call")
    public McpToolCallResponse callTool(@Valid @RequestBody McpToolCallRequest request) {
        return mcpToolService.call(request);
    }

    @GetMapping("/tool-calls")
    public List<McpToolCallAuditResponse> listToolCalls(@RequestParam(defaultValue = "50") int limit) {
        return mcpToolService.listAudits(limit);
    }
}
