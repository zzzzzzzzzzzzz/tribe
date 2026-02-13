import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

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
for _key, _value in _REQUIRED_SETTINGS_DEFAULTS.items():
    os.environ.setdefault(_key, _value)

from langchain_core.messages import AIMessage

from app.core.graph.build import chat_message_to_human_message
from app.core.graph.members import BaseNode
from app.models import ChatMessage

TINY_PNG_DATA_URL = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO7Zq1sAAAAASUVORK5CYII="
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

    model_name = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
    base_url = os.getenv("OPENAI_BASE_URL")

    chat_message = ChatMessage(
        type="human",
        content=[
            {"type": "text", "text": "What is shown in this image? Keep it short."},
            {"type": "image_url", "image_url": {"url": TINY_PNG_DATA_URL}},
        ],
    )
    human_message = chat_message_to_human_message(chat_message)

    model = BaseNode(
        provider="openai",
        model=model_name,
        base_url=base_url,
        temperature=0,
    ).model
    response = model.invoke([human_message])

    assert isinstance(response, AIMessage)
    _assert_non_empty_ai_response(response)


def test_gigachat_text_message_integration() -> None:
    if not os.getenv("GIGACHAT_AUTH_TOKEN"):
        pytest.skip("GIGACHAT_AUTH_TOKEN is not configured")

    model_name = os.getenv("GIGACHAT_MODEL", "GigaChat")
    base_url = os.getenv("GIGACHAT_BASE_URL")

    chat_message = ChatMessage(
        type="human",
        content="Ответь одним коротким предложением: что такое интеграционный тест?",
    )
    human_message = chat_message_to_human_message(chat_message)

    model = BaseNode(
        provider="gigachat",
        model=model_name,
        base_url=base_url,
        temperature=0,
    ).model
    response = model.invoke([human_message])

    assert isinstance(response, AIMessage)
    _assert_non_empty_ai_response(response)
