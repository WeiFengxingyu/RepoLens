from pathlib import Path

from app.models import CodeLanguage, RelationType, SymbolType
from app.services.parser import (
    parse_python_source,
    parse_source_file,
    parse_typescript_javascript_source,
)


def test_python_parser_extracts_symbols_imports_and_calls() -> None:
    content = "\n".join(
        [
            "import os",
            "from pathlib import Path",
            "",
            "class Greeter:",
            "    def hello(self, name):",
            "        return format_name(name)",
            "",
            "async def fetch():",
            "    return call_api()",
            "",
            "def main():",
            "    print(os.getcwd())",
        ]
    )

    parsed = parse_python_source(content, "app/main.py")

    symbols = {symbol.qualified_name: symbol for symbol in parsed.symbols}
    assert symbols["app/main.py"].symbol_type == SymbolType.FILE.value
    assert symbols["Greeter"].symbol_type == SymbolType.CLASS.value
    assert symbols["Greeter.hello"].symbol_type == SymbolType.METHOD.value
    assert symbols["fetch"].symbol_type == SymbolType.FUNCTION.value
    assert symbols["main"].symbol_type == SymbolType.FUNCTION.value
    assert symbols["Greeter.hello"].start_line == 5

    imports = {
        relation.target_symbol
        for relation in parsed.relations
        if relation.relation_type == RelationType.IMPORTS.value
    }
    assert imports == {"os", "pathlib.Path"}

    calls = {
        (relation.source_symbol, relation.target_symbol)
        for relation in parsed.relations
        if relation.relation_type == RelationType.CALLS.value
    }
    assert ("Greeter.hello", "format_name") in calls
    assert ("fetch", "call_api") in calls
    assert ("main", "print") in calls
    assert ("main", "os.getcwd") in calls


def test_python_parser_returns_file_symbol_on_syntax_error() -> None:
    parsed = parse_python_source("def broken(:\n", "broken.py")

    assert parsed.errors
    assert parsed.symbols[0].qualified_name == "broken.py"
    assert parsed.symbols[0].symbol_type == SymbolType.FILE.value


def test_typescript_javascript_fallback_parser_extracts_basic_structure() -> None:
    content = "\n".join(
        [
            'import React from "react";',
            'import "./style.css";',
            "",
            "export class View {",
            "  render() {",
            "    return null;",
            "  }",
            "  async load() {",
            "    return fetch('/api');",
            "  }",
            "}",
            "",
            "export function makeView() {",
            "  return new View();",
            "}",
            "",
            "const helper = (name: string) => name.trim();",
        ]
    )

    parsed = parse_typescript_javascript_source(
        content,
        "frontend/view.tsx",
        CodeLanguage.TYPESCRIPT.value,
    )

    symbols = {symbol.qualified_name: symbol for symbol in parsed.symbols}
    assert symbols["frontend/view.tsx"].symbol_type == SymbolType.FILE.value
    assert symbols["View"].symbol_type == SymbolType.CLASS.value
    assert symbols["View.render"].symbol_type == SymbolType.METHOD.value
    assert symbols["View.load"].symbol_type == SymbolType.METHOD.value
    assert symbols["makeView"].symbol_type == SymbolType.FUNCTION.value
    assert symbols["helper"].symbol_type == SymbolType.FUNCTION.value

    imports = {
        relation.target_symbol
        for relation in parsed.relations
        if relation.relation_type == RelationType.IMPORTS.value
    }
    assert imports == {"react", "./style.css"}

    contains = {
        (relation.source_symbol, relation.target_symbol)
        for relation in parsed.relations
        if relation.relation_type == RelationType.CONTAINS.value
    }
    assert ("frontend/view.tsx", "View") in contains
    assert ("View", "View.render") in contains
    assert ("frontend/view.tsx", "helper") in contains


def test_parse_source_file_dispatches_by_language(tmp_path: Path) -> None:
    source = tmp_path / "app.py"
    source.write_text("def main():\n    return 1\n", encoding="utf-8")

    parsed = parse_source_file(source, "app.py", CodeLanguage.PYTHON.value)

    assert parsed.language == CodeLanguage.PYTHON.value
    assert any(symbol.qualified_name == "main" for symbol in parsed.symbols)
