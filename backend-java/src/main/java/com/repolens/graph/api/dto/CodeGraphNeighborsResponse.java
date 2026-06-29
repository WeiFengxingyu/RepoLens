package com.repolens.graph.api.dto;

import java.util.List;

public record CodeGraphNeighborsResponse(
        CodeSymbolResponse symbol,
        List<CodeRelationResponse> relations
) {
}
