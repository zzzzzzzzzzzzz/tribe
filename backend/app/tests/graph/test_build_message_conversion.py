from app.core.graph.build import chat_message_to_human_message
from app.models import ChatMessage


def test_chat_message_to_human_message_with_string_content() -> None:
    message = ChatMessage(type="human", content="hello")

    result = chat_message_to_human_message(message)

    assert result.content == "hello"
    assert result.additional_kwargs == {}


def test_chat_message_to_human_message_with_multipart_content() -> None:
    message = ChatMessage(
        type="human",
        content=[
            {"type": "text", "text": "Describe this"},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64,AAA"}},
            {
                "type": "file",
                "file": {
                    "file_id": "file-123",
                    "filename": "report.pdf",
                    "file_data": "data:application/pdf;base64,BBB",
                },
            },
        ],
    )

    result = chat_message_to_human_message(message)

    assert isinstance(result.content, list)
    assert result.content[0] == {"type": "text", "text": "Describe this"}
    assert result.content[1] == {
        "type": "image_url",
        "image_url": {"url": "data:image/png;base64,AAA"},
    }
    assert result.content[2]["type"] == "file"
    assert result.additional_kwargs["attachments"] == ["file-123"]
