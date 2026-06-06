from collections import Counter, defaultdict
from dataclasses import dataclass, field
import math
import re
from typing import Protocol


class ChunkLike(Protocol):
    id: str
    file_path: str
    language: str
    symbol_name: str
    symbol_type: str
    content: str


@dataclass(frozen=True)
class BM25Document:
    chunk_id: str
    file_path: str
    symbol_name: str
    symbol_type: str
    language: str
    text: str
    tokens: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class BM25SearchResult:
    chunk_id: str
    score: float
    matched_terms: list[str]


class BM25Index:
    def __init__(
        self,
        documents: list[BM25Document],
        *,
        k1: float = 1.5,
        b: float = 0.75,
    ) -> None:
        self.documents = [
            document if document.tokens else _document_with_tokens(document)
            for document in documents
        ]
        self.k1 = k1
        self.b = b
        self.average_document_length = _average_length(self.documents)
        self.document_frequencies = _document_frequencies(self.documents)
        self.term_frequencies = [Counter(document.tokens) for document in self.documents]

    def search(self, query: str, top_k: int = 10) -> list[BM25SearchResult]:
        query_terms = tokenize(query)
        if not query_terms or top_k <= 0 or not self.documents:
            return []

        unique_query_terms = sorted(set(query_terms))
        results: list[BM25SearchResult] = []
        for index, document in enumerate(self.documents):
            score = self._score_document(index, unique_query_terms)
            if score <= 0:
                continue
            matched_terms = [
                term for term in unique_query_terms if self.term_frequencies[index].get(term, 0) > 0
            ]
            results.append(
                BM25SearchResult(
                    chunk_id=document.chunk_id,
                    score=score,
                    matched_terms=matched_terms,
                )
            )

        return sorted(results, key=lambda result: (-result.score, result.chunk_id))[:top_k]

    def _score_document(self, document_index: int, query_terms: list[str]) -> float:
        document = self.documents[document_index]
        term_frequency = self.term_frequencies[document_index]
        document_length = len(document.tokens)
        score = 0.0

        for term in query_terms:
            frequency = term_frequency.get(term, 0)
            if frequency == 0:
                continue
            idf = self._idf(term)
            denominator = frequency + self.k1 * (
                1 - self.b + self.b * document_length / self.average_document_length
            )
            score += idf * (frequency * (self.k1 + 1)) / denominator
        return score

    def _idf(self, term: str) -> float:
        total_documents = len(self.documents)
        containing_documents = self.document_frequencies.get(term, 0)
        return math.log(1 + (total_documents - containing_documents + 0.5) / (containing_documents + 0.5))


def build_bm25_index(chunks: list[ChunkLike]) -> BM25Index:
    return BM25Index([document_from_chunk(chunk) for chunk in chunks])


def document_from_chunk(chunk: ChunkLike) -> BM25Document:
    text = " ".join(
        [
            chunk.file_path,
            chunk.symbol_name,
            chunk.symbol_type,
            chunk.language,
            chunk.content,
        ]
    )
    return BM25Document(
        chunk_id=chunk.id,
        file_path=chunk.file_path,
        symbol_name=chunk.symbol_name,
        symbol_type=chunk.symbol_type,
        language=chunk.language,
        text=text,
        tokens=tokenize(text),
    )


def tokenize(text: str) -> list[str]:
    expanded = _split_camel_case(text.replace("_", " "))
    return [
        token
        for token in re.split(r"[^A-Za-z0-9]+", expanded.lower())
        if token
    ]


def _split_camel_case(text: str) -> str:
    with_acronyms = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", text)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", with_acronyms)


def _document_with_tokens(document: BM25Document) -> BM25Document:
    return BM25Document(
        chunk_id=document.chunk_id,
        file_path=document.file_path,
        symbol_name=document.symbol_name,
        symbol_type=document.symbol_type,
        language=document.language,
        text=document.text,
        tokens=tokenize(document.text),
    )


def _average_length(documents: list[BM25Document]) -> float:
    if not documents:
        return 1.0
    return sum(len(document.tokens) for document in documents) / len(documents) or 1.0


def _document_frequencies(documents: list[BM25Document]) -> dict[str, int]:
    frequencies: dict[str, int] = defaultdict(int)
    for document in documents:
        for token in set(document.tokens):
            frequencies[token] += 1
    return dict(frequencies)
