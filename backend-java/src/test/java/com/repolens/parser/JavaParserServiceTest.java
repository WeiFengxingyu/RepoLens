package com.repolens.parser;

import com.repolens.scanner.Language;
import org.junit.jupiter.api.Test;

import java.nio.file.Path;

import static org.assertj.core.api.Assertions.assertThat;

class JavaParserServiceTest {

    private final JavaParserService parser = new JavaParserService();

    @Test
    void parsesJavaClassMethodsAnnotationsAndRouteMetadata() {
        Path source = Path.of("src/test/resources/fixtures/parser/java/UserController.java");

        ParsedFile parsedFile = parser.parse(source, "src/main/java/com/repolens/demo/user/UserController.java");

        assertThat(parser.supports(Language.JAVA)).isTrue();
        assertThat(parsedFile.errors()).isEmpty();
        assertThat(parsedFile.packageName()).isEqualTo("com.repolens.demo.user");
        assertThat(parsedFile.imports())
                .contains(
                        "org.springframework.web.bind.annotation.GetMapping",
                        "org.springframework.web.bind.annotation.RestController"
                );

        ParsedSymbol controller = parsedFile.symbols().stream()
                .filter(symbol -> symbol.symbolName().equals("UserController"))
                .filter(symbol -> symbol.symbolType() == SymbolType.CLASS)
                .findFirst()
                .orElseThrow();
        assertThat(controller.qualifiedName()).isEqualTo("com.repolens.demo.user.UserController");
        assertThat(controller.annotations()).contains("RestController", "RequestMapping");
        assertThat(controller.modifiers()).contains("public");
        assertThat(controller.startLine()).isEqualTo(8);
        assertThat(controller.endLine()).isEqualTo(21);
        assertThat(controller.metadata()).containsEntry("requestMapping", "/api/users");

        ParsedSymbol constructor = parsedFile.symbols().stream()
                .filter(symbol -> symbol.symbolType() == SymbolType.CONSTRUCTOR)
                .findFirst()
                .orElseThrow();
        assertThat(constructor.parentSymbolName()).isEqualTo(controller.qualifiedName());
        assertThat(constructor.signature()).contains("UserController(UserService)");
        assertThat(constructor.metadata())
                .extracting("parameters")
                .asInstanceOf(org.assertj.core.api.InstanceOfAssertFactories.LIST)
                .contains("UserService userService");

        ParsedSymbol getUser = parsedFile.symbols().stream()
                .filter(symbol -> symbol.symbolName().equals("getUser"))
                .findFirst()
                .orElseThrow();
        assertThat(getUser.symbolType()).isEqualTo(SymbolType.METHOD);
        assertThat(getUser.parentSymbolName()).isEqualTo(controller.qualifiedName());
        assertThat(getUser.annotations()).contains("GetMapping");
        assertThat(getUser.modifiers()).contains("public");
        assertThat(getUser.signature()).contains("UserDto getUser");
        assertThat(getUser.startLine()).isEqualTo(17);
        assertThat(getUser.endLine()).isEqualTo(20);
        assertThat(getUser.metadata())
                .extracting("returnType")
                .isEqualTo("UserDto");
        assertThat(getUser.metadata())
                .extracting("route")
                .asInstanceOf(org.assertj.core.api.InstanceOfAssertFactories.MAP)
                .containsEntry("path", "/api/users/{id}")
                .containsEntry("httpMethods", java.util.List.of("GET"));
    }

    @Test
    void returnsParseErrorsForBrokenJavaFile() {
        Path source = Path.of("src/test/resources/fixtures/parser/java/BrokenJava.java");

        ParsedFile parsedFile = parser.parse(source, "BrokenJava.java");

        assertThat(parsedFile.symbols()).isEmpty();
        assertThat(parsedFile.errors()).isNotEmpty();
        assertThat(parsedFile.errors().getFirst().message()).isNotBlank();
    }
}
