package com.repolens.change.application;

import com.fasterxml.jackson.databind.JsonNode;
import com.repolens.config.RepoLensProperties;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.Map;

@Component
public class GitHubChangeRequestProvider extends AbstractPlatformChangeRequestProvider {

    public GitHubChangeRequestProvider(
            RepoLensProperties properties,
            HttpChangeRequestClient client,
            SensitiveTextRedactor redactor
    ) {
        super(properties, client, redactor);
    }

    @Override
    public boolean supports(ChangeRequestRef ref) {
        return "github".equals(ref.platform());
    }

    @Override
    public FetchedChangeRequest fetch(ChangeRequestRef ref) {
        RepoLensProperties.Provider provider = properties.getChangeRequest().getGithub();
        String base = "/repos/" + ref.owner() + "/" + ref.repo() + "/pulls/" + ref.number();
        JsonNode pr = client.getJson(provider, base, List.of());
        JsonNode files = client.getJson(provider, base + "/files", List.of("per_page", "100"));
        JsonNode commits = client.getJson(provider, base + "/commits", List.of("per_page", "100"));
        String diff = client.getText(provider, base, List.of(), "application/vnd.github.v3.diff");

        return new FetchedChangeRequest(
                ref,
                text(pr, "title"),
                text(pr.path("user"), "login"),
                text(pr.path("head"), "ref"),
                text(pr.path("base"), "ref"),
                text(pr, "state"),
                commits.isArray() ? commits.size() : 0,
                filesFromGitHub(files),
                limitDiff(diff),
                Map.of("html_url", text(pr, "html_url"), "provider", "github"),
                List.of()
        );
    }
}
