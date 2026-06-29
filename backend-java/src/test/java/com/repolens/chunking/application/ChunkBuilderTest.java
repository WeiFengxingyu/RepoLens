package com.repolens.chunking.application;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.repolens.chunking.domain.ChunkType;
import com.repolens.parser.JavaParserService;
import com.repolens.parser.ParsedFile;
import com.repolens.scanner.Language;
import org.junit.jupiter.api.Test;

import java.nio.file.Path;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

class ChunkBuilderTest {

    private final JavaParserService parser = new JavaParserService();
    private final ChunkBuilder chunkBuilder = new ChunkBuilder(
            new LineSliceService(),
            new TokenEstimateService(),
            new ObjectMapper()
    );

    @Test
    void buildsClassAndMethodChunksFromParsedJavaFile() {
        ParsedFile parsedFile = parser.parse(
                Path.of("src/test/resources/fixtures/parser/java/UserController.java"),
                "src/main/java/com/repolens/demo/user/UserController.java"
        );

        List<CodeChunkDraft> chunks = chunkBuilder.buildChunks(parsedFile);

        assertThat(chunks).anySatisfy(chunk -> {
            assertThat(chunk.chunkType()).isEqualTo(ChunkType.CLASS);
            assertThat(chunk.symbolName()).isEqualTo("com.repolens.demo.user.UserController");
            assertThat(chunk.content()).contains("// file: src/main/java/com/repolens/demo/user/UserController.java");
            assertThat(chunk.content()).contains("// annotations: RestController, RequestMapping");
            assertThat(chunk.contentHash()).matches("[0-9a-f]{64}");
            assertThat(chunk.tokenEstimate()).isPositive();
        });
        assertThat(chunks).anySatisfy(chunk -> {
            assertThat(chunk.chunkType()).isEqualTo(ChunkType.METHOD);
            assertThat(chunk.symbolName()).contains("getUser");
            assertThat(chunk.startLine()).isEqualTo(17);
            assertThat(chunk.endLine()).isEqualTo(20);
            assertThat(chunk.content()).contains("// symbol: com.repolens.demo.user.UserController#UserDto getUser(Long)");
            assertThat(chunk.content()).contains("// route: {\"path\":\"/api/users/{id}\",\"httpMethods\":[\"GET\"]");
            assertThat(chunk.content()).contains("@GetMapping(\"/{id}\")");
            assertThat(chunk.content()).contains("return userService.getUser(id);");
            assertThat(chunk.metadata()).containsKey("route");
        });
    }

    @Test
    void buildsFileFallbackChunkForBrokenJavaFile() {
        ParsedFile parsedFile = parser.parse(
                Path.of("src/test/resources/fixtures/parser/java/BrokenJava.java"),
                "BrokenJava.java"
        );

        List<CodeChunkDraft> chunks = chunkBuilder.buildChunks(parsedFile);

        assertThat(chunks).singleElement().satisfies(chunk -> {
            assertThat(chunk.chunkType()).isEqualTo(ChunkType.FILE);
            assertThat(chunk.symbolName()).isEqualTo("BrokenJava.java");
            assertThat(chunk.metadata()).containsEntry("fallback", true);
            assertThat(chunk.content()).contains("// file: BrokenJava.java");
        });
    }

    @Test
    void buildsConfigChunkAndStableHashForYamlFile() {
        ParsedFile parsedFile = new ParsedFile(
                "src/main/resources/application.yml",
                Language.YAML,
                "server:\n  port: 8080\n",
                3,
                "",
                List.of(),
                List.of(),
                List.of()
        );

        List<CodeChunkDraft> first = chunkBuilder.buildChunks(parsedFile);
        List<CodeChunkDraft> second = chunkBuilder.buildChunks(parsedFile);

        assertThat(first).singleElement().satisfies(chunk -> {
            assertThat(chunk.chunkType()).isEqualTo(ChunkType.CONFIG);
            assertThat(chunk.content()).contains("server:");
            assertThat(chunk.contentHash()).isEqualTo(second.getFirst().contentHash());
        });
    }
}
