import pytest

from app.services.agent import (
    ChatConfig,
    ChatDisabledError,
    ChatMessage,
    ChatRequestError,
    OpenAICompatibleChatAdapter,
)


def test_chat_adapter_reports_disabled_configuration() -> None:
    adapter = OpenAICompatibleChatAdapter(ChatConfig(base_url="", api_key="", model=""))

    with pytest.raises(ChatDisabledError, match="REPOLENS_CHAT_BASE_URL"):
        adapter.complete_json([ChatMessage(role="user", content="hello")], response_schema="{}")


def test_chat_adapter_posts_openai_compatible_request_and_parses_json() -> None:
    transport = FakeChatTransport(
        {
            "model": "demo-chat",
            "choices": [
                {
                    "message": {
                        "content": (
                            '{"draft_answer":"Use RepositoryService [1]",'
                            '"claims":[{"text":"claim","evidence_ids":["ev_1"]}],'
                            '"used_evidence_ids":["ev_1"]}'
                        )
                    }
                }
            ],
            "usage": {"prompt_tokens": 12, "completion_tokens": 8, "total_tokens": 20},
        }
    )
    adapter = OpenAICompatibleChatAdapter(
        ChatConfig(base_url="https://example.test/v1", api_key="secret", model="demo-chat"),
        transport=transport,
    )

    result = adapter.complete_json(
        [ChatMessage(role="user", content="question")],
        response_schema='{"draft_answer":"string"}',
    )

    assert transport.url == "https://example.test/v1/chat/completions"
    assert transport.payload["model"] == "demo-chat"
    assert transport.headers["Authorization"] == "Bearer secret"
    assert result.parsed_json["draft_answer"] == "Use RepositoryService [1]"
    assert result.total_tokens == 20


def test_chat_adapter_rejects_non_json_message_content() -> None:
    adapter = OpenAICompatibleChatAdapter(
        ChatConfig(base_url="https://example.test", api_key="secret", model="demo-chat"),
        transport=FakeChatTransport({"choices": [{"message": {"content": "not json"}}]}),
    )

    with pytest.raises(ChatRequestError, match="not valid JSON"):
        adapter.complete_json([ChatMessage(role="user", content="question")], response_schema="{}")


class FakeChatTransport:
    def __init__(self, response):
        self.response = response
        self.url = ""
        self.payload = {}
        self.headers = {}

    def post_json(self, url, payload, headers, timeout):
        self.url = url
        self.payload = payload
        self.headers = headers
        self.timeout = timeout
        return self.response
