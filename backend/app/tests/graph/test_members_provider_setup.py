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


def test_allowed_openai_models_match_catalog() -> None:
    from app.core.graph.model_catalog import OPENAI_MODELS, validate_model_selection

    assert OPENAI_MODELS == (
        "gpt-5.2",
        "gpt-4-turbo",
        "gpt-4",
        "gpt-5-nano",
        "gpt-5.1",
        "gpt-4.1",
        "gpt-4.1-mini",
        "gpt-4.1-nano",
        "gpt-6-luna",
        "gpt-5.6-luna",
        "gpt-5.6-terra",
        "gpt-5.5",
        "gpt-5.4-mini",
        "gpt-5.4-nano",
        "gpt-4o-mini",
        "gpt-4o",
        "gpt-3.5-turbo",
    )
    for model in OPENAI_MODELS:
        validate_model_selection("openai", model)


def test_openai_rejects_unknown_models() -> None:
    import pytest

    with pytest.raises(ValueError, match="Unsupported OpenAI model"):
        BaseNode("openai", "unsupported-model-id", None, 0)

    with pytest.raises(ValueError, match="Unsupported OpenAI model"):
        BaseNode("openai", "gpt-6-not-a-model", None, 0)
