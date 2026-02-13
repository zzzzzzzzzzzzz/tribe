from app.api.routes.teams import _extract_text_content
from app.models import ChatContentFilePart, ChatContentImagePart, ChatContentTextPart


def test_extract_text_content_for_plain_string() -> None:
    assert _extract_text_content("hello") == "hello"


def test_extract_text_content_for_multipart_content() -> None:
    content = [
        ChatContentTextPart(type="text", text="Line 1"),
        ChatContentImagePart(type="image_url", image_url={"url": "data:image/png;base64,AAA"}),
        ChatContentFilePart(type="file", file={"filename": "report.pdf"}),
        ChatContentTextPart(type="text", text="Line 2"),
    ]

    result = _extract_text_content(content)

    assert result == "Line 1\nLine 2"
