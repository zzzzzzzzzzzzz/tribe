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


def test_format_messages_handles_openai_input_parts() -> None:
    messages: list[AnyMessage] = [
        HumanMessage(
            name="user",
            content=[
                {"type": "input_text", "text": "What is in this contract?"},
                {"type": "input_image", "image_url": "data:image/png;base64,AAAAAA"},
                {
                    "type": "input_file",
                    "filename": "contract.pdf",
                    "file_data": "data:application/pdf;base64,BBBBBB",
                },
            ],
        )
    ]

    result = format_messages(messages)

    assert "What is in this contract?" in result
    assert "[Attached image]" in result
    assert "[Attached file: contract.pdf]" in result
    assert "base64" not in result
