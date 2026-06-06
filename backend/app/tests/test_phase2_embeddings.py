from dataclasses import dataclass

import pytest

from app.core.config import Settings
from app.services.indexing import (
    EmbeddingConfig,
    EmbeddingDisabledError,
    EmbeddingRequestError,
    OpenAICompatibleEmbeddingAdapter,
    embedding_config_from_settings,
)


@dataclass
class FakeTransport:
    response: dict[str, object]
    url: str | None = None
    payload: dict[str, object] | None = None
    headers: dict[str, str] | None = None

    def post_json(
        self,
        url: str,
        payload: dict[str, object],
        headers: dict[str, str],
        timeout: float,
    ) -> dict[str, object]:
        self.url = url
        self.payload = payload
        self.headers = headers
        return self.response


def test_embedding_config_from_settings_reads_phase2_fields() -> None:
    settings = Settings(
        embedding_base_url="https://embedding.example.com",
        embedding_api_key="secret",
        embedding_model="text-embedding-demo",
        embedding_dimension=3,
    )

    config = embedding_config_from_settings(settings)

    assert config.base_url == "https://embedding.example.com"
    assert config.api_key == "secret"
    assert config.model == "text-embedding-demo"
    assert config.dimension == 3


def test_embedding_adapter_reports_disabled_configuration() -> None:
    adapter = OpenAICompatibleEmbeddingAdapter(
        EmbeddingConfig(base_url="", api_key="", model="")
    )

    with pytest.raises(EmbeddingDisabledError) as exc:
        adapter.embed_query("repository")

    assert "REPOLENS_EMBEDDING_BASE_URL" in str(exc.value)
    assert "REPOLENS_EMBEDDING_API_KEY" in str(exc.value)
    assert "REPOLENS_EMBEDDING_MODEL" in str(exc.value)


def test_embedding_adapter_posts_openai_compatible_request_and_sorts_response() -> None:
    transport = FakeTransport(
        response={
            "data": [
                {"index": 1, "embedding": [0.3, 0.4, 0.5]},
                {"index": 0, "embedding": [0.0, 0.1, 0.2]},
            ]
        }
    )
    adapter = OpenAICompatibleEmbeddingAdapter(
        EmbeddingConfig(
            base_url="https://embedding.example.com/v1",
            api_key="secret",
            model="text-embedding-demo",
            dimension=3,
        ),
        transport=transport,
    )

    embeddings = adapter.embed_texts(["alpha", "beta"])

    assert embeddings == [[0.0, 0.1, 0.2], [0.3, 0.4, 0.5]]
    assert transport.url == "https://embedding.example.com/v1/embeddings"
    assert transport.payload == {"model": "text-embedding-demo", "input": ["alpha", "beta"]}
    assert transport.headers is not None
    assert transport.headers["Authorization"] == "Bearer secret"


def test_embedding_adapter_validates_dimension() -> None:
    adapter = OpenAICompatibleEmbeddingAdapter(
        EmbeddingConfig(
            base_url="https://embedding.example.com",
            api_key="secret",
            model="text-embedding-demo",
            dimension=4,
        ),
        transport=FakeTransport(response={"data": [{"index": 0, "embedding": [0.1, 0.2, 0.3]}]}),
    )

    with pytest.raises(EmbeddingRequestError):
        adapter.embed_query("repository")
