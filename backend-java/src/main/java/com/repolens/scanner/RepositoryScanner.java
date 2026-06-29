package com.repolens.scanner;

import com.repolens.config.RepoLensProperties;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.nio.file.FileVisitResult;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.SimpleFileVisitor;
import java.nio.file.attribute.BasicFileAttributes;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.EnumMap;
import java.util.EnumSet;
import java.util.List;
import java.util.Map;

@Component
public class RepositoryScanner {

    private final RepoLensProperties properties;
    private final FileLanguageDetector languageDetector;
    private final FileSkipPolicy fileSkipPolicy;
    private final ContentHashService contentHashService;

    public RepositoryScanner(
            RepoLensProperties properties,
            FileLanguageDetector languageDetector,
            FileSkipPolicy fileSkipPolicy,
            ContentHashService contentHashService
    ) {
        this.properties = properties;
        this.languageDetector = languageDetector;
        this.fileSkipPolicy = fileSkipPolicy;
        this.contentHashService = contentHashService;
    }

    public ScanResult scan(Path rootPath) {
        Path root = rootPath.toAbsolutePath().normalize();
        if (!Files.exists(root)) {
            throw new ScannerException("Repository scan root does not exist");
        }
        if (!Files.isDirectory(root)) {
            throw new ScannerException("Repository scan root must be a directory");
        }

        List<ScannedFile> files = new ArrayList<>();
        List<SkippedFile> skippedFiles = new ArrayList<>();
        Map<Language, Integer> languageSummary = new EnumMap<>(Language.class);
        EnumSet<java.nio.file.FileVisitOption> options = properties.getScanner().isFollowSymlinks()
                ? EnumSet.of(java.nio.file.FileVisitOption.FOLLOW_LINKS)
                : EnumSet.noneOf(java.nio.file.FileVisitOption.class);

        try {
            Files.walkFileTree(root, options, Integer.MAX_VALUE, new SimpleFileVisitor<>() {
                @Override
                public FileVisitResult preVisitDirectory(Path directory, BasicFileAttributes attrs) {
                    if (directory.equals(root)) {
                        return FileVisitResult.CONTINUE;
                    }

                    SkipReason skipReason = fileSkipPolicy.directorySkipReason(directory, root);
                    if (skipReason != null) {
                        skippedFiles.add(new SkippedFile(fileSkipPolicy.relativePath(directory, root), skipReason));
                        return FileVisitResult.SKIP_SUBTREE;
                    }
                    return FileVisitResult.CONTINUE;
                }

                @Override
                public FileVisitResult visitFile(Path file, BasicFileAttributes attrs) {
                    String relativePath = fileSkipPolicy.relativePath(file, root);
                    SkipReason skipReason = fileSkipPolicy.fileSkipReason(file, root, attrs);
                    if (skipReason != null) {
                        skippedFiles.add(new SkippedFile(relativePath, skipReason));
                        return FileVisitResult.CONTINUE;
                    }

                    Language language = languageDetector.detect(file);
                    String contentHash = contentHashService.sha256(file);
                    files.add(new ScannedFile(
                            file.toAbsolutePath().normalize(),
                            relativePath,
                            language,
                            attrs.size(),
                            contentHash
                    ));
                    languageSummary.merge(language, 1, Integer::sum);
                    return FileVisitResult.CONTINUE;
                }

                @Override
                public FileVisitResult visitFileFailed(Path file, IOException exception) {
                    skippedFiles.add(new SkippedFile(fileSkipPolicy.relativePath(file, root), SkipReason.STAT_FAILED));
                    return FileVisitResult.CONTINUE;
                }
            });
        } catch (IOException exception) {
            throw new ScannerException("Failed to scan repository", exception);
        }

        files.sort(Comparator.comparing(ScannedFile::relativePath));
        skippedFiles.sort(Comparator.comparing(SkippedFile::relativePath));
        return new ScanResult(root, List.copyOf(files), List.copyOf(skippedFiles), Map.copyOf(languageSummary));
    }
}
