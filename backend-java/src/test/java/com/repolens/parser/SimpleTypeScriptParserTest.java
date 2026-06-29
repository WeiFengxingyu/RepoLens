package com.repolens.parser;

import com.repolens.scanner.Language;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.nio.file.Files;
import java.nio.file.Path;

import static org.assertj.core.api.Assertions.assertThat;

class SimpleTypeScriptParserTest {

    private final SimpleTypeScriptParser parser = new SimpleTypeScriptParser();

    @TempDir
    private Path tempDir;

    @Test
    void extractsImportsClassesFunctionsAndMethods() throws Exception {
        Path source = tempDir.resolve("user-service.ts");
        Files.writeString(source, """
                import { http } from "./http";

                export class UserService {
                  async getUser(id: string) {
                    return http.get(id);
                  }
                }

                export function mapUser(raw: unknown) {
                  return raw;
                }

                export const createUser = async (name: string) => {
                  return { name };
                };
                """);

        ParsedFile parsedFile = parser.parse(source, "user-service.ts");

        assertThat(parser.supports(Language.TYPESCRIPT)).isTrue();
        assertThat(parsedFile.imports()).contains("import { http } from \"./http\";");
        assertThat(parsedFile.symbols())
                .extracting(ParsedSymbol::qualifiedName)
                .contains("UserService", "UserService#getUser", "mapUser", "createUser");
        assertThat(parsedFile.symbols())
                .filteredOn(symbol -> symbol.qualifiedName().equals("UserService#getUser"))
                .singleElement()
                .satisfies(symbol -> {
                    assertThat(symbol.symbolType()).isEqualTo(SymbolType.METHOD);
                    assertThat(symbol.parentSymbolName()).isEqualTo("UserService");
                });
    }
}
