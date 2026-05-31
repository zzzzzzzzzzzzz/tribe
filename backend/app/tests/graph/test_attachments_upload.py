from typing import Any

from pytest import MonkeyPatch

from app.core.graph import attachments
from app.core.graph.attachments import upload_attachments_for_thread
from app.models import (
    ChatContentFileData,
    ChatContentFilePart,
    ChatContentImageData,
    ChatContentImagePart,
    ChatContentTextPart,
    ChatMessage,
    ChatMessageType,
    Member,
)


def _build_message() -> ChatMessage:
    return ChatMessage(
        type=ChatMessageType.human,
        content=[
            ChatContentTextPart(type="text", text="Please check attachments"),
            ChatContentFilePart(
                type="file",
                file=ChatContentFileData(
                    filename="notes.txt",
                    file_data="data:text/plain;base64,aGVsbG8=",
                ),
            ),
            ChatContentImagePart(
                type="image_url",
                image_url=ChatContentImageData(
                    url="data:image/png;base64,aGVsbG8=",
                ),
            ),
        ],
    )


def _build_member(*, provider: str, base_url: str | None) -> Member:
    return Member(
        name=f"{provider}-member",
        role="assistant",
        type="worker",
        position_x=0,
        position_y=0,
        provider=provider,
        model="test-model",
        base_url=base_url,
    )


def test_upload_attachments_for_thread_uploads_to_both_providers(
    monkeypatch: MonkeyPatch,
) -> None:
    message = _build_message()

    openai_calls: list[tuple[str, bytes, str | None]] = []
    gigachat_calls: list[tuple[str, bytes, str | None]] = []

    def fake_openai(*, content: bytes, filename: str, base_url: str | None) -> str:
        openai_calls.append((filename, content, base_url))
        return f"openai-{filename}"

    def fake_gigachat(*, content: bytes, filename: str, base_url: str | None) -> str:
        gigachat_calls.append((filename, content, base_url))
        return f"gigachat-{filename}"

    monkeypatch.setattr("app.core.graph.attachments._upload_to_openai", fake_openai)
    monkeypatch.setattr("app.core.graph.attachments._upload_to_gigachat", fake_gigachat)

    members = [
        _build_member(provider="openai", base_url="https://openai.example"),
        _build_member(provider="gigachat", base_url="https://gigachat.example"),
    ]

    updated = upload_attachments_for_thread(message=message, members=members)
    assert updated is message

    assert len(openai_calls) == 2
    assert len(gigachat_calls) == 2

    file_part = next(
        part for part in message.content if isinstance(part, ChatContentFilePart)
    )
    assert file_part.file.file_id == "openai-notes.txt"
    assert file_part.file.provider_file_ids == {
        "openai": "openai-notes.txt",
        "gigachat": "gigachat-notes.txt",
    }


def test_upload_attachments_for_thread_reuses_existing_provider_ids(
    monkeypatch: MonkeyPatch,
) -> None:
    message = ChatMessage(
        type=ChatMessageType.human,
        content=[
            ChatContentFilePart(
                type="file",
                file=ChatContentFileData(
                    filename="already.txt",
                    file_data="data:text/plain;base64,aGVsbG8=",
                    provider_file_ids={"openai": "existing-openai-id"},
                ),
            )
        ],
    )

    openai_calls: list[tuple[str, bytes, str | None]] = []

    def fake_openai(*, content: bytes, filename: str, base_url: str | None) -> str:
        openai_calls.append((filename, content, base_url))
        return "new-openai-id"

    monkeypatch.setattr("app.core.graph.attachments._upload_to_openai", fake_openai)

    members = [_build_member(provider="openai", base_url=None)]
    upload_attachments_for_thread(message=message, members=members)

    assert openai_calls == []
    file_part = message.content[0]
    assert isinstance(file_part, ChatContentFilePart)
    assert file_part.file.provider_file_ids == {"openai": "existing-openai-id"}


def test_upload_attachments_for_thread_stores_image_provider_ids(
    monkeypatch: MonkeyPatch,
) -> None:
    message = ChatMessage(
        type=ChatMessageType.human,
        content=[
            ChatContentImagePart(
                type="image_url",
                image_url=ChatContentImageData(
                    url="data:image/png;base64,aGVsbG8=",
                ),
            )
        ],
    )

    def fake_openai(*, content: bytes, filename: str, base_url: str | None) -> str:
        return "openai-image-id"

    def fake_gigachat(*, content: bytes, filename: str, base_url: str | None) -> str:
        return "gigachat-image-id"

    monkeypatch.setattr("app.core.graph.attachments._upload_to_openai", fake_openai)
    monkeypatch.setattr("app.core.graph.attachments._upload_to_gigachat", fake_gigachat)

    members = [
        _build_member(provider="openai", base_url=None),
        _build_member(provider="gigachat", base_url=None),
    ]

    upload_attachments_for_thread(message=message, members=members)

    image_part = message.content[0]
    assert isinstance(image_part, ChatContentImagePart)
    assert image_part.image_url.provider_file_ids == {
        "openai": "openai-image-id",
        "gigachat": "gigachat-image-id",
    }


def test_upload_attachments_for_thread_uploads_missing_provider_after_team_change(
    monkeypatch: MonkeyPatch,
) -> None:
    message = ChatMessage(
        type=ChatMessageType.human,
        content=[
            ChatContentFilePart(
                type="file",
                file=ChatContentFileData(
                    filename="change.txt",
                    file_data="data:text/plain;base64,aGVsbG8=",
                    provider_file_ids={"openai": "existing-openai-id"},
                ),
            )
        ],
    )

    gigachat_calls: list[tuple[str, bytes, str | None]] = []

    def fake_openai(*, content: bytes, filename: str, base_url: str | None) -> str:
        return "should-not-be-used"

    def fake_gigachat(*, content: bytes, filename: str, base_url: str | None) -> str:
        gigachat_calls.append((filename, content, base_url))
        return "new-gigachat-id"

    monkeypatch.setattr("app.core.graph.attachments._upload_to_openai", fake_openai)
    monkeypatch.setattr("app.core.graph.attachments._upload_to_gigachat", fake_gigachat)

    members = [
        _build_member(provider="openai", base_url=None),
        _build_member(provider="gigachat", base_url=None),
    ]

    upload_attachments_for_thread(message=message, members=members)

    assert len(gigachat_calls) == 1
    file_part = message.content[0]
    assert isinstance(file_part, ChatContentFilePart)
    assert file_part.file.provider_file_ids == {
        "openai": "existing-openai-id",
        "gigachat": "new-gigachat-id",
    }


def test_upload_to_openai_uses_vision_purpose(monkeypatch: MonkeyPatch) -> None:
    recorded: dict[str, object] = {}

    class FakeFiles:
        def create(self, *, file: tuple[str, bytes], purpose: str) -> Any:
            recorded["file"] = file
            recorded["purpose"] = purpose

            class Uploaded:
                id = "openai-file-id"

            return Uploaded()

    class FakeOpenAI:
        def __init__(self, *, api_key: str, base_url: str | None) -> None:
            recorded["api_key"] = api_key
            recorded["base_url"] = base_url
            self.files = FakeFiles()

    monkeypatch.setenv("OPENAI_API_KEY", "token")
    monkeypatch.setattr("app.core.graph.attachments.OpenAI", FakeOpenAI)

    remote_id = attachments._upload_to_openai(
        content=b"pdf-bytes",
        filename="lease.pdf",
        base_url="https://openai.example",
    )

    assert remote_id == "openai-file-id"
    assert recorded["purpose"] == "vision"
    assert recorded["file"] == ("lease.pdf", b"pdf-bytes")


def test_upload_to_gigachat_uses_general_purpose(monkeypatch: MonkeyPatch) -> None:
    recorded: dict[str, object] = {}

    class FakeGigaChat:
        def __init__(
            self,
            *,
            credentials: str,
            base_url: str | None,
            verify_ssl_certs: bool,
        ) -> None:
            recorded["credentials"] = credentials
            recorded["base_url"] = base_url
            recorded["verify_ssl_certs"] = verify_ssl_certs

        def upload_file(self, payload: tuple[str, bytes], *, purpose: str) -> Any:
            recorded["payload"] = payload
            recorded["purpose"] = purpose

            class Uploaded:
                id_ = "giga-file-id"

            return Uploaded()

    monkeypatch.setenv("GIGACHAT_AUTH_TOKEN", "token")
    monkeypatch.setattr("app.core.graph.attachments.GigaChat", FakeGigaChat)

    remote_id = attachments._upload_to_gigachat(
        content=b"image-bytes",
        filename="contract.jpg",
        base_url="https://gigachat.example",
    )

    assert remote_id == "giga-file-id"
    assert recorded["payload"] == ("contract.jpg", b"image-bytes")
    assert recorded["purpose"] == "general"
