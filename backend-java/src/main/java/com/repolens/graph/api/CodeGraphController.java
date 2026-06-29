package com.repolens.graph.api;

import com.repolens.graph.api.dto.CodeGraphNeighborsResponse;
import com.repolens.graph.api.dto.CodeGraphSummaryResponse;
import com.repolens.graph.api.dto.CodeSymbolResponse;
import com.repolens.graph.application.CodeGraphService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/repositories/{repositoryId}")
public class CodeGraphController {

    private final CodeGraphService codeGraphService;

    public CodeGraphController(CodeGraphService codeGraphService) {
        this.codeGraphService = codeGraphService;
    }

    @GetMapping("/graph/summary")
    public CodeGraphSummaryResponse summary(@PathVariable String repositoryId) {
        return codeGraphService.summary(repositoryId);
    }

    @GetMapping("/symbols")
    public List<CodeSymbolResponse> searchSymbols(
            @PathVariable String repositoryId,
            @RequestParam(required = false) String query
    ) {
        return codeGraphService.searchSymbols(repositoryId, query);
    }

    @GetMapping("/symbols/{symbolId}/neighbors")
    public CodeGraphNeighborsResponse neighbors(
            @PathVariable String repositoryId,
            @PathVariable String symbolId
    ) {
        return codeGraphService.neighbors(repositoryId, symbolId);
    }
}
