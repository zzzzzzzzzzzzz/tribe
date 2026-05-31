import base64
import os
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_IMAGE_SAMPLE = _REPO_ROOT / "im1.png"
_TEXT_SAMPLE = _REPO_ROOT / "tezd.txt"
_TINY_PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO7Zq1sAAAAASUVORK5CYII="
)


pytestmark = pytest.mark.integration


def _read_sample(path: Path, fallback: bytes) -> bytes:
    if path.exists():
        return path.read_bytes()
    return fallback


def _delete_openai_file(file_id: str) -> None:
    from openai import OpenAI

    OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL") or None,
    ).files.delete(file_id)


def _delete_gigachat_file(file_id: str) -> None:
    from gigachat import GigaChat

    GigaChat(
        credentials=os.getenv("GIGACHAT_AUTH_TOKEN"),
        base_url=os.getenv("GIGACHAT_BASE_URL") or None,
        verify_ssl_certs=False,
    ).delete_file(file_id)


def test_openai_uploads_image_and_text_attachments() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY is not configured")

    from app.core.graph.attachments import _upload_to_openai

    uploaded_ids: list[str] = []
    try:
        image_id = _upload_to_openai(
            content=_read_sample(_IMAGE_SAMPLE, _TINY_PNG_BYTES),
            filename=_IMAGE_SAMPLE.name,
            content_type="image/png",
            base_url=os.getenv("OPENAI_BASE_URL") or None,
        )
        assert image_id
        uploaded_ids.append(image_id)

        text_id = _upload_to_openai(
            content=_read_sample(_TEXT_SAMPLE, b"hello from integration test\n"),
            filename=_TEXT_SAMPLE.name,
            content_type="text/plain",
            base_url=os.getenv("OPENAI_BASE_URL") or None,
        )
        assert text_id
        uploaded_ids.append(text_id)
    finally:
        for file_id in uploaded_ids:
            _delete_openai_file(file_id)


def test_gigachat_uploads_image_and_text_attachments() -> None:
    if not os.getenv("GIGACHAT_AUTH_TOKEN"):
        pytest.skip("GIGACHAT_AUTH_TOKEN is not configured")

    from app.core.graph.attachments import _upload_to_gigachat

    uploaded_ids: list[str] = []
    try:
        image_id = _upload_to_gigachat(
            content=_read_sample(_IMAGE_SAMPLE, _TINY_PNG_BYTES),
            filename=_IMAGE_SAMPLE.name,
            content_type="image/png",
            base_url=os.getenv("GIGACHAT_BASE_URL") or None,
        )
        assert image_id
        uploaded_ids.append(image_id)

        text_id = _upload_to_gigachat(
            content=_read_sample(_TEXT_SAMPLE, b"hello from integration test\n"),
            filename=_TEXT_SAMPLE.name,
            content_type="text/plain",
            base_url=os.getenv("GIGACHAT_BASE_URL") or None,
        )
        assert text_id
        uploaded_ids.append(text_id)
    finally:
        for file_id in uploaded_ids:
            _delete_gigachat_file(file_id)
