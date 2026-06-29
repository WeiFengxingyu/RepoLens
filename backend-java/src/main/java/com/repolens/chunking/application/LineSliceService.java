package com.repolens.chunking.application;

import org.springframework.stereotype.Component;

import java.util.Arrays;

@Component
public class LineSliceService {

    public String slice(String content, int startLine, int endLine) {
        String[] lines = content.split("\\R", -1);
        if (lines.length == 0) {
            lines = new String[]{""};
        }
        int safeStart = Math.max(1, startLine);
        int safeEnd = Math.max(safeStart, Math.min(endLine, lines.length));
        return String.join(System.lineSeparator(), Arrays.copyOfRange(lines, safeStart - 1, safeEnd));
    }
}
