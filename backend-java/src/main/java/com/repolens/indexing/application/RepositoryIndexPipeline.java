package com.repolens.indexing.application;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.repolens.chunking.application.ChunkBuilder;
import com.repolens.chunking.application.CodeChunkDraft;
import com.repolens.chunking.domain.CodeChunkEntity;
import com.repolens.chunking.infrastructure.CodeChunkJpaRepository;
import com.repolens.common.id.IdGenerator;
import com.repolens.graph.application.CodeGraphBuildResult;
import com.repolens.graph.application.CodeGraphBuilder;
import com.repolens.indexing.domain.IndexTaskStatus;
import com.repolens.indexing.lexical.LuceneIndexService;
import com.repolens.parser.LanguageParserRegistry;
import com.repolens.parser.ParsedFile;
import com.repolens.repository.domain.RepositoryEntity;
import com.repolens.repository.domain.RepositoryFileEntity;
import com.repolens.repository.domain.RepositoryStatus;
import com.repolens.repository.infrastructure.RepositoryFileJpaRepository;
import com.repolens.repository.infrastructure.RepositoryJpaRepository;
import com.repolens.retrieval.vector.VectorIndexService;
import com.repolens.scanner.Language;
import com.repolens.scanner.ScanResult;
import com.repolens.scanner.ScannedFile;
import com.repolens.scanner.SkippedFile;
import com.repolens.scanner.RepositoryScanner;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
public class RepositoryIndexPipeline {

    private final RepositoryJpaRepository repositoryJpaRepository;
    private final RepositoryFileJpaRepository repositoryFileJpaRepository;
    private final CodeChunkJpaRepository codeChunkJpaRepository;
    private final RepositoryScanner repositoryScanner;
    private final LanguageParserRegistry languageParserRegistry;
    private final ChunkBuilder chunkBuilder;
    private final LuceneIndexService luceneIndexService;
    private final CodeGraphBuilder codeGraphBuilder;
    private final VectorIndexService vectorIndexService;
    private final IdGenerator idGenerator;
    private final ObjectMapper objectMapper;
    private final Clock clock;

    public RepositoryIndexPipeline(
            RepositoryJpaRepository repositoryJpaRepository,
            RepositoryFileJpaRepository repositoryFileJpaRepository,
            CodeChunkJpaRepository codeChunkJpaRepository,
            RepositoryScanner repositoryScanner,
            LanguageParserRegistry languageParserRegistry,
            ChunkBuilder chunkBuilder,
            LuceneIndexService luceneIndexService,
            CodeGraphBuilder codeGraphBuilder,
            VectorIndexService vectorIndexService,
            IdGenerator idGenerator,
            ObjectMapper objectMapper,
            Clock clock
    ) {
        this.repositoryJpaRepository = repositoryJpaRepository;
        this.repositoryFileJpaRepository = repositoryFileJpaRepository;
        this.codeChunkJpaRepository = codeChunkJpaRepository;
        this.repositoryScanner = repositoryScanner;
        this.languageParserRegistry = languageParserRegistry;
        this.chunkBuilder = chunkBuilder;
        this.luceneIndexService = luceneIndexService;
        this.codeGraphBuilder = codeGraphBuilder;
        this.vectorIndexService = vectorIndexService;
        this.idGenerator = idGenerator;
        this.objectMapper = objectMapper;
        this.clock = clock;
    }

    @Transactional
    public RepositoryIndexResult rebuild(RepositoryEntity repository, RepositoryIndexContext context) {
        context.start(IndexTaskStatus.VALIDATING, 5);
        Path root = Path.of(repository.getLocalPath());
        context.succeed(IndexTaskStatus.VALIDATING, "Repository path validated");

        context.start(IndexTaskStatus.SCANNING, 15);
        repository.setStatus(RepositoryStatus.SCANNING);
        repository.setUpdatedAt(Instant.now(clock));
        repositoryJpaRepository.flush();

        repositoryFileJpaRepository.deleteByRepositoryId(repository.getId());
        codeChunkJpaRepository.deleteByRepositoryId(repository.getId());

        ScanResult scanResult = repositoryScanner.scan(root);
        Instant now = Instant.now(clock);
        List<RepositoryFileEntity> fileEntities = scanResult.files().stream()
                .map(scannedFile -> toRepositoryFile(repository.getId(), scannedFile, now))
                .collect(Collectors.toCollection(java.util.ArrayList::new));
        scanResult.skippedFiles().stream()
                .map(skippedFile -> toSkippedRepositoryFile(repository.getId(), skippedFile, now))
                .forEach(fileEntities::add);
        fileEntities.sort(Comparator.comparing(RepositoryFileEntity::getRelativePath));
        repositoryFileJpaRepository.saveAll(fileEntities);
        context.setCounts(scanResult.fileCount(), 0, 0, 0, 0);
        context.succeed(IndexTaskStatus.SCANNING, "Scanned " + scanResult.fileCount() + " files");

        context.start(IndexTaskStatus.PARSING, 35);
        repository.setStatus(RepositoryStatus.PARSING);
        repository.setUpdatedAt(Instant.now(clock));
        repositoryJpaRepository.flush();
        List<ParsedFile> parsedFiles = parseFiles(root, scanResult);
        int parsedFileCount = (int) parsedFiles.stream()
                .filter(parsedFile -> parsedFile.errors().isEmpty())
                .count();
        context.setCounts(scanResult.fileCount(), parsedFileCount, 0, 0, 0);
        context.succeed(IndexTaskStatus.PARSING, "Parsed " + parsedFileCount + " files");

        context.start(IndexTaskStatus.GRAPH_BUILDING, 45);
        CodeGraphBuildResult graphResult = codeGraphBuilder.rebuild(repository.getId(), parsedFiles);
        context.setCounts(scanResult.fileCount(), parsedFileCount, 0, graphResult.symbolCount(), graphResult.relationCount());
        context.succeed(IndexTaskStatus.GRAPH_BUILDING, "Built " + graphResult.relationCount() + " relations");

        context.start(IndexTaskStatus.CHUNKING, 60);
        repository.setStatus(RepositoryStatus.CHUNKING);
        repository.setUpdatedAt(Instant.now(clock));
        repositoryJpaRepository.flush();
        List<CodeChunkEntity> chunkEntities = buildChunkEntities(repository, fileEntities, parsedFiles, Instant.now(clock));
        codeChunkJpaRepository.saveAll(chunkEntities);
        context.setCounts(scanResult.fileCount(), parsedFileCount, chunkEntities.size(), graphResult.symbolCount(), graphResult.relationCount());
        context.succeed(IndexTaskStatus.CHUNKING, "Built " + chunkEntities.size() + " chunks");

        context.start(IndexTaskStatus.BM25_INDEXING, 75);
        repository.setStatus(RepositoryStatus.INDEXING);
        repository.setUpdatedAt(Instant.now(clock));
        repositoryJpaRepository.flush();
        luceneIndexService.rebuildIndex(repository.getId(), chunkEntities);
        context.succeed(IndexTaskStatus.BM25_INDEXING, "Rebuilt BM25 index");

        context.start(IndexTaskStatus.VECTOR_INDEXING, 90);
        int vectorCount = vectorIndexService.rebuild(repository.getId(), chunkEntities);
        context.succeed(IndexTaskStatus.VECTOR_INDEXING, "Indexed " + vectorCount + " vectors");

        Instant indexedAt = Instant.now(clock);
        repository.setStatus(RepositoryStatus.READY);
        repository.setFileCount(scanResult.fileCount());
        repository.setParsedFileCount(parsedFileCount);
        repository.setChunkCount(chunkEntities.size());
        repository.setRelationCount(graphResult.relationCount());
        repository.setSkippedFileCount(scanResult.skippedFileCount());
        repository.setLanguageSummary(toLanguageSummaryJson(scanResult.languageSummary()));
        repository.setLastError(null);
        repository.setUpdatedAt(indexedAt);
        repository.setIndexedAt(indexedAt);

        return new RepositoryIndexResult(
                scanResult.fileCount(),
                parsedFileCount,
                scanResult.skippedFileCount(),
                chunkEntities.size(),
                graphResult.symbolCount(),
                graphResult.relationCount(),
                vectorCount
        );
    }

    private List<ParsedFile> parseFiles(Path root, ScanResult scanResult) {
        return scanResult.files().stream()
                .filter(this::shouldParse)
                .map(scannedFile -> languageParserRegistry.parse(root.resolve(scannedFile.relativePath()), scannedFile.relativePath(), scannedFile.language()))
                .toList();
    }

    private boolean shouldParse(ScannedFile scannedFile) {
        return switch (scannedFile.language()) {
            case JAVA, PYTHON, TYPESCRIPT, JAVASCRIPT, XML, YAML, JSON, PROPERTIES, SQL, MARKDOWN, TEXT, UNKNOWN -> true;
            case KOTLIN -> false;
        };
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
}
