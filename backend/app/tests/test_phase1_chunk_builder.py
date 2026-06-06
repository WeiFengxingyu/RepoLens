from app.models import SymbolType
from app.services.chunking import build_chunks, compute_content_hash
from app.services.parser import parse_python_source


def test_chunk_builder_creates_function_class_and_file_chunks() -> None:
    content = "\n".join(
        [
            "class Greeter:",
            "    def hello(self):",
            "        return 'hi'",
            "",
            "def main():",
            "    return Greeter().hello()",
        ]
    )
    parsed = parse_python_source(content, "app/main.py")

    chunks = build_chunks(parsed)
    chunks_by_symbol = {chunk.symbol_name: chunk for chunk in chunks}

    assert list(chunks_by_symbol) == ["Greeter.hello", "main", "Greeter", "app/main.py"]
    assert chunks_by_symbol["Greeter.hello"].symbol_type == SymbolType.METHOD.value
    assert chunks_by_symbol["Greeter.hello"].start_line == 2
    assert chunks_by_symbol["Greeter.hello"].end_line == 3
    assert chunks_by_symbol["Greeter.hello"].content == "    def hello(self):\n        return 'hi'\n"
    assert chunks_by_symbol["Greeter"].symbol_type == SymbolType.CLASS.value
    assert chunks_by_symbol["app/main.py"].symbol_type == SymbolType.FILE.value
    assert chunks_by_symbol["app/main.py"].start_line == 1
    assert chunks_by_symbol["app/main.py"].end_line == 6

    method_chunk = chunks_by_symbol["Greeter.hello"]
    assert method_chunk.content_hash == compute_content_hash(
        method_chunk.language,
        method_chunk.file_path,
        method_chunk.start_line,
        method_chunk.end_line,
        method_chunk.content,
    )
    assert len(method_chunk.content_hash) == 64


def test_chunk_builder_marks_file_chunk_as_fallback_when_parser_failed() -> None:
    parsed = parse_python_source("def broken(:\n", "broken.py")

    chunks = build_chunks(parsed)

    assert len(chunks) == 1
    assert chunks[0].symbol_name == "broken.py"
    assert chunks[0].symbol_type == SymbolType.FILE.value
    assert chunks[0].metadata["fallback"] is True
    assert chunks[0].metadata["errors"] == parsed.errors
