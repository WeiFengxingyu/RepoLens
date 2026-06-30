package com.repolens.change.application;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.repolens.config.RepoLensProperties;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.web.util.UriComponentsBuilder;

import java.time.Duration;
import java.util.List;

@Component
public class HttpChangeRequestClient {

    private final ObjectMapper objectMapper;
    private final SensitiveTextRedactor redactor;
    private final RepoLensProperties properties;

    public HttpChangeRequestClient(ObjectMapper objectMapper, SensitiveTextRedactor redactor, RepoLensProperties properties) {
        this.objectMapper = objectMapper;
        this.redactor = redactor;
        this.properties = properties;
    }

    public JsonNode getJson(RepoLensProperties.Provider provider, String path, List<String> query) {
        String body = getText(provider, path, query, MediaType.APPLICATION_JSON_VALUE);
        try {
            return objectMapper.readTree(body);
        } catch (Exception exception) {
            throw new ProviderFetchException("Provider returned invalid JSON");
        }
    }

    public String getText(RepoLensProperties.Provider provider, String path, List<String> query, String accept) {
        String uri = buildUri(provider.getBaseUrl(), path, query);
        try {
            SimpleClientHttpRequestFactory requestFactory = new SimpleClientHttpRequestFactory();
            Duration timeout = Duration.ofSeconds(properties.getChangeRequest().getTimeoutSeconds());
            requestFactory.setConnectTimeout(timeout);
            requestFactory.setReadTimeout(timeout);
            RestClient.Builder builder = RestClient.builder()
                    .requestFactory(requestFactory);
            RestClient client = builder.build();
            return client.get()
                    .uri(uri)
                    .headers(headers -> applyHeaders(headers, provider.getToken(), accept))
                    .retrieve()
                    .body(String.class);
        } catch (Exception exception) {
            throw new ProviderFetchException(redactor.redact("Provider fetch failed: " + exception.getMessage()));
        }
    }

    private void applyHeaders(HttpHeaders headers, String token, String accept) {
        headers.set(HttpHeaders.ACCEPT, accept);
        headers.set(HttpHeaders.USER_AGENT, "RepoLens-Java-V1.1");
        if (token != null && !token.isBlank()) {
            headers.setBearerAuth(token);
        }
    }

    private String buildUri(String baseUrl, String path, List<String> query) {
        UriComponentsBuilder builder = UriComponentsBuilder.fromUriString(baseUrl).path(path);
        for (int i = 0; i + 1 < query.size(); i += 2) {
            builder.queryParam(query.get(i), query.get(i + 1));
        }
        return builder.build(true).toUriString();
    }
}
