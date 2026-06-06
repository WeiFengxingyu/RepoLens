from dataclasses import dataclass, field
import hashlib
from typing import Any

from app.models import SymbolType
from app.services.parser import ParsedFile, ParsedSymbol


CHUNK_SYMBOL_TYPES = {
    SymbolType.FUNCTION.value,
    SymbolType.METHOD.value,
    SymbolType.CLASS.value,
    SymbolType.FILE.value,
}


class ChunkBuilderError(ValueError):
    pass


@dataclass(frozen=True)
class CodeChunkDraft:
    file_path: str
    language: str
    symbol_name: str
    symbol_type: str
    start_line: int
    end_line: int
    content_hash: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


def build_chunks(parsed_file: ParsedFile) -> list[CodeChunkDraft]:
    symbols = [symbol for symbol in parsed_file.symbols if symbol.symbol_type in CHUNK_SYMBOL_TYPES]
    if not symbols:
        symbols = [_fallback_file_symbol(parsed_file)]

    chunks: list[CodeChunkDraft] = []
    for symbol in sorted(symbols, key=_symbol_sort_key):
        metadata: dict[str, Any] = {
            "source": "parser",
            "parent_symbol": symbol.parent_symbol,
            "symbol_id": symbol.symbol_id,
        }
        if symbol.symbol_type == SymbolType.FILE.value and parsed_file.errors:
            metadata["fallback"] = True
            metadata["errors"] = parsed_file.errors

        chunk_content = _content_for_range(
            parsed_file.content,
            symbol.start_line,
            symbol.end_line,
            parsed_file.file_path,
        )
        chunks.append(
            CodeChunkDraft(
                file_path=parsed_file.file_path,
                language=parsed_file.language,
                symbol_name=symbol.qualified_name,
                symbol_type=symbol.symbol_type,
                start_line=symbol.start_line,
                end_line=symbol.end_line,
                content_hash=compute_content_hash(
                    parsed_file.language,
                    parsed_file.file_path,
                    symbol.start_line,
                    symbol.end_line,
                    chunk_content,
                ),
                content=chunk_content,
                metadata=metadata,
            )
        )
    return chunks


def compute_content_hash(
    language: str,
    file_path: str,
    start_line: int,
    end_line: int,
    content: str,
) -> str:
    raw = f"{language}{file_path}{start_line}{end_line}{content}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _symbol_sort_key(symbol: ParsedSymbol) -> tuple[int, int, int, str]:
    priority = {
        SymbolType.METHOD.value: 0,
        SymbolType.FUNCTION.value: 0,
        SymbolType.CLASS.value: 1,
        SymbolType.FILE.value: 2,
    }.get(symbol.symbol_type, 3)
    return (priority, symbol.start_line, symbol.end_line, symbol.qualified_name)


def _content_for_range(content: str, start_line: int, end_line: int, file_path: str) -> str:
    lines = content.splitlines(keepends=True)
    if not lines:
        lines = [""]

    if start_line < 1 or end_line < start_line or end_line > len(lines):
        raise ChunkBuilderError(
            f"Invalid chunk line range for {file_path}: {start_line}-{end_line}."
        )
    return "".join(lines[start_line - 1 : end_line])


def _fallback_file_symbol(parsed_file: ParsedFile) -> ParsedSymbol:
    line_count = max(1, parsed_file.line_count)
    raw_id = f"{parsed_file.file_path}:fallback:file:1:{line_count}"
    return ParsedSymbol(
        symbol_id=hashlib.sha1(raw_id.encode("utf-8")).hexdigest(),
        name=parsed_file.file_path,
        qualified_name=parsed_file.file_path,
        symbol_type=SymbolType.FILE.value,
        start_line=1,
        end_line=line_count,
        parent_symbol=None,
    )
