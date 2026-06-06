from __future__ import annotations

import ast
from dataclasses import dataclass, field
import hashlib
import re
from pathlib import Path
from typing import Any

from app.models import CodeLanguage, RelationType, SymbolType


@dataclass(frozen=True)
class ParsedSymbol:
    symbol_id: str
    name: str
    qualified_name: str
    symbol_type: str
    start_line: int
    end_line: int
    parent_symbol: str | None = None


@dataclass(frozen=True)
class ParsedRelation:
    relation_type: str
    source_symbol: str | None
    target_symbol: str | None
    source_file: str
    target_file: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ParsedFile:
    file_path: str
    language: str
    content: str
    line_count: int
    symbols: list[ParsedSymbol] = field(default_factory=list)
    relations: list[ParsedRelation] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class ParserError(ValueError):
    pass


def parse_source_file(path: Path, relative_path: str, language: str) -> ParsedFile:
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise ParserError(f"Unable to read source file: {relative_path}") from exc

    if language == CodeLanguage.PYTHON.value:
        return parse_python_source(content, relative_path)
    if language in {CodeLanguage.TYPESCRIPT.value, CodeLanguage.JAVASCRIPT.value}:
        return parse_typescript_javascript_source(content, relative_path, language)
    return _base_parsed_file(content, relative_path, language)


def parse_python_source(content: str, file_path: str) -> ParsedFile:
    parsed_file = _base_parsed_file(content, file_path, CodeLanguage.PYTHON.value)
    try:
        tree = ast.parse(content)
    except SyntaxError as exc:
        return ParsedFile(
            file_path=parsed_file.file_path,
            language=parsed_file.language,
            content=parsed_file.content,
            line_count=parsed_file.line_count,
            symbols=parsed_file.symbols,
            relations=parsed_file.relations,
            errors=[f"SyntaxError:{exc.lineno}:{exc.msg}"],
        )

    symbols = list(parsed_file.symbols)
    relations = list(parsed_file.relations)
    file_symbol = parsed_file.file_path

    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            relations.extend(_python_import_relations(node, file_symbol, parsed_file.file_path))
        elif isinstance(node, ast.ClassDef):
            class_symbol = _python_class_symbol(node, parsed_file.file_path)
            symbols.append(class_symbol)
            relations.append(
                _contains_relation(file_symbol, class_symbol.qualified_name, parsed_file.file_path)
            )
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    method_symbol = _python_function_symbol(
                        child,
                        parsed_file.file_path,
                        parent_symbol=class_symbol.qualified_name,
                        symbol_type=SymbolType.METHOD.value,
                    )
                    symbols.append(method_symbol)
                    relations.append(
                        _contains_relation(
                            class_symbol.qualified_name,
                            method_symbol.qualified_name,
                            parsed_file.file_path,
                        )
                    )
                    relations.extend(_python_call_relations(child, method_symbol.qualified_name, file_path))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            function_symbol = _python_function_symbol(
                node,
                parsed_file.file_path,
                parent_symbol=file_symbol,
                symbol_type=SymbolType.FUNCTION.value,
            )
            symbols.append(function_symbol)
            relations.append(_contains_relation(file_symbol, function_symbol.qualified_name, file_path))
            relations.extend(_python_call_relations(node, function_symbol.qualified_name, file_path))

    return ParsedFile(
        file_path=parsed_file.file_path,
        language=parsed_file.language,
        content=parsed_file.content,
        line_count=parsed_file.line_count,
        symbols=symbols,
        relations=relations,
        errors=[],
    )


def parse_typescript_javascript_source(content: str, file_path: str, language: str) -> ParsedFile:
    parsed_file = _base_parsed_file(content, file_path, language)
    symbols = list(parsed_file.symbols)
    relations = list(parsed_file.relations)
    lines = content.splitlines()
    file_symbol = parsed_file.file_path
    class_ranges: list[tuple[int, int]] = []

    for line_number, line in enumerate(lines, start=1):
        import_target = _js_import_target(line)
        if import_target:
            relations.append(
                ParsedRelation(
                    relation_type=RelationType.IMPORTS.value,
                    source_symbol=file_symbol,
                    target_symbol=import_target,
                    source_file=file_path,
                    metadata={"line": line_number},
                )
            )

    for line_number, line in enumerate(lines, start=1):
        class_name = _js_class_name(line)
        if not class_name:
            continue
        end_line = _find_braced_block_end(lines, line_number)
        class_ranges.append((line_number, end_line))
        class_symbol = _symbol(
            name=class_name,
            qualified_name=class_name,
            symbol_type=SymbolType.CLASS.value,
            file_path=file_path,
            start_line=line_number,
            end_line=end_line,
            parent_symbol=file_symbol,
        )
        symbols.append(class_symbol)
        relations.append(_contains_relation(file_symbol, class_symbol.qualified_name, file_path))
        symbols.extend(_js_method_symbols(lines, file_path, class_symbol))
        for method in [symbol for symbol in symbols if symbol.parent_symbol == class_symbol.qualified_name]:
            relations.append(_contains_relation(class_symbol.qualified_name, method.qualified_name, file_path))

    for line_number, line in enumerate(lines, start=1):
        if _line_in_ranges(line_number, class_ranges):
            continue
        function_name = _js_function_name(line) or _js_arrow_function_name(line)
        if not function_name:
            continue
        end_line = _find_braced_block_end(lines, line_number)
        function_symbol = _symbol(
            name=function_name,
            qualified_name=function_name,
            symbol_type=SymbolType.FUNCTION.value,
            file_path=file_path,
            start_line=line_number,
            end_line=end_line,
            parent_symbol=file_symbol,
        )
        symbols.append(function_symbol)
        relations.append(_contains_relation(file_symbol, function_symbol.qualified_name, file_path))

    return ParsedFile(
        file_path=parsed_file.file_path,
        language=parsed_file.language,
        content=parsed_file.content,
        line_count=parsed_file.line_count,
        symbols=symbols,
        relations=relations,
        errors=[],
    )


def _base_parsed_file(content: str, file_path: str, language: str) -> ParsedFile:
    line_count = max(1, len(content.splitlines()))
    file_symbol = _symbol(
        name=file_path,
        qualified_name=file_path,
        symbol_type=SymbolType.FILE.value,
        file_path=file_path,
        start_line=1,
        end_line=line_count,
        parent_symbol=None,
    )
    return ParsedFile(
        file_path=file_path,
        language=language,
        content=content,
        line_count=line_count,
        symbols=[file_symbol],
    )


def _python_class_symbol(node: ast.ClassDef, file_path: str) -> ParsedSymbol:
    return _symbol(
        name=node.name,
        qualified_name=node.name,
        symbol_type=SymbolType.CLASS.value,
        file_path=file_path,
        start_line=node.lineno,
        end_line=getattr(node, "end_lineno", node.lineno),
        parent_symbol=file_path,
    )


def _python_function_symbol(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    file_path: str,
    parent_symbol: str,
    symbol_type: str,
) -> ParsedSymbol:
    qualified_name = node.name if parent_symbol == file_path else f"{parent_symbol}.{node.name}"
    return _symbol(
        name=node.name,
        qualified_name=qualified_name,
        symbol_type=symbol_type,
        file_path=file_path,
        start_line=node.lineno,
        end_line=getattr(node, "end_lineno", node.lineno),
        parent_symbol=parent_symbol,
    )


def _python_import_relations(
    node: ast.Import | ast.ImportFrom,
    source_symbol: str,
    source_file: str,
) -> list[ParsedRelation]:
    if isinstance(node, ast.Import):
        return [
            ParsedRelation(
                relation_type=RelationType.IMPORTS.value,
                source_symbol=source_symbol,
                target_symbol=alias.name,
                source_file=source_file,
                metadata={"line": node.lineno},
            )
            for alias in node.names
        ]

    module = node.module or ""
    return [
        ParsedRelation(
            relation_type=RelationType.IMPORTS.value,
            source_symbol=source_symbol,
            target_symbol=f"{module}.{alias.name}" if module else alias.name,
            source_file=source_file,
            metadata={"line": node.lineno, "level": node.level},
        )
        for alias in node.names
    ]


def _python_call_relations(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    source_symbol: str,
    source_file: str,
) -> list[ParsedRelation]:
    relations: list[ParsedRelation] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            target = _python_call_name(child.func)
            if target:
                relations.append(
                    ParsedRelation(
                        relation_type=RelationType.CALLS.value,
                        source_symbol=source_symbol,
                        target_symbol=target,
                        source_file=source_file,
                        metadata={"line": child.lineno},
                    )
                )
    return relations


def _python_call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _python_call_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return None


def _js_import_target(line: str) -> str | None:
    match = re.match(r"^\s*import\s+(?:.+?\s+from\s+)?[\"']([^\"']+)[\"']", line)
    return match.group(1) if match else None


def _js_class_name(line: str) -> str | None:
    match = re.match(r"^\s*(?:export\s+default\s+|export\s+)?class\s+([A-Za-z_$][\w$]*)", line)
    return match.group(1) if match else None


def _js_function_name(line: str) -> str | None:
    match = re.match(
        r"^\s*(?:export\s+default\s+|export\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)",
        line,
    )
    return match.group(1) if match else None


def _js_arrow_function_name(line: str) -> str | None:
    match = re.match(
        r"^\s*(?:export\s+)?(?:const|let)\s+([A-Za-z_$][\w$]*)\s*=\s*"
        r"(?:async\s*)?(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>",
        line,
    )
    return match.group(1) if match else None


def _js_method_symbols(
    lines: list[str],
    file_path: str,
    class_symbol: ParsedSymbol,
) -> list[ParsedSymbol]:
    symbols: list[ParsedSymbol] = []
    for line_number in range(class_symbol.start_line + 1, class_symbol.end_line):
        line = lines[line_number - 1]
        match = re.match(
            r"^\s*(?:public\s+|private\s+|protected\s+)?(?:static\s+)?(?:async\s+)?"
            r"([A-Za-z_$][\w$]*)\s*\([^)]*\)\s*\{",
            line,
        )
        if not match:
            continue
        method_name = match.group(1)
        if method_name in {"if", "for", "while", "switch", "catch", "function"}:
            continue
        end_line = _find_braced_block_end(lines, line_number)
        symbols.append(
            _symbol(
                name=method_name,
                qualified_name=f"{class_symbol.qualified_name}.{method_name}",
                symbol_type=SymbolType.METHOD.value,
                file_path=file_path,
                start_line=line_number,
                end_line=end_line,
                parent_symbol=class_symbol.qualified_name,
            )
        )
    return symbols


def _find_braced_block_end(lines: list[str], start_line: int) -> int:
    depth = 0
    seen_open = False
    for index in range(start_line - 1, len(lines)):
        for char in lines[index]:
            if char == "{":
                depth += 1
                seen_open = True
            elif char == "}":
                depth -= 1
                if seen_open and depth <= 0:
                    return index + 1
    return start_line


def _line_in_ranges(line_number: int, ranges: list[tuple[int, int]]) -> bool:
    return any(start <= line_number <= end for start, end in ranges)


def _contains_relation(source_symbol: str, target_symbol: str, source_file: str) -> ParsedRelation:
    return ParsedRelation(
        relation_type=RelationType.CONTAINS.value,
        source_symbol=source_symbol,
        target_symbol=target_symbol,
        source_file=source_file,
    )


def _symbol(
    name: str,
    qualified_name: str,
    symbol_type: str,
    file_path: str,
    start_line: int,
    end_line: int,
    parent_symbol: str | None,
) -> ParsedSymbol:
    raw_id = f"{file_path}:{qualified_name}:{symbol_type}:{start_line}:{end_line}"
    return ParsedSymbol(
        symbol_id=hashlib.sha1(raw_id.encode("utf-8")).hexdigest(),
        name=name,
        qualified_name=qualified_name,
        symbol_type=symbol_type,
        start_line=start_line,
        end_line=end_line,
        parent_symbol=parent_symbol,
    )
