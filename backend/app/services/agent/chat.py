from dataclasses import dataclass
import json
from typing import Protocol
from urllib import error, request

from app.core.config import Settings


class ChatDisabledError(RuntimeError):
    pass


class ChatRequestError(RuntimeError):
    pass


class ChatTransport(Protocol):
    def post_json(
        self,
        url: str,
        payload: dict[str, object],
        headers: dict[str, str],
        timeout: float,
    ) -> dict[str, object]:
        pass


@dataclass(frozen=True)
class ChatConfig:
    base_url: str
    api_key: str
    model: str
    temperature: float = 0.2
    timeout_seconds: float = 60.0

    @property
    def disabled_reason(self) -> str | None:
        missing = []
        if not self.base_url:
            missing.append("REPOLENS_CHAT_BASE_URL")
        if not self.api_key:
            missing.append("REPOLENS_CHAT_API_KEY")
        if not self.model:
            missing.append("REPOLENS_CHAT_MODEL")
        if missing:
            return "Missing chat configuration: " + ", ".join(missing)
        return None


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str


@dataclass(frozen=True)
class ChatResult:
    content: str
    parsed_json: dict[str, object]
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class UrllibChatTransport:
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
            raise ChatRequestError(f"Chat request failed with {exc.code}: {message}") from exc
        except error.URLError as exc:
            raise ChatRequestError(f"Chat request failed: {exc.reason}") from exc
        except json.JSONDecodeError as exc:
            raise ChatRequestError("Chat response is not valid JSON.") from exc


class OpenAICompatibleChatAdapter:
    def __init__(
        self,
        config: ChatConfig,
        *,
        transport: ChatTransport | None = None,
    ) -> None:
        self.config = config
        self.transport = transport or UrllibChatTransport()

    def complete_json(
        self,
        messages: list[ChatMessage],
        *,
        response_schema: str,
    ) -> ChatResult:
        disabled_reason = self.config.disabled_reason
        if disabled_reason:
            raise ChatDisabledError(disabled_reason)

        response = self.transport.post_json(
            _chat_completions_url(self.config.base_url),
            {
                "model": self.config.model,
                "messages": [
                    {"role": message.role, "content": message.content} for message in messages
                ],
                "temperature": self.config.temperature,
                "response_format": {"type": "json_object"},
                "metadata": {"response_schema": response_schema},
            },
            {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            self.config.timeout_seconds,
        )
        content = _parse_chat_content(response)
        parsed_json = _parse_json_content(content)
        usage = _parse_usage(response)
        return ChatResult(
            content=content,
            parsed_json=parsed_json,
            model=str(response.get("model") or self.config.model),
            prompt_tokens=usage["prompt_tokens"],
            completion_tokens=usage["completion_tokens"],
            total_tokens=usage["total_tokens"],
        )


def chat_config_from_settings(settings: Settings) -> ChatConfig:
    return ChatConfig(
        base_url=settings.chat_base_url.rstrip("/"),
        api_key=settings.chat_api_key,
        model=settings.chat_model,
        temperature=settings.chat_temperature,
        timeout_seconds=settings.chat_timeout_seconds,
    )


def _chat_completions_url(base_url: str) -> str:
    base = base_url.rstrip("/")
    if base.endswith("/v1"):
        return f"{base}/chat/completions"
    return f"{base}/v1/chat/completions"


def _parse_chat_content(response: dict[str, object]) -> str:
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ChatRequestError("Chat response missing choices list.")
    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        raise ChatRequestError("Chat response choice is not an object.")
    message = first_choice.get("message")
    if not isinstance(message, dict):
        raise ChatRequestError("Chat response choice missing message.")
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise ChatRequestError("Chat response message missing content.")
    return content.strip()


def _parse_json_content(content: str) -> dict[str, object]:
    normalized = content.strip()
    if normalized.startswith("```"):
        lines = normalized.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        normalized = "\n".join(lines).strip()
    try:
        parsed = json.loads(normalized)
    except json.JSONDecodeError as exc:
        raise ChatRequestError("Chat response content is not valid JSON.") from exc
    if not isinstance(parsed, dict):
        raise ChatRequestError("Chat response JSON must be an object.")
    return parsed


def _parse_usage(response: dict[str, object]) -> dict[str, int]:
    usage = response.get("usage")
    if not isinstance(usage, dict):
        return {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    prompt_tokens = _int_value(usage.get("prompt_tokens"))
    completion_tokens = _int_value(usage.get("completion_tokens"))
    total_tokens = _int_value(usage.get("total_tokens")) or prompt_tokens + completion_tokens
    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
    }


def _int_value(value: object) -> int:
    return int(value) if isinstance(value, (int, float)) else 0
