package com.repolens.change.application;

import com.fasterxml.jackson.databind.JsonNode;
import com.repolens.config.RepoLensProperties;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@Component
public class GiteeChangeRequestProvider extends AbstractPlatformChangeRequestProvider {

    public GiteeChangeRequestProvider(
            RepoLensProperties properties,
            HttpChangeRequestClient client,
            SensitiveTextRedactor redactor
    ) {
        super(properties, client, redactor);
    }

    @Override
    public boolean supports(ChangeRequestRef ref) {
        return "gitee".equals(ref.platform());
    }

    @Override
    public FetchedChangeRequest fetch(ChangeRequestRef ref) {
        RepoLensProperties.Provider provider = properties.getChangeRequest().getGitee();
        String base = "/repos/" + ref.owner() + "/" + ref.repo() + "/pulls/" + ref.number();
        JsonNode pr = client.getJson(provider, base, tokenQuery(provider));
        JsonNode files = client.getJson(provider, base + "/files", tokenQuery(provider));
        JsonNode commits = client.getJson(provider, base + "/commits", tokenQuery(provider));
        String diff = diffFromFiles(files);
        return new FetchedChangeRequest(
                ref,
                text(pr, "title"),
                text(pr.path("user"), "login"),
                text(pr.path("head"), "ref"),
                text(pr.path("base"), "ref"),
                text(pr, "state"),
                commits.isArray() ? commits.size() : 0,
                filesFromGitee(files),
                limitDiff(diff),
                Map.of("html_url", text(pr, "html_url"), "provider", "gitee"),
                List.of()
        );
    }

    private List<String> tokenQuery(RepoLensProperties.Provider provider) {
        if (provider.getToken() == null || provider.getToken().isBlank()) {
            return List.of();
        }
        return List.of("access_token", provider.getToken());
    }

    private List<ChangedRemoteFile> filesFromGitee(JsonNode files) {
        List<ChangedRemoteFile> result = new ArrayList<>();
        if (!files.isArray()) {
            return result;
        }
        for (JsonNode file : files) {
            String patch = file.path("patch").asText("");
            result.add(new ChangedRemoteFile(
                    text(file, "filename"),
                    file.path("additions").isNumber() ? file.path("additions").asInt() : countAdded(patch),
                    file.path("deletions").isNumber() ? file.path("deletions").asInt() : countDeleted(patch)
            ));
        }
        return result;
    }

    private String diffFromFiles(JsonNode files) {
        StringBuilder builder = new StringBuilder();
        if (!files.isArray()) {
            return "";
        }
        for (JsonNode file : files) {
            String path = file.path("filename").asText("unknown");
            String patch = file.path("patch").asText("");
            builder.append("diff --git a/").append(path).append(" b/").append(path).append(System.lineSeparator());
            builder.append("--- a/").append(path).append(System.lineSeparator());
            builder.append("+++ b/").append(path).append(System.lineSeparator());
            builder.append(patch).append(System.lineSeparator());
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
