package com.repolens.parser;

import com.github.javaparser.ParseProblemException;
import com.github.javaparser.Range;
import com.github.javaparser.StaticJavaParser;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.NodeList;
import com.github.javaparser.ast.body.ClassOrInterfaceDeclaration;
import com.github.javaparser.ast.body.ConstructorDeclaration;
import com.github.javaparser.ast.body.EnumDeclaration;
import com.github.javaparser.ast.body.MethodDeclaration;
import com.github.javaparser.ast.body.RecordDeclaration;
import com.github.javaparser.ast.body.TypeDeclaration;
import com.github.javaparser.ast.expr.AnnotationExpr;
import com.github.javaparser.ast.expr.MemberValuePair;
import com.github.javaparser.ast.expr.NormalAnnotationExpr;
import com.github.javaparser.ast.expr.SingleMemberAnnotationExpr;
import com.github.javaparser.ast.ImportDeclaration;
import com.github.javaparser.ast.nodeTypes.NodeWithAnnotations;
import com.github.javaparser.ast.nodeTypes.NodeWithModifiers;
import com.github.javaparser.ast.nodeTypes.NodeWithSimpleName;
import com.github.javaparser.ast.Modifier;
import com.repolens.scanner.Language;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Optional;

@Service
public class JavaParserService implements CodeParser {

    private static final Map<String, String> HTTP_MAPPING_ANNOTATIONS = Map.of(
            "GetMapping", "GET",
            "PostMapping", "POST",
            "PutMapping", "PUT",
            "DeleteMapping", "DELETE",
            "PatchMapping", "PATCH"
    );

    @Override
    public ParsedFile parse(Path file, String relativePath) {
        String content = readContent(file);
        int lineCount = lineCount(content);
        try {
            CompilationUnit compilationUnit = StaticJavaParser.parse(content);
            String packageName = compilationUnit.getPackageDeclaration()
                    .map(declaration -> declaration.getName().asString())
                    .orElse("");
            List<String> imports = compilationUnit.getImports().stream()
                    .map(ImportDeclaration::getNameAsString)
                    .toList();
            List<ParsedSymbol> symbols = new ArrayList<>();

            for (TypeDeclaration<?> typeDeclaration : compilationUnit.getTypes()) {
                collectTypeSymbols(typeDeclaration, packageName, null, lineCount, symbols);
            }

            return new ParsedFile(
                    relativePath,
                    Language.JAVA,
                    content,
                    lineCount,
                    packageName,
                    imports,
                    List.copyOf(symbols),
                    List.of()
            );
        } catch (ParseProblemException exception) {
            return new ParsedFile(
                    relativePath,
                    Language.JAVA,
                    content,
                    lineCount,
                    "",
                    List.of(),
                    List.of(),
                    List.of(parseError(exception))
            );
        }
    }

    @Override
    public boolean supports(Language language) {
        return language == Language.JAVA;
    }

    private void collectTypeSymbols(
            TypeDeclaration<?> typeDeclaration,
            String packageName,
            String parentQualifiedName,
            int lineCount,
            List<ParsedSymbol> symbols
    ) {
        String typeName = typeDeclaration.getNameAsString();
        String qualifiedName = qualify(packageName, parentQualifiedName, typeName);
        SymbolType symbolType = typeSymbolType(typeDeclaration);
        ParsedSymbol typeSymbol = new ParsedSymbol(
                typeName,
                qualifiedName,
                symbolType,
                parentQualifiedName,
                startLine(typeDeclaration.getRange(), lineCount),
                endLine(typeDeclaration.getRange(), lineCount),
                annotationNames(typeDeclaration),
                modifierNames(typeDeclaration),
                compactDeclaration(typeDeclaration.toString()),
                typeMetadata(typeDeclaration)
        );
        symbols.add(typeSymbol);

        for (ConstructorDeclaration constructor : typeDeclaration.getConstructors()) {
            symbols.add(constructorSymbol(constructor, qualifiedName, lineCount));
        }
        for (MethodDeclaration method : typeDeclaration.getMethods()) {
            symbols.add(methodSymbol(method, qualifiedName, lineCount, typeDeclaration));
        }
        for (TypeDeclaration<?> nestedType : typeDeclaration.getMembers().stream()
                .filter(TypeDeclaration.class::isInstance)
                .map(TypeDeclaration.class::cast)
                .toList()) {
            collectTypeSymbols(nestedType, packageName, qualifiedName, lineCount, symbols);
        }
    }

    private ParsedSymbol constructorSymbol(ConstructorDeclaration constructor, String parentQualifiedName, int lineCount) {
        String signature = constructor.getDeclarationAsString(false, false, false);
        String qualifiedName = parentQualifiedName + "#" + signature;
        return new ParsedSymbol(
                constructor.getNameAsString(),
                qualifiedName,
                SymbolType.CONSTRUCTOR,
                parentQualifiedName,
                startLine(constructor.getRange(), lineCount),
                endLine(constructor.getRange(), lineCount),
                annotationNames(constructor),
                modifierNames(constructor),
                signature,
                Map.of("parameters", constructor.getParameters().stream().map(Object::toString).toList())
        );
    }

    private ParsedSymbol methodSymbol(
            MethodDeclaration method,
            String parentQualifiedName,
            int lineCount,
            TypeDeclaration<?> parentType
    ) {
        String signature = method.getDeclarationAsString(false, false, false);
        String qualifiedName = parentQualifiedName + "#" + signature;
        Map<String, Object> metadata = new LinkedHashMap<>();
        metadata.put("returnType", method.getTypeAsString());
        metadata.put("parameters", method.getParameters().stream().map(Object::toString).toList());

        routeMetadata(parentType, method).ifPresent(route -> metadata.put("route", route));

        return new ParsedSymbol(
                method.getNameAsString(),
                qualifiedName,
                SymbolType.METHOD,
                parentQualifiedName,
                startLine(method.getRange(), lineCount),
                endLine(method.getRange(), lineCount),
                annotationNames(method),
                modifierNames(method),
                signature,
                Map.copyOf(metadata)
        );
    }

    private Optional<Map<String, Object>> routeMetadata(TypeDeclaration<?> parentType, MethodDeclaration method) {
        List<String> classPaths = mappingPaths(parentType.getAnnotations(), "RequestMapping");
        List<String> methodPaths = new ArrayList<>();
        List<String> httpMethods = new ArrayList<>();

        for (AnnotationExpr annotation : method.getAnnotations()) {
            String name = annotation.getNameAsString();
            if (HTTP_MAPPING_ANNOTATIONS.containsKey(name)) {
                methodPaths.addAll(mappingPaths(List.of(annotation), name));
                httpMethods.add(HTTP_MAPPING_ANNOTATIONS.get(name));
            } else if (name.equals("RequestMapping")) {
                methodPaths.addAll(mappingPaths(List.of(annotation), name));
                httpMethods.addAll(requestMappingMethods(annotation));
            }
        }

        if (methodPaths.isEmpty() && httpMethods.isEmpty()) {
            return Optional.empty();
        }

        String classPath = classPaths.isEmpty() ? "" : classPaths.getFirst();
        String methodPath = methodPaths.isEmpty() ? "" : methodPaths.getFirst();
        String path = joinRoute(classPath, methodPath);
        Map<String, Object> route = new LinkedHashMap<>();
        route.put("path", path);
        route.put("httpMethods", httpMethods.isEmpty() ? List.of("REQUEST") : List.copyOf(httpMethods));
        route.put("classPath", classPath);
        route.put("methodPath", methodPath);
        return Optional.of(route);
    }

    private List<String> mappingPaths(List<AnnotationExpr> annotations, String annotationName) {
        return annotations.stream()
                .filter(annotation -> annotation.getNameAsString().equals(annotationName))
                .flatMap(annotation -> annotationPathValues(annotation).stream())
                .toList();
    }

    private List<String> annotationPathValues(AnnotationExpr annotation) {
        if (annotation instanceof SingleMemberAnnotationExpr singleMember) {
            return List.of(cleanAnnotationString(singleMember.getMemberValue().toString()));
        }
        if (annotation instanceof NormalAnnotationExpr normalAnnotation) {
            for (MemberValuePair pair : normalAnnotation.getPairs()) {
                String name = pair.getNameAsString();
                if (name.equals("value") || name.equals("path")) {
                    return List.of(cleanAnnotationString(pair.getValue().toString()));
                }
            }
        }
        return List.of("");
    }

    private List<String> requestMappingMethods(AnnotationExpr annotation) {
        if (!(annotation instanceof NormalAnnotationExpr normalAnnotation)) {
            return List.of("REQUEST");
        }
        for (MemberValuePair pair : normalAnnotation.getPairs()) {
            if (!pair.getNameAsString().equals("method")) {
                continue;
            }
            String value = pair.getValue().toString();
            List<String> methods = new ArrayList<>();
            for (String token : value.split(",")) {
                String normalized = token.trim().toUpperCase(Locale.ROOT);
                int dotIndex = normalized.lastIndexOf('.');
                if (dotIndex >= 0) {
                    normalized = normalized.substring(dotIndex + 1);
                }
                normalized = normalized.replace("}", "").replace(")", "").trim();
                if (!normalized.isBlank()) {
                    methods.add(normalized);
                }
            }
            return methods.isEmpty() ? List.of("REQUEST") : methods;
        }
        return List.of("REQUEST");
    }

    private Map<String, Object> typeMetadata(TypeDeclaration<?> typeDeclaration) {
        Map<String, Object> metadata = new LinkedHashMap<>();
        List<String> requestPaths = mappingPaths(typeDeclaration.getAnnotations(), "RequestMapping");
        if (!requestPaths.isEmpty()) {
            metadata.put("requestMapping", requestPaths.getFirst());
        }
        return Map.copyOf(metadata);
    }

    private String joinRoute(String classPath, String methodPath) {
        String left = cleanRoutePart(classPath);
        String right = cleanRoutePart(methodPath);
        if (left.isBlank()) {
            return right.isBlank() ? "/" : right;
        }
        if (right.isBlank()) {
            return left;
        }
        return (left + "/" + right.substring(1)).replaceAll("/{2,}", "/");
    }

    private String cleanRoutePart(String path) {
        if (path == null || path.isBlank()) {
            return "";
        }
        String value = path.trim();
        return value.startsWith("/") ? value : "/" + value;
    }

    private String cleanAnnotationString(String value) {
        String trimmed = value.trim();
        if (trimmed.startsWith("{") && trimmed.endsWith("}")) {
            trimmed = trimmed.substring(1, trimmed.length() - 1).trim();
        }
        if (trimmed.startsWith("\"") && trimmed.endsWith("\"")) {
            return trimmed.substring(1, trimmed.length() - 1);
        }
        return trimmed;
    }

    private SymbolType typeSymbolType(TypeDeclaration<?> typeDeclaration) {
        if (typeDeclaration instanceof ClassOrInterfaceDeclaration declaration) {
            return declaration.isInterface() ? SymbolType.INTERFACE : SymbolType.CLASS;
        }
        if (typeDeclaration instanceof EnumDeclaration) {
            return SymbolType.ENUM;
        }
        if (typeDeclaration instanceof RecordDeclaration) {
            return SymbolType.RECORD;
        }
        return SymbolType.CLASS;
    }

    private List<String> annotationNames(NodeWithAnnotations<?> node) {
        return node.getAnnotations().stream()
                .map(annotation -> annotation.getName().getIdentifier())
                .toList();
    }

    private List<String> modifierNames(NodeWithModifiers<?> node) {
        return node.getModifiers().stream()
                .map(Modifier::getKeyword)
                .map(keyword -> keyword.asString())
                .toList();
    }

    private int startLine(Optional<Range> range, int lineCount) {
        return range.map(value -> value.begin.line).orElse(1);
    }

    private int endLine(Optional<Range> range, int lineCount) {
        return range.map(value -> value.end.line).orElse(lineCount);
    }

    private String qualify(String packageName, String parentQualifiedName, String symbolName) {
        if (parentQualifiedName != null && !parentQualifiedName.isBlank()) {
            return parentQualifiedName + "." + symbolName;
        }
        if (packageName == null || packageName.isBlank()) {
            return symbolName;
        }
        return packageName + "." + symbolName;
    }

    private ParseError parseError(ParseProblemException exception) {
        return exception.getProblems().stream()
                .findFirst()
                .map(problem -> new ParseError(problem.getMessage(), 0, 0))
                .orElseGet(() -> new ParseError(exception.getMessage(), 0, 0));
    }

    private String compactDeclaration(String source) {
        return source.lines()
                .map(String::trim)
                .filter(line -> !line.isBlank())
                .findFirst()
                .orElse(source.trim());
    }

    private String readContent(Path file) {
        try {
            return Files.readString(file);
        } catch (IOException exception) {
            throw new IllegalArgumentException("Unable to read Java source file: " + file, exception);
        }
    }

    private int lineCount(String content) {
        if (content.isEmpty()) {
            return 1;
        }
        return content.split("\\R", -1).length;
    }
}
