package com.repolens.repository.application;

import com.repolens.common.error.ResourceNotFoundException;
import com.repolens.common.id.IdGenerator;
import com.repolens.chunking.application.ChunkBuilder;
import com.repolens.chunking.application.CodeChunkDraft;
import com.repolens.chunking.domain.CodeChunkEntity;
import com.repolens.chunking.infrastructure.CodeChunkJpaRepository;
import com.repolens.indexing.lexical.LuceneIndexException;
import com.repolens.indexing.lexical.LuceneIndexService;
import com.repolens.indexing.application.RepositoryIndexingService;
import com.repolens.repository.api.dto.CreateRepositoryRequest;
import com.repolens.repository.api.dto.RepositoryDetailResponse;
import com.repolens.repository.api.dto.RepositoryStatusResponse;
import com.repolens.repository.api.dto.RepositorySummaryResponse;
import com.repolens.repository.domain.RepositoryEntity;
import com.repolens.repository.domain.RepositoryFileEntity;
import com.repolens.repository.domain.RepositorySourceType;
import com.repolens.repository.domain.RepositoryStatus;
import com.repolens.repository.infrastructure.RepositoryFileJpaRepository;
import com.repolens.repository.infrastructure.RepositoryJpaRepository;
import com.repolens.scanner.Language;
import com.repolens.scanner.ScanResult;
import com.repolens.scanner.ScannedFile;
import com.repolens.scanner.ScannerException;
import com.repolens.scanner.SkippedFile;
import com.repolens.scanner.RepositoryScanner;
import com.repolens.parser.JavaParserService;
import com.repolens.parser.ParsedFile;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.stream.Collectors;

@Service
public class RepositoryApplicationService {

    private final RepositoryJpaRepository repositoryJpaRepository;
    private final RepositoryFileJpaRepository repositoryFileJpaRepository;
    private final CodeChunkJpaRepository codeChunkJpaRepository;
    private final RepositoryPathValidator pathValidator;
    private final RepositoryScanner repositoryScanner;
    private final JavaParserService javaParserService;
    private final ChunkBuilder chunkBuilder;
    private final LuceneIndexService luceneIndexService;
    private final RepositoryIndexingService repositoryIndexingService;
    private final RepositoryMapper repositoryMapper;
    private final IdGenerator idGenerator;
    private final ObjectMapper objectMapper;
    private final Clock clock;

    public RepositoryApplicationService(
            RepositoryJpaRepository repositoryJpaRepository,
            RepositoryFileJpaRepository repositoryFileJpaRepository,
            CodeChunkJpaRepository codeChunkJpaRepository,
            RepositoryPathValidator pathValidator,
            RepositoryScanner repositoryScanner,
            JavaParserService javaParserService,
            ChunkBuilder chunkBuilder,
            LuceneIndexService luceneIndexService,
            RepositoryIndexingService repositoryIndexingService,
            RepositoryMapper repositoryMapper,
            IdGenerator idGenerator,
            ObjectMapper objectMapper,
            Clock clock
    ) {
        this.repositoryJpaRepository = repositoryJpaRepository;
        this.repositoryFileJpaRepository = repositoryFileJpaRepository;
        this.codeChunkJpaRepository = codeChunkJpaRepository;
        this.pathValidator = pathValidator;
        this.repositoryScanner = repositoryScanner;
        this.javaParserService = javaParserService;
        this.chunkBuilder = chunkBuilder;
        this.luceneIndexService = luceneIndexService;
        this.repositoryIndexingService = repositoryIndexingService;
        this.repositoryMapper = repositoryMapper;
        this.idGenerator = idGenerator;
        this.objectMapper = objectMapper;
        this.clock = clock;
    }

    @Transactional
    public RepositoryDetailResponse importRepository(CreateRepositoryRequest request) {
        RepositoryImportCommand command = toCommand(request);
        Instant now = Instant.now(clock);
        RepositoryEntity repository = new RepositoryEntity(
                idGenerator.newId("repo"),
                command.name(),
                command.sourceType(),
                RepositoryStatus.CREATED,
                now
        );
        repository.setLocalPath(command.localPath().toString());
        repository.setBranchName(command.branch());
        repository.setLanguageSummary("{}");

        RepositoryEntity saved = repositoryJpaRepository.saveAndFlush(repository);
        repositoryIndexingService.startIndex(saved.getId());
        return repositoryMapper.toDetail(saved);
    }

    @Transactional(readOnly = true)
    public List<RepositorySummaryResponse> listRepositories() {
        return repositoryJpaRepository.findAllByOrderByCreatedAtDesc()
                .stream()
                .map(repositoryMapper::toSummary)
                .toList();
    }

    @Transactional(readOnly = true)
    public RepositoryDetailResponse getRepository(String repositoryId) {
        return repositoryMapper.toDetail(findRepository(repositoryId));
    }

    @Transactional(readOnly = true)
    public RepositoryStatusResponse getStatus(String repositoryId) {
        return repositoryMapper.toStatus(findRepository(repositoryId));
    }

    private RepositoryEntity findRepository(String repositoryId) {
        return repositoryJpaRepository.findById(repositoryId)
                .orElseThrow(() -> new ResourceNotFoundException("Repository not found"));
    }

    private void scanRepository(RepositoryEntity repository) {
        Instant scanStartedAt = Instant.now(clock);
        repository.setStatus(RepositoryStatus.SCANNING);
        repository.setUpdatedAt(scanStartedAt);
        repositoryJpaRepository.flush();

        repositoryFileJpaRepository.deleteByRepositoryId(repository.getId());
        codeChunkJpaRepository.deleteByRepositoryId(repository.getId());
        ScanResult scanResult = repositoryScanner.scan(Path.of(repository.getLocalPath()));
        Instant now = Instant.now(clock);

        List<RepositoryFileEntity> fileEntities = scanResult.files().stream()
                .map(scannedFile -> toRepositoryFile(repository.getId(), scannedFile, now))
                .collect(Collectors.toCollection(java.util.ArrayList::new));
        scanResult.skippedFiles().stream()
                .map(skippedFile -> toSkippedRepositoryFile(repository.getId(), skippedFile, now))
                .forEach(fileEntities::add);
        fileEntities.sort(Comparator.comparing(RepositoryFileEntity::getRelativePath));
        repositoryFileJpaRepository.saveAll(fileEntities);

        repository.setStatus(RepositoryStatus.PARSING);
        repository.setUpdatedAt(Instant.now(clock));
        repositoryJpaRepository.flush();

        List<ParsedFile> parsedFiles = parseFiles(repository, scanResult);
        int parsedFileCount = (int) parsedFiles.stream()
                .filter(parsedFile -> parsedFile.language() == Language.JAVA)
                .filter(parsedFile -> parsedFile.errors().isEmpty())
                .count();

        repository.setStatus(RepositoryStatus.CHUNKING);
        repository.setUpdatedAt(Instant.now(clock));
        repositoryJpaRepository.flush();

        List<CodeChunkEntity> chunkEntities = buildChunkEntities(repository, fileEntities, parsedFiles, Instant.now(clock));
        codeChunkJpaRepository.saveAll(chunkEntities);

        repository.setStatus(RepositoryStatus.INDEXING);
        repository.setUpdatedAt(Instant.now(clock));
        repositoryJpaRepository.flush();

        luceneIndexService.rebuildIndex(repository.getId(), chunkEntities);
        Instant indexedAt = Instant.now(clock);

        repository.setStatus(RepositoryStatus.READY);
        repository.setFileCount(scanResult.fileCount());
        repository.setParsedFileCount(parsedFileCount);
        repository.setChunkCount(chunkEntities.size());
        repository.setSkippedFileCount(scanResult.skippedFileCount());
        repository.setLanguageSummary(toLanguageSummaryJson(scanResult.languageSummary()));
        repository.setLastError(null);
        repository.setUpdatedAt(indexedAt);
        repository.setIndexedAt(indexedAt);
    }

    private List<ParsedFile> parseFiles(RepositoryEntity repository, ScanResult scanResult) {
        Path root = Path.of(repository.getLocalPath());
        return scanResult.files().stream()
                .filter(scannedFile -> scannedFile.language() == Language.JAVA
                        || scannedFile.language() == Language.XML
                        || scannedFile.language() == Language.YAML
                        || scannedFile.language() == Language.JSON
                        || scannedFile.language() == Language.PROPERTIES
                        || scannedFile.language() == Language.SQL
                        || scannedFile.language() == Language.MARKDOWN
                        || scannedFile.language() == Language.TEXT
                        || scannedFile.language() == Language.UNKNOWN)
                .map(scannedFile -> {
                    if (scannedFile.language() == Language.JAVA) {
                        return javaParserService.parse(root.resolve(scannedFile.relativePath()), scannedFile.relativePath());
                    }
                    return parseWholeFile(root.resolve(scannedFile.relativePath()), scannedFile);
                })
                .toList();
    }

    private ParsedFile parseWholeFile(Path path, ScannedFile scannedFile) {
        try {
            String content = java.nio.file.Files.readString(path);
            int lineCount = Math.max(1, content.split("\\R", -1).length);
            return new ParsedFile(
                    scannedFile.relativePath(),
                    scannedFile.language(),
                    content,
                    lineCount,
                    "",
                    List.of(),
                    List.of(),
                    List.of()
            );
        } catch (java.io.IOException exception) {
            return new ParsedFile(
                    scannedFile.relativePath(),
                    scannedFile.language(),
                    "",
                    1,
                    "",
                    List.of(),
                    List.of(),
                    List.of(new com.repolens.parser.ParseError("Unable to read file for chunking", 0, 0))
            );
        }
    }

    private List<CodeChunkEntity> buildChunkEntities(
            RepositoryEntity repository,
            List<RepositoryFileEntity> fileEntities,
            List<ParsedFile> parsedFiles,
            Instant now
    ) {
        Map<String, RepositoryFileEntity> fileByPath = fileEntities.stream()
                .filter(file -> !file.isSkipped())
                .collect(Collectors.toMap(RepositoryFileEntity::getRelativePath, file -> file));
        List<CodeChunkEntity> chunkEntities = new java.util.ArrayList<>();
        for (ParsedFile parsedFile : parsedFiles) {
            RepositoryFileEntity file = fileByPath.get(parsedFile.relativePath());
            if (file == null) {
                continue;
            }
            for (CodeChunkDraft draft : chunkBuilder.buildChunks(parsedFile)) {
                CodeChunkEntity chunk = new CodeChunkEntity(
                        idGenerator.newId("chunk"),
                        repository.getId(),
                        file.getId(),
                        draft.filePath(),
                        draft.language(),
                        draft.chunkType(),
                        draft.startLine(),
                        draft.endLine(),
                        draft.content(),
                        now
                );
                chunk.setSymbolName(draft.symbolName());
                chunk.setContentHash(draft.contentHash());
                chunk.setTokenEstimate(draft.tokenEstimate());
                chunk.setMetadata(toMetadataJson(draft.metadata()));
                chunkEntities.add(chunk);
            }
        }
        return chunkEntities;
    }

    private String toMetadataJson(Map<String, Object> metadata) {
        try {
            return objectMapper.writeValueAsString(metadata);
        } catch (JsonProcessingException exception) {
            throw new IllegalStateException("Failed to serialize chunk metadata", exception);
        }
    }

    private RepositoryFileEntity toRepositoryFile(String repositoryId, ScannedFile scannedFile, Instant now) {
        RepositoryFileEntity file = new RepositoryFileEntity(
                idGenerator.newId("file"),
                repositoryId,
                scannedFile.relativePath(),
                scannedFile.language().name(),
                scannedFile.sizeBytes(),
                now
        );
        file.setContentHash(scannedFile.contentHash());
        return file;
    }

    private RepositoryFileEntity toSkippedRepositoryFile(String repositoryId, SkippedFile skippedFile, Instant now) {
        RepositoryFileEntity file = new RepositoryFileEntity(
                idGenerator.newId("file"),
                repositoryId,
                skippedFile.relativePath(),
                Language.UNKNOWN.name(),
                0,
                now
        );
        file.setSkipped(true);
        file.setSkipReason(skippedFile.reason().name());
        return file;
    }

    private String toLanguageSummaryJson(Map<Language, Integer> languageSummary) {
        Map<String, Integer> response = languageSummary.entrySet().stream()
                .sorted(Map.Entry.comparingByKey())
                .collect(Collectors.toMap(
                        entry -> entry.getKey().name(),
                        Map.Entry::getValue,
                        (left, right) -> left,
                        java.util.LinkedHashMap::new
                ));
        try {
            return objectMapper.writeValueAsString(response);
        } catch (JsonProcessingException exception) {
            throw new IllegalStateException("Failed to serialize language summary", exception);
        }
    }

    private RepositoryImportCommand toCommand(CreateRepositoryRequest request) {
        String sourceTypeValue = firstNonBlank(request.getSourceType(), "LOCAL");
        RepositorySourceType sourceType = parseSourceType(sourceTypeValue);
        if (sourceType != RepositorySourceType.LOCAL) {
            throw new IllegalArgumentException("Only local repository import is supported in V0");
        }

        String rawPath = firstNonBlank(request.getLocalPath(), request.getSource());
        if (looksLikeRemoteSource(rawPath)) {
            throw new IllegalArgumentException("Only local repository import is supported in V0");
        }

        Path localPath = pathValidator.validateLocalRepositoryPath(rawPath);
        String name = firstNonBlank(request.getName(), localPath.getFileName().toString());
        String branch = blankToNull(request.getBranch());
        return new RepositoryImportCommand(sourceType, localPath, name, branch);
    }

    private RepositorySourceType parseSourceType(String value) {
        try {
            return RepositorySourceType.valueOf(value.trim().toUpperCase(Locale.ROOT));
        } catch (IllegalArgumentException exception) {
            throw new IllegalArgumentException("Unsupported repository source type: " + value);
        }
    }

    private boolean looksLikeRemoteSource(String rawPath) {
        if (rawPath == null) {
            return false;
        }
        String value = rawPath.trim().toLowerCase(Locale.ROOT);
        return value.startsWith("http://")
                || value.startsWith("https://")
                || value.startsWith("git@")
                || value.endsWith(".git");
    }

    private String firstNonBlank(String primary, String fallback) {
        String value = blankToNull(primary);
        if (value != null) {
            return value;
        }
        value = blankToNull(fallback);
        if (value != null) {
            return value;
        }
        throw new IllegalArgumentException("Repository source must not be blank");
    }

    private String blankToNull(String value) {
        if (value == null || value.isBlank()) {
            return null;
        }
        return value.trim();
    }
}
