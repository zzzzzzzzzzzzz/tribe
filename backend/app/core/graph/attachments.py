import base64
import os
from collections.abc import Iterable
from typing import Literal

from gigachat import GigaChat
from openai import OpenAI

from app.models import ChatContentFilePart, ChatContentImagePart, ChatMessage, Member

ProviderName = Literal["openai", "gigachat"]


def _parse_data_url(data_url: str) -> tuple[str, bytes] | None:
    if not data_url.startswith("data:"):
        return None
    try:
        metadata, payload = data_url.split(",", 1)
    except ValueError:
        return None

    if ";base64" not in metadata:
        return None

    mime_type = metadata.split(":", 1)[1].split(";", 1)[0]
    try:
        decoded = base64.b64decode(payload, validate=True)
    except Exception:
        return None
    return mime_type, decoded


def _upload_to_openai(
    *, content: bytes, filename: str, base_url: str | None
) -> str | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    client = OpenAI(api_key=api_key, base_url=base_url)
    uploaded = client.files.create(file=(filename, content), purpose="vision")
    return uploaded.id


def _upload_to_gigachat(
    *, content: bytes, filename: str, base_url: str | None
) -> str | None:
    token = os.getenv("GIGACHAT_AUTH_TOKEN")
    if not token:
        return None

    client = GigaChat(
        credentials=token,
        base_url=base_url,
        verify_ssl_certs=False,
    )
    uploaded = client.upload_file((filename, content), purpose="general")
    return getattr(uploaded, "id_", None) or getattr(uploaded, "id", None)


def _target_provider_configs(
    members: Iterable[Member],
) -> set[tuple[ProviderName, str | None]]:
    targets: set[tuple[ProviderName, str | None]] = set()
    for member in members:
        if member.provider == "openai":
            targets.add(("openai", member.base_url))
        if member.provider == "gigachat":
            targets.add(("gigachat", member.base_url))
    return targets


def upload_attachments_for_thread(
    *, message: ChatMessage, members: list[Member]
) -> ChatMessage:
    if isinstance(message.content, str):
        return message

    provider_targets = _target_provider_configs(members)
    if not provider_targets:
        return message

    for part in message.content:
        file_data: str | None = None
        filename = "attachment.bin"

        if isinstance(part, ChatContentFilePart):
            if isinstance(part.file.filename, str) and part.file.filename:
                filename = part.file.filename
            file_data = part.file.file_data
            provider_ids = part.file.provider_file_ids or {}
        elif isinstance(part, ChatContentImagePart):
            file_data = part.image_url.url
            provider_ids = part.image_url.provider_file_ids or {}
            filename = "image.png"
        else:
            continue

        if isinstance(part, ChatContentFilePart):
            part.file.provider_file_ids = provider_ids
        elif isinstance(part, ChatContentImagePart):
            part.image_url.provider_file_ids = provider_ids

        if not isinstance(file_data, str):
            continue

        parsed = _parse_data_url(file_data)
        if not parsed:
            continue
        _, content = parsed

        for provider_name, provider_base_url in provider_targets:
            if provider_name in provider_ids:
                continue

            remote_id: str | None = None
            if provider_name == "openai":
                remote_id = _upload_to_openai(
                    content=content,
                    filename=filename,
                    base_url=provider_base_url,
                )
            elif provider_name == "gigachat":
                remote_id = _upload_to_gigachat(
                    content=content,
                    filename=filename,
                    base_url=provider_base_url,
                )

            if not remote_id:
                continue

            provider_ids[provider_name] = remote_id
            if isinstance(part, ChatContentFilePart):
                part.file.provider_file_ids = provider_ids
                if provider_name == "openai":
                    part.file.file_id = remote_id
            elif isinstance(part, ChatContentImagePart):
                part.image_url.provider_file_ids = provider_ids

    return message
