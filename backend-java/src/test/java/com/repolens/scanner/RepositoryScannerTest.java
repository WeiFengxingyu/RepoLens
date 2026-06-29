package com.repolens.scanner;

import com.repolens.config.RepoLensProperties;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Set;

import static org.assertj.core.api.Assertions.assertThat;

class RepositoryScannerTest {

    @TempDir
    private Path tempDir;

    private RepositoryScanner repositoryScanner;

    @BeforeEach
    void setUp() {
        RepoLensProperties properties = new RepoLensProperties();
        properties.getScanner().setMaxFileSizeBytes(64);
        repositoryScanner = new RepositoryScanner(
                properties,
                new FileLanguageDetector(),
                new FileSkipPolicy(properties),
                new ContentHashService()
        );
    }

    @Test
    void scansRepositoryFilesAndFiltersUnsafeOrNoisyFiles() throws Exception {
        write("src/main/java/com/demo/UserService.java", "package demo;\nclass UserService {}\n");
        write("src/main/resources/application.yml", "server:\n  port: 8080\n");
        write("pom.xml", "<project></project>\n");
        write("README.md", "# Demo\n");
        write(".env", "TOKEN=secret\n");
        write("secret.pem", "-----BEGIN PRIVATE KEY-----\n");
        write("large.txt", "x".repeat(128));
        write("binary.dat", "hello\u0000world");
        write(".git/config", "[core]\n");
        write("target/classes/Demo.class", "compiled");
        write("node_modules/pkg/index.js", "console.log('ignored');");

        ScanResult result = repositoryScanner.scan(tempDir);

        assertThat(result.files())
                .extracting(ScannedFile::relativePath)
                .containsExactly(
                        "README.md",
                        "pom.xml",
                        "src/main/java/com/demo/UserService.java",
                        "src/main/resources/application.yml"
                );
        assertThat(result.files())
                .allSatisfy(file -> assertThat(file.contentHash()).matches("[0-9a-f]{64}"));
        assertThat(result.files())
                .filteredOn(file -> file.relativePath().equals("src/main/java/com/demo/UserService.java"))
                .singleElement()
                .satisfies(file -> assertThat(file.language()).isEqualTo(Language.JAVA));
        assertThat(result.languageSummary())
                .containsEntry(Language.JAVA, 1)
                .containsEntry(Language.YAML, 1)
                .containsEntry(Language.XML, 1)
                .containsEntry(Language.MARKDOWN, 1);

        Set<SkipReason> skipReasons = result.skippedFiles().stream()
                .map(SkippedFile::reason)
                .collect(java.util.stream.Collectors.toSet());
        assertThat(skipReasons)
                .contains(
                        SkipReason.IGNORED_DIRECTORY,
                        SkipReason.IGNORED_FILE,
                        SkipReason.FILE_TOO_LARGE,
                        SkipReason.BINARY_FILE
                );
        assertThat(result.skippedFiles())
                .extracting(SkippedFile::relativePath)
                .contains(".git", "node_modules", "target", ".env", "secret.pem", "large.txt", "binary.dat");
    }

    private void write(String relativePath, String content) throws Exception {
        Path file = tempDir.resolve(relativePath);
        Files.createDirectories(file.getParent() == null ? tempDir : file.getParent());
        Files.writeString(file, content, StandardCharsets.UTF_8);
    }
}
