package com.repolens.change.application;

import com.fasterxml.jackson.databind.JsonNode;
import com.repolens.config.RepoLensProperties;
import org.springframework.stereotype.Component;

import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@Component
public class GitLabChangeRequestProvider extends AbstractPlatformChangeRequestProvider {

    public GitLabChangeRequestProvider(
            RepoLensProperties properties,
            HttpChangeRequestClient client,
            SensitiveTextRedactor redactor
    ) {
        super(properties, client, redactor);
    }

    @Override
    public boolean supports(ChangeRequestRef ref) {
        return "gitlab".equals(ref.platform());
    }

    @Override
    public FetchedChangeRequest fetch(ChangeRequestRef ref) {
        RepoLensProperties.Provider provider = properties.getChangeRequest().getGitlab();
        String project = URLEncoder.encode(ref.owner() + "/" + ref.repo(), StandardCharsets.UTF_8);
        String base = "/projects/" + project + "/merge_requests/" + ref.number();
        JsonNode mr = client.getJson(provider, base, List.of());
        JsonNode changes = client.getJson(provider, base + "/changes", List.of());
        JsonNode commits = client.getJson(provider, base + "/commits", List.of("per_page", "100"));
        String diff = diffFromGitLabChanges(changes);
        return new FetchedChangeRequest(
                ref,
                text(mr, "title"),
                text(mr.path("author"), "username"),
                text(mr, "source_branch"),
                text(mr, "target_branch"),
                text(mr, "state"),
                commits.isArray() ? commits.size() : integer(mr, "commits_count"),
                filesFromGitLabChanges(changes),
                limitDiff(diff),
                Map.of("web_url", text(mr, "web_url"), "provider", "gitlab"),
                List.of()
        );
    }

    private List<ChangedRemoteFile> filesFromGitLabChanges(JsonNode changes) {
        List<ChangedRemoteFile> files = new ArrayList<>();
        JsonNode items = changes.path("changes");
        if (!items.isArray()) {
            return files;
        }
        for (JsonNode item : items) {
            String path = text(item, "new_path");
            String diff = item.path("diff").asText("");
            files.add(new ChangedRemoteFile(path, countAdded(diff), countDeleted(diff)));
        }
        return files;
    }

    private String diffFromGitLabChanges(JsonNode changes) {
        StringBuilder builder = new StringBuilder();
        JsonNode items = changes.path("changes");
        if (!items.isArray()) {
            return "";
        }
        for (JsonNode item : items) {
            String oldPath = item.path("old_path").asText(item.path("new_path").asText("unknown"));
            String newPath = item.path("new_path").asText(oldPath);
            builder.append("diff --git a/").append(oldPath).append(" b/").append(newPath).append(System.lineSeparator());
            builder.append("--- a/").append(oldPath).append(System.lineSeparator());
            builder.append("+++ b/").append(newPath).append(System.lineSeparator());
            builder.append(item.path("diff").asText(""));
            builder.append(System.lineSeparator());
        }
        return builder.toString();
    }

    private int countAdded(String diff) {
        return (int) diff.lines().filter(line -> line.startsWith("+") && !line.startsWith("+++")).count();
    }

    private int countDeleted(String diff) {
        return (int) diff.lines().filter(line -> line.startsWith("-") && !line.startsWith("---")).count();
    }
}
