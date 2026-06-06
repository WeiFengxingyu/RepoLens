from dataclasses import dataclass
import json
from typing import Protocol
from urllib import error, request

from app.core.config import Settings


class EmbeddingDisabledError(RuntimeError):
    pass


class EmbeddingRequestError(RuntimeError):
    pass


class EmbeddingTransport(Protocol):
    def post_json(
        self,
        url: str,
        payload: dict[str, object],
        headers: dict[str, str],
        timeout: float,
    ) -> dict[str, object]:
        pass


@dataclass(frozen=True)
class EmbeddingConfig:
    base_url: str
    api_key: str
    model: str
    dimension: int | None = None

    @property
    def disabled_reason(self) -> str | None:
        missing = []
        if not self.base_url:
            missing.append("REPOLENS_EMBEDDING_BASE_URL")
        if not self.api_key:
            missing.append("REPOLENS_EMBEDDING_API_KEY")
        if not self.model:
            missing.append("REPOLENS_EMBEDDING_MODEL")
        if missing:
            return "Missing embedding configuration: " + ", ".join(missing)
        return None


class UrllibEmbeddingTransport:
    def post_json(
        self,
        url: str,
        payload: dict[str, object],
        headers: dict[str, str],
        timeout: float,
    ) -> dict[str, object]:
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(url, data=body, headers=headers, method="POST")
        try:
            with request.urlopen(req, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            message = exc.read().decode("utf-8", errors="replace")
            raise EmbeddingRequestError(f"Embedding request failed with {exc.code}: {message}") from exc
        except error.URLError as exc:
            raise EmbeddingRequestError(f"Embedding request failed: {exc.reason}") from exc
        except json.JSONDecodeError as exc:
            raise EmbeddingRequestError("Embedding response is not valid JSON.") from exc


class OpenAICompatibleEmbeddingAdapter:
    def __init__(
        self,
        config: EmbeddingConfig,
        *,
        transport: EmbeddingTransport | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.config = config
        self.transport = transport or UrllibEmbeddingTransport()
        self.timeout = timeout

    def embed_query(self, query: str) -> list[float]:
        return self.embed_texts([query])[0]

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        disabled_reason = self.config.disabled_reason
        if disabled_reason:
            raise EmbeddingDisabledError(disabled_reason)
        if not texts:
            return []

        response = self.transport.post_json(
            _embeddings_url(self.config.base_url),
            {"model": self.config.model, "input": texts},
            {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            self.timeout,
        )
        embeddings = _parse_embeddings_response(response)
        _validate_embeddings(embeddings, self.config.dimension)
        return embeddings


def embedding_config_from_settings(settings: Settings) -> EmbeddingConfig:
    return EmbeddingConfig(
        base_url=settings.embedding_base_url.rstrip("/"),
        api_key=settings.embedding_api_key,
        model=settings.embedding_model,
        dimension=settings.embedding_dimension,
    )


def _embeddings_url(base_url: str) -> str:
    base = base_url.rstrip("/")
    if base.endswith("/v1"):
        return f"{base}/embeddings"
    return f"{base}/v1/embeddings"


def _parse_embeddings_response(response: dict[str, object]) -> list[list[float]]:
    data = response.get("data")
    if not isinstance(data, list):
        raise EmbeddingRequestError("Embedding response missing data list.")

    sorted_items = sorted(
        data,
        key=lambda item: item.get("index", 0) if isinstance(item, dict) else 0,
    )
    embeddings: list[list[float]] = []
    for item in sorted_items:
        if not isinstance(item, dict):
            raise EmbeddingRequestError("Embedding response item is not an object.")
        embedding = item.get("embedding")
        if not isinstance(embedding, list) or not all(isinstance(value, (int, float)) for value in embedding):
            raise EmbeddingRequestError("Embedding response item missing numeric embedding.")
        embeddings.append([float(value) for value in embedding])
    return embeddings


def _validate_embeddings(embeddings: list[list[float]], expected_dimension: int | None) -> None:
    if expected_dimension is None:
        return
    for embedding in embeddings:
        if len(embedding) != expected_dimension:
            raise EmbeddingRequestError(
                f"Embedding dimension mismatch: expected {expected_dimension}, got {len(embedding)}."
            )
