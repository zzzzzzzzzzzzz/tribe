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
    assert recorded["args"] == ("gpt-4.1-mini",)
    assert recorded["kwargs"] == {
        "temperature": 0.2,
        "base_url": "https://openai.example/v1",
        "use_responses_api": True,
        "output_version": "responses/v1",
    }
