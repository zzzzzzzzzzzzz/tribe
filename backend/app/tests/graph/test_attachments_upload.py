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

    openai_calls: list[tuple[str, bytes, str | None, str | None]] = []
    gigachat_calls: list[tuple[str, bytes, str | None, str | None]] = []

    def fake_openai(
        *,
        content: bytes,
        filename: str,
        content_type: str | None,
        base_url: str | None,
    ) -> str:
        openai_calls.append((filename, content, content_type, base_url))
        return f"openai-{filename}"

    def fake_gigachat(
        *,
        content: bytes,
        filename: str,
        content_type: str | None,
        base_url: str | None,
    ) -> str:
        gigachat_calls.append((filename, content, content_type, base_url))
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
    assert openai_calls == [
        ("notes.txt", b"hello", "text/plain", "https://openai.example"),
        ("image.png", b"hello", "image/png", "https://openai.example"),
    ]
    assert gigachat_calls == [
        ("notes.txt", b"hello", "text/plain", "https://gigachat.example"),
        ("image.png", b"hello", "image/png", "https://gigachat.example"),
    ]

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

    openai_calls: list[tuple[str, bytes, str | None, str | None]] = []

    def fake_openai(
        *,
        content: bytes,
        filename: str,
        content_type: str | None,
        base_url: str | None,
    ) -> str:
        openai_calls.append((filename, content, content_type, base_url))
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

    def fake_openai(
        *,
        content: bytes,
        filename: str,
        content_type: str | None,
        base_url: str | None,
    ) -> str:
        return "openai-image-id"

    def fake_gigachat(
        *,
        content: bytes,
        filename: str,
        content_type: str | None,
        base_url: str | None,
    ) -> str:
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


def test_upload_attachments_for_thread_passes_data_url_content_type(
    monkeypatch: MonkeyPatch,
) -> None:
    message = ChatMessage(
        type=ChatMessageType.human,
        content=[
            ChatContentFilePart(
                type="file",
                file=ChatContentFileData(
                    filename="misleading.txt",
                    file_data="data:image/png;base64,aGVsbG8=",
                ),
            )
        ],
    )
    openai_calls: list[tuple[str, str | None]] = []

    def fake_openai(
        *,
        content: bytes,
        filename: str,
        content_type: str | None,
        base_url: str | None,
    ) -> str:
        openai_calls.append((filename, content_type))
        return "openai-image-id"

    monkeypatch.setattr("app.core.graph.attachments._upload_to_openai", fake_openai)

    upload_attachments_for_thread(
        message=message,
        members=[_build_member(provider="openai", base_url=None)],
    )

    assert openai_calls == [("misleading.txt", "image/png")]


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

    gigachat_calls: list[tuple[str, bytes, str | None, str | None]] = []

    def fake_openai(
        *,
        content: bytes,
        filename: str,
        content_type: str | None,
        base_url: str | None,
    ) -> str:
        return "should-not-be-used"

    def fake_gigachat(
        *,
        content: bytes,
        filename: str,
        content_type: str | None,
        base_url: str | None,
    ) -> str:
        gigachat_calls.append((filename, content, content_type, base_url))
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


def test_collect_provider_file_ids_from_message() -> None:
    message = ChatMessage(
        type=ChatMessageType.human,
        content=[
            ChatContentFilePart(
                type="file",
                file=ChatContentFileData(
                    provider_file_ids={
                        "openai": "openai-file-id",
                        "gigachat": "gigachat-file-id",
                    },
                ),
            ),
            ChatContentImagePart(
                type="image_url",
                image_url=ChatContentImageData(
                    url="data:image/png;base64,aGVsbG8=",
                    provider_file_ids={"openai": "openai-image-id"},
                ),
            ),
        ],
    )

    assert attachments.collect_provider_file_ids(message) == {
        "openai": ["openai-file-id", "openai-image-id"],
        "gigachat": ["gigachat-file-id"],
    }


def test_cleanup_provider_files_deletes_known_provider_ids(
    monkeypatch: MonkeyPatch,
) -> None:
    deleted: list[tuple[str, str, str | None]] = []

    def fake_delete(
        *,
        provider_name: attachments.ProviderName,
        file_id: str,
        base_url: str | None,
    ) -> None:
        deleted.append((provider_name, file_id, base_url))

    monkeypatch.setattr("app.core.graph.attachments.delete_provider_file", fake_delete)

    attachments.cleanup_provider_files(
        provider_file_ids={
            "openai": ["openai-file-id"],
            "gigachat": ["gigachat-file-id"],
        },
        members=[
            _build_member(provider="openai", base_url="https://openai.example"),
            _build_member(provider="gigachat", base_url="https://gigachat.example"),
        ],
    )

    assert deleted == [
        ("openai", "openai-file-id", "https://openai.example"),
        ("gigachat", "gigachat-file-id", "https://gigachat.example"),
    ]


def test_upload_to_openai_uses_vision_purpose_for_images(
    monkeypatch: MonkeyPatch,
) -> None:
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
        content=b"image-bytes",
        filename="photo.png",
        content_type="image/png",
        base_url="https://openai.example",
    )

    assert remote_id == "openai-file-id"
    assert recorded["purpose"] == "vision"
    assert recorded["file"] == ("photo.png", b"image-bytes")


def test_upload_to_openai_uses_user_data_purpose_for_files(
    monkeypatch: MonkeyPatch,
) -> None:
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
        content=b"text-bytes",
        filename="notes.txt",
        content_type="text/plain",
        base_url="https://openai.example",
    )

    assert remote_id == "openai-file-id"
    assert recorded["purpose"] == "user_data"
    assert recorded["file"] == ("notes.txt", b"text-bytes")


def test_upload_to_openai_uses_content_type_before_filename(
    monkeypatch: MonkeyPatch,
) -> None:
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
        content=b"image-bytes",
        filename="attachment.bin",
        content_type="image/png",
        base_url="https://openai.example",
    )

    assert remote_id == "openai-file-id"
    assert recorded["purpose"] == "vision"
    assert recorded["file"] == ("attachment.bin", b"image-bytes")


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
        content_type="image/jpeg",
        base_url="https://gigachat.example",
    )

    assert remote_id == "giga-file-id"
    assert recorded["payload"] == ("contract.jpg", b"image-bytes")
    assert recorded["purpose"] == "general"
