from langchain_core.messages import AnyMessage, HumanMessage

from app.core.graph.members import format_messages


def test_format_messages_hides_binary_attachment_payloads() -> None:
    messages: list[AnyMessage] = [
        HumanMessage(
            name="user",
            content=[
                {"type": "text", "text": "Please analyze"},
                {
                    "type": "image_url",
                    "image_url": {"url": "data:image/png;base64,AAAAAA"},
                },
                {
                    "type": "file",
                    "file": {
                        "filename": "report.pdf",
                        "file_data": "data:application/pdf;base64,BBBBBB",
                    },
                },
            ],
        )
    ]

    result = format_messages(messages)

    assert "Please analyze" in result
    assert "[Attached image]" in result
    assert "[Attached file: report.pdf]" in result
    assert "base64" not in result
