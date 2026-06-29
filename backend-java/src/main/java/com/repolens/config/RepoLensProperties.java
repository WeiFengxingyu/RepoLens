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
}
