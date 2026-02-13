import os
from typing import TYPE_CHECKING

import pytest
from langchain_core.messages import AIMessage

if TYPE_CHECKING:
    from app.core.graph.members import BaseNode
    from app.models import ChatMessage

_REQUIRED_SETTINGS_DEFAULTS = {
    "PROJECT_NAME": "tribe-tests",
    "POSTGRES_SERVER": "localhost",
    "POSTGRES_USER": "postgres",
    "POSTGRES_PASSWORD": "postgres",
    "FIRST_SUPERUSER": "admin@example.com",
    "FIRST_SUPERUSER_PASSWORD": "changeme",
    "QDRANT__SERVICE__API_KEY": "test",
    "CELERY_BROKER_URL": "redis://localhost",
    "CELERY_RESULT_BACKEND": "redis://localhost",
    "DENSE_EMBEDDING_MODEL": "BAAI/bge-small-en-v1.5",
    "SPARSE_EMBEDDING_MODEL": "Qdrant/bm25",
    "FASTEMBED_CACHE_PATH": "/tmp/fastembed",
}

TINY_PNG_DATA_URL = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO7Zq1sAAAAASUVORK5CYII="
)


def _set_required_env_defaults() -> None:
    for key, value in _REQUIRED_SETTINGS_DEFAULTS.items():
        os.environ.setdefault(key, value)


def _build_openai_message() -> "ChatMessage":
    from app.models import ChatMessage

    return ChatMessage(
        type="human",
        content=[
            {"type": "text", "text": "What is shown in this image? Keep it short."},
            {"type": "image_url", "image_url": {"url": TINY_PNG_DATA_URL}},
        ],
    )


def _build_gigachat_message() -> "ChatMessage":
    from app.models import ChatMessage

    return ChatMessage(
        type="human",
        content="Ответь одним коротким предложением: что такое интеграционный тест?",
    )


def _build_node(provider: str, model_name: str, base_url: str | None) -> "BaseNode":
    from app.core.graph.members import BaseNode

    return BaseNode(
        provider=provider,
        model=model_name,
        base_url=base_url,
        temperature=0,
    )


def _assert_non_empty_ai_response(response: AIMessage) -> None:
    content = response.content
    if isinstance(content, str):
        assert content.strip() != ""
    else:
        assert len(content) > 0


def test_openai_text_and_image_message_integration() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY is not configured")

    _set_required_env_defaults()

    from app.core.graph.build import chat_message_to_human_message

    model_name = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
    base_url = os.getenv("OPENAI_BASE_URL")

    human_message = chat_message_to_human_message(_build_openai_message())
    response = _build_node("openai", model_name, base_url).model.invoke([human_message])

    assert isinstance(response, AIMessage)
    _assert_non_empty_ai_response(response)


def test_gigachat_text_message_integration() -> None:
    if not os.getenv("GIGACHAT_AUTH_TOKEN"):
        pytest.skip("GIGACHAT_AUTH_TOKEN is not configured")

    _set_required_env_defaults()

    from app.core.graph.build import chat_message_to_human_message

    model_name = os.getenv("GIGACHAT_MODEL", "GigaChat")
    base_url = os.getenv("GIGACHAT_BASE_URL")

    human_message = chat_message_to_human_message(_build_gigachat_message())
    response = _build_node("gigachat", model_name, base_url).model.invoke([human_message])

    assert isinstance(response, AIMessage)
    _assert_non_empty_ai_response(response)
