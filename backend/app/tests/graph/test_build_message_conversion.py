from typing import Literal

import pytest

from app.core.graph.build import _file_data_to_text_part, chat_message_to_human_message
from app.models import (
    ChatContentFileData,
    ChatContentFilePart,
    ChatContentImageData,
    ChatContentImagePart,
    ChatContentTextPart,
    ChatMessage,
    ChatMessageType,
)


def _base64_data_url(data: bytes, mime: str) -> str:
    import base64

    encoded = base64.b64encode(data).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def test_file_data_to_text_part_extracts_pdf_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _FakePage:
        def get_text(self, _mode: str) -> str:
            return "Lease tenant: John Doe"

    class _FakeDocument:
        def __enter__(self) -> "_FakeDocument":
            return self

        def __exit__(self, exc_type: object, exc: object, tb: object) -> Literal[False]:
            return False

        def __iter__(self) -> object:
            return iter([_FakePage()])

    class _FakePyMuPDF:
        @staticmethod
        def open(*, stream: object, filetype: str) -> _FakeDocument:
            assert filetype == "pdf"
            assert stream is not None
            return _FakeDocument()

    import sys

    monkeypatch.setitem(sys.modules, "pymupdf", _FakePyMuPDF())

    result = _file_data_to_text_part(
        _base64_data_url(b"%PDF-1.4 fake", "application/pdf"),
        "lease.pdf",
    )

    assert result == {
        "type": "text",
        "text": "[Attached file: lease.pdf]\nLease tenant: John Doe",
    }


def test_chat_message_to_human_message_with_string_content() -> None:
    message = ChatMessage(type=ChatMessageType.human, content="hello")

    result = chat_message_to_human_message(message)

    assert result.content == "hello"
    assert result.additional_kwargs == {}


def test_chat_message_to_human_message_with_multipart_content() -> None:
    message = ChatMessage(
        type=ChatMessageType.human,
        content=[
            ChatContentTextPart(type="text", text="Describe this"),
            ChatContentImagePart(
                type="image_url",
                image_url=ChatContentImageData(url="data:image/png;base64,AAA"),
            ),
            ChatContentFilePart(
                type="file",
                file=ChatContentFileData(
                    file_id="file-123",
                    filename="report.txt",
                    file_data=_base64_data_url(b"hello from attachment", "text/plain"),
                ),
            ),
        ],
    )

    result = chat_message_to_human_message(message)

    assert isinstance(result.content, list)
    assert result.content[0] == {"type": "input_text", "text": "Describe this"}
    assert result.content[1] == {
        "type": "input_image",
        "image_url": "data:image/png;base64,AAA",
    }
    assert result.content[2] == {"type": "input_text", "text": "[Attached image]"}
    assert result.content[3] == {
        "type": "input_file",
        "file_id": "file-123",
    }
    assert result.content[4] == {
        "type": "input_text",
        "text": "[Attached file: report.txt]\nhello from attachment",
    }
    assert len(result.content) == 5
    assert result.additional_kwargs == {}


def test_chat_message_to_human_message_openai_uses_data_url_fallback_without_file_id() -> (
    None
):
    image_data = _base64_data_url(b"image-data", "image/jpeg")
    pdf_data = _base64_data_url(b"%PDF-1.4 fake", "application/pdf")
    message = ChatMessage(
        type=ChatMessageType.human,
        content=[
            ChatContentImagePart(
                type="image_url",
                image_url=ChatContentImageData(url=image_data),
            ),
            ChatContentFilePart(
                type="file",
                file=ChatContentFileData(
                    filename="contract.pdf",
                    file_data=pdf_data,
                ),
            ),
        ],
    )

    result = chat_message_to_human_message(message)

    assert isinstance(result.content, list)
    assert result.content[0] == {"type": "input_image", "image_url": image_data}
    assert result.content[1] == {"type": "input_text", "text": "[Attached image]"}
    assert result.content[2] == {
        "type": "input_text",
        "text": "[Attached file: contract.pdf]",
    }
    assert len(result.content) == 3


def test_chat_message_attachment_count_limit() -> None:
    with pytest.raises(ValueError, match="No more than 5 attachments"):
        ChatMessage(
            type=ChatMessageType.human,
            content=[
                ChatContentFilePart(
                    type="file",
                    file=ChatContentFileData(
                        filename=f"file-{index}.txt", file_data=None
                    ),
                )
                for index in range(6)
            ],
        )


def test_chat_message_attachment_size_limit() -> None:
    oversized_data = _base64_data_url(b"a" * (20 * 1024 * 1024 + 1), "text/plain")
    with pytest.raises(ValueError, match="must not exceed 20MB"):
        ChatMessage(
            type=ChatMessageType.human,
            content=[
                ChatContentFilePart(
                    type="file",
                    file=ChatContentFileData(
                        filename="big.txt", file_data=oversized_data
                    ),
                )
            ],
        )


def test_chat_message_rejects_unsupported_attachment_type() -> None:
    with pytest.raises(ValueError, match="Unsupported attachment type"):
        ChatMessage(
            type=ChatMessageType.human,
            content=[
                ChatContentFilePart(
                    type="file",
                    file=ChatContentFileData(
                        filename="archive.zip",
                        file_data=_base64_data_url(b"zip", "application/zip"),
                    ),
                )
            ],
        )


def test_chat_message_rejects_non_image_image_part() -> None:
    with pytest.raises(ValueError, match="Image attachments"):
        ChatMessage(
            type=ChatMessageType.human,
            content=[
                ChatContentImagePart(
                    type="image_url",
                    image_url=ChatContentImageData(
                        url=_base64_data_url(b"hello", "text/plain"),
                    ),
                )
            ],
        )


def test_chat_message_to_human_message_includes_uploaded_image_attachment_ids() -> None:
    message = ChatMessage(
        type=ChatMessageType.human,
        content=[
            ChatContentTextPart(type="text", text="Look at this"),
            ChatContentImagePart(
                type="image_url",
                image_url=ChatContentImageData(
                    url="data:image/png;base64,AAA",
                    provider_file_ids={"openai": "image-file-123"},
                ),
            ),
        ],
    )

    result = chat_message_to_human_message(message)

    assert isinstance(result.content, list)
    assert result.content[1] == {
        "type": "input_image",
        "file_id": "image-file-123",
    }
    assert result.content[2] == {"type": "input_text", "text": "[Attached image]"}
    assert result.additional_kwargs == {}


def test_chat_message_to_human_message_openai_treats_file_part_image_as_image() -> None:
    message = ChatMessage(
        type=ChatMessageType.human,
        content=[
            ChatContentFilePart(
                type="file",
                file=ChatContentFileData(
                    filename="uploaded.txt",
                    file_data=_base64_data_url(b"image", "image/png"),
                    provider_file_ids={"openai": "openai-image-id"},
                ),
            ),
        ],
    )

    result = chat_message_to_human_message(message, attachment_provider="openai")

    assert result.content == [
        {"type": "input_image", "file_id": "openai-image-id"},
        {"type": "input_text", "text": "[Attached image]"},
    ]
    assert result.additional_kwargs == {}


def test_chat_message_to_human_message_uses_gigachat_provider_attachment_ids() -> None:
    message = ChatMessage(
        type=ChatMessageType.human,
        content=[
            ChatContentTextPart(type="text", text="Process these"),
            ChatContentFilePart(
                type="file",
                file=ChatContentFileData(
                    filename="notes.txt",
                    file_data=_base64_data_url(b"hello", "text/plain"),
                    provider_file_ids={"gigachat": "g-file-id"},
                ),
            ),
            ChatContentImagePart(
                type="image_url",
                image_url=ChatContentImageData(
                    url="data:image/png;base64,AAA",
                    provider_file_ids={"gigachat": "g-image-id"},
                ),
            ),
        ],
    )

    result = chat_message_to_human_message(message, attachment_provider="gigachat")

    assert result.additional_kwargs["attachments"] == ["g-file-id", "g-image-id"]
    assert isinstance(result.content, list)
    image_part = next(
        part
        for part in result.content
        if isinstance(part, dict) and part.get("type") == "image_url"
    )
    assert isinstance(image_part, dict)
    assert image_part["image_url"]["giga_id"] == "g-image-id"
    assert "provider_file_ids" not in image_part["image_url"]
    assert {"type": "text", "text": "[Attached image]"} in result.content


def test_chat_message_to_human_message_openai_uses_uploaded_file_ids() -> None:
    message = ChatMessage(
        type=ChatMessageType.human,
        content=[
            ChatContentFilePart(
                type="file",
                file=ChatContentFileData(
                    filename="notes.txt",
                    file_data=_base64_data_url(b"hello", "text/plain"),
                    provider_file_ids={"openai": "openai-file-id"},
                ),
            ),
            ChatContentImagePart(
                type="image_url",
                image_url=ChatContentImageData(
                    url="data:image/png;base64,AAA",
                    provider_file_ids={"openai": "openai-image-id"},
                ),
            ),
        ],
    )

    result = chat_message_to_human_message(message, attachment_provider="openai")

    assert result.content == [
        {"type": "input_file", "file_id": "openai-file-id"},
        {"type": "input_text", "text": "[Attached file: notes.txt]\nhello"},
        {"type": "input_image", "file_id": "openai-image-id"},
        {"type": "input_text", "text": "[Attached image]"},
    ]
    assert result.additional_kwargs == {}
