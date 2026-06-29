package com.repolens.parser;

import com.repolens.scanner.Language;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.nio.file.Files;
import java.nio.file.Path;

import static org.assertj.core.api.Assertions.assertThat;

class SimplePythonParserTest {

    private final SimplePythonParser parser = new SimplePythonParser();

    @TempDir
    private Path tempDir;

    @Test
    void extractsImportsClassesFunctionsAndDecorators() throws Exception {
        Path source = tempDir.resolve("service.py");
        Files.writeString(source, """
                import os
                from app.auth import require_user

                class UserService:
                    @require_user
                    def get_user(self, user_id: str):
                        return user_id

                async def load_users():
                    return []
                """);

        ParsedFile parsedFile = parser.parse(source, "service.py");

        assertThat(parser.supports(Language.PYTHON)).isTrue();
        assertThat(parsedFile.imports()).contains("import os", "from app.auth import require_user");
        assertThat(parsedFile.symbols())
                .extracting(ParsedSymbol::qualifiedName)
                .contains("UserService", "UserService.get_user", "load_users");
        assertThat(parsedFile.symbols())
                .filteredOn(symbol -> symbol.symbolName().equals("get_user"))
                .singleElement()
                .satisfies(symbol -> {
                    assertThat(symbol.symbolType()).isEqualTo(SymbolType.FUNCTION);
                    assertThat(symbol.parentSymbolName()).isEqualTo("UserService");
                    assertThat(symbol.annotations()).contains("require_user");
                });
    }
}
