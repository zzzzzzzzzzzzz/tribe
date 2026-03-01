import pytest

from app.core.graph.build import chat_message_to_human_message
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
    assert result.content[0] == {"type": "text", "text": "Describe this"}
    assert result.content[1] == {
        "type": "image_url",
        "image_url": {"url": "data:image/png;base64,AAA"},
    }
    content_parts = result.content
    assert isinstance(content_parts, list)
    third_part = content_parts[2]
    assert isinstance(third_part, dict)
    assert third_part == {"type": "text", "text": "[Attached file: report.txt]"}
    fourth_part = content_parts[3]
    assert isinstance(fourth_part, dict)
    assert fourth_part == {
        "type": "text",
        "text": "[Attached file: report.txt]\nhello from attachment",
    }
    assert result.additional_kwargs["attachments"] == ["file-123"]


def test_chat_message_attachment_count_limit() -> None:
    with pytest.raises(ValueError, match="No more than 10 attachments"):
        ChatMessage(
            type=ChatMessageType.human,
            content=[
                ChatContentFilePart(
                    type="file",
                    file=ChatContentFileData(filename=f"file-{index}.txt", file_data=None),
                )
                for index in range(11)
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
                    file=ChatContentFileData(filename="big.txt", file_data=oversized_data),
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

    assert result.additional_kwargs["attachments"] == ["image-file-123"]
