package com.repolens.review.application;

import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Component
public class DiffParser {

    private static final Pattern HUNK_HEADER = Pattern.compile("^@@ -(\\d+)(?:,(\\d+))? \\+(\\d+)(?:,(\\d+))? @@.*$");

    public ParsedDiff parse(String diffText) {
        List<ChangedFile> files = new ArrayList<>();
        String oldPath = null;
        String newPath = null;
        List<DiffHunk> hunks = new ArrayList<>();
        MutableHunk currentHunk = null;

        for (String line : diffText.split("\\R")) {
            if (line.startsWith("diff --git ")) {
                if (oldPath != null || newPath != null) {
                    addFile(files, oldPath, newPath, hunks, currentHunk);
                    hunks = new ArrayList<>();
                    currentHunk = null;
                }
                oldPath = null;
                newPath = null;
                continue;
            }
            if (line.startsWith("--- ")) {
                oldPath = line.substring(4).trim();
                continue;
            }
            if (line.startsWith("+++ ")) {
                newPath = line.substring(4).trim();
                continue;
            }
            Matcher hunkMatcher = HUNK_HEADER.matcher(line);
            if (hunkMatcher.matches()) {
                if (currentHunk != null) {
                    hunks.add(currentHunk.toHunk());
                }
                currentHunk = new MutableHunk(
                        parseInt(hunkMatcher.group(1), 0),
                        parseInt(hunkMatcher.group(2), 1),
                        parseInt(hunkMatcher.group(3), 0),
                        parseInt(hunkMatcher.group(4), 1)
                );
                continue;
            }
            if (currentHunk != null && !line.startsWith("\\ No newline")) {
                currentHunk.add(line);
            }
        }
        if (oldPath != null || newPath != null) {
            addFile(files, oldPath, newPath, hunks, currentHunk);
        }
        return new ParsedDiff(List.copyOf(files));
    }

    private void addFile(List<ChangedFile> files, String oldPath, String newPath, List<DiffHunk> hunks, MutableHunk currentHunk) {
        List<DiffHunk> allHunks = new ArrayList<>(hunks);
        if (currentHunk != null) {
            allHunks.add(currentHunk.toHunk());
        }
        files.add(new ChangedFile(oldPath, newPath, List.copyOf(allHunks)));
    }

    private int parseInt(String value, int fallback) {
        if (value == null || value.isBlank()) {
            return fallback;
        }
        return Integer.parseInt(value);
    }

    private static class MutableHunk {
        private final int oldStart;
        private final int oldCount;
        private final int newStart;
        private final int newCount;
        private final List<DiffLine> lines = new ArrayList<>();
        private int oldCursor;
        private int newCursor;

        private MutableHunk(int oldStart, int oldCount, int newStart, int newCount) {
            this.oldStart = oldStart;
            this.oldCount = oldCount;
            this.newStart = newStart;
            this.newCount = newCount;
            this.oldCursor = oldStart;
            this.newCursor = newStart;
        }

        private void add(String rawLine) {
            if (rawLine.startsWith("+") && !rawLine.startsWith("+++")) {
                lines.add(new DiffLine(DiffLineType.ADDED, 0, newCursor++, rawLine.substring(1)));
            } else if (rawLine.startsWith("-") && !rawLine.startsWith("---")) {
                lines.add(new DiffLine(DiffLineType.REMOVED, oldCursor++, 0, rawLine.substring(1)));
            } else {
                String content = rawLine.startsWith(" ") ? rawLine.substring(1) : rawLine;
                lines.add(new DiffLine(DiffLineType.CONTEXT, oldCursor++, newCursor++, content));
            }
        }

        private DiffHunk toHunk() {
            return new DiffHunk(oldStart, oldCount, newStart, newCount, List.copyOf(lines));
        }
    }
}
