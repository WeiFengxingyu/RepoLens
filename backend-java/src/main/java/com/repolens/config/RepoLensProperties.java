package com.repolens.config;

import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.validation.annotation.Validated;

@Validated
@ConfigurationProperties(prefix = "repolens")
public class RepoLensProperties {

    @NotBlank
    private String version = "v1";

    @NotBlank
    private String workspaceRoot = "./.repolens-java/repos";

    @NotBlank
    private String indexRoot = "./.repolens-java/indexes";

    @Valid
    private Scanner scanner = new Scanner();

    @Valid
    private Indexing indexing = new Indexing();

    @Valid
    private Retrieval retrieval = new Retrieval();

    @Valid
    private ChangeRequest changeRequest = new ChangeRequest();

    @Valid
    private V2Lite v2Lite = new V2Lite();

    public String getVersion() {
        return version;
    }

    public void setVersion(String version) {
        this.version = version;
    }

    public String getWorkspaceRoot() {
        return workspaceRoot;
    }

    public void setWorkspaceRoot(String workspaceRoot) {
        this.workspaceRoot = workspaceRoot;
    }

    public String getIndexRoot() {
        return indexRoot;
    }

    public void setIndexRoot(String indexRoot) {
        this.indexRoot = indexRoot;
    }

    public Scanner getScanner() {
        return scanner;
    }

    public void setScanner(Scanner scanner) {
        this.scanner = scanner;
    }

    public Indexing getIndexing() {
        return indexing;
    }

    public void setIndexing(Indexing indexing) {
        this.indexing = indexing;
    }

    public Retrieval getRetrieval() {
        return retrieval;
    }

    public void setRetrieval(Retrieval retrieval) {
        this.retrieval = retrieval;
    }

    public ChangeRequest getChangeRequest() {
        return changeRequest;
    }

    public void setChangeRequest(ChangeRequest changeRequest) {
        this.changeRequest = changeRequest;
    }

    public V2Lite getV2Lite() {
        return v2Lite;
    }

    public void setV2Lite(V2Lite v2Lite) {
        this.v2Lite = v2Lite;
    }

    public static class Scanner {
        @Min(1024)
        @Max(104_857_600)
        private long maxFileSizeBytes = 1_048_576;

        private boolean followSymlinks = false;

        public long getMaxFileSizeBytes() {
            return maxFileSizeBytes;
        }

        public void setMaxFileSizeBytes(long maxFileSizeBytes) {
            this.maxFileSizeBytes = maxFileSizeBytes;
        }

        public boolean isFollowSymlinks() {
            return followSymlinks;
        }

        public void setFollowSymlinks(boolean followSymlinks) {
            this.followSymlinks = followSymlinks;
        }
    }

    public static class Indexing {
        private boolean asyncEnabled = true;

        @Min(1)
        @Max(8)
        private int maxActiveTasksPerRepository = 1;

        public boolean isAsyncEnabled() {
            return asyncEnabled;
        }

        public void setAsyncEnabled(boolean asyncEnabled) {
            this.asyncEnabled = asyncEnabled;
        }

        public int getMaxActiveTasksPerRepository() {
            return maxActiveTasksPerRepository;
        }

        public void setMaxActiveTasksPerRepository(int maxActiveTasksPerRepository) {
            this.maxActiveTasksPerRepository = maxActiveTasksPerRepository;
        }
    }

    public static class Retrieval {
        @Min(1)
        @Max(50)
        private int defaultTopK = 10;

        private boolean vectorEnabled = true;

        private boolean graphEnabled = true;

        @Min(8)
        @Max(512)
        private int vectorDimensions = 64;

        public int getDefaultTopK() {
            return defaultTopK;
        }

        public void setDefaultTopK(int defaultTopK) {
            this.defaultTopK = defaultTopK;
        }

        public boolean isVectorEnabled() {
            return vectorEnabled;
        }

        public void setVectorEnabled(boolean vectorEnabled) {
            this.vectorEnabled = vectorEnabled;
        }

        public boolean isGraphEnabled() {
            return graphEnabled;
        }

        public void setGraphEnabled(boolean graphEnabled) {
            this.graphEnabled = graphEnabled;
        }

        public int getVectorDimensions() {
            return vectorDimensions;
        }

        public void setVectorDimensions(int vectorDimensions) {
            this.vectorDimensions = vectorDimensions;
        }
    }

    public static class ChangeRequest {
        @Min(1)
        @Max(120)
        private int timeoutSeconds = 20;

        @Min(1000)
        @Max(1_000_000)
        private int maxDiffChars = 200_000;

        @Valid
        private Provider github = new Provider("https://api.github.com");

        @Valid
        private Provider gitlab = new Provider("https://gitlab.com/api/v4");

        @Valid
        private Provider gitee = new Provider("https://gitee.com/api/v5");

        public int getTimeoutSeconds() {
            return timeoutSeconds;
        }

        public void setTimeoutSeconds(int timeoutSeconds) {
            this.timeoutSeconds = timeoutSeconds;
        }

        public int getMaxDiffChars() {
            return maxDiffChars;
        }

        public void setMaxDiffChars(int maxDiffChars) {
            this.maxDiffChars = maxDiffChars;
        }

        public Provider getGithub() {
            return github;
        }

        public void setGithub(Provider github) {
            this.github = github;
        }

        public Provider getGitlab() {
            return gitlab;
        }

        public void setGitlab(Provider gitlab) {
            this.gitlab = gitlab;
        }

        public Provider getGitee() {
            return gitee;
        }

        public void setGitee(Provider gitee) {
            this.gitee = gitee;
        }
    }

    public static class Provider {
        @NotBlank
        private String baseUrl;

        private String token = "";

        public Provider() {
        }

        public Provider(String baseUrl) {
            this.baseUrl = baseUrl;
        }

        public String getBaseUrl() {
            return baseUrl;
        }

        public void setBaseUrl(String baseUrl) {
            this.baseUrl = baseUrl;
        }

        public String getToken() {
            return token;
        }

        public void setToken(String token) {
            this.token = token;
        }
    }

    public static class V2Lite {
        private boolean enabled = true;

        @Valid
        private Worker worker = new Worker();

        @Valid
        private Concurrency concurrency = new Concurrency();

        @Valid
        private ReviewHub reviewHub = new ReviewHub();

        @Valid
        private Webhook webhook = new Webhook();

        public boolean isEnabled() {
            return enabled;
        }

        public void setEnabled(boolean enabled) {
            this.enabled = enabled;
        }

        public Worker getWorker() {
            return worker;
        }

        public void setWorker(Worker worker) {
            this.worker = worker;
        }

        public Concurrency getConcurrency() {
            return concurrency;
        }

        public void setConcurrency(Concurrency concurrency) {
            this.concurrency = concurrency;
        }

        public ReviewHub getReviewHub() {
            return reviewHub;
        }

        public void setReviewHub(ReviewHub reviewHub) {
            this.reviewHub = reviewHub;
        }

        public Webhook getWebhook() {
            return webhook;
        }

        public void setWebhook(Webhook webhook) {
            this.webhook = webhook;
        }
    }

    public static class Worker {
        private boolean localEnabled = true;

        @Min(1)
        @Max(16)
        private int poolSize = 2;

        @Min(1)
        @Max(10)
        private int maxAttempts = 3;

        @Min(0)
        @Max(3600)
        private int retryBackoffSeconds = 2;

        @Min(5)
        @Max(3600)
        private int heartbeatTimeoutSeconds = 60;

        public boolean isLocalEnabled() {
            return localEnabled;
        }

        public void setLocalEnabled(boolean localEnabled) {
            this.localEnabled = localEnabled;
        }

        public int getPoolSize() {
            return poolSize;
        }

        public void setPoolSize(int poolSize) {
            this.poolSize = poolSize;
        }

        public int getMaxAttempts() {
            return maxAttempts;
        }

        public void setMaxAttempts(int maxAttempts) {
            this.maxAttempts = maxAttempts;
        }

        public int getRetryBackoffSeconds() {
            return retryBackoffSeconds;
        }

        public void setRetryBackoffSeconds(int retryBackoffSeconds) {
            this.retryBackoffSeconds = retryBackoffSeconds;
        }

        public int getHeartbeatTimeoutSeconds() {
            return heartbeatTimeoutSeconds;
        }

        public void setHeartbeatTimeoutSeconds(int heartbeatTimeoutSeconds) {
            this.heartbeatTimeoutSeconds = heartbeatTimeoutSeconds;
        }
    }

    public static class Concurrency {
        @Min(1)
        @Max(86_400)
        private int lockTtlSeconds = 1800;

        @Min(1)
        @Max(604_800)
        private int idempotencyTtlSeconds = 86_400;

        @Min(1)
        @Max(10_000)
        private int reviewRateLimitPerMinute = 60;

        @Min(1)
        @Max(86_400)
        private int statusCacheTtlSeconds = 300;

        public int getLockTtlSeconds() {
            return lockTtlSeconds;
        }

        public void setLockTtlSeconds(int lockTtlSeconds) {
            this.lockTtlSeconds = lockTtlSeconds;
        }

        public int getIdempotencyTtlSeconds() {
            return idempotencyTtlSeconds;
        }

        public void setIdempotencyTtlSeconds(int idempotencyTtlSeconds) {
            this.idempotencyTtlSeconds = idempotencyTtlSeconds;
        }

        public int getReviewRateLimitPerMinute() {
            return reviewRateLimitPerMinute;
        }

        public void setReviewRateLimitPerMinute(int reviewRateLimitPerMinute) {
            this.reviewRateLimitPerMinute = reviewRateLimitPerMinute;
        }

        public int getStatusCacheTtlSeconds() {
            return statusCacheTtlSeconds;
        }

        public void setStatusCacheTtlSeconds(int statusCacheTtlSeconds) {
            this.statusCacheTtlSeconds = statusCacheTtlSeconds;
        }
    }

    public static class ReviewHub {
        @Min(1)
        @Max(1_000_000)
        private int defaultQuotaLimit = 1000;

        @Min(1)
        @Max(43_200)
        private int quotaWindowMinutes = 60;

        public int getDefaultQuotaLimit() {
            return defaultQuotaLimit;
        }

        public void setDefaultQuotaLimit(int defaultQuotaLimit) {
            this.defaultQuotaLimit = defaultQuotaLimit;
        }

        public int getQuotaWindowMinutes() {
            return quotaWindowMinutes;
        }

        public void setQuotaWindowMinutes(int quotaWindowMinutes) {
            this.quotaWindowMinutes = quotaWindowMinutes;
        }
    }

    public static class Webhook {
        private boolean requireSecret = false;

        public boolean isRequireSecret() {
            return requireSecret;
        }

        public void setRequireSecret(boolean requireSecret) {
            this.requireSecret = requireSecret;
        }
    }
}
