package com.repolens.change.application;

import com.fasterxml.jackson.databind.JsonNode;
import com.repolens.config.RepoLensProperties;

import java.util.ArrayList;
import java.util.List;

abstract class AbstractPlatformChangeRequestProvider implements ChangeRequestProvider {

    protected final RepoLensProperties properties;
    protected final HttpChangeRequestClient client;
    protected final SensitiveTextRedactor redactor;

    protected AbstractPlatformChangeRequestProvider(
            RepoLensProperties properties,
            HttpChangeRequestClient client,
            SensitiveTextRedactor redactor
    ) {
        this.properties = properties;
        this.client = client;
        this.redactor = redactor;
    }

    protected String text(JsonNode node, String field) {
        JsonNode value = node.path(field);
        if (value.isMissingNode() || value.isNull()) {
            return null;
        }
        return redactor.redact(value.asText());
    }

    protected int integer(JsonNode node, String field) {
        JsonNode value = node.path(field);
        return value.isNumber() ? value.asInt() : 0;
    }

    protected List<ChangedRemoteFile> filesFromGitHub(JsonNode files) {
        List<ChangedRemoteFile> result = new ArrayList<>();
        if (!files.isArray()) {
            return result;
        }
        for (JsonNode file : files) {
            result.add(new ChangedRemoteFile(text(file, "filename"), integer(file, "additions"), integer(file, "deletions")));
        }
        return result;
    }

    protected String limitDiff(String diff) {
        if (diff.length() > properties.getChangeRequest().getMaxDiffChars()) {
            return diff.substring(0, properties.getChangeRequest().getMaxDiffChars());
        }
        return diff;
    }
}
