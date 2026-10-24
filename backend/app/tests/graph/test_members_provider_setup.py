from typing import Any

from pytest import MonkeyPatch

from app.core.graph.members import BaseNode


def test_base_node_openai_uses_responses_api(monkeypatch: MonkeyPatch) -> None:
    recorded: dict[str, Any] = {}

    class FakeChatOpenAI:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            recorded["args"] = args
            recorded["kwargs"] = kwargs

    monkeypatch.setattr("app.core.graph.members.ChatOpenAI", FakeChatOpenAI)

    node = BaseNode(
        provider="openai",
        model="gpt-4.1-mini",
        base_url="https://openai.example/v1",
        temperature=0.2,
    )

    assert isinstance(node.model, FakeChatOpenAI)
    assert recorded["args"] == ()
    assert recorded["kwargs"] == {
        "model": "gpt-4.1-mini",
        "temperature": 0.2,
        "base_url": "https://openai.example/v1",
        "use_responses_api": True,
        "output_version": "responses/v1",
    }

def test_gigachat_uses_b2b_scope_and_only_max_model(monkeypatch: MonkeyPatch) -> None:
    recorded: dict[str, Any] = {}

    class FakeGigaChat:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            recorded.update(kwargs)

    monkeypatch.setenv("GIGACHAT_AUTH_TOKEN", "test-credential")
    monkeypatch.setattr("app.core.graph.members.GigaChat", FakeGigaChat)

    node = BaseNode("gigachat", "GigaChat-2-Max", None, 0.2)
    assert isinstance(node.model, FakeGigaChat)
    assert recorded == {
        "credentials": "test-credential",
        "scope": "GIGACHAT_API_B2B",
        "timeout": 120,
        "verify_ssl_certs": False,
        "model": "GigaChat-2-Max",
        "temperature": 0.2,
        "base_url": None,
        "auto_upload_images": True,
    }


def test_gigachat_rejects_other_models() -> None:
    import pytest

    with pytest.raises(ValueError, match="GigaChat-2-Max"):
        BaseNode("gigachat", "GigaChat-Max", None, 0)
