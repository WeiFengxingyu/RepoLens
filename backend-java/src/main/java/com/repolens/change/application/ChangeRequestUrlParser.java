package com.repolens.change.application;

import org.springframework.stereotype.Component;

import java.net.URI;
import java.util.Arrays;
import java.util.List;

@Component
public class ChangeRequestUrlParser {

    public ChangeRequestRef parse(String rawUrl) {
        URI uri = URI.create(rawUrl.trim());
        if (!"https".equalsIgnoreCase(uri.getScheme()) && !"http".equalsIgnoreCase(uri.getScheme()) && !"fixture".equalsIgnoreCase(uri.getScheme())) {
            throw new IllegalArgumentException("Only http, https, or fixture change request URLs are supported");
        }
        if ("fixture".equalsIgnoreCase(uri.getScheme())) {
            return parseFixture(uri);
        }
        String host = uri.getHost() == null ? "" : uri.getHost().toLowerCase();
        List<String> segments = Arrays.stream(uri.getPath().split("/"))
                .filter(segment -> !segment.isBlank())
                .toList();
        if (host.equals("github.com")) {
            return parseGitHub(rawUrl, segments);
        }
        if (host.equals("gitee.com")) {
            return parseGitee(rawUrl, segments);
        }
        if (segments.contains("-") && segments.contains("merge_requests")) {
            return parseGitLab(rawUrl, host, segments);
        }
        throw new IllegalArgumentException("Unsupported change request URL");
    }

    private ChangeRequestRef parseFixture(URI uri) {
        String host = uri.getHost();
        List<String> segments = Arrays.stream(uri.getPath().split("/"))
                .filter(segment -> !segment.isBlank())
                .toList();
        if (host == null || segments.size() < 2) {
            throw new IllegalArgumentException("Fixture URL must look like fixture://github/owner/repo/1");
        }
        String platform = host.toLowerCase();
        String owner = segments.size() == 2 ? "fixture" : segments.get(0);
        String repo = segments.size() == 2 ? segments.get(0) : segments.get(1);
        String number = segments.size() == 2 ? segments.get(1) : segments.get(2);
        String type = platform.equals("gitlab") ? "merge_request" : "pull_request";
        return new ChangeRequestRef("fixture-" + platform, type, owner, repo, number, uri.toString());
    }

    private ChangeRequestRef parseGitHub(String url, List<String> segments) {
        if (segments.size() < 4 || !"pull".equals(segments.get(2))) {
            throw new IllegalArgumentException("GitHub PR URL must look like https://github.com/{owner}/{repo}/pull/{number}");
        }
        return new ChangeRequestRef("github", "pull_request", segments.get(0), segments.get(1), segments.get(3), url);
    }

    private ChangeRequestRef parseGitee(String url, List<String> segments) {
        if (segments.size() < 4 || !"pulls".equals(segments.get(2))) {
            throw new IllegalArgumentException("Gitee PR URL must look like https://gitee.com/{owner}/{repo}/pulls/{number}");
        }
        return new ChangeRequestRef("gitee", "pull_request", segments.get(0), segments.get(1), segments.get(3), url);
    }

    private ChangeRequestRef parseGitLab(String url, String host, List<String> segments) {
        int marker = segments.indexOf("-");
        int mr = segments.indexOf("merge_requests");
        if (marker < 1 || mr != marker + 1 || segments.size() <= mr + 1) {
            throw new IllegalArgumentException("GitLab MR URL must look like https://gitlab.example.com/group/project/-/merge_requests/{iid}");
        }
        String owner = String.join("/", segments.subList(0, marker - 1));
        String repo = segments.get(marker - 1);
        if (owner.isBlank()) {
            owner = host;
        }
        return new ChangeRequestRef("gitlab", "merge_request", owner, repo, segments.get(mr + 1), url);
    }
}
