from dataclasses import dataclass

from app.services.retrieval.evidence import Evidence

DEFAULT_CONTEXT_EVIDENCE_COUNT = 10
DEFAULT_CONTEXT_MAX_CHARS = 12000


@dataclass(frozen=True)
class ContextPackage:
    evidences: list[Evidence]
    context_text: str
    total_chars: int
    truncated: bool


def build_context_package(
    evidences: list[Evidence],
    *,
    max_evidence_count: int = DEFAULT_CONTEXT_EVIDENCE_COUNT,
    max_chars: int = DEFAULT_CONTEXT_MAX_CHARS,
) -> ContextPackage:
    if not evidences or max_evidence_count <= 0 or max_chars <= 0:
        return ContextPackage(
            evidences=[],
            context_text="",
            total_chars=0,
            truncated=bool(evidences),
        )

    selected_evidences: list[Evidence] = []
    context_blocks: list[str] = []
    truncated = len(evidences) > max_evidence_count

    for index, evidence in enumerate(evidences[:max_evidence_count], start=1):
        block = _format_evidence_block(index, evidence)
        next_text = "\n\n".join([*context_blocks, block]) if context_blocks else block
        if len(next_text) > max_chars:
            current_text = "\n\n".join(context_blocks)
            separator_chars = 2 if context_blocks else 0
            remaining_chars = max_chars - len(current_text) - separator_chars
            if remaining_chars > 0:
                suffix = "\n..."
                snippet_chars = max(remaining_chars - len(suffix), 0)
                context_blocks.append(block[:snippet_chars].rstrip() + suffix)
                selected_evidences.append(evidence)
            truncated = True
            break
        context_blocks.append(block)
        selected_evidences.append(evidence)

    context_text = "\n\n".join(context_blocks)
    return ContextPackage(
        evidences=selected_evidences,
        context_text=context_text,
        total_chars=len(context_text),
        truncated=truncated,
    )


def _format_evidence_block(index: int, evidence: Evidence) -> str:
    return "\n".join(
        [
            (
                f"[{index}] {evidence.file_path}:{evidence.start_line}-{evidence.end_line} "
                f"{evidence.symbol_name} ({evidence.source}, score={evidence.score:.4f})"
            ),
            evidence.snippet,
        ]
    )
